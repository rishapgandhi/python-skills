# Git Workflow Standards

**Applies to:** All Python projects.

---

## Branch Naming

```
feature/{ticket-id}-short-description     ← New features
fix/{ticket-id}-short-description         ← Bug fixes
chore/{ticket-id}-short-description       ← Non-functional changes
hotfix/{ticket-id}-short-description      ← Production emergency fixes
release/v{major}.{minor}.{patch}          ← Release preparation
```

---

## Commit Message Format (Conventional Commits)

```
{type}({scope}): {short description}

{optional body}

{optional footer: BREAKING CHANGE or issue reference}
```

Types: `feat` `fix` `chore` `docs` `test` `refactor` `perf` `ci`

Examples:
```
feat(users): add email verification on registration
fix(auth): prevent token reuse after logout
test(orders): add integration tests for checkout flow
perf(queries): add composite index for user search
```

---

## PR Rules

- Every PR must reference a ticket.
- PRs must pass: linting (Ruff) + type check (mypy) + tests (pytest ≥80% coverage).
- Minimum 1 peer review required before merge.
- Squash merge to keep main history clean.
- Delete branch after merge.
- PR title follows conventional commit format: `feat(scope): description`
- PR description must include: what changed, why, how to test.

---

## Protected Branches

| Branch | Purpose | Push | Merge via | Requirements |
|--------|---------|------|-----------|--------------|
| `main` | Production | ❌ Direct push blocked | PR only | CI green + 1 review + no unresolved threads |
| `develop` | Integration | ❌ Direct push blocked | PR only | CI green |
| `release/*` | Release prep | ❌ | PR to main | QA sign-off + CI green |

---

## Release Strategy (Semantic Versioning)

Format: `v{MAJOR}.{MINOR}.{PATCH}`

| Increment | When |
|-----------|------|
| MAJOR | Breaking API changes, incompatible schema migrations |
| MINOR | New features, backward-compatible additions |
| PATCH | Bug fixes, security patches, no new features |

### Release Flow

```
1. develop accumulates features via PRs
2. Cut release branch: release/v1.2.0
3. Only bug fixes allowed on release branch
4. QA validates on staging
5. Merge release → main (PR, squash)
6. Tag: git tag v1.2.0
7. Merge main → develop (sync back)
8. CI auto-deploys tagged commit to production
```

### Tagging

```bash
git tag -a v1.2.0 -m "Release v1.2.0: user verification, performance improvements"
git push origin v1.2.0
```

Tags trigger the release pipeline (see `skills/common/ci-cd.md`).

---

## Environment Promotion

```
develop → staging → production
```

| Environment | Branch/Tag | Deploy trigger | Purpose |
|-------------|-----------|----------------|---------|
| Development | `develop` | Auto on merge | Integration testing |
| Staging | `release/*` | Auto on push | QA validation, pre-prod mirror |
| Production | `main` (tagged) | Tag push `v*` | Live traffic |

### Rules

- Same Docker image promoted across environments — only env vars change.
- Staging must mirror production infrastructure (same DB engine, same Redis version).
- Feature flags for incomplete features merged to develop.
- No environment-specific code paths — use configuration only.

---

## Hotfix Flow

For critical production bugs that cannot wait for the next release:

```
1. Branch from main: hotfix/TICKET-123-fix-auth-bypass
2. Fix + test (must include regression test)
3. PR to main — expedited review (1 reviewer, senior)
4. Tag: v1.2.1
5. Merge main → develop (sync the fix)
```

Hotfixes skip staging only when:
- P0/P1 severity (data loss, security breach, full outage)
- Fix is isolated and well-tested
- On-call engineer approves

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

```bash
# Redeploy previous known-good tag
git checkout v1.1.0
# Or via CI: trigger deploy of previous tag
```

### Database Rollback

- If the release included migrations: check if they are reversible.
- Alembic: `alembic downgrade -1` (only if migration has `downgrade()` implemented).
- **Rule:** All migrations MUST have a working `downgrade()` function.
- If data migration is irreversible, use expand-contract pattern instead.

### Rollback Decision Matrix

| Scenario | Action |
|----------|--------|
| App crash on startup | Redeploy previous tag immediately |
| Error rate > 5% after deploy | Rollback, investigate |
| Slow degradation (p99 creeping up) | Monitor 10 min, rollback if worsening |
| Single user report | Investigate first, don't rollback |
| Data corruption | Rollback + restore from backup |

### Post-Rollback

1. Create incident ticket.
2. Write postmortem within 48 hours.
3. Fix must include regression test before re-release.

---

## Changelog

Maintain `CHANGELOG.md` using [Keep a Changelog](https://keepachangelog.com/) format. Every PR that changes user-facing behavior must update the changelog under `[Unreleased]`.
