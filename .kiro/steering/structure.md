# Project Structure

## Repository Layout

```
python-agent-standards/
├── CLAUDE.md                    ← Master agent contract (Claude Code)
├── AGENTS.md                    ← Open standard (Codex, Kiro, Antigravity)
├── GEMINI.md                    ← Gemini CLI context
├── .cursorrules                 ← Cursor/Windsurf auto-load
├── .kiro/steering/              ← Kiro steering files (you are here)
├── .github/copilot-instructions.md  ← GitHub Copilot
├── .windsurfrules               ← Windsurf rules
├── .agents/                     ← Google Antigravity skills
├── skills/
│   ├── common/                  ← Universal Python skills (22 files)
│   │   ├── code-style.md
│   │   ├── testing.md
│   │   ├── security.md
│   │   ├── api-auth.md
│   │   ├── db-design.md
│   │   ├── data-migrations.md
│   │   ├── error-handling.md
│   │   ├── logging.md
│   │   ├── performance.md
│   │   ├── ci-cd.md
│   │   ├── deployment.md
│   │   ├── observability.md
│   │   ├── async-patterns.md
│   │   ├── microservices.md
│   │   ├── feature-flags.md
│   │   ├── dependency-management.md
│   │   ├── folder-structure.md
│   │   ├── llm-patterns.md
│   │   └── code-style-index.md
│   ├── fastapi/SKILL.md
│   ├── django/SKILL.md
│   ├── drf/SKILL.md
│   └── flask/SKILL.md
├── rules/
│   ├── api-design.md
│   ├── git-workflow.md
│   └── code-review.md
├── agents/
│   └── qa-agent.md
├── docs/
│   ├── onboarding.md
│   ├── incident-response.md
│   ├── tech-debt.md
│   └── adr/ADR-template.md
└── examples/
    └── fastapi-app/             ← Reference implementation
```

## Naming Conventions

- Skill files: `kebab-case.md` in `skills/common/`
- Framework skills: `SKILL.md` in `skills/{framework}/`
- Rules: `kebab-case.md` in `rules/`
- All config files reference `skills/` — never duplicate content

## How to Use

1. Load `skills/common/code-style.md` for every task.
2. Load the framework-specific `skills/{framework}/SKILL.md`.
3. Load domain skills as needed (see table in `AGENTS.md`).
4. Follow `rules/` for process decisions (API design, git, reviews).
