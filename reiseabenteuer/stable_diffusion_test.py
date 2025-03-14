import os
from dotenv import load_dotenv
import requests
from pathlib import Path
import time

# Load environment variables
load_dotenv()
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

if not HUGGING_FACE_TOKEN:
    raise ValueError("Please set HUGGING_FACE_TOKEN in your .env file")

def generate_image(prompt):
    """
    Generate an image using Stable Diffusion 3.5 Medium model via Hugging Face API
    """
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}
    
    # Ensure output directory exists
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Make API request
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt}
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status code: {response.status_code}")
        
        # Generate unique filename using timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        output_path = output_dir / f"generated_image_{timestamp}.png"
        
        # Save the image
        with open(output_path, "wb") as f:
            f.write(response.content)
            
        print(f"Image generated successfully and saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None

def main():
    print("Stable Diffusion Image Generator")
    print("--------------------------------")
    prompt = input("Enter your image prompt: ")
    
    if prompt.strip():
        print("Generating image... (this may take a few moments)")
        generate_image(prompt)
    else:
        print("Please enter a valid prompt")

if __name__ == "__main__":
    main() 