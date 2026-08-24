import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from app.core.database import engine, Base
from app.models import job, candidate  # Ensure user model is imported if you have one
from app.api.v1.api import api_router

# 1. Initialize Supabase Client
SUPABASE_URL = "https://zzmdssxvswlpfcjkfkqu.supabase.co"
# Paste your actual key (starts with sb_secret_...) here
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# 2. Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# 3. Create FastAPI app
app = FastAPI(title="AI Resume Screener API", version="1.0")

# 4. Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Resume Upload Endpoint
@app.post("/api/v1/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        file_bytes = await file.read()
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        
        # Upload directly to the 'resumes' bucket
        supabase.storage.from_("resumes").upload(
            file=file_bytes,
            path=unique_filename,
            file_options={"content-type": "application/pdf", "upsert": "false"}
        )
        
        # Get public access URL
        public_url = supabase.storage.from_("resumes").get_public_url(unique_filename)
        
        return {
            "message": "Resume uploaded successfully",
            "filename": unique_filename,
            "url": public_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload resume: {str(e)}")

# 6. Include API Routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "Backend is running and database is connected"}