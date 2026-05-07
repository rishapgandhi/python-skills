# Deployment — Enterprise Standard

**Applies to:** All Python projects deployed as containers or services.
**Philosophy:** 12-factor app. Immutable artifacts. Infrastructure as code.

---

## SECTION 1 — DOCKERFILE (Multi-Stage)

```dockerfile
# syntax=docker/dockerfile:1

# ── Build stage ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
COPY app/ app/

RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /build/dist

# ── Production stage ─────────────────────────────────────────
FROM python:3.11-slim AS production

# Security: non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Install only production dependencies
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl

# Copy application code
COPY app/ app/

# Security: drop privileges
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## SECTION 2 — .dockerignore

```
.git
.env
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.ruff_cache
tests/
docs/
*.md
.github/
```

---

## SECTION 3 — HEALTH CHECK ENDPOINT

```python
# app/api/v1/health.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Liveness probe — app is running."""
    return HealthResponse(status="healthy", version=settings.app_version)


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> dict:
    """Readiness probe — dependencies are reachable."""
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
        return JSONResponse(status_code=503, content={"status": "unhealthy", "checks": checks})

    return {"status": "ready", "checks": checks}
```

---

## SECTION 4 — GRACEFUL SHUTDOWN

```python
# app/main.py
import signal
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    # Startup
    await db_pool.connect()
    yield
    # Shutdown — drain connections, finish in-flight requests
    await db_pool.disconnect()
    await http_client.aclose()


app = create_app(lifespan=lifespan)
```

Signal handling for workers:

```python
# Uvicorn handles SIGTERM/SIGINT gracefully by default.
# For custom workers or Celery:
shutdown_event = asyncio.Event()

def handle_sigterm(signum, frame):
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)
```

---

## SECTION 5 — 12-FACTOR COMPLIANCE CHECKLIST

| Factor | Implementation |
|--------|---------------|
| Codebase | One repo per service, tracked in git |
| Dependencies | Declared in `pyproject.toml`, pinned in lockfile |
| Config | Environment variables via pydantic-settings |
| Backing services | Attached via URLs (DATABASE_URL, REDIS_URL) |
| Build/release/run | CI builds image → tag → deploy |
| Processes | Stateless; session state in Redis |
| Port binding | Uvicorn binds port; no external web server required |
| Concurrency | Scale via container replicas, not threads |
| Disposability | Fast startup, graceful shutdown (lifespan) |
| Dev/prod parity | Same Docker image, different env vars |
| Logs | Emit to stdout as JSON; collected externally |
| Admin processes | One-off tasks via `python -m app.scripts.X` |

---

## SECTION 6 — ENVIRONMENT CONFIGURATION

```yaml
# docker-compose.yml (local development)
services:
  app:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev
      POSTGRES_DB: app_dev
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
```

---

## SECTION 7 — RULES

- Never install dev dependencies in production image.
- Always run as non-root user.
- Pin base image to minor version (`python:3.11-slim`, not `python:3-slim`).
- Use multi-stage builds to minimize image size.
- Health check must verify dependency connectivity (readiness), not just process liveness.
- Logs to stdout/stderr only — never write to files inside containers.
- One process per container — no supervisord.
