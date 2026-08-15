import json
import os
import logging
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Explicitly load .env from the backend root directory
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")

# Configure the Gemini client
if api_key:
    genai.configure(api_key=api_key)

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """
You are an expert technical recruiter and AI resume screening assistant.
Evaluate the candidate's resume against the Job Description (JD).

Job Title: {job_title}
Job Requirements & Description:
{job_requirements}

Candidate Resume:
{resume_text}

Analyze the resume and output strictly in the following JSON format:
{{
  "name": "Candidate Full Name or Unknown",
  "email": "Candidate Email or Unknown",
  "phone": "Candidate Phone or Unknown",
  "skills_matched": ["skill1", "skill2"],
  "skills_score": 85.0,
  "seniority_score": 80.0,
  "domain_score": 90.0,
  "overall_fit_score": 85.0,
  "red_flags": ["List of red flags or empty list"],
  "is_shortlisted": true,
  "one_line_summary": "One concise sentence explaining the candidate's fit."
}}
"""

def screen_resume(job_title: str, job_requirements: str, resume_text: str) -> dict:
    if not api_key:
        return {
            "overall_fit_score": 0.0,
            "red_flags": ["Server Configuration Error: GEMINI_API_KEY is missing"],
            "is_shortlisted": False
        }

    prompt = PROMPT_TEMPLATE.format(
        job_title=job_title,
        job_requirements=job_requirements,
        resume_text=resume_text[:4000] # Limiting input length for faster processing
    )
    
    try:
        # Using the available 3.5-flash model from your key
        model = genai.GenerativeModel(
            model_name="gemini-3.5-flash", 
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
            "red_flags": [f"AI Error: {str(e)}"],
            "is_shortlisted": False
        }
        
        r
        
        
    except Exception as e:
        print(f"\n[AI Engine Error Details]: {repr(e)}\n")
        return {
            "overall_fit_score": 0.0,
            "red_flags": [f"AI Error: {str(e)}"],
            "is_shortlisted": False
        }