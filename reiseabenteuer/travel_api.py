from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
from destinations import (
    Destination,
    get_destinations_for_activities,
    find_similar_destinations,
    vector_storage_available
)

app = FastAPI(
    title="Deutsche Reiseempfehlungen API",
    description="API für Reiseziele in Deutschland basierend auf Aktivitäten"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActivityRequest(BaseModel):
    activities: List[str]

class SimilarDestinationRequest(BaseModel):
    description: str
    limit: int = 5

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

@app.post("/similar-destinations")
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 