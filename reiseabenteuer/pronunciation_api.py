from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import Optional
import numpy as np
import whisper
import base64
import tempfile
import os
import subprocess
import logging
import string
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Load Whisper model once at startup
try:
    model = whisper.load_model("tiny")
    print("✓ Loaded Whisper model")
except Exception as e:
    print(f"⚠️ Error loading Whisper model: {str(e)}")
    model = None

class PronunciationRequest(BaseModel):
    audio_data: str  # Base64 encoded audio data
    expected_text: str  # The text that should have been spoken

class PronunciationResponse(BaseModel):
    is_correct: bool
    transcribed_text: str
    confidence: float

def normalize_text(text: str) -> str:
    """Normalize text by removing punctuation, extra spaces, and converting to lowercase"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except for specific German characters
    # Keep äöüß and hyphens in compound words
    text = re.sub(r'[^\w\s\-äöüß]', '', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()

def convert_webm_to_wav(input_path: str, output_path: str) -> bool:
    """Convert WebM audio to WAV format using ffmpeg"""
    try:
        subprocess.run([
            'ffmpeg',
            '-i', input_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',  # Overwrite output file if it exists
            output_path
        ], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
        return False

@router.post("/check_recording", response_model=PronunciationResponse)
async def check_pronunciation(request: PronunciationRequest):
    """Check pronunciation using Whisper"""
    if not model:
        raise HTTPException(
            status_code=503,
            detail="Whisper model is not available"
        )

    try:
        # Create temporary directory for audio processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(request.audio_data)
            
            # Save original audio file (WebM)
            webm_path = os.path.join(temp_dir, "audio.webm")
            wav_path = os.path.join(temp_dir, "audio.wav")
            
            with open(webm_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Convert to WAV
            if not convert_webm_to_wav(webm_path, wav_path):
                raise Exception("Failed to convert audio format")

            # Load the audio file using whisper
            try:
                audio = whisper.load_audio(wav_path)
            except Exception as e:
                logger.error(f"Error loading audio with whisper: {str(e)}")
                raise

            # Transcribe using Whisper
            try:
                result = model.transcribe(
                    audio,
                    language="de",
                    fp16=False  # Force FP32 since we're on CPU
                )
            except Exception as e:
                logger.error(f"Error during transcription: {str(e)}")
                raise

            # Normalize both transcribed and expected text
            transcribed_text = normalize_text(result["text"])
            expected_text = normalize_text(request.expected_text)
            
            logger.info(f"Transcribed (normalized): '{transcribed_text}'")
            logger.info(f"Expected (normalized): '{expected_text}'")

            # Simple text matching for now
            is_correct = transcribed_text == expected_text
            
            return PronunciationResponse(
                is_correct=is_correct,
                transcribed_text=transcribed_text,
                confidence=result.get("confidence", 0.0)
            )

    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing audio: {str(e)}"
        ) 