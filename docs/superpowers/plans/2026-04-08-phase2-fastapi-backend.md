# Phase 2: FastAPI Backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the FastAPI backend layer that wraps the core engine with REST API, WebSocket, task queue, user auth, and video preview — making the core accessible to the Tauri frontend.

**Architecture:** FastAPI application in `backend/app/` wraps `backend/core/` through a service layer. SQLite via SQLAlchemy stores users and tasks. An async FIFO queue processes one task at a time, pushing progress via WebSocket. Video preview uses HTTP range streaming. Glossary/TM/back-translation are Phase 3 — this phase builds the infrastructure they plug into.

**Tech Stack:** FastAPI, SQLAlchemy (async SQLite), Pydantic v2, PyJWT, uvicorn, asyncio.Queue

**Working directory:** `/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/backend`

**Run tests with:** `cd backend && python3 -m pytest tests/ -v`

---

## File Structure

```
backend/app/
├── __init__.py
├── main.py              # FastAPI app factory, lifespan, CORS, router mounting
├── config.py            # Server settings (Pydantic BaseSettings)
├── database.py          # SQLAlchemy async engine + session factory
├── dependencies.py      # FastAPI Depends: get_db, get_current_user
├── models/
│   ├── __init__.py
│   ├── user.py          # User SQLAlchemy model
│   └── task.py          # Task SQLAlchemy model
├── schemas/
│   ├── __init__.py
│   ├── user.py          # Pydantic request/response schemas for auth
│   ├── task.py          # Pydantic schemas for tasks
│   └── settings.py      # Pydantic schemas for settings
├── api/
│   ├── __init__.py
│   ├── auth.py          # POST /api/auth/register, /api/auth/login
│   ├── tasks.py         # POST/GET/DELETE /api/tasks, GET /api/queue
│   ├── subtitles.py     # GET/PUT /api/tasks/{id}/subtitles, POST export/synthesize
│   ├── preview.py       # GET /api/preview/{task_id}/video|waveform|thumbnail
│   └── settings.py      # GET/PUT /api/settings, GET /api/settings/models
├── ws/
│   ├── __init__.py
│   └── handlers.py      # WebSocket /ws/tasks/{id} and /ws/queue
├── services/
│   ├── __init__.py
│   ├── auth.py          # Password hashing, JWT create/verify
│   ├── task_queue.py    # FIFO queue manager + worker loop
│   ├── pipeline.py      # Orchestrates core ASR → split → optimize → translate
│   └── path_resolver.py # Converts client mount path ↔ server path
```

---

### Task 1: FastAPI App Skeleton + Config

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Test: `backend/tests/test_api/__init__.py`
- Test: `backend/tests/test_api/test_health.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/__init__.py` (empty file).

Write `backend/tests/test_api/test_health.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_health.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Install test dependencies**

```bash
cd backend && pip install httpx pytest-asyncio
```

- [ ] **Step 4: Write app/config.py**

```python
"""Server configuration via environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings — loaded from env vars or .env file."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./studio_captioner.db"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72

    # Shared storage
    storage_base_path: str = ""

    # ASR defaults
    default_asr_model: str = "faster_whisper"
    default_whisper_model: str = "large-v3"

    # LLM defaults
    llm_api_base: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5:7b"

    model_config = {"env_prefix": "SCA_", "env_file": ".env"}


settings = Settings()
```

- [ ] **Step 5: Write app/__init__.py**

```python
```

- [ ] **Step 6: Write app/main.py**

```python
"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title="Studio Captioner AI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_api/test_health.py -v`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/ backend/tests/test_api/
git commit -m "feat: FastAPI app skeleton with health endpoint"
```

---

### Task 2: Database + User Model

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Test: `backend/tests/test_api/test_database.py`

- [ ] **Step 1: Install async SQLite driver**

```bash
pip install aiosqlite sqlalchemy[asyncio] pydantic-settings
```

- [ ] **Step 2: Write the failing test**

Write `backend/tests/test_api/test_database.py`:

```python
import pytest
from sqlalchemy import select

from app.database import async_engine, async_session, Base
from app.models.user import User


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_user():
    async with async_session() as session:
        user = User(name="alice", password_hash="hashed123")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.name == "alice"
        assert user.created_at is not None


@pytest.mark.asyncio
async def test_unique_username():
    async with async_session() as session:
        session.add(User(name="bob", password_hash="hash1"))
        await session.commit()

    with pytest.raises(Exception):
        async with async_session() as session:
            session.add(User(name="bob", password_hash="hash2"))
            await session.commit()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_database.py -v`

Expected: FAIL

- [ ] **Step 4: Write app/database.py**

```python
"""Async SQLAlchemy engine and session factory."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

async_engine = create_async_engine(
    settings.database_url,
    echo=False,
)

async_session = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 5: Write app/models/__init__.py**

```python
from app.models.user import User
```

- [ ] **Step 6: Write app/models/user.py**

```python
"""User database model."""

import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_api/test_database.py -v`

Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/database.py backend/app/models/ backend/tests/test_api/test_database.py
git commit -m "feat: async SQLite database + User model"
```

---

### Task 3: Auth Service + Auth API

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/auth.py`
- Create: `backend/app/dependencies.py`
- Modify: `backend/app/main.py` (mount auth router)
- Test: `backend/tests/test_api/test_auth.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_auth.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine
from app.main import create_app


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "alice"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_name(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    resp = await client.post("/api/auth/register", json={"name": "alice", "password": "other456"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["name"] == "alice"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    resp = await client.get("/api/tasks")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_token(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "secret123"})
    login_resp = await client.post("/api/auth/login", json={"name": "alice", "password": "secret123"})
    token = login_resp.json()["token"]
    resp = await client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_auth.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/services/__init__.py** (empty)

- [ ] **Step 4: Write app/services/auth.py**

```python
"""Authentication service — password hashing and JWT tokens."""

import datetime
import hashlib
import hmac
import secrets

import jwt

from app.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}:{h.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, stored_hash = password_hash.split(":")
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return hmac.compare_digest(h.hex(), stored_hash)


def create_token(user_id: int, user_name: str) -> str:
    payload = {
        "sub": str(user_id),
        "name": user_name,
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
```

- [ ] **Step 5: Write app/schemas/__init__.py** (empty)

- [ ] **Step 6: Write app/schemas/user.py**

```python
"""Auth request/response schemas."""

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    name: str
    password: str


class LoginRequest(BaseModel):
    name: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str


class LoginResponse(BaseModel):
    token: str
    id: int
    name: str
```

- [ ] **Step 7: Write app/dependencies.py**

```python
"""FastAPI dependency injection."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.user import User
from app.services.auth import decode_token

security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [ ] **Step 8: Write app/api/__init__.py** (empty)

- [ ] **Step 9: Write app/api/auth.py**

```python
"""Auth API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.services.auth import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.name == body.name))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Name already taken")

    user = User(name=body.name, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse(id=user.id, name=user.name)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.name == body.name))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_token(user.id, user.name)
    return LoginResponse(token=token, id=user.id, name=user.name)
```

- [ ] **Step 10: Create stub tasks router for the protected endpoint test**

Write `backend/app/api/tasks.py`:

```python
"""Tasks API routes."""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(user: User = Depends(get_current_user)):
    return []
```

- [ ] **Step 11: Update app/main.py to mount routers**

Replace `backend/app/main.py` with:

```python
"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, tasks
from app.database import Base, async_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Studio Captioner AI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(tasks.router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app
```

- [ ] **Step 12: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 13: Commit**

```bash
git add backend/app/ backend/tests/test_api/
git commit -m "feat: auth service + register/login API + JWT protection"
```

---

### Task 4: Task Model + Task CRUD API

**Files:**
- Create: `backend/app/models/task.py`
- Create: `backend/app/schemas/task.py`
- Modify: `backend/app/models/__init__.py` (add Task import)
- Modify: `backend/app/api/tasks.py` (full CRUD implementation)
- Test: `backend/tests/test_api/test_tasks.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_tasks.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine
from app.main import create_app


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "pass123"})
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_task(client, auth_headers):
    resp = await client.post(
        "/api/tasks",
        json={"video_path": "/shared/input/interview.mxf", "asr_model": "faster_whisper"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["video_path"] == "/shared/input/interview.mxf"
    assert data["status"] == "queued"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_tasks(client, auth_headers):
    await client.post(
        "/api/tasks",
        json={"video_path": "/shared/input/a.mxf"},
        headers=auth_headers,
    )
    await client.post(
        "/api/tasks",
        json={"video_path": "/shared/input/b.mxf"},
        headers=auth_headers,
    )
    resp = await client.get("/api/tasks", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_task(client, auth_headers):
    create_resp = await client.post(
        "/api/tasks",
        json={"video_path": "/shared/input/a.mxf"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]
    resp = await client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_delete_queued_task(client, auth_headers):
    create_resp = await client.post(
        "/api/tasks",
        json={"video_path": "/shared/input/a.mxf"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200

    get_resp = await client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_queue_status(client, auth_headers):
    resp = await client.get("/api/queue", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "queue_length" in data
    assert "current_task" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_tasks.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/models/task.py**

```python
"""Task database model."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="queued"
    )  # queued, processing, ready_for_review, completed, failed
    video_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    output_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    subtitle_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
```

- [ ] **Step 4: Update app/models/__init__.py**

```python
from app.models.user import User
from app.models.task import Task
```

- [ ] **Step 5: Write app/schemas/task.py**

```python
"""Task request/response schemas."""

import datetime
from typing import Optional

from pydantic import BaseModel


class TaskCreate(BaseModel):
    video_path: str
    asr_model: str = "faster_whisper"
    config: dict = {}


class TaskResponse(BaseModel):
    id: int
    user_id: int
    status: str
    video_path: str
    output_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    progress: int = 0
    stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None


class QueueStatus(BaseModel):
    queue_length: int
    current_task: Optional[TaskResponse] = None
```

- [ ] **Step 6: Replace app/api/tasks.py with full implementation**

```python
"""Tasks API routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import QueueStatus, TaskCreate, TaskResponse

router = APIRouter(tags=["tasks"])


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        status=task.status,
        video_path=task.video_path,
        output_path=task.output_path,
        subtitle_path=task.subtitle_path,
        progress=task.progress,
        stage=task.stage,
        error_message=task.error_message,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )


@router.post("/api/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = Task(
        user_id=user.id,
        video_path=body.video_path,
        status="queued",
        config_json=json.dumps({"asr_model": body.asr_model, **body.config}),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_response(task)


@router.get("/api/tasks", response_model=list[TaskResponse])
async def list_tasks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc())
    )
    return [_task_to_response(t) for t in result.scalars().all()]


@router.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)


@router.delete("/api/tasks/{task_id}")
async def delete_task(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "queued":
        raise HTTPException(status_code=409, detail="Can only delete queued tasks")
    await db.delete(task)
    await db.commit()
    return {"detail": "Task deleted"}


@router.get("/api/queue", response_model=QueueStatus)
async def get_queue_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(sa_func.count()).select_from(Task).where(Task.status == "queued")
    )
    queue_length = count_result.scalar() or 0

    current_result = await db.execute(
        select(Task).where(Task.status == "processing").limit(1)
    )
    current = current_result.scalar_one_or_none()

    return QueueStatus(
        queue_length=queue_length,
        current_task=_task_to_response(current) if current else None,
    )
```

- [ ] **Step 7: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: Task model + CRUD API + queue status endpoint"
```

---

### Task 5: Task Queue Service + Pipeline Orchestrator

**Files:**
- Create: `backend/app/services/task_queue.py`
- Create: `backend/app/services/pipeline.py`
- Modify: `backend/app/main.py` (start queue worker in lifespan)
- Modify: `backend/app/api/tasks.py` (enqueue on create)
- Test: `backend/tests/test_api/test_queue.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_queue.py`:

```python
import asyncio

import pytest

from app.services.task_queue import TaskQueue


@pytest.mark.asyncio
async def test_queue_enqueue_dequeue():
    queue = TaskQueue()
    await queue.enqueue(1)
    await queue.enqueue(2)
    assert queue.length == 2

    task_id = await queue.dequeue()
    assert task_id == 1
    assert queue.length == 1


@pytest.mark.asyncio
async def test_queue_cancel():
    queue = TaskQueue()
    await queue.enqueue(1)
    await queue.enqueue(2)
    await queue.enqueue(3)

    removed = queue.cancel(2)
    assert removed is True
    assert queue.length == 2

    removed_again = queue.cancel(2)
    assert removed_again is False


@pytest.mark.asyncio
async def test_queue_current_task():
    queue = TaskQueue()
    assert queue.current_task_id is None

    await queue.enqueue(42)
    queue.current_task_id = 42
    assert queue.current_task_id == 42
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_queue.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/services/task_queue.py**

```python
"""FIFO task queue manager."""

import asyncio
from collections import deque
from typing import Optional


class TaskQueue:
    """In-process FIFO task queue."""

    def __init__(self):
        self._queue: deque[int] = deque()
        self._event = asyncio.Event()
        self.current_task_id: Optional[int] = None

    @property
    def length(self) -> int:
        return len(self._queue)

    async def enqueue(self, task_id: int) -> None:
        self._queue.append(task_id)
        self._event.set()

    async def dequeue(self) -> int:
        while not self._queue:
            self._event.clear()
            await self._event.wait()
        return self._queue.popleft()

    def cancel(self, task_id: int) -> bool:
        try:
            self._queue.remove(task_id)
            return True
        except ValueError:
            return False
```

- [ ] **Step 4: Write app/services/pipeline.py**

```python
"""Pipeline orchestrator — connects API layer to core engine."""

import json
import os
import traceback
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.task import Task


async def update_task_status(
    task_id: int,
    status: str,
    stage: Optional[str] = None,
    progress: int = 0,
    error_message: Optional[str] = None,
    output_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
):
    """Update task status in DB."""
    import datetime

    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return
        task.status = status
        if stage is not None:
            task.stage = stage
        task.progress = progress
        if error_message is not None:
            task.error_message = error_message
        if output_path is not None:
            task.output_path = output_path
        if subtitle_path is not None:
            task.subtitle_path = subtitle_path
        if status in ("completed", "ready_for_review", "failed"):
            task.completed_at = datetime.datetime.now(datetime.timezone.utc)
        await db.commit()


async def run_pipeline(task_id: int, progress_callback: Optional[Callable] = None):
    """Execute the full captioning pipeline for a task.

    Stages: transcribe → split → optimize → translate → ready_for_review
    """
    async with async_session() as db:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task is None:
            return

        config = json.loads(task.config_json) if task.config_json else {}
        video_path = task.video_path

    try:
        # Stage 1: Transcribe
        await update_task_status(task_id, "processing", stage="transcribe", progress=0)
        if progress_callback:
            await progress_callback(task_id, "transcribe", 0, "Starting transcription")

        # Import core modules
        from core.asr.transcribe import transcribe
        from core.entities import TranscribeConfig, TranscribeModelEnum
        from core.utils.video_utils import video2audio

        # Extract audio
        import tempfile
        audio_path = os.path.join(tempfile.gettempdir(), f"task_{task_id}.wav")
        video2audio(video_path, audio_path)

        # Run ASR
        asr_model = config.get("asr_model", "faster_whisper")
        model_enum = (
            TranscribeModelEnum.FASTER_WHISPER
            if asr_model == "faster_whisper"
            else TranscribeModelEnum.WHISPER_CPP
        )
        transcribe_config = TranscribeConfig(transcribe_model=model_enum)

        def asr_callback(progress: int, message: str):
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(
                    update_task_status(task_id, "processing", stage="transcribe", progress=progress)
                )

        asr_data = transcribe(audio_path, transcribe_config, callback=asr_callback)

        # Save subtitle data
        subtitle_dir = os.path.dirname(video_path)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        subtitle_path = os.path.join(subtitle_dir, f"{base_name}.srt")
        asr_data.to_srt(subtitle_path)

        await update_task_status(
            task_id,
            "ready_for_review",
            stage="done",
            progress=100,
            subtitle_path=subtitle_path,
        )
        if progress_callback:
            await progress_callback(task_id, "done", 100, "Ready for review")

    except Exception as e:
        await update_task_status(
            task_id,
            "failed",
            error_message=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
        )
        if progress_callback:
            await progress_callback(task_id, "failed", 0, str(e))
```

- [ ] **Step 5: Update app/main.py — start queue worker in lifespan**

Replace `backend/app/main.py`:

```python
"""FastAPI application factory."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, tasks
from app.database import Base, async_engine
from app.services.task_queue import TaskQueue


task_queue = TaskQueue()


async def queue_worker():
    """Background worker that processes tasks from the queue one at a time."""
    from app.services.pipeline import run_pipeline

    while True:
        task_id = await task_queue.dequeue()
        task_queue.current_task_id = task_id
        try:
            await run_pipeline(task_id)
        except Exception:
            pass
        finally:
            task_queue.current_task_id = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    worker_task = asyncio.create_task(queue_worker())
    app.state.task_queue = task_queue

    yield

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="Studio Captioner AI",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(tasks.router)

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app
```

- [ ] **Step 6: Update app/api/tasks.py — enqueue on create, cancel from queue**

In `create_task`, add after `await db.refresh(task)`:

```python
    # Enqueue for processing
    from app.main import task_queue
    await task_queue.enqueue(task.id)
```

In `delete_task`, add before `await db.delete(task)`:

```python
    from app.main import task_queue
    task_queue.cancel(task_id)
```

- [ ] **Step 7: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: FIFO task queue + pipeline orchestrator + background worker"
```

---

### Task 6: WebSocket Handlers

**Files:**
- Create: `backend/app/ws/__init__.py`
- Create: `backend/app/ws/handlers.py`
- Modify: `backend/app/main.py` (mount WS routes)
- Test: `backend/tests/test_api/test_websocket.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_websocket.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine
from app.main import create_app
from app.ws.handlers import progress_manager


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_progress_manager_subscribe_unsubscribe():
    """Test the progress manager tracks subscribers."""
    assert progress_manager is not None
    assert hasattr(progress_manager, "subscribe")
    assert hasattr(progress_manager, "unsubscribe")
    assert hasattr(progress_manager, "broadcast_task")
    assert hasattr(progress_manager, "broadcast_queue")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_websocket.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/ws/__init__.py** (empty)

- [ ] **Step 4: Write app/ws/handlers.py**

```python
"""WebSocket handlers for real-time progress and queue updates."""

import asyncio
import json
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ProgressManager:
    """Manages WebSocket connections and broadcasts progress updates."""

    def __init__(self):
        self._task_subscribers: Dict[int, Set[WebSocket]] = {}
        self._queue_subscribers: Set[WebSocket] = set()

    def subscribe(self, task_id: int, ws: WebSocket):
        if task_id not in self._task_subscribers:
            self._task_subscribers[task_id] = set()
        self._task_subscribers[task_id].add(ws)

    def unsubscribe(self, task_id: int, ws: WebSocket):
        if task_id in self._task_subscribers:
            self._task_subscribers[task_id].discard(ws)
            if not self._task_subscribers[task_id]:
                del self._task_subscribers[task_id]

    def subscribe_queue(self, ws: WebSocket):
        self._queue_subscribers.add(ws)

    def unsubscribe_queue(self, ws: WebSocket):
        self._queue_subscribers.discard(ws)

    async def broadcast_task(self, task_id: int, data: dict):
        message = json.dumps(data)
        subscribers = self._task_subscribers.get(task_id, set()).copy()
        for ws in subscribers:
            try:
                await ws.send_text(message)
            except Exception:
                self._task_subscribers.get(task_id, set()).discard(ws)

    async def broadcast_queue(self, data: dict):
        message = json.dumps(data)
        for ws in self._queue_subscribers.copy():
            try:
                await ws.send_text(message)
            except Exception:
                self._queue_subscribers.discard(ws)


progress_manager = ProgressManager()


@router.websocket("/ws/tasks/{task_id}")
async def ws_task_progress(websocket: WebSocket, task_id: int):
    await websocket.accept()
    progress_manager.subscribe(task_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.unsubscribe(task_id, websocket)


@router.websocket("/ws/queue")
async def ws_queue_status(websocket: WebSocket):
    await websocket.accept()
    progress_manager.subscribe_queue(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        progress_manager.unsubscribe_queue(websocket)
```

- [ ] **Step 5: Update app/main.py — mount WS router**

Add import at top:

```python
from app.ws import handlers as ws_handlers
```

Add in `create_app()` after `app.include_router(tasks.router)`:

```python
    app.include_router(ws_handlers.router)
```

- [ ] **Step 6: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: WebSocket handlers for task progress and queue status"
```

---

### Task 7: Subtitle API (Get, Save, Export)

**Files:**
- Create: `backend/app/api/subtitles.py`
- Modify: `backend/app/main.py` (mount subtitles router)
- Test: `backend/tests/test_api/test_subtitles.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_subtitles.py`:

```python
import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine, async_session
from app.main import create_app
from app.models.task import Task
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "pass123"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest.fixture
async def task_with_subtitle():
    """Create a task with a real SRT file."""
    tmpdir = tempfile.mkdtemp()
    srt_path = os.path.join(tmpdir, "test.srt")
    with open(srt_path, "w") as f:
        f.write("1\n00:00:01,000 --> 00:00:03,000\nHello world\n\n")
        f.write("2\n00:00:04,000 --> 00:00:06,000\nSecond line\n\n")

    async with async_session() as db:
        user = User(name="alice", password_hash=hash_password("pass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)

        task = Task(
            user_id=user.id,
            video_path="/shared/input/test.mxf",
            status="ready_for_review",
            subtitle_path=srt_path,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task.id, srt_path, tmpdir


@pytest.mark.asyncio
async def test_get_subtitles(client, auth_headers, task_with_subtitle):
    task_id, srt_path, _ = task_with_subtitle
    resp = await client.get(f"/api/tasks/{task_id}/subtitles", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "segments" in data
    assert len(data["segments"]) == 2
    assert data["segments"][0]["text"] == "Hello world"


@pytest.mark.asyncio
async def test_save_subtitles(client, auth_headers, task_with_subtitle):
    task_id, srt_path, _ = task_with_subtitle
    resp = await client.put(
        f"/api/tasks/{task_id}/subtitles",
        json={
            "segments": [
                {"text": "Modified hello", "start_time": 1000, "end_time": 3000},
                {"text": "Modified second", "start_time": 4000, "end_time": 6000},
            ]
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    # Verify saved
    get_resp = await client.get(f"/api/tasks/{task_id}/subtitles", headers=auth_headers)
    assert get_resp.json()["segments"][0]["text"] == "Modified hello"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_subtitles.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/api/subtitles.py**

```python
"""Subtitle API routes — get, save, export, synthesize."""

import os
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User

router = APIRouter(tags=["subtitles"])


class SubtitleSegment(BaseModel):
    text: str
    start_time: int  # milliseconds
    end_time: int  # milliseconds
    translated_text: Optional[str] = None


class SubtitleData(BaseModel):
    segments: List[SubtitleSegment]


class SubtitleSaveRequest(BaseModel):
    segments: List[SubtitleSegment]


class ExportRequest(BaseModel):
    format: str = "srt"  # srt, ass, vtt


async def _get_user_task(task_id: int, user: User, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/api/tasks/{task_id}/subtitles", response_model=SubtitleData)
async def get_subtitles(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path or not os.path.exists(task.subtitle_path):
        raise HTTPException(status_code=404, detail="No subtitle data available")

    from core.asr.asr_data import ASRData

    asr_data = ASRData.from_subtitle_file(task.subtitle_path)
    segments = [
        SubtitleSegment(
            text=seg.text,
            start_time=seg.start_time,
            end_time=seg.end_time,
            translated_text=getattr(seg, "translated_text", None) or None,
        )
        for seg in asr_data.segments
    ]
    return SubtitleData(segments=segments)


@router.put("/api/tasks/{task_id}/subtitles")
async def save_subtitles(
    task_id: int,
    body: SubtitleSaveRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path:
        raise HTTPException(status_code=400, detail="No subtitle path set for this task")

    from core.asr.asr_data import ASRData, ASRDataSeg

    segments = [
        ASRDataSeg(
            text=seg.text,
            start_time=seg.start_time,
            end_time=seg.end_time,
            translated_text=seg.translated_text or "",
        )
        for seg in body.segments
    ]
    asr_data = ASRData(segments)
    asr_data.to_srt(task.subtitle_path)

    return {"detail": "Subtitles saved"}


@router.post("/api/tasks/{task_id}/export")
async def export_subtitles(
    task_id: int,
    body: ExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.subtitle_path or not os.path.exists(task.subtitle_path):
        raise HTTPException(status_code=404, detail="No subtitle data available")

    from core.asr.asr_data import ASRData

    asr_data = ASRData.from_subtitle_file(task.subtitle_path)

    export_dir = os.path.dirname(task.subtitle_path)
    base_name = os.path.splitext(os.path.basename(task.subtitle_path))[0]

    fmt = body.format.lower()
    if fmt == "srt":
        out_path = os.path.join(export_dir, f"{base_name}.srt")
        asr_data.to_srt(out_path)
    elif fmt == "ass":
        out_path = os.path.join(export_dir, f"{base_name}.ass")
        asr_data.to_ass(out_path)
    elif fmt == "vtt":
        out_path = os.path.join(export_dir, f"{base_name}.vtt")
        asr_data.to_vtt(out_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    return FileResponse(out_path, filename=os.path.basename(out_path))
```

- [ ] **Step 4: Mount subtitles router in app/main.py**

Add import:
```python
from app.api import auth, tasks, subtitles
```

Add in `create_app()`:
```python
    app.include_router(subtitles.router)
```

- [ ] **Step 5: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: subtitle API — get, save, export endpoints"
```

---

### Task 8: Preview API (Video Streaming, Waveform, Thumbnail)

**Files:**
- Create: `backend/app/api/preview.py`
- Modify: `backend/app/main.py` (mount preview router)
- Test: `backend/tests/test_api/test_preview.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_preview.py`:

```python
import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine, async_session
from app.main import create_app
from app.models.task import Task
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={"name": "alice", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "alice", "password": "pass123"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest.fixture
async def task_with_video():
    """Create a task pointing to a dummy video file."""
    tmpdir = tempfile.mkdtemp()
    video_path = os.path.join(tmpdir, "test.mp4")
    # Create a minimal file (not a real video, but enough for path checks)
    with open(video_path, "wb") as f:
        f.write(b"\x00" * 1024)

    async with async_session() as db:
        user = User(name="alice", password_hash=hash_password("pass123"))
        db.add(user)
        await db.commit()
        await db.refresh(user)

        task = Task(user_id=user.id, video_path=video_path, status="ready_for_review")
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task.id


@pytest.mark.asyncio
async def test_preview_video_file_not_found(client, auth_headers):
    """Task with non-existent video returns 404."""
    # Create a task with bad path
    async with async_session() as db:
        user_result = await db.execute(
            __import__("sqlalchemy").select(User).where(User.name == "alice")
        )
        user = user_result.scalar_one()
        task = Task(user_id=user.id, video_path="/nonexistent/video.mp4", status="queued")
        db.add(task)
        await db.commit()
        await db.refresh(task)
        task_id = task.id

    resp = await client.get(f"/api/preview/{task_id}/video", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_preview_video_streaming(client, auth_headers, task_with_video):
    task_id = task_with_video
    resp = await client.get(f"/api/preview/{task_id}/video", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.content) == 1024
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_preview.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/api/preview.py**

```python
"""Preview API — video streaming, waveform data, thumbnails."""

import os
import stat

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.task import Task
from app.models.user import User

router = APIRouter(prefix="/api/preview", tags=["preview"])


async def _get_user_task(task_id: int, user: User, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/{task_id}/video")
async def preview_video(
    task_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    file_size = os.path.getsize(task.video_path)
    range_header = request.headers.get("range")

    if range_header:
        # HTTP range request for seeking
        range_val = range_header.replace("bytes=", "")
        start_str, end_str = range_val.split("-")
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
        chunk_size = end - start + 1

        def iter_file():
            with open(task.video_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(8192, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_file(),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Type": "video/mp4",
            },
        )

    return FileResponse(task.video_path, media_type="video/mp4")


@router.get("/{task_id}/waveform")
async def get_waveform(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return audio waveform peak data as JSON.

    Generates peaks using FFmpeg if not cached.
    """
    task = await _get_user_task(task_id, user, db)
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    # Check for cached waveform
    waveform_path = task.video_path + ".peaks.json"
    if os.path.exists(waveform_path):
        return FileResponse(waveform_path, media_type="application/json")

    # Generate waveform peaks using FFmpeg
    import json
    import subprocess
    import tempfile

    try:
        raw_path = os.path.join(tempfile.gettempdir(), f"task_{task_id}_raw.pcm")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", task.video_path,
                "-ac", "1", "-ar", "8000", "-f", "s16le", raw_path,
            ],
            capture_output=True,
            timeout=120,
        )

        if not os.path.exists(raw_path):
            raise HTTPException(status_code=500, detail="Failed to extract audio")

        # Read raw PCM and compute peaks
        import struct
        peaks = []
        with open(raw_path, "rb") as f:
            while True:
                chunk = f.read(8000 * 2)  # 1 second of 16-bit mono at 8kHz
                if not chunk:
                    break
                samples = struct.unpack(f"<{len(chunk)//2}h", chunk)
                peak = max(abs(s) for s in samples) / 32768.0 if samples else 0
                peaks.append(round(peak, 3))

        os.unlink(raw_path)

        with open(waveform_path, "w") as f:
            json.dump({"peaks": peaks, "sample_rate": 1}, f)

        return FileResponse(waveform_path, media_type="application/json")

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Waveform generation timed out")


@router.get("/{task_id}/thumbnail")
async def get_thumbnail(
    task_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_user_task(task_id, user, db)
    if not task.video_path or not os.path.exists(task.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    thumb_path = task.video_path + ".thumb.jpg"
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path, media_type="image/jpeg")

    import subprocess
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", task.video_path,
                "-ss", "00:00:02", "-frames:v", "1",
                "-q:v", "5", thumb_path,
            ],
            capture_output=True,
            timeout=30,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate thumbnail")

    if not os.path.exists(thumb_path):
        raise HTTPException(status_code=500, detail="Thumbnail generation failed")

    return FileResponse(thumb_path, media_type="image/jpeg")
```

- [ ] **Step 4: Mount preview router in app/main.py**

Add import:
```python
from app.api import auth, tasks, subtitles, preview
```

Add in `create_app()`:
```python
    app.include_router(preview.router)
```

- [ ] **Step 5: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: preview API — video streaming, waveform, thumbnail"
```

---

### Task 9: Settings API

**Files:**
- Create: `backend/app/schemas/settings.py`
- Create: `backend/app/api/settings.py`
- Modify: `backend/app/main.py` (mount settings router)
- Test: `backend/tests/test_api/test_settings.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_settings.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, async_engine
from app.main import create_app


@pytest.fixture(autouse=True)
async def setup_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def auth_headers(client):
    await client.post("/api/auth/register", json={"name": "admin", "password": "pass123"})
    resp = await client.post("/api/auth/login", json={"name": "admin", "password": "pass123"})
    return {"Authorization": f"Bearer {resp.json()['token']}"}


@pytest.mark.asyncio
async def test_get_settings(client, auth_headers):
    resp = await client.get("/api/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "default_asr_model" in data
    assert "llm_model" in data
    assert "storage_base_path" in data


@pytest.mark.asyncio
async def test_get_available_models(client, auth_headers):
    resp = await client.get("/api/settings/models", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "asr_models" in data
    assert "faster_whisper" in data["asr_models"]
    assert "whisper_cpp" in data["asr_models"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_settings.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/schemas/settings.py**

```python
"""Settings schemas."""

from typing import List

from pydantic import BaseModel


class SettingsResponse(BaseModel):
    storage_base_path: str
    default_asr_model: str
    default_whisper_model: str
    llm_api_base: str
    llm_model: str


class SettingsUpdate(BaseModel):
    storage_base_path: str | None = None
    default_asr_model: str | None = None
    default_whisper_model: str | None = None
    llm_api_base: str | None = None
    llm_model: str | None = None


class AvailableModels(BaseModel):
    asr_models: List[str]
    whisper_sizes: List[str]
```

- [ ] **Step 4: Write app/api/settings.py**

```python
"""Settings API routes."""

from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import AvailableModels, SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(user: User = Depends(get_current_user)):
    return SettingsResponse(
        storage_base_path=settings.storage_base_path,
        default_asr_model=settings.default_asr_model,
        default_whisper_model=settings.default_whisper_model,
        llm_api_base=settings.llm_api_base,
        llm_model=settings.llm_model,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate, user: User = Depends(get_current_user)):
    if body.storage_base_path is not None:
        settings.storage_base_path = body.storage_base_path
    if body.default_asr_model is not None:
        settings.default_asr_model = body.default_asr_model
    if body.default_whisper_model is not None:
        settings.default_whisper_model = body.default_whisper_model
    if body.llm_api_base is not None:
        settings.llm_api_base = body.llm_api_base
    if body.llm_model is not None:
        settings.llm_model = body.llm_model

    return SettingsResponse(
        storage_base_path=settings.storage_base_path,
        default_asr_model=settings.default_asr_model,
        default_whisper_model=settings.default_whisper_model,
        llm_api_base=settings.llm_api_base,
        llm_model=settings.llm_model,
    )


@router.get("/models", response_model=AvailableModels)
async def get_available_models(user: User = Depends(get_current_user)):
    return AvailableModels(
        asr_models=["faster_whisper", "whisper_cpp"],
        whisper_sizes=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
    )
```

- [ ] **Step 5: Mount settings router in app/main.py**

Add to imports:
```python
from app.api import auth, tasks, subtitles, preview, settings as settings_api
```

Add in `create_app()`:
```python
    app.include_router(settings_api.router)
```

- [ ] **Step 6: Run tests**

Run: `cd backend && python3 -m pytest tests/test_api/ -v`

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: settings API — get, update, list available models"
```

---

### Task 10: Path Resolver Service

**Files:**
- Create: `backend/app/services/path_resolver.py`
- Test: `backend/tests/test_api/test_path_resolver.py`

- [ ] **Step 1: Write the failing test**

Write `backend/tests/test_api/test_path_resolver.py`:

```python
import pytest

from app.services.path_resolver import PathResolver


def test_resolve_client_to_server_path():
    resolver = PathResolver(
        server_base="/data/media",
        client_mounts={
            "/Volumes/MediaShare": "/data/media",
            "Z:\\": "/data/media",
        },
    )

    # macOS client path
    result = resolver.to_server_path("/Volumes/MediaShare/input/video.mxf")
    assert result == "/data/media/input/video.mxf"

    # Windows client path
    result = resolver.to_server_path("Z:\\input\\video.mxf")
    assert result == "/data/media/input/video.mxf"


def test_resolve_server_to_client_path():
    resolver = PathResolver(
        server_base="/data/media",
        client_mounts={
            "/Volumes/MediaShare": "/data/media",
        },
    )
    result = resolver.to_client_path("/data/media/output/result.mp4", "/Volumes/MediaShare")
    assert result == "/Volumes/MediaShare/output/result.mp4"


def test_server_local_path_unchanged():
    resolver = PathResolver(server_base="/data/media", client_mounts={})
    result = resolver.to_server_path("/data/media/input/video.mxf")
    assert result == "/data/media/input/video.mxf"


def test_unknown_mount_raises():
    resolver = PathResolver(
        server_base="/data/media",
        client_mounts={"/Volumes/MediaShare": "/data/media"},
    )
    with pytest.raises(ValueError, match="Cannot resolve"):
        resolver.to_server_path("/Users/someone/Desktop/video.mxf")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python3 -m pytest tests/test_api/test_path_resolver.py -v`

Expected: FAIL

- [ ] **Step 3: Write app/services/path_resolver.py**

```python
"""Path resolver — converts between client mount paths and server paths."""

from pathlib import PurePosixPath, PureWindowsPath
from typing import Dict


class PathResolver:
    """Translates file paths between client SMB mounts and server-local paths.

    Args:
        server_base: The base path on the server (e.g., "/data/media")
        client_mounts: Mapping of client mount point → server path
            e.g., {"/Volumes/MediaShare": "/data/media", "Z:\\": "/data/media"}
    """

    def __init__(self, server_base: str, client_mounts: Dict[str, str]):
        self.server_base = server_base
        self.client_mounts = client_mounts

    def to_server_path(self, client_path: str) -> str:
        """Convert a client-side path to the server-side equivalent."""
        # Normalize backslashes for Windows paths
        normalized = client_path.replace("\\", "/")

        # Check if it's already a server path
        if normalized.startswith(self.server_base):
            return normalized

        # Try each known mount
        for mount, server_path in self.client_mounts.items():
            mount_normalized = mount.replace("\\", "/").rstrip("/")
            if normalized.startswith(mount_normalized):
                relative = normalized[len(mount_normalized):]
                return server_path.rstrip("/") + relative

        raise ValueError(f"Cannot resolve path: {client_path}")

    def to_client_path(self, server_path: str, client_mount: str) -> str:
        """Convert a server-side path to a client-side equivalent."""
        if not server_path.startswith(self.server_base):
            raise ValueError(f"Path not under server base: {server_path}")

        relative = server_path[len(self.server_base):]
        return client_mount.rstrip("/") + relative
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python3 -m pytest tests/test_api/test_path_resolver.py -v`

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/path_resolver.py backend/tests/test_api/test_path_resolver.py
git commit -m "feat: path resolver — client mount ↔ server path translation"
```

---

### Task 11: Server Entry Point + Push

**Files:**
- Create: `backend/run.py`
- Modify: `backend/pyproject.toml` (add async dependencies)

- [ ] **Step 1: Write backend/run.py**

```python
"""Server entry point — run with: python run.py"""

import uvicorn

from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=True,
    )
```

- [ ] **Step 2: Update pyproject.toml dependencies**

Add these to the `dependencies` list in `backend/pyproject.toml`:

```toml
    "aiosqlite>=0.20.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.27.0",
    "pytest-asyncio>=0.24.0",
```

- [ ] **Step 3: Run full test suite**

```bash
cd backend && python3 -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 4: Commit and push**

```bash
git add backend/
git commit -m "feat: server entry point + update dependencies"
git push origin main
```

---

## Task Summary

| Task | Description | Key Files |
|------|-------------|-----------|
| 1 | FastAPI skeleton + health endpoint | app/main.py, app/config.py |
| 2 | Database + User model | app/database.py, app/models/user.py |
| 3 | Auth service + register/login API | app/services/auth.py, app/api/auth.py |
| 4 | Task model + CRUD API + queue status | app/models/task.py, app/api/tasks.py |
| 5 | Task queue + pipeline orchestrator | app/services/task_queue.py, app/services/pipeline.py |
| 6 | WebSocket handlers | app/ws/handlers.py |
| 7 | Subtitle API (get/save/export) | app/api/subtitles.py |
| 8 | Preview API (video/waveform/thumbnail) | app/api/preview.py |
| 9 | Settings API | app/api/settings.py |
| 10 | Path resolver service | app/services/path_resolver.py |
| 11 | Server entry point + push | run.py |

**Phase 2 output:** A fully functional FastAPI backend with:
- JWT auth (register/login)
- Task CRUD + FIFO queue + background processing worker
- WebSocket for real-time progress
- Subtitle get/save/export
- Video preview streaming + waveform + thumbnails
- Settings management
- Path resolver for SMB mount mapping
- All endpoints tested
- Ready for Phase 3 (Glossary, TM, Back-translation) and Phase 4 (Tauri frontend)
