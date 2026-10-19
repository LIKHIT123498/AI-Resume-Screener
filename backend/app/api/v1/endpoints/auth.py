import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token

# Allow HTTP on localhost during development (OAuthlib requires HTTPS by default)
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Resolve path to client_secret.json (works whether run from root or backend directory)
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ENV_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json")
if os.path.isabs(ENV_SECRET_FILE):
    CLIENT_SECRETS_FILE = ENV_SECRET_FILE
else:
    potential_path = os.path.join(BACKEND_DIR, ENV_SECRET_FILE)
    CLIENT_SECRETS_FILE = potential_path if os.path.exists(potential_path) else ENV_SECRET_FILE

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/google/callback/")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

router = APIRouter()

@router.post("/register")
def register_user(email: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        auth_provider="local"
    )
    db.add(new_user)
    db.commit()
    return {"message": "User registered successfully"}

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/login")
def google_login():
    """
    Initiate Google OAuth 2.0 flow: redirects browser to Google Consent Screen
    """
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise HTTPException(
            status_code=500,
            detail=f"Google credentials file not found at: {CLIENT_SECRETS_FILE}"
        )

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    return RedirectResponse(url=authorization_url)

@router.get("/google/callback")
@router.get("/google/callback/")
def google_callback(code: str = None, error: str = None, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback, issue application JWT token, and redirect to frontend
    """
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={error}")

    if not code:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=Authorization+code+missing")

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        token_request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            token_request,
            flow.client_config["client_id"]
        )

        email = id_info.get("email")
        if not email:
            return RedirectResponse(url=f"{FRONTEND_URL}/login?error=Email+not+provided+by+Google")

        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                auth_provider="google"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generate JWT token
        access_token = create_access_token(data={"sub": user.email})
        return RedirectResponse(url=f"{FRONTEND_URL}/login?token={access_token}")

    except Exception as e:
        import urllib.parse
        err_msg = urllib.parse.quote(str(e))
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={err_msg}")