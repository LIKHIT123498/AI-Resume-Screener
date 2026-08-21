from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CandidateResponse(BaseModel):
    id: int
    job_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    overall_fit_score: float
    skills_score: float
    seniority_score: float
    domain_score: float
    company_changes: int = 0
    avg_duration_months: float = 0.0
    extracted_skills: List[str] = []
    red_flags: List[str] = []
    is_shortlisted: int
    one_line_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True