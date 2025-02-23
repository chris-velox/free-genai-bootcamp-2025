import groq
import streamlit as st
from typing import Optional, Dict, Any, List
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
            1: """You are an expert at extracting questions and answers from German A2 level language learning transcripts.
            Your goal is to identify all questions and their corresponding conversations from the provided transcript section.
            Each question is marked by a "Nummer #" German designator (e.g., "Nummer eins", "Nummer 1", "Nummer 2").
            The conversation follows the question number.

            Ignore any "[Applaus] [Musik]" literal text.

            Identify each question number and its corresponding conversation. Format each as follows:

            <question>
                <number>[Nummer #]</number>
                <conversation>[the conversation in German]</conversation>
            </question>

            For example:

            <question>
                <number>Nummer 1</number>
                <conversation>Sprecher: Was ist dein Hobby? Teilnehmer: Ich spiele gern Fußball.</conversation>
            </question>

            Now extract all questions and conversations from the following transcript section.
            """,
            2: """You are an expert at extracting questions and answers from German A2 level language learning transcripts.
            Your goal is to identify all questions and their corresponding conversations from the provided transcript section.
            Each question is marked by a "Nummer #" designator (e.g., "Nummer 1", "Nummer 1", "Nummer 2").
            The conversation follows the question number.

            Ignore any "[Applaus] [Musik]" literal text.

            Identify each question number and its corresponding conversation. Format each as follows:

            <question>
                <number>[Nummer #]</number>
                <conversation>[the conversation in German]</conversation>
            </question>

            For example:

            <question>
                <number>Nummer 1</number>
                <conversation>Sprecher: Was ist dein Hobby? Teilnehmer: Ich spiele gern Fußball.</conversation>
            </question>

            Now extract all questions and conversations from the following transcript section.
            """,
            3: """You are an expert at extracting questions and answers from German A2 level language learning transcripts.
            Your goal is to identify all questions and their corresponding conversations from the provided transcript section.
            This section uses the same question format as Section 1.
            Each question is marked by a "Nummer #" designator (e.g., "Nummer eins", "Nummer 1", "Nummer 2").
            The conversation follows the question number.

            Ignore any "[Applaus] [Musik]" literal text.

            Identify each question number and its corresponding conversation. Format each as follows:

            <question>
                <number>[Nummer #]</number>
                <conversation>[the conversation in German]</conversation>
            </question>

            For example:

            <question>
                <number>Nummer 1</number>
                <conversation>Sprecher: Was ist dein Hobby? Teilnehmer: Ich spiele gern Fußball.</conversation>
            </question>

            Now extract all questions and conversations from the following transcript section.
            """
        }
        try:
            # Get API key from environment variable
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
                
            # Initialize Groq client with API key
            self.client = groq.Groq(api_key=api_key)
            self.model_id = model_id
        except Exception as e:
            st.error(f"""Groq API key not found. Please ensure:
            1. You have a .env file with GROQ_API_KEY=your_key OR
            2. You have set the GROQ_API_KEY environment variable
            
            Error: {str(e)}""")
            raise

    def _invoke_bedrock(self, prompt: str, transcript: str) -> Optional[str]:
        """Invokes the Groq model with the given prompt and transcript."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt + "\n\n" + transcript
                }
            ]
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model_id,
                temperature=0.0,
                stream=False,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error invoking Bedrock: {str(e)}")
            return None

    def structure_transcript(self, transcript: str) -> Dict[str, List[Dict[str, str]]]:
        """Structure the transcript into three sections using separate prompts"""
        results = {}
        for section_num in range(1, 4):
            # Find the start of the section
            section_header = f"Teil {section_num}"
            start_index = transcript.find(section_header)
            if start_index != -1:
                # Extract the section text
                section_text = transcript[start_index:]
                result = self._invoke_bedrock(self.prompts[section_num], section_text)
                if result:
                    # Parse the structured data from the result
                    structured_data = self._parse_structured_data(result)
                    results[f"Teil {section_num}"] = structured_data
        return results

    def _parse_structured_data(self, text: str) -> List[Dict[str, str]]:
        """Parse the structured data from the model's output."""
        questions = []
        question_tags = re.findall(r'<question>(.*?)</question>', text, re.DOTALL)
        for question_tag in question_tags:
            number_match = re.search(r'<number>(.*?)</number>', question_tag)
            conversation_match = re.search(r'<conversation>(.*?)</conversation>', question_tag)

            if number_match and conversation_match:
                number = number_match.group(1).strip()
                conversation = conversation_match.group(1).strip()
                questions.append({
                    "number": number,
                    "conversation": conversation
                })
        return questions

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load transcript from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None

    def save_structured_data(self, data: Dict[str, List[Dict[str, str]]], transcript_filename: str):
        """Save the structured data to a JSON file in the 'structured' folder
        with the same name as the transcript file.
        """
        try:
            # Extract the base filename from the transcript path
            base_filename = os.path.splitext(os.path.basename(transcript_filename))[0]

            # Define the output directory
            output_dir = "structured"

            # Create the output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Create the output filename
            output_filename = os.path.join(output_dir, f"{base_filename}.json")

            with open(output_filename, 'w', encoding='utf-8') as f:
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
      structured_data = structurer.structure_transcript(transcript)
      structurer.save_structured_data(structured_data, transcript_filename)

