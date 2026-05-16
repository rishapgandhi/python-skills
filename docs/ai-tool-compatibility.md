# AI Tool Compatibility Reference

> How this repository works with every major AI coding tool.
> All tools reference the same `skills/` and `rules/` directories — no content duplication.

---

## Architecture: Single Source of Truth

```
skills/common/*.md          ← Canonical standards (22 files)
skills/{framework}/SKILL.md ← Framework-specific skills (4 files)
rules/*.md                  ← Process rules (3 files)
        │
        ├── CLAUDE.md                    → Claude Code
        ├── AGENTS.md                    → Codex / Kiro / Antigravity
        ├── GEMINI.md                    → Gemini CLI
        ├── .cursorrules                 → Cursor (legacy)
        ├── .cursor/rules/*.mdc          → Cursor (modern MDC)
        ├── .windsurfrules               → Windsurf
        ├── .kiro/steering/*.md          → Kiro (steering)
        ├── .github/copilot-instructions.md → GitHub Copilot
        └── .agents/skills/*/SKILL.md    → Google Antigravity
```

**Key principle:** Each tool-specific file is a thin "loader" that points to the canonical `skills/` directory. If you update a skill, ALL tools get the update automatically.

---

## Tool-by-Tool Reference

### 1. Claude Code

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Master agent contract — loaded automatically |

**How it works:** Claude Code reads `CLAUDE.md` at project root before every task. It contains the full file structure map, non-negotiable rules table, and instructions to load skill files.

**Setup:** Already configured. Just use Claude Code in this repo.

---

### 2. OpenAI Codex CLI

| File | Purpose |
|------|---------|
| `AGENTS.md` | Project instructions — auto-loaded |

**How it works:** Codex reads `AGENTS.md` at project root. Supports subdirectory `AGENTS.md` files for module-specific overrides. This is an open standard shared with Kiro and Antigravity.

**Setup:** Already configured. Run `codex` in this repo.

---

### 3. Kiro

| File | Purpose |
|------|---------|
| `.kiro/steering/product.md` | Product context |
| `.kiro/steering/tech.md` | Technology stack |
| `.kiro/steering/structure.md` | Project structure |
| `AGENTS.md` | Also auto-loaded by Kiro |

**How it works:** Kiro loads all `.kiro/steering/*.md` files automatically in every chat session. It also supports `AGENTS.md` as an additional context source.

**Setup:** Already configured. Open this repo in Kiro IDE or use `kiro-cli`.

---

### 4. Cursor

| File | Purpose |
|------|---------|
| `.cursorrules` | Legacy rules (auto-loaded, all files) |
| `.cursor/rules/python-core.mdc` | Core Python rules (always active) |
| `.cursor/rules/python-testing.mdc` | Testing rules (auto-attach to `tests/**`) |
| `.cursor/rules/python-security.mdc` | Security rules (always active) |

**How it works:** Cursor ≥0.45 uses `.cursor/rules/*.mdc` files with glob-based auto-attachment. The `.cursorrules` root file is kept for backward compatibility with older versions.

**MDC format:**
```
---
description: Rule description
globs: "**/*.py"
alwaysApply: true
---
# Rule content in markdown
```

**Setup:** Already configured. Open this repo in Cursor.

---

### 5. Gemini CLI

| File | Purpose |
|------|---------|
| `GEMINI.md` | Project context — auto-loaded |

**How it works:** Gemini CLI reads `GEMINI.md` at project root. Also supports `~/.gemini/GEMINI.md` for global user-level instructions. Project-level takes precedence.

**Setup:** Already configured. Run `gemini` in this repo.

---

### 6. Windsurf

| File | Purpose |
|------|---------|
| `.windsurfrules` | Workspace rules — auto-loaded by Cascade |

**How it works:** Windsurf reads `.windsurfrules` at workspace root. Rules are included in every Cascade interaction. Also supports workspace-level memories that persist across sessions.

**Setup:** Already configured. Open this repo in Windsurf.

---

### 7. Google Antigravity

| File | Purpose |
|------|---------|
| `.agents/skills/python-standards/SKILL.md` | Main skill definition |
| `.agents/workflows/new-endpoint.md` | Endpoint scaffolding workflow |
| `AGENTS.md` | Also auto-loaded |

**How it works:** Antigravity reads `.agents/skills/*/SKILL.md` files with YAML frontmatter. Skills are reusable capability packages. Workflows define step-by-step procedures. It also reads `AGENTS.md` for ambient context.

**Setup:** Already configured. Open this repo in Antigravity.

---

### 8. GitHub Copilot

| File | Purpose |
|------|---------|
| `.github/copilot-instructions.md` | Repository custom instructions |

**How it works:** Copilot reads `.github/copilot-instructions.md` and injects it as context in every interaction. Works in VS Code, JetBrains, and GitHub.com.

**Setup:** Already configured. Use Copilot in any IDE with this repo.

---

## Switching Between Tools

Because all tool-specific files reference the same `skills/` directory:

1. **Switching tools requires zero migration** — just open the repo in the new tool.
2. **Updating a skill updates all tools** — edit `skills/common/testing.md` and every tool sees the change.
3. **No content drift** — there's only one source of truth per topic.

### What to do when switching:

| From → To | Action needed |
|-----------|--------------|
| Claude → Cursor | None — `.cursorrules` already exists |
| Claude → Kiro | None — `.kiro/steering/` already exists |
| Claude → Codex | None — `AGENTS.md` already exists |
| Claude → Gemini | None — `GEMINI.md` already exists |
| Any → Any | None — all loaders are pre-configured |

---

## Adding a New AI Tool

When a new AI coding tool emerges:

1. Research what context file it reads (check docs for "custom instructions" or "rules").
2. Create the file in the appropriate location.
3. Make it a thin loader that references `skills/` — never duplicate content.
4. Add it to this compatibility doc.
5. Update `.gitignore` if the tool generates cache files.

---

## File Size Reference

| File | Size | Purpose |
|------|------|---------|
| `CLAUDE.md` | ~5KB | Full contract with file structure |
| `AGENTS.md` | ~3KB | Skill table + rules |
| `GEMINI.md` | ~2.5KB | Stack + skill references |
| `.cursorrules` | ~2KB | Summary rules |
| `.windsurfrules` | ~2KB | Summary rules |
| `.github/copilot-instructions.md` | ~2.5KB | Rules + conventions |
| `.kiro/steering/*.md` | ~4KB total | Product + tech + structure |
| `.agents/skills/*/SKILL.md` | ~2.5KB | Antigravity skill |

All loaders are intentionally small (2-5KB) to fit within tool context limits. The detailed content lives in `skills/` (200KB+ total) and is loaded on demand.
