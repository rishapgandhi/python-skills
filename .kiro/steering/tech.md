# Technology Stack

## Language & Runtime

- **Python 3.11+** (check `requires-python` in pyproject.toml before using version-specific syntax)
- Type checking: mypy --strict
- Linting/formatting: Ruff 0.4+

## Frameworks (project-specific — load the relevant SKILL.md)

| Framework | Skill file | Use case |
|-----------|-----------|----------|
| FastAPI 0.111+ | `skills/fastapi/SKILL.md` | Async APIs, microservices |
| Django 5.x | `skills/django/SKILL.md` | Full-stack web apps |
| DRF 3.15+ | `skills/drf/SKILL.md` | Django REST APIs |
| Flask 3.x | `skills/flask/SKILL.md` | Lightweight APIs, internal tools |

## Core Libraries

| Purpose | Library | Notes |
|---------|---------|-------|
| ORM | SQLAlchemy 2.x (async) / Django ORM | See `skills/common/db-design.md` |
| Validation | Pydantic v2 | All request/response schemas |
| Config | pydantic-settings | All secrets from env vars |
| Logging | structlog | Never print() — see `skills/common/logging.md` |
| HTTP client | httpx (async) | For external API calls |
| Testing | pytest + factory_boy + pytest-asyncio | See `skills/common/testing.md` |
| Migrations | Alembic / Django migrations | See `skills/common/data-migrations.md` |
| Task queue | Celery + Redis (or ARQ) | See `skills/common/async-patterns.md` |
| Observability | OpenTelemetry | See `skills/common/observability.md` |

## Architecture Principles

- Layer discipline: API → Service → Repository → Model
- 12-factor app compliance (see `skills/common/deployment.md`)
- Domain exceptions with HTTP mapping (see `skills/common/error-handling.md`)
- All endpoints authenticated unless explicitly public

## Development Tools

- Git workflow: Conventional Commits, squash merge (see `rules/git-workflow.md`)
- CI: GitHub Actions (see `skills/common/ci-cd.md`)
- Containers: Docker multi-stage builds (see `skills/common/deployment.md`)
