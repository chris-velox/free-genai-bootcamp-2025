from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import os

# Update the Qdrant initialization constants
QDRANT_PATH = "./qdrant_storage/vocabulary"  # Changed path
collection_name = "german_vocabulary"  # This was already different

router = APIRouter()

# Initialize Qdrant client and encoder
try:
    qdrant_client = QdrantClient(path=QDRANT_PATH)
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("✓ Connected to vocabulary database")
except Exception as e:
    print(f"⚠️ Error connecting to vocabulary database: {str(e)}")
    qdrant_client = None
    model = None

class VocabularyWord(BaseModel):
    german_word: str
    english_word: str
    part_of_speech: str
    cefr_level: str
    gender: Optional[str] = None
    frequency: Optional[float] = None
    # Optional verb-specific fields
    separable: Optional[bool] = None
    perfect: Optional[str] = None
    gerund: Optional[str] = None
    # Optional adjective-specific fields
    comparative: Optional[str] = None
    superlative: Optional[str] = None

class VocabularyResponse(BaseModel):
    vocabulary_words: List[VocabularyWord]

@router.get("/words", response_model=VocabularyResponse)
async def get_vocabulary_words(
    cefr_level: str,
    part_of_speech: str,
    limit: int = 50
):
    """Get vocabulary words from the vector database"""
    if not qdrant_client or not model:
        raise HTTPException(
            status_code=503,
            detail="Vocabulary database is not available"
        )

    # Validate input parameters
    valid_cefr_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
    valid_parts_of_speech = ['noun', 'verb', 'adjective']
    
    cefr_level = cefr_level.lower()
    part_of_speech = part_of_speech.lower()
    
    if cefr_level not in valid_cefr_levels:
        raise HTTPException(status_code=400, detail="Invalid CEFR level")
    if part_of_speech not in valid_parts_of_speech:
        raise HTTPException(status_code=400, detail="Invalid part of speech")

    try:
        # Create search vector from request parameters
        search_text = f"German {part_of_speech} {cefr_level}"
        search_vector = model.encode(search_text)
        
        # Create filter using Qdrant models
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="cefr_level",
                    match=models.MatchValue(value=cefr_level)
                ),
                models.FieldCondition(
                    key="part_of_speech",
                    match=models.MatchValue(value=part_of_speech)
                )
            ]
        )
        
        # Search the vector database with proper filter model
        results = qdrant_client.search(
            collection_name=collection_name,
            query_vector=search_vector.tolist(),
            query_filter=search_filter,
            limit=limit
        )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"No vocabulary words found for {part_of_speech}s at {cefr_level} level"
            )

        # Convert results to VocabularyWord objects
        vocabulary_words = []
        for hit in results:
            word_data = hit.payload
            
            # Create base word object
            word = {
                'german_word': word_data['german_word'],
                'english_word': word_data['english_word'],
                'part_of_speech': word_data['part_of_speech'],
                'cefr_level': word_data['cefr_level'],
                'frequency': word_data.get('frequency')
            }
            
            # Add type-specific fields if they exist
            if word_data['part_of_speech'] == 'noun':
                word['gender'] = word_data.get('gender')
            elif word_data['part_of_speech'] == 'verb':
                word.update({
                    'separable': word_data.get('separable'),
                    'perfect': word_data.get('perfect'),
                    'gerund': word_data.get('gerund')
                })
            elif word_data['part_of_speech'] == 'adjective':
                word.update({
                    'comparative': word_data.get('comparative'),
                    'superlative': word_data.get('superlative')
                })
            
            vocabulary_words.append(VocabularyWord(**word))

        return VocabularyResponse(vocabulary_words=vocabulary_words)

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching vocabulary words: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Note: Using port 8001 to avoid conflict with main.py 