from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.models import job, candidate
from app.api.v1.api import api_router  # <-- Add this import

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Resume Screener API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add this line to include all the routes we just built!
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "Backend is running and database is connected"}