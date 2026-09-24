import asyncio
import time
import os
import logging
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
from app.core.database import get_db
from app.models.job import Job
from app.models.candidate import Candidate, ResumeFile
from app.services.parser import extract_text_from_file
from app.services.ai_engine import screen_resume, calculate_overall_fit
from app.services.email_service import send_screening_digest_email
from app.models.user import User
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("uploads")

# In-memory session store to combine multi-batch uploads into 1 single email digest
_upload_sessions: dict[str, dict] = {}

def _cleanup_old_sessions():
    now = time.time()
    expired = [sid for sid, data in _upload_sessions.items() if now - data.get("created_at", 0) > 600]
    for sid in expired:
        _upload_sessions.pop(sid, None)

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

@router.get("/email-status")
def get_email_status():
    """
    Public diagnostic endpoint to check if SMTP environment variables
    are configured on the server. Masks credentials for security.
    """
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = os.getenv("SMTP_PORT", "587")

    masked = None
    if smtp_user and "@" in smtp_user:
        u, d = smtp_user.split("@", 1)
        masked = f"{u[:3]}***@{d}"
    elif smtp_user:
        masked = f"{smtp_user[:3]}***"

    resend_key = os.getenv("RESEND_API_KEY")
    masked_resend = f"{resend_key[:6]}..." if resend_key else None

    gmail_relay_url = os.getenv("GMAIL_RELAY_URL")
    masked_relay = f"{gmail_relay_url[:35]}..." if gmail_relay_url else None

    active_provider = (
        "gmail_relay" if gmail_relay_url else (
            "resend_api" if resend_key else (
                "smtp" if (smtp_user and smtp_password) else "none"
            )
        )
    )

    return {
        "active_provider": active_provider,
        "gmail_relay_configured": bool(gmail_relay_url),
        "gmail_relay_preview": masked_relay,
        "resend_configured": bool(resend_key),
        "resend_key_preview": masked_resend,
        "smtp_configured": bool(smtp_user and smtp_password),
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": masked,
        "render_smtp_blocked": True,
        "note": "Render free tier blocks outbound SMTP ports 25, 465, 587. GMAIL_RELAY_URL or RESEND_API_KEY provides reliable HTTPS email delivery over Port 443."
    }

@router.get("/smtp-check")
def smtp_check():
    """
    Diagnostic endpoint to test TCP connectivity to Gmail SMTP from this server.
    """
    import socket
    results = {}
    for p in [465, 587]:
        t0 = time.time()
        try:
            sock = socket.create_connection(("smtp.gmail.com", p), timeout=5)
            sock.close()
            results[f"port_{p}"] = f"OPEN ({round((time.time() - t0)*1000)}ms)"
        except Exception as e:
            results[f"port_{p}"] = f"FAILED: {e}"
    return results

@router.post("/test-email")
async def send_test_email(
    to_email: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Allows sending a diagnostic test digest email directly to the logged-in user.
    """
    target_email = to_email or current_user.email
    if not target_email:
        raise HTTPException(status_code=400, detail="No recipient email address.")

    sample_candidates = [
        {
            "name": "Alex Morgan (Diagnostic Test)",
            "overall_fit_score": 94.0,
            "one_line_summary": "Expert Senior Full-Stack Engineer with 6+ years React, Python, and cloud infrastructure experience."
        },
        {
            "name": "Taylor Swift (Diagnostic Test)",
            "overall_fit_score": 81.5,
            "one_line_summary": "Proficient Software Engineer skilled in TypeScript, Node.js, and automated testing."
        }
    ]

    sample_attachments = [
        ("alex_morgan_resume.pdf", b"%PDF-1.4 sample resume content for Alex Morgan\n"),
        ("taylor_swift_resume.pdf", b"%PDF-1.4 sample resume content for Taylor Swift\n")
    ]

    success = await run_in_threadpool(
        send_screening_digest_email,
        recipient_email=target_email,
        job_title="Diagnostic Test Run",
        candidates=sample_candidates,
        attachments=sample_attachments
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to send test email. Please check if SMTP_USER and SMTP_PASSWORD are configured in the environment."
        )
    return {"success": True, "message": f"Test email sent successfully to {target_email}"}

@router.post("/{job_id}/finalize-upload-session")
def finalize_upload_session(
    job_id: int,
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Forces immediate finalization and email dispatch of an upload session,
    ensuring that even if an upload stops midway, screened candidates are emailed.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    current_session_key = f"{current_user.id}_{session_id}"
    if current_session_key in _upload_sessions:
        session_data = _upload_sessions.pop(current_session_key)
        candidates = session_data["candidates"]
        attachments = session_data["attachments"]
        if candidates and current_user.email:
            logger.info(f"Finalizing session {session_id} - sending {len(candidates)} candidates to {current_user.email}")
            background_tasks.add_task(
                send_screening_digest_email,
                recipient_email=current_user.email,
                job_title=job.title,
                candidates=candidates,
                attachments=attachments
            )
        return {"finalized": True, "candidates_count": len(candidates)}
    return {"finalized": False, "message": "Session not found or already dispatched."}

@router.post("/{job_id}/resend-digest-email")
def resend_job_digest_email(
    job_id: int,
    background_tasks: BackgroundTasks,
    to_email: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sends or re-sends the candidate screening digest email for any job,
    fetching all candidates currently saved in the database for that job.
    Attaches the original uploaded resume files if present on disk, or generates
    clean candidate evaluation PDF profiles so attachments are always included!
    """
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized.")

    candidates = db.query(Candidate).filter(Candidate.job_id == job_id).all()
    if not candidates:
        raise HTTPException(status_code=400, detail="No candidates found for this job yet.")

    candidate_summaries = [
        {
            "name": c.name,
            "overall_fit_score": c.overall_fit_score,
            "one_line_summary": c.one_line_summary
        }
        for c in candidates
    ]

    target = to_email or current_user.email
    if not target:
        raise HTTPException(status_code=400, detail="No recipient email address.")

    # 1. First, check if original uploaded resume files exist on disk for this job
    attachments = []
    job_upload_dir = UPLOAD_DIR / str(job_id)
    if job_upload_dir.exists():
        for f in job_upload_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                try:
                    attachments.append((f.name, f.read_bytes()))
                except Exception as read_err:
                    logger.warning(f"Could not read cached file {f.name}: {read_err}")

    # 2. If not on disk (e.g. Render restarted or container wiped), fetch REAL original files from PostgreSQL!
    if not attachments:
        try:
            db_resumes = db.query(ResumeFile).filter(ResumeFile.job_id == job_id).all()
            for rf in db_resumes:
                if rf.filename and rf.file_bytes:
                    attachments.append((rf.filename, rf.file_bytes))
        except Exception as db_err:
            logger.warning(f"Error querying resume files from DB: {db_err}")

    logger.info(f"Queuing resend of screening digest for job {job_id} ({len(candidates)} candidates, {len(attachments)} original resume attachments) to {target}...")
    background_tasks.add_task(
        send_screening_digest_email,
        recipient_email=target,
        job_title=job.title,
        candidates=candidate_summaries,
        attachments=attachments
    )

    if attachments:
        msg = f"Screening digest email queued for {len(candidates)} candidate(s) with {len(attachments)} original resume attachment(s) to {target}."
    else:
        msg = f"Screening digest email queued for {len(candidates)} candidate(s) to {target}. (Note: Original resume files were not archived for this previous upload session. Newly uploaded candidates will have their original PDF/DOCX resumes attached)."

    return {
        "success": True,
        "message": msg
    }

@router.post("/{job_id}/upload-resumes")
async def upload_and_screen_resumes(
    job_id: int,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    is_last_batch: Optional[str] = Form(None),
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
    job_upload_dir = UPLOAD_DIR / str(job_id)
    try:
        job_upload_dir.mkdir(parents=True, exist_ok=True)
    except Exception as dir_err:
        logger.warning(f"Could not create upload directory {job_upload_dir}: {dir_err}")

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
                fname = item["filename"]
                fbytes = item["file_bytes"]
                attachments.append((fname, fbytes))
                
                # 1. Permanently store the REAL uploaded resume file in PostgreSQL
                try:
                    resume_record = ResumeFile(
                        job_id=job.id,
                        candidate_id=candidate.id,
                        filename=fname,
                        content_type="application/pdf" if fname.lower().endswith(".pdf") else "application/octet-stream",
                        file_bytes=fbytes
                    )
                    db.add(resume_record)
                    db.commit()
                except Exception as resume_db_err:
                    db.rollback()
                    logger.error(f"Error saving resume file to DB for candidate {candidate.id}: {resume_db_err}")

                # 2. Also cache to disk for fast local reads
                try:
                    safe_fname = Path(fname).name
                    file_path = job_upload_dir / safe_fname
                    file_path.write_bytes(fbytes)
                except Exception as save_err:
                    logger.warning(f"Could not persist resume file {fname} to disk: {save_err}")
        except Exception as db_err:
            db.rollback()
            logger.error(f"Database commit error for candidate: {db_err}")

    # Accumulate results across batches so 1 single email digest is sent per upload session
    _cleanup_old_sessions()
    
    candidate_summaries = [
        {
            "name": c.name,
            "overall_fit_score": c.overall_fit_score,
            "one_line_summary": c.one_line_summary
        }
        for c in results
    ]

    current_session_key = f"{current_user.id}_{session_id}" if session_id else None

    if current_session_key:
        if current_session_key not in _upload_sessions:
            _upload_sessions[current_session_key] = {
                "candidates": [],
                "attachments": [],
                "created_at": time.time()
            }
        _upload_sessions[current_session_key]["candidates"].extend(candidate_summaries)
        _upload_sessions[current_session_key]["attachments"].extend(attachments)

    # Determine if we should trigger the combined email now
    last_batch_flag = True if is_last_batch is None else (str(is_last_batch).lower() in ("true", "1", "yes"))

    if last_batch_flag or not current_session_key:
        if current_session_key and current_session_key in _upload_sessions:
            session_data = _upload_sessions.pop(current_session_key)
            all_candidates = session_data["candidates"]
            all_attachments = session_data["attachments"]
        else:
            all_candidates = candidate_summaries
            all_attachments = attachments

        if all_candidates and current_user.email:
            logger.info(
                f"Queueing digest email to {current_user.email} for '{job.title}' "
                f"({len(all_candidates)} candidates, {len(all_attachments)} attachments)..."
            )
            background_tasks.add_task(
                send_screening_digest_email,
                recipient_email=current_user.email,
                job_title=job.title,
                candidates=all_candidates,
                attachments=all_attachments
            )
        elif not current_user.email:
            logger.warning(f"User {current_user.id} has no email address. Skipping email digest.")

    return {"processed_count": len(results), "candidates": results}