from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.services.parser import extract_text_from_pdf
from app.services.ai_engine import screen_resume

router = APIRouter()

@router.post("/{job_id}/upload-resumes")
async def upload_and_screen_resumes(
    job_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = []
    for file in files:
        contents = await file.read()
        resume_text = extract_text_from_pdf(contents)
        
        if not resume_text:
            continue
            
        evaluation = screen_resume(job.title, job.requirements, resume_text)
        
        candidate = Candidate(
            job_id=job.id,
            name=evaluation.get("name", "Unknown"),
            email=evaluation.get("email", "Unknown"),
            phone=evaluation.get("phone", "Unknown"),
            raw_text=resume_text,
            overall_fit_score=evaluation.get("overall_fit_score", 0.0),
            skills_score=evaluation.get("skills_score", 0.0),
            seniority_score=evaluation.get("seniority_score", 0.0),
            domain_score=evaluation.get("domain_score", 0.0),
            extracted_skills=evaluation.get("skills_matched", []),
            red_flags=evaluation.get("red_flags", []),
            is_shortlisted=1 if evaluation.get("is_shortlisted") else 0,
            one_line_summary=evaluation.get("one_line_summary", "")
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        results.append(candidate)

    return {"processed_count": len(results), "candidates": results}