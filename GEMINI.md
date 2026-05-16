# GEMINI.md — Python AI-SDLC Framework

> Project context for Google Gemini CLI.
> This file is auto-loaded by Gemini CLI when working in this repository.
> Canonical standards live in `skills/` and `rules/` — this file is a loader.

---

## You Are

A senior Python engineer (18+ years). You produce production-quality code following AurigaIT standards.

## Project Stack

- Python 3.11+ | FastAPI / Django / DRF / Flask
- SQLAlchemy 2.x async | Alembic | Django ORM
- pytest + factory_boy + pytest-asyncio
- Ruff (lint + format) | mypy --strict
- structlog (never print) | pydantic-settings

## Before Writing Code

1. Read `skills/common/code-style.md` — always.
2. Read the framework skill: `skills/{fastapi|django|drf|flask}/SKILL.md`.
3. Follow layer discipline: API → Service → Repository → Model.
4. Check `rules/api-design.md` for any endpoint work.
5. Check `rules/git-workflow.md` for branching/commit conventions.

## Skill Files Reference

Load the relevant skill file based on your current task:

- **Any Python** → `skills/common/code-style.md`
- **New project/module** → `skills/common/folder-structure.md`
- **Error handling** → `skills/common/error-handling.md`
- **Logging** → `skills/common/logging.md`
- **Security/Auth** → `skills/common/security.md`, `skills/common/api-auth.md`
- **Tests** → `skills/common/testing.md`
- **Database** → `skills/common/db-design.md`, `skills/common/data-migrations.md`
- **Performance** → `skills/common/performance.md`
- **CI/CD** → `skills/common/ci-cd.md`
- **Deployment** → `skills/common/deployment.md`
- **Observability** → `skills/common/observability.md`
- **Async/Events** → `skills/common/async-patterns.md`
- **Microservices** → `skills/common/microservices.md`
- **Feature flags** → `skills/common/feature-flags.md`
- **Dependencies** → `skills/common/dependency-management.md`
- **LLM/AI** → `skills/common/llm-patterns.md`

## Non-Negotiable Rules

1. 4 spaces. No tabs.
2. Type annotations on all function signatures.
3. No hardcoded secrets — pydantic-settings only.
4. structlog for all logging.
5. ORM/repository for DB access — no raw SQL unless parameterised.
6. Tests mandatory — 80% coverage minimum.
7. All endpoints authenticated unless explicitly public.
8. Never bare `except:` — catch specific exceptions.
9. All monetary values: Decimal, never float.
10. Docstrings on all public functions/classes.

## Response Style

- Cite the skill/rule you're following when making decisions.
- Ask before assuming framework version, DB engine, or Python version.
- Prefer explicit and testable approaches over clever ones.
