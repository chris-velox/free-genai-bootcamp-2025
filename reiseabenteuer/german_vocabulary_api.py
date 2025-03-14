from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import os
import random

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
    english_translations: List[str]
    part_of_speech: str
    cefr_level: str
    frequency: Optional[float] = None
    
    # Noun-specific fields
    gender: Optional[str] = None
    cases: Optional[dict] = None
    no_article: Optional[bool] = None
    singular_only: Optional[bool] = None
    plural_only: Optional[bool] = None
    
    # Verb-specific fields
    separable: Optional[bool] = None
    present: Optional[dict] = None
    simple: Optional[dict] = None
    perfect: Optional[str] = None
    conjunctive1: Optional[dict] = None
    conjunctive2: Optional[dict] = None
    imperative: Optional[dict] = None
    gerund: Optional[str] = None
    zuinfinitive: Optional[str] = None
    
    # Adjective-specific fields
    predicative_only: Optional[bool] = None
    absolute: Optional[bool] = None
    not_declinable: Optional[bool] = None
    no_mixed: Optional[bool] = None
    strong: Optional[dict] = None
    weak: Optional[dict] = None
    mixed: Optional[dict] = None
    is_comparative: Optional[bool] = None
    is_superlative: Optional[bool] = None
    superlative_only: Optional[bool] = None
    no_comparative: Optional[bool] = None
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
    """Get random vocabulary words from the vector database"""
    if not qdrant_client or not model:
        raise HTTPException(
            status_code=503,
            detail="Vocabulary database is not available"
        )

    # Validate input parameters
    valid_cefr_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    valid_parts_of_speech = ['noun', 'verb', 'adjective']
    
    cefr_level = cefr_level.upper()
    part_of_speech = part_of_speech.lower()
    
    if cefr_level not in valid_cefr_levels:
        raise HTTPException(status_code=400, detail="Invalid CEFR level")
    if part_of_speech not in valid_parts_of_speech:
        raise HTTPException(status_code=400, detail="Invalid part of speech")

    try:
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
        
        # Get all matching words first
        all_results = []
        offset = None
        while True:
            batch, offset = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=search_filter,
                limit=100,  # Fetch in batches of 100
                offset=offset
            )
            all_results.extend(batch)
            if not offset:  # No more results
                break
        
        if not all_results:
            raise HTTPException(
                status_code=404,
                detail=f"No vocabulary words found for {part_of_speech}s at {cefr_level} level"
            )

        # Randomly select the requested number of words
        selected_results = random.sample(all_results, min(limit, len(all_results)))

        # Convert results to VocabularyWord objects
        vocabulary_words = []
        for hit in selected_results:
            word_data = hit.payload
            
            # Create base word object with all fields
            word = {
                'german_word': word_data['german_word'],
                'english_word': word_data['english_word'],
                'english_translations': word_data.get('english_translations', []),
                'part_of_speech': word_data['part_of_speech'],
                'cefr_level': word_data['cefr_level'],
                'frequency': word_data.get('frequency')
            }
            
            # Add type-specific fields
            if word_data['part_of_speech'] == 'noun':
                word.update({
                    'gender': word_data.get('gender'),
                    'cases': word_data.get('cases'),
                    'no_article': word_data.get('no_article'),
                    'singular_only': word_data.get('singular_only'),
                    'plural_only': word_data.get('plural_only')
                })
            elif word_data['part_of_speech'] == 'verb':
                word.update({
                    'separable': word_data.get('separable'),
                    'present': word_data.get('present'),
                    'simple': word_data.get('simple'),
                    'perfect': word_data.get('perfect'),
                    'conjunctive1': word_data.get('conjunctive1'),
                    'conjunctive2': word_data.get('conjunctive2'),
                    'imperative': word_data.get('imperative'),
                    'gerund': word_data.get('gerund'),
                    'zuinfinitive': word_data.get('zuinfinitive')
                })
            elif word_data['part_of_speech'] == 'adjective':
                word.update({
                    'predicative_only': word_data.get('predicative_only'),
                    'absolute': word_data.get('absolute'),
                    'not_declinable': word_data.get('not_declinable'),
                    'no_mixed': word_data.get('no_mixed'),
                    'strong': word_data.get('strong'),
                    'weak': word_data.get('weak'),
                    'mixed': word_data.get('mixed'),
                    'is_comparative': word_data.get('is_comparative'),
                    'is_superlative': word_data.get('is_superlative'),
                    'superlative_only': word_data.get('superlative_only'),
                    'no_comparative': word_data.get('no_comparative'),
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