# Python AI-SDLC Framework — Developer Onboarding

## What Is This?

This repository is the **Python AI-SDLC skill set** — a set of rules, standards, and skill files that AI coding agents (Claude Code, Cursor, Kiro, Gemini, etc.) use to generate consistent, production-quality Python code across all AurigaIT Python projects.

Think of it as a shared engineering brain that every agent reads before touching your code.

---

## Quick Setup for a New Project

### Step 1 — Copy skill files into your project

```bash
# From your project root
git clone https://github.com/aurigait/python-ai-sdlc skills-ref

# Copy the relevant files
cp -r skills-ref/skills ./skills
cp -r skills-ref/rules ./rules
cp -r skills-ref/agents ./agents
cp -r skills-ref/.claude ./.claude
cp skills-ref/CLAUDE.md ./CLAUDE.md
cp skills-ref/.cursorrules ./.cursorrules
```

### Step 2 — Tell the agent your framework

Add to the top of your `CLAUDE.md` (or in your first prompt):

```
This project uses FastAPI with PostgreSQL and Redis.
Load skills/fastapi/SKILL.md as the primary framework skill.
```

### Step 3 — Start coding

For Claude Code:
```bash
claude code
# Then use /load-skill fastapi to prime the agent
```

For Cursor: The `.cursorrules` file is auto-loaded.

For Kiro: Point to `CLAUDE.md` as the project spec.

---

## File Guide

| File | Read When |
|---|---|
| `CLAUDE.md` | Always — master context |
| `skills/common/code-style.md` | Writing any Python |
| `skills/common/folder-structure.md` | Starting a new project or module |
| `skills/common/logging.md` | Adding any logging |
| `skills/common/error-handling.md` | Writing error handling |
| `skills/common/security.md` | Anything touching auth, input, secrets |
| `skills/common/testing.md` | Writing tests |
| `skills/common/db-design.md` | Creating or modifying models |
| `skills/fastapi/SKILL.md` | FastAPI projects |
| `skills/django/SKILL.md` | Django projects |
| `skills/drf/SKILL.md` | DRF projects |
| `skills/flask/SKILL.md` | Flask projects |
| `rules/api-design.md` | Designing or reviewing API endpoints |
| `agents/qa-agent.md` | Setting up automated QA in pipeline |
| `.claude/commands/README.md` | Claude Code slash-commands reference |

---

## Keeping Skills Updated

This framework is a living document. When you discover a new best practice or fix a gap:

1. Update the relevant skill file.
2. Create a PR with a clear description of what changed and why.
3. Tag it `skills-update`.
4. Notify the team on Slack — other project teams need to pull the update.

**Cadence:** Review and update skill files during each sprint retrospective.

---

## Contact

Python SDLC framework owner: **Your Name**
Team: AurigaIT Engineering Platform
Last Updated: May 2026
