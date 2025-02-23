# Create GroqChat
# groq_chat.py
import groq
import streamlit as st
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model ID
MODEL_ID = "mixtral-8x7b-32768"  # Groq's Mixtral model



class GroqChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Groq chat client"""
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

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate a response using Groq"""
        if inference_config is None:
            inference_config = {"temperature": 0.7}

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": message}
                ],
                model=self.model_id,
                temperature=inference_config.get("temperature", 0.7)
            )
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")
            return None


if __name__ == "__main__":
    chat = GroqChat()
    while True:
        user_input = input("You: ")
        if user_input.lower() == '/exit':
            break
        response = chat.generate_response(user_input)
        print("Bot:", response)
