# FastAPI Skill

> Load this file when working on a FastAPI project. Use alongside all `skills/common/` files.

---

## Stack

| Layer | Library |
|---|---|
| Framework | FastAPI 0.111+ |
| ASGI Server | Uvicorn with Gunicorn workers (prod) |
| ORM | SQLAlchemy 2.x async + Alembic |
| Validation | Pydantic v2 |
| Auth | python-jose / PyJWT + passlib |
| HTTP Client | httpx (async) |
| Task Queue | Celery + Redis (or ARQ for lighter workloads) |
| Settings | pydantic-settings |

---

## Project Structure (FastAPI-specific additions)

```
app/
├── main.py                   ← App factory: create_app()
├── core/
│   ├── config.py
│   ├── security.py
│   ├── exceptions.py
│   └── logging.py
├── api/
│   ├── deps.py               ← Shared FastAPI dependencies
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── router.py         ← Aggregates all v1 routers
│   │   ├── users.py
│   │   ├── auth.py
│   │   └── health.py
├── models/                   ← SQLAlchemy ORM models
├── schemas/                  ← Pydantic request/response models
├── repositories/
├── services/
└── workers/                  ← Background task definitions
```

---

## App Factory Pattern

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.exceptions import AppBaseException, app_exception_handler
from app.api.v1.router import v1_router

def create_app() -> FastAPI:
    """Application factory."""
    configure_logging(log_level=settings.log_level, json_logs=not settings.debug)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,   # hide Swagger in prod
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, ...)
    app.add_exception_handler(AppBaseException, app_exception_handler)
    app.include_router(v1_router, prefix="/api/v1")

    return app

app = create_app()
```

---

## Dependency Injection

```python
# app/api/deps.py
from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.security import decode_token
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService

bearer_scheme = HTTPBearer()

async def get_db() -> AsyncSession:
    async with get_session() as session:
        yield session

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    repo = UserRepository(session)
    user = await repo.find_by_id(int(payload["sub"]))
    if not user or not user.is_active:
        raise AuthenticationError()
    return user
```

---

## Router + Endpoint Pattern

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user, get_db
from app.schemas.user import UserCreateRequest, UserResponse, UserListResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserListResponse:
    """List all users with pagination."""
    service = UserService(UserRepository(session))
    return await service.list_users(page=page, page_size=page_size)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreateRequest,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Create a new user account."""
    service = UserService(UserRepository(session))
    return await service.create_user(data)
```

---

## Pydantic Schemas

```python
# app/schemas/user.py
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class UserBase(BaseModel):
    email: str
    name: str

class UserCreateRequest(UserBase):
    password: str = Field(min_length=8)

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)  # enables ORM mode

    id: int
    is_active: bool
    created_at: datetime

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
```

---

## Database Session

```python
# app/core/database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Background Tasks

For CPU-light tasks: use FastAPI `BackgroundTasks`.
For heavy/reliable tasks: use **Celery**.

```python
# Lightweight (email sending, audit logging)
@router.post("/users/")
async def create_user(data: UserCreateRequest, background_tasks: BackgroundTasks):
    user = await service.create_user(data)
    background_tasks.add_task(send_welcome_email, user.email)
    return user
```

---

## Health Check Endpoint

Every service must expose:

```python
@router.get("/health", include_in_schema=False)
async def health_check(session: AsyncSession = Depends(get_db)) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "version": settings.app_version}
```

---

## LIFESPAN CONTEXT MANAGER (replaces deprecated @app.on_event)

`@app.on_event("startup")` and `@app.on_event("shutdown")` are deprecated since FastAPI 0.93.
Always use the `lifespan` context manager:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — runs once before the app begins accepting requests
    await db_pool.connect()
    configure_logging(json_output=not settings.debug)
    logger.info("app_started", version=settings.app_version)

    yield   # application runs here

    # Shutdown — runs once after the last request is handled
    await db_pool.disconnect()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    return FastAPI(lifespan=lifespan, ...)
```

---

## ANNOTATED DEPENDENCIES (Python 3.9+)

Define reusable dependency annotations at module level for cleaner route signatures:

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Define once in deps.py
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]

# Use cleanly in every route
@router.get("/orders/", response_model=OrderListResponse)
async def list_orders(
    db: DbSession,
    current_user: CurrentUser,
    page: int = 1,
) -> OrderListResponse:
    ...
```

---

## RORO IN FASTAPI ROUTES

All routes receive a Pydantic request model (or query params for GETs) and return a Pydantic response model.
Never accept `dict` or return `dict` from a route.

```python
# CORRECT — RORO
@router.post("/orders/", response_model=OrderResponse, status_code=201)
async def create_order(data: OrderCreate, db: DbSession, user: CurrentUser) -> OrderResponse:
    return await order_service.create_order(user_id=user.id, data=data)

# WRONG — raw dict in, raw dict out
@router.post("/orders/")
async def create_order(request: Request) -> dict:
    body = await request.json()
    ...
```
