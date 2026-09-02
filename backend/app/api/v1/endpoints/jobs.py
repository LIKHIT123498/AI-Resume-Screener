from typing import List  # <-- Add this import
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=JobResponse)
def create_job(
    job_in: JobCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- THE SECURITY LOCK
):
    # Explicitly tying the new job to the logged-in user
    new_job = Job(
        title=job_in.title,
        department=job_in.department,
        description=job_in.description,
        requirements=job_in.requirements,
        role_type=job_in.role_type or "technical",
        user_id=current_user.id 
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

# --- NEW GET ENDPOINT ---
@router.get("/", response_model=List[JobResponse])
def get_user_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- THE SECURITY LOCK
):
    # Strictly filter jobs so the user only sees their own
    jobs = db.query(Job).filter(Job.user_id == current_user.id).all()
    return jobs
@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # <--- THE SECURITY LOCK
):
    # Verify the job exists AND belongs to the logged-in user
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    
    if not job:
        raise HTTPException(
            status_code=404, 
            detail="Job not found or you do not have permission to view it."
        )
        
    return job