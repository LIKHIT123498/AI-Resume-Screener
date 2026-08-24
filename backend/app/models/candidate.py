from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

# IMPORTANT: Adjust this import to wherever your Base is defined! 
# (e.g., from app.database import Base)
from app.core.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    overall_fit_score = Column(Float, default=0.0)
    skills_score = Column(Float, default=0.0)
    seniority_score = Column(Float, default=0.0)
    domain_score = Column(Float, default=0.0)
    
    company_changes = Column(Integer, default=0)
    avg_duration_months = Column(Float, default=0.0)
    
    extracted_skills = Column(JSON, default=list)
    red_flags = Column(JSON, default=list)
    
    is_shortlisted = Column(Integer, default=0)
    one_line_summary = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="candidates")