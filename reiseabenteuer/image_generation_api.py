from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel, validator
from pathlib import Path
import os
from dotenv import load_dotenv
import requests
import hashlib
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
HUGGING_FACE_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

if not HUGGING_FACE_TOKEN:
    logger.warning("HUGGING_FACE_TOKEN not set in .env file")

router = APIRouter()

# Valid values for validation
VALID_CEFR_LEVELS = {'A1', 'A2', 'B1', 'B2', 'C1', 'C2'}
VALID_PARTS_OF_SPEECH = {'noun', 'verb', 'adjective'}

class ImageRequest(BaseModel):
    phrase: str
    cefr_level: str
    part_of_speech: str
    force_regenerate: bool = False  # New field with default False

    @validator('phrase')
    def validate_phrase(cls, v):
        if not v.strip():
            raise ValueError('Phrase cannot be empty')
        return v.strip()

    @validator('cefr_level')
    def validate_cefr_level(cls, v):
        if v.upper() not in VALID_CEFR_LEVELS:
            raise ValueError(f'Invalid CEFR level. Must be one of: {", ".join(VALID_CEFR_LEVELS)}')
        return v.upper()

    @validator('part_of_speech')
    def validate_part_of_speech(cls, v):
        if v.lower() not in VALID_PARTS_OF_SPEECH:
            raise ValueError(f'Invalid part of speech. Must be one of: {", ".join(VALID_PARTS_OF_SPEECH)}')
        return v.lower()

class ImageResponse(BaseModel):
    image_path: str
    is_new: bool

def get_safe_filename(phrase: str) -> str:
    """Convert phrase to a safe filename using hash to ensure uniqueness"""
    # Create hash of the phrase to ensure unique filenames
    phrase_hash = hashlib.md5(phrase.encode()).hexdigest()[:8]
    # Create safe filename by removing special characters and adding hash
    safe_name = "".join(c if c.isalnum() else "_" for c in phrase.lower())
    return f"{safe_name}_{phrase_hash}"

def generate_image_prompt(phrase: str, part_of_speech: str) -> str:
    """Generate an appropriate prompt for the stable diffusion model"""
    base_prompt = f"'{phrase}', "
    # base_prompt += "suitable for all ages, "
    
    if part_of_speech == "noun":
        base_prompt += "focus on the object or subject, minimal background"
    elif part_of_speech == "verb":
        base_prompt += "showing the action being performed, dynamic pose"
    elif part_of_speech == "adjective":
        base_prompt += "emphasizing the descriptive quality"
    
    # base_prompt += ", 2D art style, clean lines, vibrant colors"
    return base_prompt

async def create_stable_diffusion_image(prompt: str, output_path: Path) -> bool:
    """Generate image using Stable Diffusion via Hugging Face API"""
    if not HUGGING_FACE_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="HUGGING_FACE_TOKEN not configured"
        )

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HUGGING_FACE_TOKEN}"}
    
    try:
        # Make API request with specific dimensions
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "inputs": prompt,
                "parameters": {
                    #"width": 296,
                    #"height": 296,
                    "negative_prompt": "nsfw, violence, gore, text, watermark",
                    # "guidance_scale": 7.5  # Increase adherence to prompt
                }
            }
        )
        
        if response.status_code == 503:
            raise HTTPException(
                status_code=503,
                detail="Model is currently loading. Please try again in a few minutes."
            )
        elif response.status_code != 200:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return False
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the image
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return False

@router.post("/generate_image", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """Generate or retrieve an image for the given phrase"""
    try:
        # Create base directory structure
        base_dir = Path("./pictures")
        cefr_dir = base_dir / request.cefr_level
        pos_dir = cefr_dir / request.part_of_speech
        
        # Generate safe filename
        safe_filename = get_safe_filename(request.phrase)
        image_path = pos_dir / f"{safe_filename}.jpg"
        
        # Check if image already exists and we're not forcing regeneration
        if image_path.exists() and not request.force_regenerate:
            logger.info(f"Using existing image for '{request.phrase}'")
            return ImageResponse(
                image_path=str(image_path),
                is_new=False
            )
        
        # Generate prompt for stable diffusion
        prompt = generate_image_prompt(request.phrase, request.part_of_speech)
        
        # Generate new image
        logger.info(f"{'Regenerating' if request.force_regenerate else 'Generating'} image for '{request.phrase}'")
        success = await create_stable_diffusion_image(prompt, image_path)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate image"
            )
        
        return ImageResponse(
            image_path=str(image_path),
            is_new=True
        )
        
    except Exception as e:
        logger.error(f"Error in generate_image: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error generating image: {str(e)}"
        ) 