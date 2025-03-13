import requests
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import json
import os
from enum import Enum

# Update paths to match german_vocabulary_api.py
QDRANT_PATH = "./qdrant_storage/vocabulary"  # Changed to match german_vocabulary_api.py
collection_name = "german_vocabulary"

class WordType(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"

class Level(str, Enum):
    A1 = "a1"
    A2 = "a2"
    B1 = "b1"
    B2 = "b2"
    C1 = "c1"
    C2 = "c2"

def init_qdrant():
    """Initialize Qdrant client and create collection"""
    os.makedirs(QDRANT_PATH, exist_ok=True)
    client = QdrantClient(path=QDRANT_PATH)
    encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=encoder.get_sentence_embedding_dimension(),
                distance=Distance.COSINE
            )
        )
        print("✓ Created new collection for vocabulary")
    except Exception as e:
        print(f"Collection initialization note: {str(e)}")
    
    return client, encoder

def fetch_word_data() -> List[Dict[str, Any]]:
    """Fetch word data from GitHub repository"""
    base_url = "https://raw.githubusercontent.com/Nordsword3m/German-Words/main/data"
    all_words = []
    
    try:
        # First try to get all.json which should contain all words
        response = requests.get(f"{base_url}/all.json")
        if response.status_code == 200:
            print("Successfully fetched all.json")
            return response.json()
        
        # If all.json fails, fetch individual numbered files
        print("Fetching individual word files...")
        file_index = 0
        while True:
            response = requests.get(f"{base_url}/{file_index}.json")
            if response.status_code != 200:
                break
                
            words = response.json()
            all_words.extend(words)
            print(f"Fetched {len(words)} words from {file_index}.json")
            file_index += 1
            
    except Exception as e:
        print(f"Error fetching word data: {str(e)}")
        return []
        
    return all_words

def process_word_data(word: Dict[str, Any]) -> Dict[str, Any]:
    """Process a word entry into our vocabulary format"""
    
    # Get English translation from translations
    english_translations = word.get('translations', {}).get('en', [])
    english_word = english_translations[0] if english_translations else ""
    
    # Get the word type
    word_type = word.get('type', '').lower()
    
    # Get additional info based on word type
    additional_info = {}
    if word_type == WordType.NOUN:
        additional_info = {
            'gender': word.get('gender'),
            'singular_only': word.get('singularOnly', False),
            'plural_only': word.get('pluralOnly', False)
        }
    elif word_type == WordType.VERB:
        additional_info = {
            'separable': word.get('separable', False),
            'perfect': word.get('perfect', ''),
            'gerund': word.get('gerund', '')
        }
    elif word_type == WordType.ADJECTIVE:
        additional_info = {
            'comparative': word.get('comparative', ''),
            'superlative': word.get('superlative', '')
        }
    
    # Create vocabulary entry
    vocab_entry = {
        'german_word': word['lemma'],
        'english_word': english_word,
        'part_of_speech': word_type,
        'cefr_level': word.get('level', '').lower(),
        'frequency': word.get('frequency', 0),
        **additional_info
    }
    
    return vocab_entry

def store_vocabulary_in_qdrant(client: QdrantClient, encoder: SentenceTransformer, words: List[Dict]):
    """Store vocabulary words in Qdrant"""
    points = []
    
    for word in words:
        # Create embedding from word data
        text_to_embed = f"{word['german_word']} {word['english_word']}"
        if 'gender' in word:
            text_to_embed += f" {word['gender']}"
        embedding = encoder.encode(text_to_embed)
        
        # Create point
        point = PointStruct(
            id=hash(f"{word['german_word']}_{word.get('cefr_level', '')}"),
            vector=embedding.tolist(),
            payload=word
        )
        points.append(point)
    
    # Upsert points in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=collection_name,
            points=batch
        )
        print(f"Stored batch of {len(batch)} words")

def main():
    # Initialize Qdrant
    client, encoder = init_qdrant()
    
    # Fetch word data
    print("\nFetching word data from GitHub...")
    raw_words = fetch_word_data()
    
    # Process words
    print("\nProcessing words...")
    processed_words = [
        process_word_data(word) 
        for word in raw_words 
        if word.get('type') in [t.value for t in WordType]
    ]
    
    # Group words by CEFR level for reporting
    words_by_level = {}
    for word in processed_words:
        level = word.get('cefr_level', 'unknown')
        words_by_level[level] = words_by_level.get(level, 0) + 1
    
    for level, count in words_by_level.items():
        print(f"Found {count} words for level {level.upper()}")
    
    print(f"\nStoring {len(processed_words)} words in Qdrant...")
    store_vocabulary_in_qdrant(client, encoder, processed_words)
    
    print("\n✓ Vocabulary database initialization complete")

if __name__ == "__main__":
    main() 