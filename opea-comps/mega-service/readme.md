# Second attempt at a MegaService

I want to just do a chat with an LLM with guardrails in front.

## First attempt failed miserably

I tried to do too much too soon. I went back to a basic chat.py file.

```python
import json
import os
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

class ChatTemplate:
    @staticmethod
    def generate_rag_prompt(question, documents):
        context_str = "\n".join(documents)
        template = """
        ### You are a helpful, respectful and honest assistant to help the user with questions. \
        Please refer to the search results obtained from the local knowledge base. \
        But be careful to not incorporate the information that you think is not relevant to the question. \
        If you don't know the answer to a question, please don't share false information. \n
        ### Search results: {context} \n
        ### Question: {question} \n
        ### Answer:
        """
        return template.format(context=context_str, question=question)        

GUARDRAIL_SERVICE_HOST_IP = os.getenv("GUARDRAIL_SERVICE_HOST_IP", "0.0.0.0")
GUARDRAIL_SERVICE_PORT = int(os.getenv("GUARDRAIL_SERVICE_PORT", 80))
LLM_SERVER_HOST_IP = os.getenv("LLM_SERVER_HOST_IP", "0.0.0.0")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 11434))
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma:2b")

class ChatService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()
        self.endpoint = str(MegaServiceEndpoint.CHAT)
        print(f"ChatService init: {self.host}:{self.port}")
        print(f"Endpoint: {self.endpoint}")

    def add_remote_service(self):
        llm = MicroService(
            name="llm",
            host=LLM_SERVER_HOST_IP,
            port=LLM_SERVER_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(llm)
        print(f"Added LLM service with host={LLM_SERVER_HOST_IP}, port={LLM_SERVER_PORT}")

    async def handle_request(self, request: Request):
        print('handle_request')

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])

        self.service.start()


if __name__ == "__main__":

    chat = ChatService(port=MEGA_SERVICE_PORT)
    chat.add_remote_service()

    chat.start()
```

And a basic docker-compose.yaml

```yaml
services:
  ollama-service:
    image: ollama/ollama
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama:/root/.ollama
    entrypoint: ["bash", "-c"]
    command: ["ollama serve & sleep 10 && ollama run ${OLLAMA_MODEL} & wait"]
    environment:
      no_proxy: ${no_proxy}
      https_proxy: ${https_proxy}
      OLLAMA_MODEL: ${OLLAMA_MODEL}

volumes:
  ollama:

networks:
  default:
    driver: bridge
```

Use this command to see if things are working

```sh
curl http://localhost:8888/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "What is the revenue of Nike in 2023?"
    }'
```

Returns `null%`, so I'm thinking the model isn't actually loaded into the ollama-server container yet.

I had to load the model with

```sh
curl --noproxy "*" http://localhost:11434/api/pull -d '{
  "model": "gemma:2b"
}'
```

## Key Modifications in chat.py

1. `parse_obj(data)` has to be changed to `model_validate(data)`
1. In `def align_inputs` we have to change `next_inputs["messages"] = [{"role": "user", "content": inputs["inputs"]}]` to `next_inputs["messages"] = [{"role": "user", "content": inputs["text"]}]`

## Dockerfile for chat.py

https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/Dockerfile.guardrails

Needed to change Dockerfile to replacy all `chatqna.py` references to `chat.py`

Build the docker image for chat.py

`docker build -t chat:latest .`

