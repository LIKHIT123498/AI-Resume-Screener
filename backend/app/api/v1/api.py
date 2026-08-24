from fastapi import APIRouter
from app.api.v1.endpoints import jobs,screening,auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(screening.router, prefix="/screening", tags=["screening"])