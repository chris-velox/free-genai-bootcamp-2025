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
from fastapi import APIRouter, HTTPException

# Define path for local storage
QDRANT_PATH = "./qdrant_storage/destinations"

# Initialize Qdrant client and sentence transformer
qdrant_client = None
encoder = None
COLLECTION_NAME = "destinations"

# Add these models and router
router = APIRouter()

class Destination(BaseModel):
    destination_name: str
    state: str
    activities: List[str]
    description: str

class ActivityRequest(BaseModel):
    activities: List[str]

class SimilarDestinationRequest(BaseModel):
    description: str
    limit: int = 5

def init_services():
    """Initialize Qdrant client and create collection"""
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
    
    # Common German cities to help validate locations
    known_cities = {
        "Berlin", "Hamburg", "München", "Munich", "Köln", "Cologne", "Frankfurt",
        "Stuttgart", "Düsseldorf", "Leipzig", "Dresden", "Hannover", "Nuremberg",
        "Nürnberg", "Heidelberg", "Rothenburg", "Freiburg", "Würzburg", "Potsdam"
    }
    
    # Words that indicate we're dealing with a location
    location_indicators = [
        "city", "town", "Stadt", "village", "Dorf", "visit", "besuchen",
        "located in", "situated in", "liegt in", "befindet sich in"
    ]
    
    # Pattern to find locations followed by state references
    location_patterns = [
        r'(?:in|at|near|visit|Stadt|Dorf)\s+([A-Z][a-zäöüß\s-]+)(?:\s+in\s+([A-Z][a-zäöüß\s-]+))?',
        r'([A-Z][a-zäöüß\s-]+)(?:\s*,\s*([A-Z][a-zäöüß\s-]+))',
        r'(?:Die|Der|Das)\s+([A-Z][a-zäöüß\s-]+)(?:\s+in\s+([A-Z][a-zäöüß\s-]+))?'
    ]
    
    locations = []
    seen_locations = set()
    
    # Split text into sentences for better context
    sentences = text.split('.')
    
    for sentence in sentences:
        # Skip if sentence doesn't contain any location indicators
        if not any(indicator in sentence.lower() for indicator in location_indicators):
            continue
            
        for pattern in location_patterns:
            matches = re.finditer(pattern, sentence)
            for match in matches:
                location = match.group(1).strip()
                state = match.group(2).strip() if match.group(2) else "Unknown"
                
                # Skip if we've seen this location or if it's actually a state name
                if (location.lower() in seen_locations or 
                    location in german_states or 
                    len(location) < 3):
                    continue
                
                # Skip common words that might be mistaken for locations
                if any(word in location.lower() for word in ["website", "article", "guide", "blog", "tips", "best"]):
                    continue
                
                # Validate that it's likely a real location
                is_valid = False
                if location in known_cities:
                    is_valid = True
                elif any(indicator in sentence.lower() for indicator in location_indicators):
                    is_valid = True
                
                if not is_valid:
                    continue
                
                # Verify state is actually a German state, otherwise try to find it in context
                if state not in german_states:
                    for german_state in german_states:
                        if german_state in text[:text.find(location) + 200]:
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
            f"where to {activities[0]} in Germany",
            f"recommended German cities for {', '.join(activities)}",
            f"popular {activities[0]} locations Germany",
            f"Germany tourism {', '.join(activities)}",
            # Add more specific queries
            "top tourist cities Germany",
            "most visited places Germany",
            "best German cities to visit",
            "popular German tourist destinations"
        ]
        
        for search_query in search_queries:
            if len(destinations) >= 5:
                break
                
            try:
                results = list(ddgs.text(
                    search_query,
                    region='de-de',
                    max_results=10  # Increased to get more potential results
                ))
                
                if not results:
                    continue
                
                for result in results:
                    if len(destinations) >= 5:
                        break
                        
                    # Get text from both URL and body
                    article_text = extract_text_from_url(result.get('link', ''))
                    if not article_text:
                        article_text = result.get('body', '')
                    if not article_text:
                        continue
                    
                    # Add the title to improve location finding
                    if result.get('title'):
                        article_text = result['title'] + ". " + article_text
                    
                    locations = find_german_locations(article_text)
                    
                    for location in locations:
                        if len(destinations) >= 5:
                            break
                            
                        if location['destination_name'].lower() in seen_places:
                            continue
                        
                        # Skip very short location names or likely false positives
                        if len(location['destination_name']) < 3 or location['destination_name'] in ['Germany', 'Deutschland']:
                            continue
                        
                        # Get description
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
                
            except Exception as e:
                print(f"Error during search with query '{search_query}': {str(e)}")
                continue
    
    # If we still don't have enough destinations, add some popular German cities
    default_cities = [
        {"destination_name": "Berlin", "state": "Berlin"},
        {"destination_name": "Munich", "state": "Bayern"},
        {"destination_name": "Hamburg", "state": "Hamburg"},
        {"destination_name": "Frankfurt", "state": "Hessen"},
        {"destination_name": "Cologne", "state": "Nordrhein-Westfalen"}
    ]
    
    for city in default_cities:
        if len(destinations) >= 5:
            break
        if city['destination_name'].lower() not in seen_places:
            description = f"Eine bedeutende deutsche Stadt, die sich gut für {', '.join(activities)} eignet."
            destinations.append({
                "destination_name": city['destination_name'],
                "state": city['state'],
                "activities": activities,
                "description": description
            })
            seen_places.add(city['destination_name'].lower())
    
    return destinations[:5]  # Ensure we return exactly 5 destinations

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

# Add these endpoints using the router
@router.post("", response_model=List[Destination])
async def get_destinations(request: ActivityRequest):
    if len(request.activities) > 3:
        raise HTTPException(
            status_code=400,
            detail="Maximum 3 activities allowed"
        )
    
    if len(request.activities) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one activity must be specified"
        )
    
    requested_activities = [activity.lower() for activity in request.activities]
    
    try:
        final_results = get_destinations_for_activities(requested_activities)
        
        if not final_results:
            raise HTTPException(
                status_code=404,
                detail="No destinations found for the specified activities"
            )
        
        return final_results
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for destinations: {str(e)}"
        )

@router.post("/similar", response_model=List[Destination])
async def similar_destinations(request: SimilarDestinationRequest):
    if not vector_storage_available:
        raise HTTPException(
            status_code=503,
            detail="Vector search functionality is currently unavailable"
        )
        
    try:
        results = find_similar_destinations(request.description, request.limit)
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail="No similar destinations found"
            )
            
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching similar destinations: {str(e)}"
        ) 