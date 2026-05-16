# CI/CD — Enterprise Standard

**Applies to:** All Python projects using GitHub Actions (adapt for GitLab CI / Azure Pipelines).
**Pipeline philosophy:** Fail fast, fail cheap. Lint before test, test before build, build before deploy.

---

## SECTION 1 — PIPELINE STAGES

```
lint → type-check → test → build → deploy
```

Each stage gates the next. If lint fails, nothing else runs.

---

## SECTION 2 — GITHUB ACTIONS TEMPLATE

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.11"
  POETRY_VERSION: "1.8"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  type-check:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install -e ".[dev]"
      - run: mypy app/ --strict

  test:
    runs-on: ubuntu-latest
    needs: type-check
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]
    env:
      DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/test_db
      REDIS_URL: redis://localhost:6379/0
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=app --cov-report=xml --cov-fail-under=80
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## SECTION 3 — RULES

| Rule | Rationale |
|------|-----------|
| Pin all CI action versions with full SHA or `@v4` | Prevent supply-chain attacks |
| Use `concurrency` to cancel stale runs | Save CI minutes |
| Cache dependencies (`actions/cache` or setup-python cache) | Speed up pipelines |
| Never store secrets in workflow files | Use GitHub Secrets / OIDC |
| Run DB-dependent tests with service containers | Matches production; no SQLite shortcuts |
| Coverage gate at 80% minimum | Enforced via `--cov-fail-under` |
| Build Docker image only on main | PRs validate; main deploys |

---

## SECTION 4 — PR CHECKS (Required Status Checks)

Configure in repo settings → Branch protection:

- `lint` — must pass
- `type-check` — must pass
- `test` — must pass
- At least 1 approving review

---

## SECTION 5 — RELEASE AUTOMATION

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*"]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ghcr.io/${{ github.repository }}:latest
          push: true
      - uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
```

Tag-based releases: `git tag v1.2.3 && git push --tags` triggers production deploy.
