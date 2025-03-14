import requests
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import json
import os
from enum import Enum
import time

# Update paths to match german_vocabulary_api.py
QDRANT_PATH = "./qdrant_storage/vocabulary"  # Changed to match german_vocabulary_api.py
collection_name = "german_vocabulary"

class WordType(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"

class Level(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

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
    """Fetch word data from GitHub"""
    # Try multiple possible URLs since the repository structure might change
    urls = [
        "https://raw.githubusercontent.com/Nordsword3m/German-Words/main/data/all.json",
        "https://raw.githubusercontent.com/Nordsword3m/German-Words/master/data/all.json",
        "https://raw.githubusercontent.com/Nordsword3m/German-Words/refs/heads/main/data/all.json"
    ]
    
    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"Successfully fetched data from {url}")
                return response.json()
        except Exception as e:
            print(f"Failed to fetch from {url}: {str(e)}")
            continue
    
    # If all URLs fail, try fetching individual files
    base_url = "https://raw.githubusercontent.com/Nordsword3m/German-Words/main/data"
    all_words = []
    
    try:
        file_index = 0
        while True:
            response = requests.get(f"{base_url}/{file_index}.json")
            if response.status_code != 200:
                break
                
            words = response.json()
            all_words.extend(words)
            print(f"Fetched {len(words)} words from {file_index}.json")
            file_index += 1
            
        if all_words:
            return all_words
            
    except Exception as e:
        print(f"Error fetching individual files: {str(e)}")
    
    raise Exception("Failed to fetch vocabulary data from all known sources")

def translate_with_ollama(german_word: str, context: str = "") -> str:
    """
    Translate German word to English using local Ollama server
    """
    API_URL = "http://localhost:11434/api/generate"
    
    # Construct prompt with context if available
    prompt = f"Translate the German word '{german_word}' to English."
    if context:
        prompt += f" Context: {context}"
    prompt += " Respond with only the English translation, no explanation."
    
    try:
        response = requests.post(
            API_URL,
            json={
                "model": "gemma2:2b",
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            translation = result.get('response', '').strip()
            # Remove quotes if present
            translation = translation.strip('"\'')
            print(f"✓ Generated translation for '{german_word}': '{translation}'")
            return translation
        else:
            print(f"× Failed to translate '{german_word}': HTTP {response.status_code}")
            return ""
            
    except Exception as e:
        print(f"× Error translating '{german_word}': {str(e)}")
        return ""

def process_word_data(word: Dict[str, Any]) -> Dict[str, Any] | None:
    """Process raw word data into the required format. Returns None if no English translation exists."""
    # Normalize level and type
    level = word.get("level", "").upper() if word.get("level") else None
    word_type = word.get("type", "").lower()
    
    # Get English translations safely
    translations = word.get("translations", {})
    english_translations = translations.get("en", [])
    
    # Skip words without English translations
    if not english_translations:
        return None
    
    english_word = english_translations[0]
    
    # Create the payload with normalized fields
    processed = {
        "german_word": word["lemma"],
        "lemma": word["lemma"],
        "part_of_speech": word_type,
        "type": word_type,
        "english_translations": english_translations,
        "english_word": english_word,
        "frequency": word.get("frequency", 0.0),
        "cefr_level": level,
        "level": level,
    }
    
    # Add type-specific attributes
    if word_type == WordType.NOUN.value:
        processed.update({
            "gender": word.get("gender"),
            "cases": word.get("cases", {}),
            "no_article": word.get("noArticle", False),
            "singular_only": word.get("singularOnly", False),
            "plural_only": word.get("pluralOnly", False)
        })
    
    elif word_type == WordType.VERB.value:
        processed.update({
            "separable": word.get("separable", False),
            "present": word.get("present", {}),
            "simple": word.get("simple", {}),
            "perfect": word.get("perfect"),
            "conjunctive1": word.get("conjunctive1", {}),
            "conjunctive2": word.get("conjunctive2", {}),
            "imperative": word.get("imperative", {}),
            "gerund": word.get("gerund"),
            "zuinfinitive": word.get("zuinfinitive")
        })
    
    elif word_type == WordType.ADJECTIVE.value:
        processed.update({
            "predicative_only": word.get("predicativeOnly", False),
            "singular_only": word.get("singularOnly", False),
            "plural_only": word.get("pluralOnly", False),
            "absolute": word.get("absolute", False),
            "not_declinable": word.get("notDeclinable", False),
            "no_mixed": word.get("noMixed", False),
            "strong": word.get("strong", {}),
            "weak": word.get("weak", {}),
            "mixed": word.get("mixed", {}),
            "is_comparative": word.get("isComparative", False),
            "is_superlative": word.get("isSuperlative", False),
            "superlative_only": word.get("superlativeOnly", False),
            "no_comparative": word.get("noComparative", False),
            "comparative": word.get("comparative"),
            "superlative": word.get("superlative")
        })

    return processed

def store_vocabulary_in_qdrant(client: QdrantClient, encoder: SentenceTransformer, words: List[Dict[str, Any]]):
    """Store processed vocabulary in Qdrant"""
    points = []
    
    for i, word in enumerate(words):
        # Create embedding from lemma and translations
        text_to_embed = f"{word['lemma']} {' '.join(word['english_translations'])}"
        if 'gender' in word:
            text_to_embed += f" {word['gender']}"
        
        # Add machine translation flag to embedding if applicable
        if word.get('machine_translated'):
            text_to_embed += " (MT)"
            
        embedding = encoder.encode(text_to_embed, convert_to_tensor=False)
        
        # Create unique ID based on word properties
        unique_id = hash(f"{word['lemma']}_{word.get('cefr_level', '')}_{word['type']}")
        
        # Create point
        point = PointStruct(
            id=unique_id,
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
        result 
        for word in raw_words 
        if word.get('type') in [t.value for t in WordType]
        and (result := process_word_data(word)) is not None  # Only include words with translations
    ]
    
    # Print statistics about skipped words
    total_words = len([w for w in raw_words if w.get('type') in [t.value for t in WordType]])
    skipped_words = total_words - len(processed_words)
    print(f"\nSkipped {skipped_words} words without English translations")
    
    # Group words by CEFR level for reporting
    words_by_level = {}
    for word in processed_words:
        level = word.get('level', 'unknown')
        words_by_level[level] = words_by_level.get(level, 0) + 1
    
    for level, count in words_by_level.items():
        print(f"Found {count} words for level {level.upper() if level else 'UNKNOWN'}")
    
    print(f"\nStoring {len(processed_words)} words in Qdrant...")
    store_vocabulary_in_qdrant(client, encoder, processed_words)
    
    print("\n✓ Vocabulary database initialization complete")

if __name__ == "__main__":
    main() 