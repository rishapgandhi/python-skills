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

## First PR Workflow (Target: Day 2)

### Day 1 — Setup & Context

1. Clone the project repo and run the setup script.
2. Read `CLAUDE.md` and `skills/common/folder-structure.md` to understand the architecture.
3. Run the test suite locally — ensure everything passes.
4. Read the last 5 merged PRs to understand team conventions.
5. Pick a starter ticket (labelled `good-first-issue` or assigned by your buddy).

### Day 2 — First PR

1. Create a feature branch: `feature/TICKET-123-short-description`
2. Implement the change following the skill files.
3. Write tests (minimum: happy path + one edge case).
4. Run locally: `ruff check . && mypy app/ --strict && pytest`
5. Self-review your diff before pushing.
6. Open PR with description: what, why, how to test.
7. Request review from your assigned buddy.

### First Week Checklist

- [ ] Local dev environment running (Docker, DB, Redis)
- [ ] First PR merged
- [ ] Attended one standup
- [ ] Read `rules/code-review.md` — understand review expectations
- [ ] Read `docs/incident-response.md` — know the escalation path
- [ ] Access to: Slack channels, Jira/Linear, CI dashboard, monitoring

---

## Mentoring Structure

### Buddy System

Every new developer is assigned a **buddy** (senior dev on the same team):

| Buddy responsibility | Timeline |
|---------------------|----------|
| Pair on first PR | Day 1-2 |
| Review all PRs for first 2 weeks | Week 1-2 |
| Daily 15-min check-in | Week 1-2 |
| Weekly 30-min check-in | Week 3-4 |
| Available for questions async | Ongoing |

### Buddy Selection Criteria

- Same team, same project
- At least 6 months tenure on the project
- Volunteers (not assigned against will)

### What the Buddy Does NOT Do

- Performance evaluation
- Task assignment
- Escalation decisions

---

## Ramp-Up Expectations

| Timeframe | Expected capability |
|-----------|-------------------|
| **Week 1** | Environment setup, first PR merged, understands project structure |
| **Week 2** | Handles small bug fixes independently, writes tests |
| **Week 4** | Delivers small features end-to-end (API + tests + docs) |
| **Week 6** | Participates in code reviews, handles medium features |
| **Week 8** | Fully autonomous on standard tasks, starts reviewing others' PRs |
| **Month 3** | Contributes to architectural discussions, mentors newer joiners |

### Signs of Healthy Ramp-Up

- Asking questions (not staying stuck silently)
- PRs getting smaller over time (learning to scope)
- Fewer review comments per PR over time
- Starting to catch issues in others' code reviews

### Signs of Trouble (Lead should intervene)

- No PR by end of Day 3
- Same review feedback repeated across multiple PRs
- Not asking questions (may be stuck or disengaged)
- Scope creep on tickets (trying to do too much)

---

## Key Resources for New Developers

| Resource | Purpose |
|----------|---------|
| `CLAUDE.md` | Master contract — read first |
| `skills/common/code-style.md` | How we write Python |
| `rules/code-review.md` | How we review code |
| `rules/git-workflow.md` | Branching, commits, PRs |
| `docs/adr/` | Why past decisions were made |
| `examples/fastapi-app/` | Reference implementation |
| `docs/incident-response.md` | What to do when things break |

---

## Contact

Python SDLC framework owner: **Rishap / Ravi**
Team: AurigaIT Engineering Platform
Last Updated: May 2026
