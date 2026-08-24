from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.candidate import CandidateResponse # <-- Import the new schema

class JobCreate(BaseModel):
    title: str
    department: Optional[str] = None
    description: str
    requirements: str

class JobResponse(JobCreate):
    id: int
    created_at: datetime
    # Tell FastAPI to include the list of candidates in the response!
    candidates: List[CandidateResponse] = [] 

    class Config:
        from_attributes = True