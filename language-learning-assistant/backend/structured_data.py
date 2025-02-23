import groq
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
import os
import json  # Import the json module
import re # Import the regular expression module
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model ID
MODEL_ID = "mixtral-8x7b-32768"  # Groq's Mixtral model

class TranscriptStructurer:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Groq client"""
        self.model_id = model_id
        self.prompts = {
            1: """You are an expert at creating multiple-choice questions from German A2 level language learning transcripts.
            Your goal is to create one question with four answer options for each conversation in the provided transcript section.
            Each question is marked by a "Nummer #" German designator (e.g., "Nummer eins", "Nummer 1", "Nummer 2").
            The conversation follows the question number.

            Ignore any "[Applaus] [Musik]" literal text.

            Include only conversations in this section for this section. Section 1 ends at Teil 2.
            For each conversation, create one question and four answer options (A, B, C, D).
            One of the options should be the correct answer, and the other three should be incorrect but plausible.

            Format each question and its options as follows:

            <question>
                <number>[Nummer #]</number>
                <conversation>[The conversation in German]</conversation>
                <text>[The question in German]</text>
                <optionA>[Option A in German]</optionA>
                <optionB>[Option B in German]</optionB>
                <optionC>[Option C in German]</optionC>
                <optionD>[Option D in German]</optionD>
                <correctOption>[A, B, C, or D]</correctOption>
            </question>

            For example:

            <question>
                <number>Nummer 1</number>
                <conversation>Sprecher: Was ist dein Hobby? Teilnehmer: Ich spiele gern Fußball.</conversation>
                <text>Was macht Peter in seiner Freizeit?</text>
                <optionA>Er spielt gern Fußball.</optionA>
                <optionB>Er liest ein Buch.</optionB>
                <optionC>Er geht ins Kino.</optionC>
                <optionD>Er lernt Deutsch.</optionD>
                <correctOption>A</correctOption>
            </question>

            Now create multiple-choice questions and answers for each conversation in the following transcript section.
            """,
            2: """You are an expert at creating true/false questions from German A2 level language learning transcripts.
            Your goal is to create one true/false question for each conversation in the provided transcript section.
            Each conversation is marked by a "Nummer #" designator (e.g., "Nummer eins", "Nummer 1", "Nummer 2").
            The conversation follows the question number.

            Ignore any "[Applaus] [Musik]" literal text.

            Include only conversations in this section for this section. Section 2 ends at Teil 3.
            For each conversation in this section, create one true/false question. Some questions should generate false as the answer.

            Format each question as follows:

            <question>
                <number>[Nummer #]</number>
                <conversation>[The conversation in German]</conversation>
                <text>[The question in German]</text>
                <answer>[True or False]</answer>
            </question>

            For example:

            <question>
                <number>Nummer 1</number>
                <conversation>Sprecher: Peter spielt gern Basketball. Teilnehmer: Das ist richtig.</conversation>
                <text>Peter spielt gern Basketball.</text>
                <answer>True</answer>
            </question>

            Now create true/false questions for each conversation in the following transcript section.
            """,
            3: """You are an expert at creating multiple-choice questions from German A2 level language learning transcripts.
            Your goal is to create one question with four answer options for each conversation in the provided transcript section.
            This section uses the same question format as Section 1.
            Each question is marked by a "Nummer #" German designator (e.g., "Nummer eins", "Nummer 1", "Nummer 2").
            The conversation follows the question number.

            Ignore any "[Applaus] [Musik]" literal text.

            Include only conversations in this section for this section. For each conversation, create one question and four answer options (A, B, C, D).
            One of the options should be the correct answer, and the other three should be incorrect but plausible.

            Format each question and its options as follows:

            <question>
                <number>[Nummer #]</number>
                <conversation>[The conversation in German]</conversation>
                <text>[The question in German]</text>
                <optionA>[Option A in German]</optionA>
                <optionB>[Option B in German]</optionB>
                <optionC>[Option C in German]</optionC>
                <optionD>[Option D in German]</optionD>
                <correctOption>[A, B, C, or D]</correctOption>
            </question>

            For example:

            <question>
                <number>Nummer 1</number>
                <conversation>Sprecher: Was ist dein Hobby? Teilnehmer: Ich spiele gern Fußball.</conversation>
                <text>Was macht Peter in seiner Freizeit?</text>
                <optionA>Er spielt gern Fußball.</optionA>
                <optionB>Er liest ein Buch.</optionB>
                <optionC>Er geht ins Kino.</optionC>
                <optionD>Er lernt Deutsch.</optionD>
                <correctOption>A</correctOption>
            </question>

            Now create multiple-choice questions and answers for each conversation in the following transcript section.
            """,
        }
        try:
            # Get API key from environment variable
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY not found in environment variables")

            # Initialize Groq client with API key
            self.client = groq.Groq(api_key=api_key)
            self.model_id = model_id
        except Exception as e:
            st.error(
                f"""Groq API key not found. Please ensure:
            1. You have a .env file with GROQ_API_KEY=your_key OR
            2. You have set the GROQ_API_KEY environment variable

            Error: {str(e)}"""
            )
            raise

    def _invoke_bedrock(self, prompt: str, transcript: str) -> Optional[str]:
        """Invokes the Groq model with the given prompt and transcript."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt + "\n\n" + transcript,
                }
            ]
            chat_completion = self.client.chat.completions.create(
                messages=messages, model=self.model_id, temperature=0.0, stream=False
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}")
            return None

    def structure_transcript(
        self, transcript: str
    ) -> Tuple[Dict[str, str], Dict[str, List[Dict[str, str]]]]:
        """Structure the transcript into three sections using separate prompts.

        Returns:
            A tuple containing:
            - A dictionary of the original transcript sections (Teil 1, Teil 2, Teil 3).
            - A dictionary of the structured data (questions, options, answers).
        """
        transcript_sections = {}  # Store the original transcript sections
        structured_data = {}  # Store the structured data

        for section_num in range(1, 4):
            # Find the start of the section
            section_header = f"Teil {section_num}"
            start_index = transcript.find(section_header)
            if start_index != -1:
                # Extract the section text
                section_text = transcript[start_index:]
                transcript_sections[f"Teil {section_num}"] = section_text  # Store the original section

                result = self._invoke_bedrock(
                    self.prompts[section_num], section_text)
                if result:
                    # Parse the structured data from the result
                    parsed_data = self._parse_structured_data(
                        result, section_num)
                    structured_data[f"Teil {section_num}"] = parsed_data

        return transcript_sections, structured_data

    def _parse_structured_data(self, text: str, section_num: int) -> List[Dict[str, str]]:
        """Parse the structured data from the model's output."""
        questions = []
        question_tags = re.findall(r"<question>(.*?)</question>", text, re.DOTALL)

        for question_tag in question_tags:
            number_match = re.search(r"<number>(.*?)</number>", question_tag)
            conversation_match = re.search(
                r"<conversation>(.*?)</conversation>", question_tag
            )

            if section_num in [1, 3]:
                text_match = re.search(r"<text>(.*?)</text>", question_tag)
                option_a_match = re.search(r"<optionA>(.*?)</optionA>", question_tag)
                option_b_match = re.search(r"<optionB>(.*?)</optionB>", question_tag)
                option_c_match = re.search(r"<optionC>(.*?)</optionC>", question_tag)
                option_d_match = re.search(r"<optionD>(.*?)</optionD>", question_tag)
                correct_option_match = re.search(
                    r"<correctOption>(.*?)</correctOption>", question_tag
                )

                if (
                    number_match
                    and conversation_match
                    and text_match
                    and option_a_match
                    and option_b_match
                    and option_c_match
                    and option_d_match
                    and correct_option_match
                ):
                    number = number_match.group(1).strip()
                    conversation = conversation_match.group(1).strip()
                    text = text_match.group(1).strip()
                    option_a = option_a_match.group(1).strip()
                    option_b = option_b_match.group(1).strip()
                    option_c = option_c_match.group(1).strip()
                    option_d = option_d_match.group(1).strip()
                    correct_option = correct_option_match.group(1).strip()

                    questions.append(
                        {
                            "number": number,
                            "conversation": conversation,
                            "text": text,
                            "optionA": option_a,
                            "optionB": option_b,
                            "optionC": option_c,
                            "optionD": option_d,
                            "correctOption": correct_option,
                        }
                    )
            elif section_num == 2:
                text_match = re.search(r"<text>(.*?)</text>", question_tag)
                answer_match = re.search(r"<answer>(.*?)</answer>", question_tag)
                conversation_match = re.search(
                    r"<conversation>(.*?)</conversation>", question_tag
                )

                if number_match and text_match and answer_match and conversation_match:
                    number = number_match.group(1).strip()
                    conversation = conversation_match.group(1).strip()
                    text = text_match.group(1).strip()
                    answer = answer_match.group(1).strip()

                    questions.append(
                        {
                            "number": number,
                            "conversation": conversation,
                            "text": text,
                            "answer": answer,
                        }
                    )

        return questions

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load transcript from a file"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None

    def save_structured_data(
        self, data: Dict[str, List[Dict[str, str]]], transcript_filename: str
    ):
        """Save the structured data to a JSON file in the 'structured' folder
        with the same name as the transcript file.
        """
        try:
            # Extract the base filename from the transcript path
            base_filename = os.path.splitext(
                os.path.basename(transcript_filename))[0]

            # Define the output directory
            output_dir = "structured"

            # Create the output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Create the output filename
            output_filename = os.path.join(
                output_dir, f"{base_filename}.json")

            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Structured data saved to {output_filename}")
        except Exception as e:
            print(f"Error saving structured data: {str(e)}")


# Example usage
if __name__ == "__main__":
    structurer = TranscriptStructurer()
    transcript_filename = "./transcripts/mLUTv35RigE.txt"
    transcript = structurer.load_transcript(transcript_filename)

    if transcript:
        transcript_sections, structured_data = structurer.structure_transcript(transcript)
        # structurer.save_structured_data(
        #     structured_data, transcript_filename)
        print("Transcript Sections:")
        print(transcript_sections)
        print("\nStructured Data:")
        print(structured_data)

