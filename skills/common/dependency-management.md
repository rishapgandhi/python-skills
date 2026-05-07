# Dependency Management — Enterprise Standard

**Applies to:** All Python projects.
**Tools:** pip, uv, pip-audit, Dependabot/Renovate.

---

## SECTION 1 — PINNING STRATEGY

### pyproject.toml — pin to minor version

```toml
[project]
dependencies = [
    "fastapi>=0.111,<0.112",
    "sqlalchemy>=2.0,<2.1",
    "pydantic>=2.7,<3.0",
    "structlog>=24.1,<25.0",
    "httpx>=0.27,<0.28",
]

[project.optional-dependencies]
dev = [
    "pytest==8.2.0",       # Dev tools: pin exact
    "ruff==0.4.4",
    "mypy==1.10.0",
]
```

### Rules

| Dependency type | Pin strategy | Rationale |
|----------------|-------------|-----------|
| Application deps | `>=X.Y,<X.(Y+1)` | Allow patches, block breaking minor bumps |
| Dev/test tools | Exact (`==X.Y.Z`) | Reproducible CI across all machines |
| Libraries you publish | Loose (`>=X.Y`) | Don't constrain consumers |

### Lock File

Always commit a lock file for applications:
- `uv.lock` (if using uv)
- `requirements.lock` (pip-compile output)
- `poetry.lock` (if using Poetry)

```bash
# Generate lock file
uv pip compile pyproject.toml -o requirements.lock
# Install from lock
uv pip sync requirements.lock
```

---

## SECTION 2 — VULNERABILITY SCANNING

### Automated Scanning

```yaml
# .github/workflows/security.yml
name: Security Scan
on:
  schedule:
    - cron: "0 8 * * 1"  # Weekly Monday 8am
  push:
    paths: ["pyproject.toml", "requirements.lock"]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pip-audit
      - run: pip-audit --requirement requirements.lock --strict
```

### Tools

| Tool | Purpose |
|------|---------|
| `pip-audit` | Check installed packages against OSV/PyPI advisories |
| `safety` | Alternative vulnerability scanner |
| Dependabot | Auto-create PRs for vulnerable deps (GitHub native) |
| Renovate | More configurable alternative to Dependabot |
| Snyk | Enterprise-grade SCA with license compliance |

### Response SLA

| Severity | Action | Timeline |
|----------|--------|----------|
| Critical (CVSS ≥ 9.0) | Patch immediately, deploy same day | < 24 hours |
| High (CVSS 7.0–8.9) | Patch within sprint | < 1 week |
| Medium (CVSS 4.0–6.9) | Schedule in next sprint | < 2 weeks |
| Low (CVSS < 4.0) | Bundle with next regular update | < 1 month |

---

## SECTION 3 — UPDATE CADENCE

| Activity | Frequency |
|----------|-----------|
| Security patches (critical/high) | Immediately |
| Minor version bumps | Bi-weekly |
| Major version upgrades | Quarterly (planned, with ADR) |
| Full dependency audit | Monthly |
| Lock file refresh | Weekly (automated via Renovate/Dependabot) |

### Renovate Configuration

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "automerge": true
    },
    {
      "matchUpdateTypes": ["minor"],
      "automerge": false,
      "labels": ["dependencies"]
    },
    {
      "matchUpdateTypes": ["major"],
      "labels": ["dependencies", "breaking"],
      "reviewers": ["team:leads"]
    }
  ],
  "schedule": ["before 9am on Monday"]
}
```

---

## SECTION 4 — PRIVATE REGISTRY

For internal packages:

```toml
# pyproject.toml
[tool.uv]
index-url = "https://pypi.org/simple"
extra-index-url = "https://pypi.internal.company.com/simple"
```

```bash
# .env or CI secrets
UV_EXTRA_INDEX_URL=https://${PYPI_TOKEN}@pypi.internal.company.com/simple
```

### Rules

- Never publish internal packages to public PyPI.
- Use scoped package names: `aurigait-common`, `aurigait-auth`.
- Internal packages follow the same versioning (semver) as external.
- Pin internal packages to exact versions in consuming services.

---

## SECTION 5 — RULES SUMMARY

| Rule | Rationale |
|------|-----------|
| Always commit a lock file | Reproducible builds across environments |
| Run `pip-audit` in CI | Catch vulnerabilities before deploy |
| Never use `*` or unbounded versions | Prevents surprise breaking changes |
| Review major upgrades as a team | Breaking changes need migration planning |
| Prefer well-maintained packages (>1000 GitHub stars, recent commits) | Reduce supply-chain risk |
| Verify package names carefully | Typosquatting is real (`python-dateutil` vs `python-dateutl`) |
| Minimize dependency count | Each dep is an attack surface and maintenance burden |
