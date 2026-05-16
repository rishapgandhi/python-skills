---
name: python-standards
description: AurigaIT Python AI-SDLC enterprise coding standards
---

# Python AI-SDLC Standards

## Overview

This skill provides the AurigaIT Python enterprise coding standards. All code generated must follow these standards.

## Prerequisites

- Python 3.11+ project
- One of: FastAPI, Django, DRF, or Flask

## Instructions

### Before Writing Code

1. Read `skills/common/code-style.md` — always loaded.
2. Identify the framework and read `skills/{framework}/SKILL.md`.
3. Follow layer discipline: API → Service → Repository → Model.

### Non-Negotiable Rules

- 4 spaces indentation, no tabs
- Full type annotations on all function signatures
- No hardcoded secrets — pydantic-settings only
- structlog for all logging — never print()
- ORM/repository for DB access — no raw SQL unless parameterised
- Tests mandatory — 80% coverage minimum
- All endpoints authenticated unless explicitly public
- Never bare `except:` — catch specific exceptions
- Monetary values: Decimal, never float

### Skill Files

Load from `skills/common/` based on task:

| Task | File |
|------|------|
| Any Python | `code-style.md` |
| New project | `folder-structure.md` |
| Errors | `error-handling.md` |
| Logging | `logging.md` |
| Security | `security.md`, `api-auth.md` |
| Tests | `testing.md` |
| Database | `db-design.md`, `data-migrations.md` |
| Performance | `performance.md` |
| CI/CD | `ci-cd.md` |
| Deploy | `deployment.md` |
| Monitoring | `observability.md` |
| Async/Events | `async-patterns.md` |
| Multi-service | `microservices.md` |
| Feature flags | `feature-flags.md` |
| Dependencies | `dependency-management.md` |
| LLM/AI | `llm-patterns.md` |

### Rules

- `rules/api-design.md` — REST conventions
- `rules/git-workflow.md` — Branching, releases
- `rules/code-review.md` — Review process

## Verification

- Code passes `ruff check .`
- Code passes `mypy app/ --strict`
- Tests pass with `pytest --cov-fail-under=80`
