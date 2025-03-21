from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from destinations import router as destinations_router
from german_vocabulary_api import router as vocabulary_router
from pronunciation_api import router as pronunciation_router
from image_generation_api import router as image_router
import uvicorn

app = FastAPI(
    title="Deutsche Reise und Vokabeln API",
    description="API für Reiseziele in Deutschland und deutsche Vokabeln"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create pictures directory if it doesn't exist
pictures_dir = Path("./pictures")
pictures_dir.mkdir(exist_ok=True)

# Mount static files directory for serving images
app.mount("/pictures", StaticFiles(directory="pictures"), name="pictures")

# Include routes from both APIs
app.include_router(
    destinations_router,
    prefix="/destinations",
    tags=["destinations"]
)

app.include_router(
    vocabulary_router,
    prefix="/vocabulary",
    tags=["vocabulary"]
)

app.include_router(
    pronunciation_router,
    tags=["pronunciation"]
)

app.include_router(
    image_router,
    prefix="/images",
    tags=["images"]
)

@app.get("/")
async def root():
    return {"message": "German Learning API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 