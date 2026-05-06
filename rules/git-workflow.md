# Git Workflow Standards

## Branch Naming

```
feature/{ticket-id}-short-description     ← New features
fix/{ticket-id}-short-description         ← Bug fixes
chore/{ticket-id}-short-description       ← Non-functional changes
hotfix/{ticket-id}-short-description      ← Production emergency fixes
```

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
```

## PR Rules

- Every PR must reference a ticket.
- PRs must pass: linting (Ruff) + type check (mypy) + tests (pytest ≥80% coverage).
- Minimum 1 peer review required before merge.
- Squash merge to keep main history clean.
- Delete branch after merge.

## Protected Branches

- `main` — production. No direct pushes. Requires PR + CI green + 1 review.
- `develop` — integration. Requires CI green.
