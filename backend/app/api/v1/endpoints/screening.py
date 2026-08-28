from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.services.parser import extract_text_from_file
from app.services.ai_engine import screen_resume
from app.models.user import User
from app.api.deps import get_current_user
from fastapi import HTTPException
router = APIRouter()

@router.post("/{job_id}/upload-resumes")
async def upload_and_screen_resumes(
    job_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    
    if not job:
        raise HTTPException(
            status_code=404, 
            detail="Job not found or you do not have permission to upload candidates here."
        )

    results = []
    for file in files:
        contents = await file.read()
        resume_text = extract_text_from_file(contents, file.filename)
        
        if not resume_text:
            continue
            
       #evaluation = screen_resume(job.title, job.requirements, resume_text)
        # Combine the title and requirements into one string for the AI, and pass the resume text
        evaluation = screen_resume(
    resume_text=resume_text, 
    job_requirements=f"Role: {job.title} | Requirements: {job.requirements}")

        candidate = Candidate(
            job_id=job.id,
            name=evaluation.get("name"),
            email=evaluation.get("email"),
            phone=evaluation.get("phone"),
            overall_fit_score=evaluation.get("overall_fit_score", 0.0),
            skills_score=evaluation.get("skills_score", 0.0),
            seniority_score=evaluation.get("seniority_score", 0.0),
            domain_score=evaluation.get("domain_score", 0.0),
            company_changes=evaluation.get("company_changes", 0),
            avg_duration_months=evaluation.get("avg_duration_months", 0.0),
            extracted_skills=evaluation.get("extracted_skills", []),
            red_flags=evaluation.get("red_flags", []),
            is_shortlisted=evaluation.get("is_shortlisted", False),
            one_line_summary=evaluation.get("one_line_summary")
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        results.append(candidate)

    return {"processed_count": len(results), "candidates": results}