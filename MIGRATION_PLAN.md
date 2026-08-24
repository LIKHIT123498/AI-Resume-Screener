# Migration Plan — MySQL → MongoDB + Per-User Authentication

**Project:** AI Resume Screener ATS
**Stack today:** FastAPI + SQLAlchemy 2.0 + PyMySQL · React 19 + Vite + TypeScript + Tailwind
**Stack after:** FastAPI + Beanie (async MongoDB ODM) · JWT auth with per-user data isolation
**Status:** Plan only — no files in your repo have been modified.

---

## Read this first: three blockers before any deployment

These came out of the audit and are independent of the migration itself. The first one is time-sensitive.

**1. Your `.env` is committed to git, and it contains your Gemini API key.** `git ls-files` confirms `backend/.env` is tracked. Anyone who clones or forks the repo — or browses it, if the remote is public — has that key. Rewriting history does not help you here, because the key has already been distributed. **Rotate the key in Google AI Studio first**, then purge the file (Section 7.1). Treat the old key as burned.

**2. Your virtualenv is committed too.** 9,972 tracked files, nearly all of them `backend/.venv/**`. This bloats the repo, breaks builds on any machine whose Python or OS differs from yours (the tracked paths are `Lib/site-packages`, so it is a Windows venv), and will confuse every deployment platform you try. Section 7.1 covers removing it.

**3. `allow_origins=["*"]` combined with `allow_credentials=True` in `main.py` is silently invalid.** The CORS spec forbids a wildcard origin on credentialed requests, and browsers reject the response. It works today only because you are not sending credentials yet. The moment you add auth, this configuration becomes a live bug. Section 7.3 fixes it.

---

## 1. Why this migration is bigger than swapping a driver

The instinct is that changing databases is a change to one file — `app/core/database.py`. It isn't, for one specific reason: **your primary keys change type.**

MySQL gives you `id = Column(Integer, primary_key=True)` → `1`, `2`, `3`. MongoDB gives you an `ObjectId` → `"68f3a1c9d4e5b6a7c8d9e0f1"`. That single change propagates outward through your whole stack:

| Layer | What breaks | Where |
|---|---|---|
| Models | `Integer` PKs, `ForeignKey`, `relationship()` | `models/job.py`, `models/candidate.py` |
| Schemas | `id: int`, `job_id: int` | `schemas/job.py`, `schemas/candidate.py` |
| Endpoints | `job_id: int` path params, `db.query()` | `endpoints/jobs.py`, `endpoints/screening.py` |
| Frontend types | `id: number`, `job_id: number` | `frontend/src/types/index.ts` |
| Frontend logic | `j.id === Number(id)` | `pages/JobDetail.tsx` line ~23 |

That `Number(id)` comparison in `JobDetail.tsx` is the kind of thing that bites silently: `Number("68f3a1c9...")` returns `NaN`, `NaN === NaN` is `false`, so the page renders "Error 404: Job not found" with no error in the console and nothing obviously wrong in the network tab. Fix it in the same commit as the model change, not after you start debugging.

The second structural change: **`relationship()` does not exist in MongoDB.** Your `JobResponse` schema currently declares `candidates: List[CandidateResponse] = []`, and SQLAlchemy populates it through the ORM relationship on attribute access. `GET /jobs/` returns every job with all its candidates nested, for free. Mongo has no equivalent — you either embed candidates inside the job document, or keep them in their own collection and assemble the response yourself.

**Recommendation: keep them separate.** Embedding is tempting because it preserves your current response shape with zero frontend changes, but it fails on this specific workload. A job in an ATS accumulates candidates without bound, documents cap at 16 MB, and you cannot index or sort an embedded array as efficiently as a real collection. You also load every candidate every time you read the job — which is exactly what your dashboard does today, on a page that only needs job titles. Separate collections, plus one endpoint that joins them explicitly, is the right call. Section 5.3 shows it.

### Decisions locked in for this plan

- **MongoDB layer:** Beanie ODM. Async, Pydantic-v2-native, and its `Document` class maps closely onto the declarative style you already use, so the models stay readable.
- **Auth:** self-hosted JWT — bcrypt password hashes in Mongo, tokens signed by FastAPI, verified by a `get_current_user` dependency. No vendor, no cost, deploys anywhere.
- **Existing data:** none to migrate. Test data only, so no ETL script.

---

## 2. Dependencies

Replace `backend/requirements.txt` with this. Removals matter as much as additions — leaving SQLAlchemy installed lets a stale import keep working and hides an unmigrated code path.

```txt
# --- Web framework ---
fastapi==0.110.0
uvicorn[standard]==0.28.0
python-multipart==0.0.9

# --- MongoDB (replaces sqlalchemy + pymysql + cryptography) ---
beanie==1.26.0
motor==3.4.0

# --- Auth (new) ---
pyjwt==2.8.0
bcrypt==4.1.3
email-validator==2.1.1

# --- Config & validation ---
pydantic==2.6.4
pydantic-settings==2.2.1
python-dotenv==1.0.1

# --- AI & parsing (unchanged) ---
pypdf==4.1.0
google-generativeai==0.4.1
```

Dropped: `sqlalchemy`, `pymysql`, `cryptography` (it was only there as PyMySQL's auth dependency), and `openai` (nothing imports it — `ai_engine.py` uses Gemini).

Three notes on the choices:

**Beanie/Motor versions.** Beanie 1.x is built on Motor. Motor is being wound down in favour of the async client that now ships inside PyMongo itself, and Beanie 2.x follows that move — which changes the client class you instantiate. Pin the versions above so you get the 1.x API the snippets in this document use, and run `pip index versions beanie` before you upgrade. If you do go to 2.x, the change is confined to `database.py`: `AsyncIOMotorClient` becomes PyMongo's `AsyncMongoClient` and `motor` leaves your requirements. Nothing else in this plan moves.

**PyJWT over python-jose.** Most FastAPI tutorials reach for `python-jose`, but it has been effectively unmaintained for years and carries a heavier crypto dependency chain. PyJWT is actively maintained and its API is smaller. You only need HS256 symmetric signing.

**bcrypt directly, not passlib.** The classic `passlib[bcrypt]` combination throws `AttributeError: module 'bcrypt' has no attribute '__about__'` against bcrypt 4.1+, because passlib reads a private attribute that bcrypt removed and passlib's last release predates it. You can pin `bcrypt<4.1` to dodge it, but calling `bcrypt` directly is three lines of code and removes the whole problem. Section 4.1.

### While you are in the backend: fix the `__init__` filenames

Every package marker in `backend/app/` is named `__init__py` — no dot:

```
app/__init__py          app/core/__init__py
app/models/__init__py    app/services/__init__py
```

Your imports resolve anyway, because Python 3.3+ treats a directory without `__init__.py` as an implicit namespace package. But namespace packages behave differently from regular ones in ways that surface exactly when you deploy: packaging tools that discover modules via `find_packages()` skip them, and some import hooks and freezers handle them inconsistently. Rename all five to `__init__.py`, and note that `app/api/` and `app/api/v1/` and `app/schemas/` appear to have no marker file at all — add those too.

```bash
cd backend/app
for f in $(find . -name '__init__py'); do git mv "$f" "${f%py}.py"; done
touch api/__init__.py api/v1/__init__.py api/v1/endpoints/__init__.py schemas/__init__.py
```

---

## 3. Phase 1 — The MongoDB layer

### 3.1 New file: `backend/app/core/config.py`

You currently call `load_dotenv()` in three separate places (`database.py`, `ai_engine.py`, and again inside `ai_engine.py` with an explicit path). That is a symptom worth fixing while you are here: config read at import time from scattered `os.getenv` calls fails late and quietly. One settings object, validated once at startup, fails immediately and tells you which variable is missing.

```python
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Database ---
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "resume_screener"

    # --- Auth ---
    # Generate with: openssl rand -hex 32
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- AI ---
    GEMINI_API_KEY: str

    # --- CORS: comma-separated, e.g. "http://localhost:5173,https://app.example.com"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

Because `MONGODB_URL`, `SECRET_KEY` and `GEMINI_API_KEY` have no defaults, the app refuses to boot without them. That is deliberate — it converts a silent production misconfiguration into a loud startup crash. Compare with `ai_engine.py` today, which prints `❌ CRITICAL ERROR` to stdout and then carries on running in a broken state.

### 3.2 Replace `backend/app/core/database.py`

The whole file goes. No more `engine`, `SessionLocal`, `Base`, or `get_db`.

```python
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient | None = None


async def init_db() -> None:
    """Open the Mongo connection and register Beanie document models."""
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL, tz_aware=True)

    # Import here, not at module top, to avoid a circular import:
    # models import nothing from this module, but keeping it local
    # also guarantees they are only loaded once settings are valid.
    from app.models.user import User
    from app.models.job import Job
    from app.models.candidate import Candidate

    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[User, Job, Candidate],
    )
    logger.info("Connected to MongoDB database '%s'", settings.MONGODB_DB_NAME)


async def close_db() -> None:
    if client is not None:
        client.close()
        logger.info("MongoDB connection closed")
```

Two things to notice. There is **no session and no dependency injection** — Beanie documents carry their own connection, so `db: Session = Depends(get_db)` disappears from every endpoint signature. And `init_beanie` is what creates your indexes, so any model you forget to list in `document_models` will raise `CollectionWasNotInitialized` on first use rather than failing at import.

### 3.3 Rewrite `backend/main.py`

`Base.metadata.create_all(bind=engine)` at import time is the SQLAlchemy idiom for "make the tables exist". Its Mongo equivalent is `init_beanie`, but it is `async`, so it cannot run at import — it needs the lifespan hook.

```python
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.api import api_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(title="AI Resume Screener API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # explicit list, never "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

Note that `/` became `/health`, and it no longer claims "database is connected" — it never actually checked. If you want a real readiness probe, ping the server inside it:

```python
@app.get("/health")
async def health_check():
    from app.core.database import client
    try:
        await client.admin.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "unreachable"}
```

### 3.4 The models

Each model is its own file, mirroring your current layout.

**`backend/app/models/user.py`** (new)

```python
from datetime import datetime, timezone
from typing import Annotated

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    email: Annotated[EmailStr, Indexed(unique=True)]
    hashed_password: str
    full_name: str | None = None
    company_name: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
```

The `unique=True` index is the thing that actually prevents duplicate accounts. Your registration endpoint will also check for an existing email, but that check is a race — two simultaneous signups can both pass it. The database constraint is what holds under concurrency, so treat the application check as a source of nice error messages, not as the guarantee.

**`backend/app/models/job.py`** (replaces the SQLAlchemy version)

```python
from datetime import datetime, timezone

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class Job(Document):
    owner_id: PydanticObjectId          # ← the isolation key
    title: str
    department: str | None = None
    description: str
    requirements: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "jobs"
        indexes = [
            # Compound index backing the dashboard query:
            # "this user's jobs, newest first"
            [("owner_id", pymongo.ASCENDING), ("created_at", pymongo.DESCENDING)],
        ]
```

**`backend/app/models/candidate.py`**

```python
from datetime import datetime, timezone
from typing import List

import pymongo
from beanie import Document, PydanticObjectId
from pydantic import Field


class Candidate(Document):
    owner_id: PydanticObjectId          # denormalised from Job — see note below
    job_id: PydanticObjectId

    name: str | None = None
    email: str | None = None
    phone: str | None = None

    overall_fit_score: float = 0.0
    skills_score: float = 0.0
    seniority_score: float = 0.0
    domain_score: float = 0.0

    company_changes: int = 0
    avg_duration_months: float = 0.0

    extracted_skills: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

    is_shortlisted: bool = False
    one_line_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "candidates"
        indexes = [
            # Backs "this job's candidates, best fit first"
            [("job_id", pymongo.ASCENDING), ("overall_fit_score", pymongo.DESCENDING)],
            [("owner_id", pymongo.ASCENDING)],
        ]
```

Four deliberate changes from your SQLAlchemy models:

**`owner_id` on `Candidate` is denormalised on purpose.** Strictly it is redundant — a candidate belongs to a job, and the job has an owner. But without it, every candidate query needs a join through `jobs` to prove ownership, and in Mongo that means either two round trips or an aggregation pipeline. Storing it lets you write `Candidate.find(Candidate.owner_id == user.id)` directly. The cost is that you must set it on every insert; the benefit is that ownership is checkable in one indexed query. For a security boundary, cheap and direct beats normalised.

**`is_shortlisted` is now `bool`, not `Integer`.** You were storing a boolean in an int column because MySQL has no native boolean — but look at what that did to `screening.py`: it writes `evaluation.get("is_shortlisted", False)`, a Python bool, into an `Integer` column, and the frontend type says `is_shortlisted: number`. Three layers disagreeing about one field. Mongo has real booleans, so make it a bool everywhere and update `types/index.ts` to `is_shortlisted: boolean`. Also grep `CandidateTable.tsx` and `CandidateDetailModal.tsx` for truthiness checks on this field — `=== 1` comparisons will silently stop matching.

**`extracted_skills`/`red_flags` use `default_factory=list`, not `default=list`.** Your SQLAlchemy models pass `default=list`, which happens to work there because SQLAlchemy calls callables. In Pydantic, `default=list` sets the default *to the `list` type object itself*, and `default_factory=list` is what produces a fresh empty list per document. Get this wrong and you either serialize garbage or share one mutable list across instances.

**`datetime.utcnow` is gone.** It is deprecated in Python 3.12+ and returns a naive datetime, which makes timezone-correct comparison impossible. `datetime.now(timezone.utc)` returns an aware one, and `tz_aware=True` on the Motor client means what you read back is aware too. Mixing the two raises `TypeError: can't subtract offset-naive and offset-aware datetimes` — usually months later, in whatever code first tries to sort or diff timestamps.

No `ForeignKey`, and no `relationship(... cascade="all, delete-orphan")`. Mongo enforces neither. **Cascade deletes are now your job:** deleting a job must explicitly delete its candidates, or you leave orphans that no query returns and nothing cleans up. Section 5.4.

### 3.5 Schemas — the ObjectId serialization pattern

Your API currently returns `"id": 1`. It will now return `"id": "68f3a1c9d4e5b6a7c8d9e0f1"`. Rather than sprinkling `str()` calls through your endpoints, define one reusable annotated type and use it everywhere an ObjectId crosses the wire.

**New file `backend/app/schemas/common.py`:**

```python
from typing import Annotated
from pydantic import BeforeValidator

# Coerces ObjectId (or anything else) to str during validation, so
# response models can declare plain `str` for id fields.
ObjectIdStr = Annotated[str, BeforeValidator(str)]
```

**`backend/app/schemas/job.py`:**

```python
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ObjectIdStr
from app.schemas.candidate import CandidateResponse


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    department: Optional[str] = Field(default=None, max_length=100)
    description: str = Field(min_length=1)
    requirements: str = Field(min_length=1)


class JobUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    department: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ObjectIdStr
    title: str
    department: Optional[str] = None
    description: str
    requirements: str
    created_at: datetime
    candidate_count: int = 0        # cheap summary for the dashboard


class JobDetailResponse(JobResponse):
    """Single-job view — includes the candidate list."""
    candidates: List[CandidateResponse] = []
```

Note that `owner_id` is deliberately **absent** from every response schema. Internal ownership plumbing has no business being visible to clients, and Pydantic response models are the enforcement point: a field not declared here cannot leak, even if you accidentally return a full document.

Splitting `JobResponse` from `JobDetailResponse` also fixes a real inefficiency. Today `GET /jobs/` nests every candidate of every job — the dashboard downloads your entire database to render a grid of titles. The list endpoint now returns a count; only the detail endpoint returns candidates.

**`backend/app/schemas/candidate.py`:**

```python
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ObjectIdStr


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ObjectIdStr
    job_id: ObjectIdStr
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
    is_shortlisted: bool
    one_line_summary: Optional[str] = None
    created_at: datetime
```

`from_attributes=True` (your old `Config.from_attributes`) still matters — it is what lets `response_model=CandidateResponse` read attributes off a Beanie `Document` instead of requiring a dict.

---

## 4. Phase 2 — Authentication

### 4.1 New file: `backend/app/core/security.py`

Two independent concerns live here: turning passwords into hashes, and turning user IDs into signed tokens.

```python
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# --- Passwords ---------------------------------------------------------

# bcrypt hashes at most 72 bytes and silently ignores the rest, which
# would make "<72 chars><anything>" authenticate as the same password.
# Reject long passwords explicitly rather than truncating.
MAX_PASSWORD_BYTES = 72


def hash_password(plain: str) -> str:
    pw = plain.encode("utf-8")
    if len(pw) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be at most 72 bytes")
    return bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed stored hash — treat as a failed login, never a 500.
        return False


# --- Tokens ------------------------------------------------------------


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": subject,          # the user's ObjectId as a string
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError (incl. ExpiredSignatureError) on any problem."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],   # a list, never a bare string
    )
```

Three details that are easy to get wrong and consequential when you do:

**`algorithms=[...]` must be an explicit allow-list.** This is the guard against the algorithm-confusion class of attack, where a token arrives claiming `"alg": "none"` or a different family and a permissive verifier accepts it. PyJWT requires the parameter, so you cannot omit it — but people do sometimes widen it carelessly. Keep it to exactly the one algorithm you sign with.

**`verify_password` returns `False` on a malformed hash rather than raising.** Without the `try`, a corrupt or empty `hashed_password` in the database turns a login attempt into a 500, which is both an availability problem and an information leak — the error distinguishes "this account exists but is broken" from "no such account."

**`rounds=12`** is the cost factor. Higher is slower to brute-force and slower to log in; 12 is the current sensible default. If your login endpoint feels sluggish on a small free-tier instance, that is the reason, and it is working as intended.

### 4.2 New file: `backend/app/core/deps.py`

This is the single chokepoint through which every authenticated request passes. It is short, and it is the most security-sensitive file in the project.

```python
import jwt
from beanie import PydanticObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            raise CREDENTIALS_EXCEPTION
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION

    try:
        oid = PydanticObjectId(user_id)
    except Exception:
        raise CREDENTIALS_EXCEPTION

    user = await User.get(oid)
    if user is None or not user.is_active:
        raise CREDENTIALS_EXCEPTION
    return user
```

Why each guard is there rather than being defensive noise:

- **`payload.get("type") != "access"`** stops a token minted for another purpose from being replayed as a login. You have only one token type today, but the moment you add refresh tokens or email-verification links, this check is what keeps them from being interchangeable. Adding it now is free; retrofitting it after you've issued refresh tokens is a breaking change.
- **`PydanticObjectId(user_id)` in a try/except** — the `sub` claim is attacker-controlled in the sense that a validly-signed token from an old `SECRET_KEY`, or a hand-crafted one if your key ever leaks, could carry garbage. An unhandled `InvalidId` is a 500.
- **The database lookup on every request** is the deliberate cost of this design. A JWT is self-contained, so you *could* trust the claims and skip the query — but then deactivating a user does nothing until their token expires. Re-reading the user means `is_active = False` takes effect on the next request. That is one indexed primary-key lookup per request; on Atlas, sub-millisecond.
- **Expired tokens get their own distinct message.** The frontend needs to tell "your session ended, log in again" apart from "something is wrong with this request," and the 401 body is where that signal comes from.

`tokenUrl` only affects the Swagger UI's Authorize button; it does not create a route.

### 4.3 New file: `backend/app/schemas/user.py`

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ObjectIdStr


class UserRegister(BaseModel):
    email: EmailStr
    # 8-char floor, 72-byte ceiling to match bcrypt's limit.
    password: str = Field(min_length=8, max_length=72)
    full_name: Optional[str] = Field(default=None, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ObjectIdStr
    email: EmailStr
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

`hashed_password` appears in no response schema. That is not an oversight to fill in later — it is the reason to route every response through an explicit schema instead of returning documents directly.

Returning the `user` object inside `TokenResponse` saves the frontend an immediate follow-up call to `/auth/me` after login, which matters because that round trip happens while the user is staring at a spinner.

### 4.4 New file: `backend/app/api/v1/endpoints/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    existing = await User.find_one(User.email == payload.email.lower())
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        company_name=payload.company_name,
    )
    try:
        await user.insert()
    except DuplicateKeyError:
        # Lost the race against a concurrent signup; the unique index caught it.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    user = await User.find_one(User.email == payload.email.lower())

    # Same response whether the email is unknown or the password is wrong.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def read_me(user: User = Depends(get_current_user)):
    return user
```

**Email is lowercased on both write and read.** Without this, `Alice@example.com` and `alice@example.com` become two accounts, each holding half the user's jobs — a data-partitioning bug that presents to the user as "my results disappeared." The unique index is case-*sensitive*, so it will not save you; normalising at the boundary is the fix.

**Both login failure modes return the identical 401.** Distinguishing "no such user" from "wrong password" hands an attacker a free account-enumeration oracle: they learn which emails are registered. (The fully rigorous version also runs a dummy hash comparison when the user is absent, so response *timing* doesn't leak the same fact. Worth knowing about; for this application the message-level fix is the part that matters.)

**Registration returns a token.** The user is logged in immediately rather than being bounced to a login form to retype what they just typed.

### 4.5 Update `backend/app/api/v1/api.py`

```python
from fastapi import APIRouter

from app.api.v1.endpoints import auth, jobs, screening

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(screening.router, prefix="/screening", tags=["screening"])
```

---

## 5. Phase 3 — Scoping every query to its owner

This is where the actual isolation guarantee lives. The rule, stated once:

> **Ownership goes in the query filter, never in an `if` statement after the fetch.**

The tempting shape is fetch-then-check:

```python
job = await Job.get(job_id)            # ✗ don't
if job.owner_id != user.id:
    raise HTTPException(403)
```

It is wrong in two ways. It leaks existence — a 403 tells the caller that `job_id` is real and belongs to someone else, which is information they should not have. And it is fragile: the check is a separate statement that a later refactor can drop, move, or bypass on one code path, with nothing failing loudly when it does. Filtering in the query makes another user's data simply *not exist* from this request's point of view, and there is no separate line to forget:

```python
job = await Job.find_one(Job.id == job_id, Job.owner_id == user.id)   # ✓
if job is None:
    raise HTTPException(404, "Job not found")
```

Same 404 whether the job is absent or belongs to someone else. The caller cannot tell the difference, which is the point.

### 5.1 Rewrite `backend/app/api/v1/endpoints/jobs.py`

```python
from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.schemas.candidate import CandidateResponse
from app.schemas.job import JobCreate, JobDetailResponse, JobResponse, JobUpdate

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, user: User = Depends(get_current_user)):
    job = Job(**payload.model_dump(), owner_id=user.id)
    await job.insert()
    return JobResponse.model_validate(job)


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    jobs = (
        await Job.find(Job.owner_id == user.id)
        .sort(-Job.created_at)
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    # One aggregation for all counts, instead of N count queries.
    job_ids = [j.id for j in jobs]
    counts: dict[PydanticObjectId, int] = {}
    if job_ids:
        pipeline = [
            {"$match": {"job_id": {"$in": job_ids}}},
            {"$group": {"_id": "$job_id", "n": {"$sum": 1}}},
        ]
        async for row in Candidate.aggregate(pipeline):
            counts[row["_id"]] = row["n"]

    out = []
    for j in jobs:
        item = JobResponse.model_validate(j)
        item.candidate_count = counts.get(j.id, 0)
        out.append(item)
    return out


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: PydanticObjectId, user: User = Depends(get_current_user)):
    job = await Job.find_one(Job.id == job_id, Job.owner_id == user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = (
        await Candidate.find(Candidate.job_id == job.id, Candidate.owner_id == user.id)
        .sort(-Candidate.overall_fit_score)
        .to_list()
    )

    detail = JobDetailResponse.model_validate(job)
    detail.candidate_count = len(candidates)
    detail.candidates = [CandidateResponse.model_validate(c) for c in candidates]
    return detail


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: PydanticObjectId,
    payload: JobUpdate,
    user: User = Depends(get_current_user),
):
    job = await Job.find_one(Job.id == job_id, Job.owner_id == user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    updates = payload.model_dump(exclude_unset=True)
    if updates:
        await job.set(updates)
    return JobResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: PydanticObjectId, user: User = Depends(get_current_user)):
    job = await Job.find_one(Job.id == job_id, Job.owner_id == user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Manual cascade — Mongo will not do this for you.
    await Candidate.find(Candidate.job_id == job.id).delete()
    await job.delete()
```

Notice `job_id: PydanticObjectId` in the path signature. FastAPI validates and coerces it before your function body runs, so a malformed ID returns a clean 422 instead of blowing up inside the query. This replaces the `job_id: int` you have today.

`sort(-Job.created_at)` is Beanie's descending-sort syntax and is served by the compound index from Section 3.4. The candidate sort by `-overall_fit_score` is likewise indexed — and it moves your "Ranked Shortlist" ordering from the client to the database, which is where it belongs once a job has more candidates than one page can show.

### 5.2 Rewrite `backend/app/api/v1/endpoints/screening.py`

This endpoint changes the most, and not only because of the database.

```python
import asyncio
import logging
from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.core.deps import get_current_user
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.user import User
from app.schemas.candidate import CandidateResponse
from app.services.ai_engine import screen_resume
from app.services.parser import extract_text_from_pdf

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILES_PER_REQUEST = 20
MAX_FILE_BYTES = 10 * 1024 * 1024   # 10 MB


@router.post("/{job_id}/upload-resumes")
async def upload_and_screen_resumes(
    job_id: PydanticObjectId,
    files: List[UploadFile] = File(...),
    user: User = Depends(get_current_user),
):
    job = await Job.find_one(Job.id == job_id, Job.owner_id == user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload at most {MAX_FILES_PER_REQUEST} resumes per request",
        )

    requirements_blob = f"Role: {job.title} | Requirements: {job.requirements}"
    created: List[Candidate] = []
    skipped: List[dict] = []

    for file in files:
        contents = await file.read()

        if len(contents) > MAX_FILE_BYTES:
            skipped.append({"filename": file.filename, "reason": "file too large"})
            continue
        if file.content_type != "application/pdf":
            skipped.append({"filename": file.filename, "reason": "not a PDF"})
            continue

        # Both of these are blocking, CPU/network-bound calls. In an async
        # endpoint they would stall the entire event loop — every other
        # request, for every other user, waits. Offload them.
        resume_text = await run_in_threadpool(extract_text_from_pdf, contents)
        if not resume_text:
            skipped.append({"filename": file.filename, "reason": "no extractable text"})
            continue

        try:
            evaluation = await run_in_threadpool(
                screen_resume,
                resume_text=resume_text,
                job_requirements=requirements_blob,
            )
        except Exception:
            logger.exception("AI screening failed for %s", file.filename)
            skipped.append({"filename": file.filename, "reason": "AI screening failed"})
            continue

        created.append(
            Candidate(
                owner_id=user.id,          # ← stamped from the token, never the client
                job_id=job.id,
                name=evaluation.get("name"),
                email=evaluation.get("email"),
                phone=evaluation.get("phone"),
                overall_fit_score=float(evaluation.get("overall_fit_score", 0.0)),
                skills_score=float(evaluation.get("skills_score", 0.0)),
                seniority_score=float(evaluation.get("seniority_score", 0.0)),
                domain_score=float(evaluation.get("domain_score", 0.0)),
                company_changes=int(evaluation.get("company_changes", 0)),
                avg_duration_months=float(evaluation.get("avg_duration_months", 0.0)),
                extracted_skills=evaluation.get("extracted_skills") or [],
                red_flags=evaluation.get("red_flags") or [],
                is_shortlisted=bool(evaluation.get("is_shortlisted", False)),
                one_line_summary=evaluation.get("one_line_summary"),
            )
        )

    if created:
        await Candidate.insert_many(created)   # one round trip, not N

    return {
        "processed_count": len(created),
        "skipped": skipped,
        "candidates": [CandidateResponse.model_validate(c) for c in created],
    }
```

Five changes worth calling out:

**`owner_id=user.id` comes from the verified token.** Never from the request body, a query parameter, or a header. If a client could specify the owner, the isolation boundary would be decorative.

**`run_in_threadpool` around the blocking calls.** This is the single most important line in the file, and it is easy to miss. Your current endpoint is `async def` but calls `screen_resume` — a synchronous Gemini HTTP request that can take many seconds — directly. In a sync `def` endpoint FastAPI would have run the whole thing in a threadpool for you; in an `async def` it does not, so that call blocks the event loop. With one user you never notice. With two, the second user's dashboard hangs while the first user's batch of 20 resumes is screened one at a time. This bug exists in your code *today*; the migration is a good moment to fix it.

**`db.commit()` inside the loop is gone.** You were committing and refreshing per candidate — one round trip each. `insert_many` sends the whole batch once.

**Failures no longer abort the batch.** Previously an exception from Gemini on resume #7 would 500 the request, and because you committed as you went, candidates 1–6 were saved while 8–20 were never attempted — leaving the client with an error and a partial result it cannot distinguish from a total failure. Now each file succeeds or is reported in `skipped`, and the caller gets a complete accounting.

**Uploads are bounded and type-checked.** `content_type` is client-supplied and therefore a hint, not proof — `extract_text_from_pdf` returning empty is the real backstop for a non-PDF, and it already handles that. The size and count caps are what stop one request from exhausting memory or your Gemini quota.

### 5.3 A new candidates endpoint

`JobDetail.tsx` currently gets candidates nested inside the job. With the split schemas it still can, via `GET /jobs/{id}`. But once a job has hundreds of candidates you will want to page and filter them independently — so add this now while the shape is fresh in your head. **New file `backend/app/api/v1/endpoints/candidates.py`:**

```python
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.models.candidate import Candidate
from app.models.user import User
from app.schemas.candidate import CandidateResponse

router = APIRouter()


@router.get("/", response_model=List[CandidateResponse])
async def list_candidates(
    user: User = Depends(get_current_user),
    job_id: Optional[PydanticObjectId] = None,
    shortlisted_only: bool = False,
    min_score: float = Query(0.0, ge=0, le=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    query = Candidate.find(Candidate.owner_id == user.id)   # always first
    if job_id is not None:
        query = query.find(Candidate.job_id == job_id)
    if shortlisted_only:
        query = query.find(Candidate.is_shortlisted == True)  # noqa: E712
    if min_score > 0:
        query = query.find(Candidate.overall_fit_score >= min_score)

    return await query.sort(-Candidate.overall_fit_score).skip(skip).limit(limit).to_list()


@router.patch("/{candidate_id}/shortlist", response_model=CandidateResponse)
async def toggle_shortlist(
    candidate_id: PydanticObjectId,
    shortlisted: bool,
    user: User = Depends(get_current_user),
):
    candidate = await Candidate.find_one(
        Candidate.id == candidate_id, Candidate.owner_id == user.id
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    await candidate.set({Candidate.is_shortlisted: shortlisted})
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: PydanticObjectId, user: User = Depends(get_current_user)
):
    candidate = await Candidate.find_one(
        Candidate.id == candidate_id, Candidate.owner_id == user.id
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    await candidate.delete()
```

The `owner_id` filter is applied **before** any optional filter, unconditionally. If it were inside one of the `if` branches, a request that omitted that parameter would return every user's candidates — the classic shape of this bug. Note also that `job_id` here needs no separate ownership check: a candidate matching both `owner_id == user.id` and the given `job_id` is necessarily under a job this user owns, which is precisely what the denormalised `owner_id` bought you.

Register it in `api.py`:

```python
from app.api.v1.endpoints import auth, candidates, jobs, screening
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
```

### 5.4 The complete endpoint inventory

| Method | Path | Auth | Notes |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | public | returns token + user |
| `POST` | `/api/v1/auth/login` | public | returns token + user |
| `GET` | `/api/v1/auth/me` | required | session rehydration on page load |
| `GET` | `/api/v1/jobs/` | required | owner-scoped, paged, no nested candidates |
| `POST` | `/api/v1/jobs/` | required | stamps `owner_id` from token |
| `GET` | `/api/v1/jobs/{id}` | required | **new** — job + ranked candidates |
| `PATCH` | `/api/v1/jobs/{id}` | required | **new** |
| `DELETE` | `/api/v1/jobs/{id}` | required | **new** — cascades to candidates |
| `POST` | `/api/v1/screening/{job_id}/upload-resumes` | required | owner-scoped |
| `GET` | `/api/v1/candidates/` | required | **new** — filterable |
| `PATCH` | `/api/v1/candidates/{id}/shortlist` | required | **new** |
| `DELETE` | `/api/v1/candidates/{id}` | required | **new** |
| `GET` | `/health` | public | no data exposure |

Every row marked "required" takes `user: User = Depends(get_current_user)` and filters by `owner_id`. There are no exceptions, and an endpoint added later without that dependency is the one way this design fails — which is why Section 8 tests for it directly rather than trusting review.

---

## 6. Phase 4 — Frontend

### 6.1 `src/types/index.ts` — the type changes

```ts
export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  company_name?: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Candidate {
  id: string;                    // was number
  job_id: string;                // was number
  name: string | null;
  email: string | null;
  phone: string | null;
  overall_fit_score: number;
  skills_score: number;
  seniority_score: number;
  domain_score: number;
  company_changes: number;
  avg_duration_months: number;
  extracted_skills: string[];
  red_flags: string[];
  is_shortlisted: boolean;       // was number
  one_line_summary: string | null;
  created_at: string;
}

export interface Job {
  id: string;                    // was number
  title: string;
  department?: string | null;
  description: string;
  requirements: string;
  created_at: string;
  candidate_count: number;
  candidates?: Candidate[];      // only present on GET /jobs/{id}
}
```

I also widened the nullable fields to `| null`, because your backend already returns `null` for them (`name`, `email`, `phone` and `one_line_summary` are all `Optional`) while the current types promise `string`. TypeScript has been trusting a lie, which is why a missing name renders as blank rather than as a fallback you chose. Once you make them nullable the compiler will point at each place that needs `?? '—'` or similar — accept that as a to-do list, not an obstacle.

`tsc -b` runs as part of your `build` script, so `npm run build` will now enumerate every site that assumed a numeric id or an `is_shortlisted` integer. Work through the list; it is the cheapest audit you will get.

### 6.2 `src/api/client.ts` — token attachment and 401 handling

```ts
import axios from 'axios';

const TOKEN_KEY = 'ats_access_token';

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t: string) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

export const apiClient = axios.create({
  // Set VITE_API_URL in .env.production; falls back to local dev.
  baseURL: import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1',
});

// --- Request: attach the bearer token -------------------------------
apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Let axios set Content-Type itself. For FormData it must emit
  // multipart/form-data *with a boundary parameter*, which it can only
  // do if we haven't hard-coded the header.
  if (!(config.data instanceof FormData)) {
    config.headers['Content-Type'] ??= 'application/json';
  }
  return config;
});

// --- Response: force a re-login on 401 ------------------------------
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const isAuthRoute = error.config?.url?.includes('/auth/');
    if (status === 401 && !isAuthRoute) {
      clearToken();
      // Hard redirect: simplest reliable way to reset all app state.
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

**The `Content-Type` handling fixes a real latent bug in your current setup.** Today `apiClient` is created with a global `'Content-Type': 'application/json'`, and `ResumeUploader.tsx` overrides it per-request with `'multipart/form-data'`. That override is itself the problem: a multipart body is only parseable if the header carries the `boundary=...` parameter that delimits the parts, and that boundary is generated by the browser when it serializes the `FormData`. By setting the header manually you send `multipart/form-data` with no boundary, and the server has no way to split the body. It works right now largely by luck of how axios and Starlette interact. Removing the global default and deleting the manual override — letting axios detect `FormData` and set the header itself — is the correct fix. **So in `ResumeUploader.tsx`, delete the `headers` option from the `post` call:**

```ts
// before
await apiClient.post(`/screening/${jobId}/upload-resumes`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' },   // ← delete this
});

// after
await apiClient.post(`/screening/${jobId}/upload-resumes`, formData);
```

**On storing the token in `localStorage`:** the tradeoff is XSS versus CSRF. `localStorage` is readable by any JavaScript running on your origin, so a successful XSS — a malicious dependency, an unescaped render — can exfiltrate the token. The hardened alternative is a short-lived access token in memory plus a refresh token in an `httpOnly`, `Secure`, `SameSite=Lax` cookie, which script cannot read; that costs you a refresh endpoint, rotation logic, and CSRF protection on the cookie path. For this application `localStorage` with a bounded token lifetime is a defensible choice, and it is what the code above implements. Make it a conscious decision rather than a default, and revisit it if you ever store real candidate PII for real clients — resumes are personal data, and depending on where your users are, regulated.

**Exclude `/auth/` routes from the redirect.** Otherwise a wrong password on the login form returns 401, the interceptor fires, and the page reloads out from under the user before your form can render "Incorrect email or password."

### 6.3 New file: `src/context/AuthContext.tsx`

```tsx
import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { AuthResponse, User } from '../types';
import { apiClient, clearToken, getToken, setToken } from '../api/client';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterInput) => Promise<void>;
  logout: () => void;
}

interface RegisterInput {
  email: string;
  password: string;
  full_name?: string;
  company_name?: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount: if a token is present, verify it and rehydrate the session.
  useEffect(() => {
    const bootstrap = async () => {
      if (!getToken()) {
        setLoading(false);
        return;
      }
      try {
        const { data } = await apiClient.get<User>('/auth/me');
        setUser(data);
      } catch {
        clearToken();   // expired or invalid
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await apiClient.post<AuthResponse>('/auth/login', { email, password });
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const { data } = await apiClient.post<AuthResponse>('/auth/register', input);
    setToken(data.access_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
};
```

The `loading` flag is load-bearing, not cosmetic. Without it, `user` is `null` on the very first render even for a signed-in user, so `ProtectedRoute` bounces them to `/login` before `/auth/me` resolves — a page refresh appears to log you out. `loading: true` until the check settles is what prevents that.

### 6.4 New file: `src/components/ProtectedRoute.tsx`

```tsx
import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const ProtectedRoute: React.FC = () => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64 text-gray-500 font-medium">
        Loading…
      </div>
    );
  }
  if (!user) {
    // Remember where they were headed so login can send them back.
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
};
```

Be clear about what this component is and is not. It is a **UX** guard: it keeps signed-out users from seeing a broken page. It is **not** a security boundary — anyone can edit client-side state or call your API directly with `curl`. The security boundary is `get_current_user` plus the `owner_id` filter on the server. Never move an authorization decision into React.

### 6.5 New file: `src/pages/Login.tsx`

```tsx
import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Loader2, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: Location })?.from?.pathname ?? '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Login failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-16">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="flex items-center gap-2 mb-6">
          <Lock className="w-5 h-5 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Sign in</h1>
        </div>

        {error && (
          <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              id="email" type="email" required autoComplete="email"
              value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              id="password" type="password" required autoComplete="current-password"
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>
          <button
            type="submit" disabled={submitting}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white px-5 py-2.5 rounded-lg font-medium transition"
          >
            {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="mt-6 text-sm text-gray-600 text-center">
          No account?{' '}
          <Link to="/register" className="text-blue-600 font-semibold hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
};
```

`src/pages/Register.tsx` is the same component with `full_name` and `company_name` fields added, a `password` of `minLength={8}`, `autoComplete="new-password"`, and `register({ ... })` in place of `login(...)`. The `autoComplete` values are what let password managers offer to save and fill credentials — worth getting right, and frequently omitted.

### 6.6 Update `src/App.tsx`

```tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { JobDetail } from './pages/JobDetail';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
          <Navbar />
          <main>
            <Routes>
              {/* Public */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Everything below requires a session */}
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/jobs/:id" element={<JobDetail />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
```

`AuthProvider` sits **inside** `BrowserRouter` because `ProtectedRoute` and the login page call router hooks. Wrapping the other way round throws "useLocation must be used within a Router."

### 6.7 Update `src/components/Navbar.tsx`

Add the signed-in identity and a logout control:

```tsx
import React from 'react';
import { Briefcase, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2">
        <Briefcase className="text-blue-600 w-6 h-6" />
        <span className="text-xl font-bold text-gray-900">AI Recruiter</span>
      </Link>

      {user && (
        <div className="flex items-center gap-4">
          <div className="text-right leading-tight hidden sm:block">
            <p className="text-sm font-semibold text-gray-900">
              {user.full_name ?? user.email}
            </p>
            {user.company_name && (
              <p className="text-xs text-gray-500">{user.company_name}</p>
            )}
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-red-600 transition"
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      )}
    </nav>
  );
};
```

Showing the signed-in email is not decoration — it is how a user notices they are in the wrong account before they wonder where their data went.

### 6.8 Update `src/pages/JobDetail.tsx`

Replace the fetch-all-and-filter block with the real endpoint. This resolves the `Number(id)` → `NaN` problem from Section 1 and the comment in your own code that says "in a real prod app, you would create a `GET /jobs/{id}` endpoint."

```tsx
const fetchJobData = async () => {
  try {
    const { data } = await apiClient.get<Job>(`/jobs/${id}`);
    setJob(data);
    setCandidates(data.candidates ?? []);
  } catch (error: any) {
    if (error?.response?.status === 404) {
      setJob(null);            // renders your existing "Job not found"
    } else {
      console.error('Failed to fetch job', error);
    }
  } finally {
    setLoading(false);
  }
};
```

Beyond correctness, this is the isolation guarantee working end to end: request another user's job id and the server returns 404, so the page shows "not found" rather than their candidate list.

### 6.9 Update `src/pages/Dashboard.tsx`

`fetchJobs` needs no change — the interceptor attaches the token and the backend scopes the results. Two smaller touches:

`JobCard` can now show `job.candidate_count` instead of `job.candidates?.length`, which is what the new list schema provides.

And the error path deserves better than `console.error`. Add an error state so a failed load says so on screen rather than rendering an empty grid that reads as "you have no jobs" — a distinction that matters a great deal on a page whose whole purpose is showing the user their own data.

### 6.10 New file: `frontend/.env.production`

```
VITE_API_URL=https://your-backend-host.example.com/api/v1
```

Vite inlines `VITE_`-prefixed variables at **build** time, not runtime. Two consequences: this file must exist before `npm run build`, and anything you put in it ships inside your JavaScript bundle where any visitor can read it. API base URLs are fine. Never put a secret in a `VITE_` variable — your `GEMINI_API_KEY` stays server-side, which is already how you have it.

For local development add `frontend/.env.development` with `VITE_API_URL=http://127.0.0.1:8000/api/v1`, and commit neither if you would rather keep host names out of git (the fallback in `client.ts` covers the dev case regardless).
