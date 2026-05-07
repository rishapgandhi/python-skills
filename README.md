# python-agent-standards

> **AurigaIT Python AI-SDLC Framework**
> Skills, rules, and agent definitions that AI coding agents use to generate
> consistent, production-quality Python code across all AurigaIT projects.

Compatible with: **Claude Code · OpenAI Codex · Cursor · Kiro · Windsurf · Gemini CLI · Google Antigravity · GitHub Copilot**

---

## What Is This?

This repository is the shared engineering brain that every AI agent reads before touching your code.
It encodes 18+ years of Python best practice into structured skill files that agents load as context.

## Multi-Tool Setup

Every AI tool reads its own config file, but all reference the same `skills/` directory:

| Tool | Config file | Auto-loaded? |
|------|------------|:---:|
| Claude Code | `CLAUDE.md` | ✅ |
| OpenAI Codex | `AGENTS.md` | ✅ |
| Kiro | `.kiro/steering/*.md` + `AGENTS.md` | ✅ |
| Cursor | `.cursorrules` + `.cursor/rules/*.mdc` | ✅ |
| Gemini CLI | `GEMINI.md` | ✅ |
| Windsurf | `.windsurfrules` | ✅ |
| Google Antigravity | `.agents/skills/*/SKILL.md` + `AGENTS.md` | ✅ |
| GitHub Copilot | `.github/copilot-instructions.md` | ✅ |

**Zero migration between tools** — open this repo in any supported tool and it works immediately.

See `docs/ai-tool-compatibility.md` for full details on each tool's architecture.

## Quick Setup

```bash
# Copy into your project root
cp -r skills ./skills
cp -r rules ./rules
cp -r agents ./agents
cp -r .claude ./.claude
cp CLAUDE.md ./CLAUDE.md
cp AGENTS.md ./AGENTS.md
cp GEMINI.md ./GEMINI.md
cp .cursorrules ./.cursorrules
cp -r .cursor ./.cursor
cp .windsurfrules ./.windsurfrules
cp -r .kiro ./.kiro
cp -r .agents ./.agents
cp -r .github ./.github
```

Then tell the agent your framework in `CLAUDE.md` or your first prompt:

```
This project uses FastAPI with PostgreSQL on Python 3.11.
requires-python = ">=3.11"
Load skills/fastapi/SKILL.md as the primary framework skill.
```

## Claude Code Slash Commands

| Command | Purpose |
|---|---|
| `/load-skill [framework]` | Load all common + framework skills |
| `/new-endpoint METHOD path "description"` | Scaffold a complete endpoint with tests |
| `/review [file]` | Standards audit — returns ✅ / ⚠️ / ❌ |
| `/add-tests [file]` | Generate missing pytest tests |
| `/migrate "description"` | Create and apply an Alembic migration |

## File Guide

| Path | Load when |
|---|---|
| `CLAUDE.md` | Always — master agent contract |
| `skills/common/code-style.md` | Writing any Python |
| `skills/common/code-style-index.md` | Quick lookup — section map for code-style.md |
| `skills/common/folder-structure.md` | Starting a new module or project |
| `skills/common/error-handling.md` | Writing error or exception logic |
| `skills/common/logging.md` | Adding any logging |
| `skills/common/security.md` | Auth, input validation, secrets |
| `skills/common/api-auth.md` | OAuth2, JWT, RBAC/ABAC, service-to-service auth |
| `skills/common/testing.md` | Writing tests |
| `skills/common/db-design.md` | Creating or modifying models |
| `skills/common/data-migrations.md` | Zero-downtime migrations, backfills |
| `skills/common/performance.md` | Caching, async, N+1 prevention |
| `skills/common/llm-patterns.md` | LLM client abstraction, prompt management |
| `skills/common/ci-cd.md` | Setting up pipelines, GitHub Actions |
| `skills/common/deployment.md` | Docker, health checks, 12-factor |
| `skills/common/observability.md` | Metrics, tracing, OpenTelemetry |
| `skills/common/async-patterns.md` | Task queues, retries, events, DLQ |
| `skills/common/microservices.md` | Service boundaries, inter-service communication |
| `skills/common/feature-flags.md` | Gradual rollouts, flag lifecycle |
| `skills/common/dependency-management.md` | Pinning, vulnerability scanning, updates |
| `skills/fastapi/SKILL.md` | FastAPI projects |
| `skills/django/SKILL.md` | Django projects |
| `skills/drf/SKILL.md` | Django REST Framework projects |
| `skills/flask/SKILL.md` | Flask projects |
| `rules/api-design.md` | Designing or reviewing API endpoints |
| `rules/git-workflow.md` | Branching, commits, PRs, releases, rollback |
| `rules/code-review.md` | Reviewing code — checklist, severity, feedback |
| `agents/qa-agent.md` | Automated QA pipeline setup |
| `docs/onboarding.md` | New developer onboarding |
| `docs/incident-response.md` | On-call, severity, postmortems |
| `docs/tech-debt.md` | Tracking and prioritizing tech debt |
| `docs/adr/ADR-template.md` | Architecture decision records |
| `examples/fastapi-app/` | Reference implementation |

## Contributing

When you discover a new best practice or fix a gap:

1. Update the relevant skill file.
2. Open a PR with a clear description of what changed and why.
3. Tag it `skills-update`.
4. Post to the team Slack channel — other projects need to pull the update.

Review and update skill files during each sprint retrospective.

---

**Owner:** AurigaIT Engineering Platform
**Contact:** Rishap / Ravi
