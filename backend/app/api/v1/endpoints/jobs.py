from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse

router = APIRouter()

@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@router.get("/", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()