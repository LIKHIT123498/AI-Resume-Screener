import asyncio
import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate
from app.services.parser import extract_text_from_file
from app.services.ai_engine import screen_resume, calculate_overall_fit
from app.services.email_service import send_screening_digest_email
from app.models.user import User
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        cleaned = str(val).replace('%', '').strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return default

def safe_int(val, default: int = 0) -> int:
    if val is None:
        return default
    try:
        cleaned = str(val).split('-')[0].split('+')[0].strip()
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default

async def process_single_file(
    file: UploadFile,
    job_id: int,
    job_title: str,
    job_requirements: str,
    role_type: str
) -> Optional[dict]:
    try:
        contents = await file.read()
        resume_text = await run_in_threadpool(extract_text_from_file, contents, file.filename)
        
        if not resume_text or len(resume_text.strip()) == 0:
            logger.warning(f"Skipping {file.filename}: no extractable text found.")
            return None
            
        evaluation = await run_in_threadpool(
            screen_resume,
            resume_text=resume_text, 
            job_requirements=f"Role: {job_title} | Requirements: {job_requirements}"
        )

        skills_score = safe_float(evaluation.get("skills_score"), 0.0)
        seniority_score = safe_float(evaluation.get("seniority_score"), 0.0)
        domain_score = safe_float(evaluation.get("domain_score"), 0.0)
        
        overall_fit_score = calculate_overall_fit(
            skills_score=skills_score,
            seniority_score=seniority_score,
            domain_score=domain_score,
            role_type=role_type
        )

        name_val = evaluation.get("name")
        if not name_val or str(name_val).strip() in ("", "None", "null", "Candidate Name"):
            name_val = file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')

        summary_val = evaluation.get("one_line_summary")
        if summary_val:
            summary_val = str(summary_val)[:950]

        extracted_skills = evaluation.get("extracted_skills")
        if not isinstance(extracted_skills, list):
            extracted_skills = []

        red_flags = evaluation.get("red_flags")
        if not isinstance(red_flags, list):
            red_flags = []

        return {
            "candidate": {
                "job_id": job_id,
                "name": str(name_val)[:250],
                "email": str(evaluation.get("email"))[:250] if evaluation.get("email") else None,
                "phone": str(evaluation.get("phone"))[:45] if evaluation.get("phone") else None,
                "overall_fit_score": overall_fit_score,
                "skills_score": skills_score,
                "seniority_score": seniority_score,
                "domain_score": domain_score,
                "company_changes": safe_int(evaluation.get("company_changes"), 0),
                "avg_duration_months": safe_float(evaluation.get("avg_duration_months"), 0.0),
                "extracted_skills": extracted_skills,
                "red_flags": red_flags,
                "is_shortlisted": 1 if overall_fit_score >= 70.0 else 0,
                "one_line_summary": summary_val
            },
            "filename": file.filename,
            "file_bytes": contents
        }
    except Exception as err:
        logger.error(f"Error processing candidate file {file.filename}: {err}")
        return None

@router.post("/{job_id}/upload-resumes")
async def upload_and_screen_resumes(
    job_id: int,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    
    if not job:
        raise HTTPException(
            status_code=404, 
            detail="Job not found or you do not have permission to upload candidates here."
        )

    role_type = getattr(job, "role_type", "technical") or "technical"
    
    # Process all files in the batch in parallel!
    tasks = [
        process_single_file(
            file=file,
            job_id=job.id,
            job_title=job.title,
            job_requirements=job.requirements,
            role_type=role_type
        )
        for file in files
    ]
    
    candidate_data_list = await asyncio.gather(*tasks, return_exceptions=False)

    results = []
    attachments = []
    for item in candidate_data_list:
        if not item:
            continue
        try:
            candidate = Candidate(**item["candidate"])
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            results.append(candidate)
            if item.get("filename") and item.get("file_bytes"):
                attachments.append((item["filename"], item["file_bytes"]))
        except Exception as db_err:
            db.rollback()
            logger.error(f"Database commit error for candidate: {db_err}")

    # Queue email digest to the user's email in the background
    if results and current_user.email:
        candidate_summaries = [
            {
                "name": c.name,
                "overall_fit_score": c.overall_fit_score,
                "one_line_summary": c.one_line_summary
            }
            for c in results
        ]
        background_tasks.add_task(
            send_screening_digest_email,
            recipient_email=current_user.email,
            job_title=job.title,
            candidates=candidate_summaries,
            attachments=attachments
        )

    return {"processed_count": len(results), "candidates": results}