# Security — Enterprise Standard

**Applies to:** All Python projects handling user data, authentication, or external APIs.
**Authority:** OWASP Top 10 (2021), CWE/SANS Top 25, PCI DSS for payment code, GDPR for PII handling.

---

## SECTION 1 — SECRETS MANAGEMENT

### 1.1 Non-negotiable rules

```python
# RULE 1 — No secrets in source code. Ever. No exceptions.
DATABASE_URL = "postgresql://admin:password@localhost/mydb"   # WRONG — commit history is forever

# RULE 2 — All secrets via environment variables
from app.core.config import settings
db_url = settings.database_url   # CORRECT

# RULE 3 — pydantic-settings for config loading with validation
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",   # ignore unknown env vars; prevents noise
    )

    # Required — will raise ValidationError at startup if missing
    database_url: str
    secret_key: str = Field(min_length=32)   # enforce minimum entropy

    # Optional with defaults
    debug: bool = False
    log_level: str = "INFO"
    allowed_hosts: list[str] = []

    # Sensitive fields — redacted in repr/logs automatically
    stripe_secret_key: str = Field(repr=False)   # never printed in logs
    smtp_password: str = Field(repr=False)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}")
        return v.upper()


settings = Settings()  # fails fast at startup if config is invalid
```

### 1.2 .env.example — always committed

```bash
# .env.example — all keys present, no real values, descriptive comments
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb
SECRET_KEY=change-me-to-a-random-32-plus-character-string
DEBUG=false
LOG_LEVEL=INFO
ALLOWED_HOSTS=localhost,127.0.0.1

# Stripe integration
STRIPE_SECRET_KEY=sk_test_...   # get from https://dashboard.stripe.com/apikeys

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=change-me
```

### 1.3 Production secrets management

Never use `.env` files in production environments. Use:
- AWS Secrets Manager / Parameter Store
- HashiCorp Vault
- GCP Secret Manager
- Azure Key Vault
- Kubernetes Secrets (with encryption at rest)

---

## SECTION 2 — AUTHENTICATION

### 2.1 JWT Standards

```python
# app/core/security.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt  # PyJWT; use jwt>=2.0 (breaking API from 1.x)
from app.core.config import settings
from app.core.exceptions import AuthenticationError

ALGORITHM = "HS256"   # Use RS256 for multi-service architectures (asymmetric key)

# Token lifetimes — never negotiate these downward
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)    # short; stolen tokens expire quickly
REFRESH_TOKEN_LIFETIME = timedelta(days=7)       # longer; stored server-side for revocation


def create_access_token(
    subject: str | int,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: User identifier (typically user.id as str).
        extra_claims: Additional payload claims. Do NOT include sensitive data.

    Returns:
        Encoded JWT string. Valid for ACCESS_TOKEN_LIFETIME.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "iss": settings.app_name,    # issuer claim
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Validates: signature, expiry, issuer, token type.

    Args:
        token: JWT string from Authorization header.

    Returns:
        Decoded payload dict.

    Raises:
        AuthenticationError: If token is invalid, expired, or tampered.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={
                "verify_exp": True,
                "verify_iss": True,
                "require": ["sub", "exp", "iat", "iss", "type"],
            },
            issuer=settings.app_name,
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please log in again.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid token: {exc}") from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Token type is not 'access'.")

    return payload
```

### 2.2 Password Hashing

```python
from passlib.context import CryptContext

# bcrypt with cost factor 12 — the minimum acceptable for production
# Cost factor 12 → ~300ms per hash on modern hardware — intentionally slow
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        plain_password: User-supplied plain-text password.

    Returns:
        bcrypt hash string. Safe to store in database.

    Note:
        This function is intentionally slow (300ms+) to resist brute-force.
        Never call it in a hot path or inside a loop.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored hash.

    Args:
        plain_password: User-supplied password to verify.
        hashed_password: Hash retrieved from database.

    Returns:
        True if password matches. False otherwise.

    Note:
        Uses constant-time comparison to prevent timing attacks.
    """
    return _pwd_context.verify(plain_password, hashed_password)
```

---

## SECTION 3 — INPUT VALIDATION

### 3.1 All user input must pass through Pydantic before use

```python
# CORRECT — Pydantic validates before any code sees the data
@router.post("/users/")
async def create_user(data: UserCreateRequest) -> UserResponse:
    # data is validated; email is valid format, password meets complexity
    return await user_service.create_user(data)

# WRONG — raw dict from request body used directly
@router.post("/users/")
async def create_user(request: Request) -> dict:
    body = await request.json()   # no validation; any shape accepted
    return await user_service.create_user(body)
```

### 3.2 Complex validation with Pydantic v2

```python
from pydantic import BaseModel, field_validator, model_validator, Field
import re


class UserCreateRequest(BaseModel):
    """Request schema for creating a new user account."""

    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    role: str = Field(default="viewer")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip().lower()
        # RFC 5322 simplified pattern
        if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email address format.")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        errors = []
        if not re.search(r"[A-Z]", v):
            errors.append("at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("at least one lowercase letter")
        if not re.search(r"\d", v):
            errors.append("at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("at least one special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"viewer", "editor", "admin"}
        if v not in allowed:
            raise ValueError(f"Role must be one of: {allowed}.")
        return v

    @model_validator(mode="after")
    def validate_admin_age_requirement(self) -> "UserCreateRequest":
        """Admins must be at least 18 years old."""
        if self.role == "admin" and self.age < 18:
            raise ValueError("Admin users must be at least 18 years old.")
        return self
```

---

## SECTION 4 — SQL INJECTION PREVENTION

```python
# CORRECT — ORM with parameterised queries (always safe)
result = await session.execute(
    select(User).where(User.email == email)    # parameterised internally by SQLAlchemy
)

# CORRECT — explicit parameterised text() when raw SQL is necessary
from sqlalchemy import text
result = await session.execute(
    text("SELECT * FROM users WHERE email = :email AND tenant_id = :tid"),
    {"email": email, "tid": tenant_id},   # parameters; never interpolated
)

# WRONG — string interpolation into SQL — classic SQL injection
result = await session.execute(
    text(f"SELECT * FROM users WHERE email = '{email}'")   # CRITICAL VULNERABILITY
)

# WRONG — .format() is equally dangerous
query = "SELECT * FROM users WHERE name = '{}'".format(name)   # CRITICAL VULNERABILITY
```

---

## SECTION 5 — RATE LIMITING

```python
# Apply to all authentication endpoints and public-facing APIs

# FastAPI with slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Authentication endpoints — strict limits to prevent credential stuffing
@router.post("/auth/login")
@limiter.limit("5/minute")               # 5 attempts per minute per IP
async def login(request: Request, data: LoginRequest) -> TokenResponse:
    ...

@router.post("/auth/forgot-password")
@limiter.limit("3/hour")                 # 3 resets per hour per IP
async def forgot_password(request: Request, data: ForgotPasswordRequest):
    ...

# API endpoints — generous but bounded
@router.get("/users/")
@limiter.limit("100/minute")             # authenticated users: 100/min
async def list_users(request: Request):
    ...
```

---

## SECTION 6 — CORS

```python
# WRONG — wildcard in production
CORSMiddleware(allow_origins=["*"])   # allows any origin to make credentialed requests

# CORRECT — explicit allowlist from config
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,         # ["https://app.example.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],                # headers visible to JS
    max_age=3600,                                   # preflight cache time
)
```

---

## SECTION 7 — RESPONSE SANITISATION

```python
# RULE: response schemas are always distinct from ORM models
# Never return ORM objects directly — always convert through a response schema

# WRONG — ORM model returned directly (may expose password_hash, internal flags)
@router.get("/users/{id}")
async def get_user(id: int) -> User:   # User is the ORM model — dangerous
    return await repo.find_by_id(id)

# CORRECT — Pydantic response schema strips sensitive fields
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_id: UUID
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    # NOT INCLUDED: password_hash, secret_token, internal_flags, ssn, raw_api_key

@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: int) -> UserResponse:
    user = await user_service.get_user(id)
    return UserResponse.model_validate(user)   # Pydantic strips anything not in schema
```

---

## SECTION 8 — DEPENDENCY SECURITY

```python
# In CI pipeline — fail on known CVEs
# pip install pip-audit
# pip-audit --requirement requirements.txt --fail-on-vuln

# pyproject.toml — pin all versions; floating ranges are dangerous in production
[project]
dependencies = [
    "fastapi==0.111.0",
    "sqlalchemy==2.0.29",
    "pydantic==2.7.0",
]

# Update cadence: minimum monthly. Script:
# pip list --outdated
# pip-audit
# safety check (commercial; more comprehensive)
```

---

## SECTION 9 — SECURITY HEADERS (configure at reverse proxy or middleware)

```python
# Apply via middleware in Python if reverse proxy is not available
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # CSP: configure per application
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none';"
        )
        return response
```

---

## SECTION 10 — SECURITY CHECKLIST FOR CODE REVIEW

Use this before approving any PR touching auth, payment, or user data:

```
[ ] No hardcoded credentials, tokens, or passwords anywhere in the diff
[ ] New endpoints have authentication applied (or explicitly documented as public)
[ ] New endpoints have rate limiting applied
[ ] All user input validated through Pydantic schema before use
[ ] No raw SQL — all DB queries use ORM or parameterised text()
[ ] Response schema does not expose sensitive fields
[ ] Passwords hashed with bcrypt before storage
[ ] JWT validated (signature + expiry + type + issuer)
[ ] No sensitive data in log statements
[ ] Exception messages don't expose internal details to API consumers
[ ] No direct access to environment variables (use settings object)
[ ] CORS origins come from config, not hardcoded
[ ] New dependencies checked with pip-audit before adding
```
