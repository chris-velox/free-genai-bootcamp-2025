import os
#import argparse
import json
import re

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import LLMParams, RerankerParms, RetrieverParms
from fastapi import Request
from fastapi.responses import StreamingResponse
from langchain_core.prompts import PromptTemplate

MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8888))
#EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
#EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 8008)
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma:2b")
GUARDRAIL_SERVICE_HOST_IP = os.getenv("GUARDRAIL_SERVICE_HOST_IP", "0.0.0.0")
GUARDRAIL_SERVICE_PORT = int(os.getenv("GUARDRAIL_SERVICE_PORT", 80))

def align_inputs(self, inputs, cur_node, runtime_graph, llm_parameters_dict, **kwargs):
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        inputs["inputs"] = inputs["text"]
        del inputs["text"]
    elif self.services[cur_node].service_type == ServiceType.RETRIEVER:
        # prepare the retriever params
        retriever_parameters = kwargs.get("retriever_parameters", None)
        if retriever_parameters:
            inputs.update(retriever_parameters.dict())
    elif self.services[cur_node].service_type == ServiceType.LLM:
        # convert TGI/vLLM to unified OpenAI /v1/chat/completions format
        next_inputs = {}
        next_inputs["model"] = LLM_MODEL
        next_inputs["messages"] = [{"role": "user", "content": inputs["inputs"]}]
        next_inputs["max_tokens"] = llm_parameters_dict["max_tokens"]
        next_inputs["top_p"] = llm_parameters_dict["top_p"]
        next_inputs["stream"] = inputs["stream"]
        next_inputs["frequency_penalty"] = inputs["frequency_penalty"]
        # next_inputs["presence_penalty"] = inputs["presence_penalty"]
        # next_inputs["repetition_penalty"] = inputs["repetition_penalty"]
        next_inputs["temperature"] = inputs["temperature"]
        inputs = next_inputs
    return inputs


def align_outputs(self, data, cur_node, inputs, runtime_graph, llm_parameters_dict, **kwargs):
    next_data = {}
    if self.services[cur_node].service_type == ServiceType.EMBEDDING:
        assert isinstance(data, list)
        next_data = {"text": inputs["inputs"], "embedding": data[0]}
    elif self.services[cur_node].service_type == ServiceType.RETRIEVER:

        docs = [doc["text"] for doc in data["retrieved_docs"]]

        with_rerank = runtime_graph.downstream(cur_node)[0].startswith("rerank")
        if with_rerank and docs:
            # forward to rerank
            # prepare inputs for rerank
            next_data["query"] = data["initial_query"]
            next_data["texts"] = [doc["text"] for doc in data["retrieved_docs"]]
        else:
            # forward to llm
            if not docs and with_rerank:
                # delete the rerank from retriever -> rerank -> llm
                for ds in reversed(runtime_graph.downstream(cur_node)):
                    for nds in runtime_graph.downstream(ds):
                        runtime_graph.add_edge(cur_node, nds)
                    runtime_graph.delete_node_if_exists(ds)

            # handle template
            # if user provides template, then format the prompt with it
            # otherwise, use the default template
            prompt = data["initial_query"]
            chat_template = llm_parameters_dict["chat_template"]
            if chat_template:
                prompt_template = PromptTemplate.from_template(chat_template)
                input_variables = prompt_template.input_variables
                if sorted(input_variables) == ["context", "question"]:
                    prompt = prompt_template.format(question=data["initial_query"], context="\n".join(docs))
                elif input_variables == ["question"]:
                    prompt = prompt_template.format(question=data["initial_query"])
                else:
                    print(f"{prompt_template} not used, we only support 2 input variables ['question', 'context']")
                    prompt = ChatTemplate.generate_rag_prompt(data["initial_query"], docs)
            else:
                prompt = ChatTemplate.generate_rag_prompt(data["initial_query"], docs)

            next_data["inputs"] = prompt

    elif self.services[cur_node].service_type == ServiceType.RERANK:
        # rerank the inputs with the scores
        reranker_parameters = kwargs.get("reranker_parameters", None)
        top_n = reranker_parameters.top_n if reranker_parameters else 1
        docs = inputs["texts"]
        reranked_docs = []
        for best_response in data[:top_n]:
            reranked_docs.append(docs[best_response["index"]])

        # handle template
        # if user provides template, then format the prompt with it
        # otherwise, use the default template
        prompt = inputs["query"]
        chat_template = llm_parameters_dict["chat_template"]
        if chat_template:
            prompt_template = PromptTemplate.from_template(chat_template)
            input_variables = prompt_template.input_variables
            if sorted(input_variables) == ["context", "question"]:
                prompt = prompt_template.format(question=prompt, context="\n".join(reranked_docs))
            elif input_variables == ["question"]:
                prompt = prompt_template.format(question=prompt)
            else:
                print(f"{prompt_template} not used, we only support 2 input variables ['question', 'context']")
                prompt = ChatTemplate.generate_rag_prompt(prompt, reranked_docs)
        else:
            prompt = ChatTemplate.generate_rag_prompt(prompt, reranked_docs)

        next_data["inputs"] = prompt

    elif self.services[cur_node].service_type == ServiceType.LLM and not llm_parameters_dict["stream"]:
        next_data["text"] = data["choices"][0]["message"]["content"]
    else:
        next_data = data

    return next_data


def align_generator(self, gen, **kwargs):
    # openai reaponse format
    # b'data:{"id":"","object":"text_completion","created":1725530204,"model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"2.0.1-native","choices":[{"index":0,"delta":{"role":"assistant","content":"?"},"logprobs":null,"finish_reason":null}]}\n\n'
    for line in gen:
        line = line.decode("utf-8")
        start = line.find("{")
        end = line.rfind("}") + 1

        json_str = line[start:end]
        try:
            # sometimes yield empty chunk, do a fallback here
            json_data = json.loads(json_str)
            if (
                json_data["choices"][0]["finish_reason"] != "eos_token"
                and "content" in json_data["choices"][0]["delta"]
            ):
                yield f"data: {repr(json_data['choices'][0]['delta']['content'].encode('utf-8'))}\n\n"
        except Exception as e:
            yield f"data: {repr(json_str.encode('utf-8'))}\n\n"
    yield "data: [DONE]\n\n"

#class ExampleService:
#    def __init__(self, host="0.0.0.0", port=8000):
#        self.host = host
#        self.port = port
#        self.megaservice = ServiceOrchestrator()
#
#    def add_remote_service(self):
#        embedding = MicroService(
#            name="embedding",
#            host=EMBEDDING_SERVICE_HOST_IP,
#            port=EMBEDDING_SERVICE_PORT,
#            endpoint="/v1/embeddings",
#            use_remote_service=True,
#            service_type=ServiceType.EMBEDDING,
#        )
#        llm = MicroService(
#            name="llm",
#            host=LLM_SERVICE_HOST_IP,
#            port=LLM_SERVICE_PORT,
#            endpoint="/v1/chat/completions",
#            use_remote_service=True,
#            service_type=ServiceType.LLM,
#        )
#        self.megaservice.add(embedding).add(llm)
#        self.megaservice.flow_to(embedding, llm)

class ChatService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        ServiceOrchestrator.align_generator = align_generator
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.CHAT)

    def add_remote_service(self):
#        guardrail_in = MicroService(
#            name="guardrail_in",
#            host=GUARDRAIL_SERVICE_HOST_IP,
#            port=GUARDRAIL_SERVICE_PORT,
#            endpoint="/v1/guardrails",
#            use_remote_service=True,
#            service_type=ServiceType.GUARDRAIL,
#        )

#        embedding = MicroService(
#            name="embedding",
#            host=EMBEDDING_SERVICE_HOST_IP,
#            port=EMBEDDING_SERVICE_PORT,
#            endpoint="/v1/embeddings",
#            use_remote_service=True,
#            service_type=ServiceType.EMBEDDING,
#        )

        llm = MicroService(
            name = "llm",
            host = LLM_SERVICE_HOST_IP,
            port = LLM_SERVICE_PORT,
            endpoint = "/v1/chat/completions",
            use_remote_service=True,
            service_role=ServiceType.LLM,
        )

#        guardrail_out = MicroService(
#            name="guardrail_out",
#            host=GUARDRAIL_SERVICE_HOST_IP,
#            port=GUARDRAIL_SERVICE_PORT,
#            endpoint="/v1/guardrails",
#            use_remote_service=True,
#            service_type=ServiceType.GUARDRAIL,
#        )

        #self.megaservice.add(guardrail_in).add(llm)
        #.add(guardrail_out)
        self.megaservice.add(llm)
        #self.megaservice.flow_to(guardrail_in, llm)
        #self.megaservice.flow_to(llm, guardrail_out)

    async def handle_request(self, request: Request):
        data = await request.json()
        stream_opt = data.get("stream", True)
        #chat_request = ChatCompletionRequest.parse_obj(data)
        chat_request = ChatCompletionRequest.model_validate(data)
        prompt = handle_message(chat_request.messages)
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=stream_opt,
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
        )
        #retriever_parameters = RetrieverParms(
        #    search_type=chat_request.search_type if chat_request.search_type else "similarity",
        #    k=chat_request.k if chat_request.k else 4,
        #    distance_threshold=chat_request.distance_threshold if chat_request.distance_threshold else None,
        #    fetch_k=chat_request.fetch_k if chat_request.fetch_k else 20,
        #    lambda_mult=chat_request.lambda_mult if chat_request.lambda_mult else 0.5,
        #    score_threshold=chat_request.score_threshold if chat_request.score_threshold else 0.2,
        #)
        #reranker_parameters = RerankerParms(
        #    top_n=chat_request.top_n if chat_request.top_n else 1,
        #)
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"text": prompt},
            llm_parameters=parameters,
            #retriever_parameters=retriever_parameters,
            #reranker_parameters=reranker_parameters,
        )
        for node, response in result_dict.items():
            if isinstance(response, StreamingResponse):
                return response
        last_node = runtime_graph.all_leaves()[-1]
        response = result_dict[last_node]["text"]
        choices = []
        usage = UsageInfo()
        choices.append(
            ChatCompletionResponseChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response),
                finish_reason="stop",
            )
        )
        return ChatCompletionResponse(model="chatqna", choices=choices, usage=usage)


    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role = ServiceRoleType.MEGASERVICE,
            host = self.host,
            port = self.port,
            endpoint = self.endpoint,
            input_datatype = ChatCompletionRequest,
            output_datatype = ChatCompletionResponse,
        )
 
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])

        self.service.start()

if __name__ == "__main__":
#    parser = argparse.ArgumentParser()
#    parser.add_argument("--without-rerank", action="store_true")
#    parser.add_argument("--with-guardrails", action="store_true")
#
#    args = parser.parse_args()

    chatqna = ChatService(port=MEGA_SERVICE_PORT)
#    if args.without_rerank:
#        chatqna.add_remote_service_without_rerank()
#    elif args.with_guardrails:
#        chatqna.add_remote_service_with_guardrails()
#    else:
    chatqna.add_remote_service()

    chatqna.start()
