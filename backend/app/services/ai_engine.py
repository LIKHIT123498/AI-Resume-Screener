import json
import os
import logging
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Try loading from the current working directory first, then fallback to explicit path
load_dotenv() 
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

api_key = os.getenv("GEMINI_API_KEY")

# Strict check to immediately flag if the key is missing
if not api_key:
    print("\n❌ CRITICAL ERROR: GEMINI_API_KEY is not loaded into the environment! Check your .env file.\n")
else:
    genai.configure(api_key=api_key)

logger = logging.getLogger(__name__)

def calculate_overall_fit(
    skills_score: float, 
    seniority_score: float, 
    domain_score: float, 
    role_type: str = "technical"
) -> float:
    """
    Computes overall fit score based on role track:
    - Technical: 50% skills, 30% seniority, 20% domain
    - Non-Technical: 40% skills, 20% seniority, 40% domain
    """
    if role_type == "technical":
        overall = (skills_score * 0.50) + (seniority_score * 0.30) + (domain_score * 0.20)
    else:
        # Non-Technical: Seniority (20%), Domain (40%), Skills (40%)
        overall = (skills_score * 0.40) + (seniority_score * 0.20) + (domain_score * 0.40)
        
    return round(overall, 2)

def screen_resume(resume_text: str, job_requirements: str) -> dict:
    # The prompt MUST be inside this function so it can use the variables passed to it!
    prompt = f"""
    You are an expert technical AI recruiter. Analyze the following resume against the job requirements.
    
    Job Requirements: {job_requirements}
    
    Resume Text: {resume_text}
    
    You must return your analysis STRICTLY as a JSON object with the following rules:
    
    1. ATS Grading System (0-100 for each):
       - skills_score: Match candidate skills against requirements.
       - domain_score: Relevance of candidate's industry experience.
       - seniority_score: Match years of experience against requirements.
       - overall_fit_score: YOU MUST CALCULATE THIS EXACTLY AS: (seniority_score * 0.20) + (domain_score * 0.40) + (skills_score * 0.40).
       
    2. Job Stints & Red Flags:
       - company_changes: Count the total number of different companies the candidate has worked for.
       - avg_duration_months: Calculate the average duration (in months) they spent at their last 3 companies.
       - If `avg_duration_months` is less than 18, you MUST add a specific red flag to the `red_flags` array stating: "Frequent job changes: Average tenure at last 3 companies is less than 1.5 years."
       
    Return ONLY valid JSON matching this exact structure:
    {{
        "name": "Candidate Name",
        "email": "email",
        "phone": "phone",
        "skills_score": 0,
        "domain_score": 0,
        "seniority_score": 0,
        "overall_fit_score": 0,
        "company_changes": 0,
        "avg_duration_months": 0,
        "extracted_skills": ["Skill1", "Skill2"],
        "red_flags": ["Flag1"],
        "is_shortlisted": 0,
        "one_line_summary": "Summary here"
    }}
    """
    
    try:
        # Using the lite model to bypass the quota limit
        model = genai.GenerativeModel(
            model_name="gemini-3.5-flash-lite", 
            generation_config={"temperature": 0.1}
        )
        
        response = model.generate_content(prompt)
        
        # Bulletproof JSON cleaner to strip Markdown formatting
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        return json.loads(clean_text.strip())
        
    except Exception as e:
        print(f"\n[AI Engine Error Details]: {repr(e)}\n")
        return {
            "overall_fit_score": 0.0,
            "skills_score": 0.0,
            "seniority_score": 0.0,
            "domain_score": 0.0,
            "company_changes": 0,
            "avg_duration_months": 0.0,
            "extracted_skills": [],
            "red_flags": [f"AI Error: {str(e)}"],
            "is_shortlisted": False,
            "one_line_summary": "Error processing candidate."
        }