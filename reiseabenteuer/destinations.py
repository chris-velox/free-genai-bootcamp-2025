from typing import List, Dict, Any
from pydantic import BaseModel
from duckduckgo_search import DDGS
import re
from deep_translator import GoogleTranslator
import trafilatura
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import os

# Define path for local storage
QDRANT_PATH = "./qdrant_storage"

# Initialize Qdrant client and sentence transformer
qdrant_client = None
encoder = None
COLLECTION_NAME = "destinations"

class Destination(BaseModel):
    destination_name: str
    state: str
    activities: List[str]
    description: str

def init_services():
    global qdrant_client, encoder
    try:
        os.makedirs(QDRANT_PATH, exist_ok=True)
        qdrant_client = QdrantClient(path=QDRANT_PATH)
        encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        try:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=encoder.get_sentence_embedding_dimension(),
                    distance=models.Distance.COSINE
                )
            )
        except Exception as e:
            print(f"Collection initialization note: {e}")
            
        print(f"✓ Qdrant initialized with local storage at {QDRANT_PATH}")
        return True
        
    except Exception as e:
        print(f"⚠️ Qdrant initialization failed: {e}")
        print("Application will run without vector storage functionality")
        qdrant_client = None
        encoder = None
        return False

# Initialize services
vector_storage_available = init_services()

def translate_to_german(text: str) -> str:
    translator = GoogleTranslator(source='en', target='de')
    return translator.translate(text)

def extract_text_from_url(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(downloaded)
        return text or ""
    except Exception:
        return ""

def find_german_locations(text: str) -> List[dict]:
    """Extract German locations and their states from text"""
    # Common German states for verification
    german_states = [
        "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
        "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
        "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen",
        "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
    ]
    
    # Pattern to find locations followed by state references
    location_patterns = [
        r'(?:in|at|near|visit)\s+([A-Z][a-zäöüß\s-]+)(?:\s+in\s+([A-Z][a-zäöüß\s-]+))?',
        r'([A-Z][a-zäöüß\s-]+)(?:\s*,\s*([A-Z][a-zäöüß\s-]+))?'
    ]
    
    locations = []
    seen_locations = set()
    
    for pattern in location_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            location = match.group(1).strip()
            state = match.group(2).strip() if match.group(2) else "Unknown"
            
            # Skip if we've seen this location or if it's actually a state name
            if (location.lower() in seen_locations or 
                location in german_states or 
                len(location) < 3):
                continue
            
            # Verify state is actually a German state, otherwise try to find it in context
            if state not in german_states:
                for german_state in german_states:
                    if german_state in text[:text.find(location) + 100]:
                        state = german_state
                        break
                else:
                    state = "Unknown"
            
            locations.append({
                "destination_name": location,
                "state": state
            })
            seen_locations.add(location.lower())
    
    return locations

def search_destinations(activities: List[str]) -> List[dict]:
    """Search for destinations using DuckDuckGo"""
    destinations = []
    seen_places = set()
    
    with DDGS() as ddgs:
        # Try different search queries to improve results
        search_queries = [
            f"{', '.join(activities)} top destinations Germany",
            f"best places in Germany for {', '.join(activities)}",
            f"where to {activities[0]} in Germany"
        ]
        
        for search_query in search_queries:
            try:
                results = list(ddgs.text(
                    search_query,
                    region='de-de',
                    max_results=3
                ))
                
                if not results:
                    continue
                
                for result in results:
                    url = result.get('link') or result.get('url')
                    if not url:
                        continue
                    
                    article_text = extract_text_from_url(url)
                    if not article_text:
                        article_text = result.get('body', '')
                    
                    if not article_text:
                        continue
                    
                    locations = find_german_locations(article_text)
                    
                    for location in locations:
                        if location['destination_name'].lower() in seen_places:
                            continue
                        
                        location_mention = article_text.find(location['destination_name'])
                        if location_mention != -1:
                            start = max(0, location_mention - 100)
                            end = min(len(article_text), location_mention + 200)
                            description = article_text[start:end].strip()
                        else:
                            description = result.get('body', '')[:200]
                        
                        if not description:
                            description = f"Ein beliebtes Reiseziel in {location['state']} für {', '.join(activities)}."
                        
                        try:
                            german_description = translate_to_german(description)
                        except Exception:
                            german_description = description
                        
                        destination = {
                            "destination_name": location['destination_name'],
                            "state": location['state'],
                            "activities": activities,
                            "description": german_description
                        }
                        
                        destinations.append(destination)
                        seen_places.add(location['destination_name'].lower())
                        
                        if len(destinations) >= 5:
                            return destinations
                
                if destinations:
                    return destinations
                    
            except Exception as e:
                print(f"Error during search with query '{search_query}': {str(e)}")
                continue
    
    return destinations

def store_destinations_in_qdrant(destinations: List[Dict[str, Any]]) -> None:
    """Store destinations in Qdrant with their embeddings"""
    if not vector_storage_available:
        return  # Silently skip if Qdrant is not available
        
    try:
        points = []
        
        for idx, destination in enumerate(destinations):
            # Create embedding from description
            description_vector = encoder.encode(destination['description'])
            
            # Create point
            point = models.PointStruct(
                id=hash(f"{destination['destination_name']}_{destination['state']}"),
                vector=description_vector.tolist(),
                payload={
                    "destination_name": destination['destination_name'],
                    "state": destination['state'],
                    "activities": destination['activities'],
                    "description": destination['description']
                }
            )
            points.append(point)
        
        # Upsert points to Qdrant
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
    except Exception as e:
        print(f"Warning: Failed to store destinations in vector database: {e}")

def search_vector_db(activities: List[str], limit: int = 5) -> List[dict]:
    """Search for destinations in vector database based on activities"""
    if not vector_storage_available:
        return []
        
    try:
        # Create a search query from activities
        query = f"Destination for {', '.join(activities)}"
        query_vector = encoder.encode(query)
        
        # Search in vector database
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector.tolist(),
            limit=limit
        )
        
        return [hit.payload for hit in search_result]
    except Exception as e:
        print(f"Vector search error: {e}")
        return []

def merge_and_rank_results(vector_results: List[dict], web_results: List[dict], 
                          activities: List[str], max_results: int = 5) -> List[dict]:
    """Merge and rank results from both sources"""
    all_results = []
    seen_destinations = set()
    
    # Helper function to calculate relevance score
    def calculate_relevance(destination: dict) -> float:
        score = 0.0
        dest_activities = set(a.lower() for a in destination['activities'])
        requested_activities = set(a.lower() for a in activities)
        
        # Activity match score
        activity_matches = len(dest_activities.intersection(requested_activities))
        score += activity_matches * 2.0
        
        # Known state bonus
        if destination['state'] != "Unknown":
            score += 0.5
            
        # Description length and quality score
        if len(destination['description']) > 100:
            score += 0.5
            
        return score
    
    # Process vector database results first (they're pre-existing and verified)
    for result in vector_results:
        dest_name = result['destination_name'].lower()
        if dest_name not in seen_destinations:
            result['source'] = 'vector_db'
            result['relevance_score'] = calculate_relevance(result)
            all_results.append(result)
            seen_destinations.add(dest_name)
    
    # Process web results
    for result in web_results:
        dest_name = result['destination_name'].lower()
        if dest_name not in seen_destinations:
            result['source'] = 'web_search'
            result['relevance_score'] = calculate_relevance(result)
            all_results.append(result)
            seen_destinations.add(dest_name)
    
    # Sort by relevance score
    ranked_results = sorted(all_results, 
                          key=lambda x: x['relevance_score'], 
                          reverse=True)
    
    # Remove the scoring fields before returning
    for result in ranked_results:
        result.pop('source', None)
        result.pop('relevance_score', None)
    
    return ranked_results[:max_results]

def get_destinations_for_activities(activities: List[str]) -> List[Dict[str, Any]]:
    """Main function to get destinations based on activities"""
    # Get results from both sources
    vector_results = search_vector_db(activities)
    web_results = search_destinations(activities)
    
    # Merge and rank results
    final_results = merge_and_rank_results(
        vector_results,
        web_results,
        activities
    )
    
    # Store results if vector DB is available
    if final_results and vector_storage_available:
        store_destinations_in_qdrant(final_results)
    
    return final_results

def find_similar_destinations(description: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Find similar destinations based on description"""
    if not vector_storage_available:
        return []
        
    query_vector = encoder.encode(description)
    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector.tolist(),
        limit=limit
    )
    
    return [hit.payload for hit in search_result] 