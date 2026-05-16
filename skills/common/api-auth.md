# API Authentication & Authorization — Enterprise Standard

**Applies to:** All Python APIs serving external or internal consumers.
**Stack:** PyJWT / python-jose, OAuth2 (authlib), passlib, RBAC/ABAC patterns.

---

## SECTION 1 — AUTHENTICATION METHODS

| Method | Use when | Security level |
|--------|----------|---------------|
| JWT (Bearer token) | User-facing APIs, SPAs, mobile | High |
| API Key | Third-party integrations, webhooks | Medium |
| OAuth2 Client Credentials | Service-to-service | High |
| mTLS | Internal microservices, zero-trust | Very High |
| Session cookie | Server-rendered web apps | High (with CSRF) |

**Rule:** Never use API keys as the sole auth for user-facing endpoints. API keys are for machine clients.

---

## SECTION 2 — JWT LIFECYCLE

### Token Structure

```python
# Access token payload
{
    "sub": "user_uuid",          # Subject — user identifier
    "exp": 1717200000,           # Expiry — short-lived (15-30 min)
    "iat": 1717198200,           # Issued at
    "jti": "unique-token-id",    # JWT ID — for revocation
    "scopes": ["read", "write"], # Permissions
    "org_id": "org_uuid",        # Tenant context
}
```

### Token Pair Pattern

```python
# app/core/security.py
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)


def create_access_token(user_id: str, scopes: list[str]) -> str:
    """Short-lived access token."""
    payload = {
        "sub": user_id,
        "scopes": scopes,
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    """Long-lived refresh token — stored in httpOnly cookie or secure storage."""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.refresh_secret_key, algorithm="HS256")


def verify_token(token: str, token_type: str = "access") -> dict:
    """Verify and decode token. Raises on expiry or tampering."""
    secret = settings.secret_key if token_type == "access" else settings.refresh_secret_key
    return jwt.decode(token, secret, algorithms=["HS256"])
```

### Token Refresh Flow

```
1. Client sends expired access token → 401
2. Client sends refresh token to /auth/refresh
3. Server validates refresh token, issues new access + refresh pair
4. Old refresh token is revoked (rotation)
```

### Token Revocation

```python
# Store revoked JTIs in Redis with TTL matching token expiry
async def revoke_token(jti: str, expires_in: int) -> None:
    await redis.setex(f"revoked:{jti}", expires_in, "1")

async def is_token_revoked(jti: str) -> bool:
    return await redis.exists(f"revoked:{jti}")
```

---

## SECTION 3 — OAUTH2 FLOWS

### Authorization Code Flow (user-facing apps)

```python
# Using authlib
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/auth/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    # Create or update local user, issue JWT pair
    ...
```

### Client Credentials Flow (service-to-service)

```python
# Service A calling Service B
import httpx

async def get_service_token() -> str:
    """Obtain token for service-to-service communication."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.auth_server_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.service_client_id,
                "client_secret": settings.service_client_secret,
                "scope": "orders:read orders:write",
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]
```

---

## SECTION 4 — RBAC (Role-Based Access Control)

```python
# app/core/permissions.py
from enum import StrEnum
from functools import wraps
from fastapi import HTTPException, status


class Role(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role hierarchy — higher roles inherit lower permissions
ROLE_HIERARCHY: dict[Role, set[str]] = {
    Role.VIEWER: {"read"},
    Role.EDITOR: {"read", "write", "delete_own"},
    Role.ADMIN: {"read", "write", "delete_own", "delete_any", "manage_users"},
    Role.SUPER_ADMIN: {"read", "write", "delete_own", "delete_any", "manage_users", "manage_org"},
}


def require_permission(permission: str):
    """Dependency that checks user has required permission via their role."""
    def dependency(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_HIERARCHY.get(current_user.role, set())
        if permission not in user_permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return Depends(dependency)


# Usage in endpoint
@router.delete("/users/{user_id}")
async def delete_user(user_id: int, user: User = require_permission("delete_any")):
    ...
```

---

## SECTION 5 — ABAC (Attribute-Based Access Control)

For complex authorization beyond roles:

```python
# app/core/policies.py
from dataclasses import dataclass


@dataclass
class AccessContext:
    user_id: str
    user_role: str
    user_org_id: str
    resource_owner_id: str
    resource_org_id: str
    action: str


def evaluate_policy(ctx: AccessContext) -> bool:
    """Evaluate access based on multiple attributes."""
    # Super admin can do anything
    if ctx.user_role == "super_admin":
        return True

    # Users can only access resources in their org
    if ctx.user_org_id != ctx.resource_org_id:
        return False

    # Owners can edit their own resources
    if ctx.action in ("update", "delete") and ctx.user_id == ctx.resource_owner_id:
        return True

    # Admins can manage anything in their org
    if ctx.user_role == "admin":
        return True

    # Editors can read and create
    if ctx.user_role == "editor" and ctx.action in ("read", "create"):
        return True

    return False
```

---

## SECTION 6 — API KEY MANAGEMENT

```python
# app/core/api_keys.py
import secrets
import hashlib

def generate_api_key() -> tuple[str, str]:
    """Generate API key. Return (raw_key, hashed_key).
    Store hashed_key in DB. Show raw_key to user ONCE.
    """
    raw_key = f"sk_{secrets.token_urlsafe(32)}"
    hashed = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, hashed


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    computed = hashlib.sha256(raw_key.encode()).hexdigest()
    return secrets.compare_digest(computed, stored_hash)
```

### API Key Rules

- Prefix keys for identification: `sk_live_`, `sk_test_`, `pk_`
- Hash before storing — never store raw keys in DB.
- Support key rotation: allow multiple active keys per client.
- Set expiry dates — no permanent keys.
- Rate-limit per key, not just per IP.
- Log key usage for audit trail.

---

## SECTION 7 — SERVICE-TO-SERVICE AUTH

### Option A: Signed JWTs (lightweight)

```python
# Each service has its own signing key
# Service A signs a request token, Service B verifies with A's public key
SERVICE_KEYS = {
    "order-service": "public_key_of_order_service",
    "payment-service": "public_key_of_payment_service",
}
```

### Option B: mTLS (zero-trust)

```yaml
# In Kubernetes / service mesh (Istio, Linkerd)
# Automatic mTLS between services — no application code needed
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: STRICT
```

### Rules

- Internal services MUST authenticate each other — no "trusted network" assumptions.
- Propagate correlation IDs and user context in headers (`X-Request-ID`, `X-User-ID`).
- Use short-lived tokens (5 min max) for service-to-service calls.
- Rotate service credentials automatically (Vault, AWS Secrets Manager).
