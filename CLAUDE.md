# Python AI-SDLC Framework — Master Context

> **Universal skills, rules and standards for AI-assisted Python development.**
> Compatible with: Claude Code · Cursor · Kiro · Windsurf · Gemini Code Assist · GitHub Copilot · Amazon Q
> Target experience level: 18-20 years of professional Python development.

---

## AGENT CONTRACT — READ BEFORE EVERY CODING TASK

1. Read this file entirely before writing any code.
2. Check `[project] requires-python` in `pyproject.toml` before using ANY version-specific syntax.
3. Load `skills/common/code-style.md` for every task — no exceptions.
4. Load the framework-specific `skills/{framework}/SKILL.md` for the project's framework.
5. Load domain-specific skills (`skills/common/security.md`, `db-design.md`, etc.) when relevant.
6. Cite the rule you are enforcing when you make a style or architectural decision.
7. Ask before assuming framework version, DB engine, auth mechanism, or Python version.
8. Never delete existing migrations, test files, or `.env.example` entries.
9. When in doubt between two approaches, choose the one that is more explicit and testable.

---

## NON-NEGOTIABLE RULES (always active — no exceptions)

| # | Rule | Source |
|---|---|---|
| 1 | Check `requires-python` before using version-specific syntax | code-style.md §1.3 |
| 2 | 4 spaces indentation. No tabs. | PEP 8, code-style.md §2.1 |
| 3 | All public functions/methods/classes must have docstrings | PEP 257, code-style.md §7 |
| 4 | Full type annotations on all function signatures | PEP 484, code-style.md §9 |
| 5 | No hardcoded secrets — all config via pydantic-settings | security.md §1 |
| 6 | All logging uses structlog — no `print()` in production code | logging.md |
| 7 | All DB access through ORM/repository — no raw SQL unless parameterised | db-design.md §6 |
| 8 | Tests mandatory for all business logic — 80% coverage minimum | testing.md |
| 9 | All API endpoints authenticated unless explicitly marked public | security.md §2 |
| 10 | Layer discipline enforced — API→Service→Repository→Model | folder-structure.md §3.2 |
| 11 | Never use mutable default arguments | code-style.md §10.7 |
| 12 | Always catch specific exceptions — never bare `except:` | error-handling.md §4.1 |
| 13 | Never compare to None with `==` — always use `is` / `is not` | code-style.md §10.1 |
| 14 | Exceptions derive from Exception, not BaseException | error-handling.md §1.1 |
| 15 | All monetary values use Decimal, never float | db-design.md §7 |

---

## FILE STRUCTURE

```
CLAUDE.md                         ← you are here (master context)
.cursorrules                      ← Cursor / Kiro / Windsurf auto-load
skills/
  common/
    code-style.md                 ← PEP 8 full compliance + modern Python
    folder-structure.md           ← 5 project archetypes + layer contract
    error-handling.md             ← exception hierarchy + HTTP mapping
    logging.md                    ← structlog setup + field vocabulary
    security.md                   ← OWASP + auth + input validation
    testing.md                    ← pytest + factories + coverage rules
    db-design.md                  ← SQLAlchemy 2.x + Alembic + indexing
    performance.md                ← async, caching, N+1 prevention, pagination
    llm-patterns.md               ← prompt mgmt, LLM client abstraction, context
  fastapi/SKILL.md
  django/SKILL.md
  drf/SKILL.md
  flask/SKILL.md
rules/
  api-design.md
  git-workflow.md
agents/
  qa-agent.md
docs/
  onboarding.md
  adr/                            ← architecture decision records
```

---

## HOW TO PRIME AN AGENT FOR A PROJECT

Add to your project's CLAUDE.md (or first message):

```
This project uses [framework] with [database] on Python [version].
requires-python = ">=3.11"
Load skills/[framework]/SKILL.md as the primary framework skill.
```

Or in Claude Code:
```
/load-skill fastapi
```

---

## MODERN CURSOR RULES (.cursor/rules/*.mdc)

For Cursor ≥0.45, the authoritative rules are in `.cursor/rules/`:

| File | Globs | alwaysApply |
|---|---|---|
| `python-core.mdc` | `**/*.py` | true |
| `python-security.mdc` | `**/*.py` | true |
| `python-fastapi.mdc` | `app/api/**`, `app/main.py` | false (auto-attached by glob) |
| `python-django.mdc` | `**/models.py`, `**/views.py`, etc. | false (auto-attached by glob) |
| `python-testing.mdc` | `tests/**/*.py` | false (auto-attached by glob) |

The `.cursorrules` root file is kept for backward compatibility with older Cursor versions and other tools (Kiro, Windsurf).
