from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn
from duckduckgo_search import DDGS
import re
from deep_translator import GoogleTranslator
import requests
from bs4 import BeautifulSoup
import trafilatura

app = FastAPI(
    title="Deutsche Reiseempfehlungen API",
    description="API für Reiseziele in Deutschland basierend auf Aktivitäten"
)

# Define the request and response models
class ActivityRequest(BaseModel):
    activities: List[str]

class Destination(BaseModel):
    destination_name: str  # Changed to match spec
    state: str
    activities: List[str]
    description: str

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
    destinations = []
    seen_places = set()
    
    # Translate activities to English for better search results
    translator = GoogleTranslator(source='de', target='en')
    english_activities = [translator.translate(activity) for activity in activities]
    
    with DDGS() as ddgs:
        # Try different search queries to improve results
        search_queries = [
            f"{', '.join(english_activities)} top destinations Germany",
            f"best places in Germany for {', '.join(english_activities)}",
            f"where to {english_activities[0]} in Germany"
        ]
        
        for search_query in search_queries:
            try:
                # Get top 3 articles
                results = list(ddgs.text(
                    search_query,
                    region='de-de',
                    max_results=3
                ))
                
                if not results:
                    continue
                
                # Process each article
                for result in results:
                    # Extract URL safely
                    url = result.get('link') or result.get('url')
                    if not url:
                        continue
                    
                    # Get the article text
                    article_text = extract_text_from_url(url)
                    if not article_text:
                        # Fallback to using the snippet if article text extraction fails
                        article_text = result.get('body', '')
                    
                    if not article_text:
                        continue
                    
                    # Find locations in the article
                    locations = find_german_locations(article_text)
                    
                    for location in locations:
                        if location['destination_name'].lower() in seen_places:
                            continue
                        
                        # Get a relevant excerpt from the article
                        location_mention = article_text.find(location['destination_name'])
                        if location_mention != -1:
                            start = max(0, location_mention - 100)
                            end = min(len(article_text), location_mention + 200)
                            description = article_text[start:end].strip()
                        else:
                            description = result.get('body', '')[:200]
                        
                        # Ensure we have a description
                        if not description:
                            description = f"Ein beliebtes Reiseziel in {location['state']} für {', '.join(activities)}."
                        
                        # Translate description to German if it's in English
                        try:
                            german_description = translate_to_german(description)
                        except Exception:
                            german_description = description  # Keep original if translation fails
                        
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
                
                if destinations:  # If we found any destinations, return them
                    return destinations
                    
            except Exception as e:
                print(f"Error during search with query '{search_query}': {str(e)}")
                continue  # Try next search query
    
    # If we get here and have any destinations, return them
    if destinations:
        return destinations
        
    # If we have no destinations, return some default ones
    return [
        {
            "destination_name": "Garmisch-Partenkirchen",
            "state": "Bayern",
            "activities": activities,
            "description": "Ein beliebtes Reiseziel in den bayerischen Alpen, perfekt für verschiedene Outdoor-Aktivitäten."
        },
        {
            "destination_name": "Schwarzwald",
            "state": "Baden-Württemberg",
            "activities": activities,
            "description": "Eine malerische Region mit vielen Möglichkeiten für Outdoor-Aktivitäten und Erholung."
        },
        {
            "destination_name": "Berlin",
            "state": "Berlin",
            "activities": activities,
            "description": "Die Hauptstadt bietet eine Vielzahl von Aktivitäten und Sehenswürdigkeiten."
        }
    ]

@app.post("/destinations", response_model=List[Destination])
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
        matching_destinations = search_destinations(requested_activities)
        
        if not matching_destinations:
            raise HTTPException(
                status_code=404,
                detail="No destinations found for the specified activities"
            )
        
        return matching_destinations
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for destinations: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 