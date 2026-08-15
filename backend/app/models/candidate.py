from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    raw_text = Column(Text, nullable=False)
    
    overall_fit_score = Column(Float, default=0.0)
    skills_score = Column(Float, default=0.0)
    seniority_score = Column(Float, default=0.0)
    domain_score = Column(Float, default=0.0)
    
    one_line_summary = Column(String(500), nullable=True)
    extracted_skills = Column(JSON, nullable=True)
    red_flags = Column(JSON, nullable=True)
    is_shortlisted = Column(Integer, default=0) 
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="candidates")