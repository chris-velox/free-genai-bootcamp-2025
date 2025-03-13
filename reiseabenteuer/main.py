from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from destinations import router as destinations_router
from german_vocabulary_api import router as vocabulary_router
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 