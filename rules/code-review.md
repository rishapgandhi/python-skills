# Code Review Guidelines

**Applies to:** All PRs across all Python projects.
**Audience:** Reviewers (leads, seniors) and authors.

---

## SECTION 1 — REVIEW CHECKLIST

### Correctness
- [ ] Does the code do what the ticket/PR description says?
- [ ] Are edge cases handled (empty input, None, max values, concurrent access)?
- [ ] Are error paths tested?
- [ ] Is the logic correct under race conditions?

### Security
- [ ] No hardcoded secrets or credentials
- [ ] Input validated and sanitized
- [ ] SQL injection prevented (parameterized queries)
- [ ] Auth/authz checks present on new endpoints
- [ ] Sensitive data not logged or exposed in responses

### Performance
- [ ] No N+1 queries (check ORM usage)
- [ ] Pagination on list endpoints
- [ ] Appropriate indexes for new queries
- [ ] No blocking I/O in async context
- [ ] Large datasets processed in batches

### Maintainability
- [ ] Functions < 30 lines (ideally < 20)
- [ ] Single responsibility — one reason to change
- [ ] Clear naming — intent obvious without comments
- [ ] No dead code or commented-out blocks
- [ ] Type annotations on all public interfaces

### Testing
- [ ] New logic has corresponding tests
- [ ] Tests cover happy path + error paths
- [ ] No flaky tests (time-dependent, order-dependent)
- [ ] Mocks are minimal — prefer real dependencies where fast

### Standards Compliance
- [ ] Follows layer discipline (API → Service → Repository)
- [ ] Matches project's existing patterns
- [ ] Docstrings on public functions
- [ ] No new linting suppressions without justification

---

## SECTION 2 — SEVERITY LEVELS

Use these prefixes in review comments:

| Prefix | Meaning | Blocks merge? |
|--------|---------|---------------|
| `🔴 BLOCKER:` | Security flaw, data loss risk, broken logic | Yes |
| `🟠 MUST FIX:` | Bug, missing test, standards violation | Yes |
| `🟡 SUGGESTION:` | Better approach exists, readability improvement | No |
| `🟢 NIT:` | Style preference, minor naming | No |
| `💬 QUESTION:` | Clarification needed, not necessarily wrong | No |
| `👍 PRAISE:` | Good pattern, clever solution, well-tested | No |

**Rule:** Every review must include at least one `👍 PRAISE` comment. Positive reinforcement matters.

---

## SECTION 3 — FEEDBACK PATTERNS

### Good Feedback (actionable, specific, kind)

```
🟠 MUST FIX: This query runs inside a loop — it'll cause N+1.
Consider using `select_related("author")` on the queryset.
See: skills/common/performance.md §1.4
```

```
🟡 SUGGESTION: This could be simplified with a dict comprehension:
`{u.id: u.name for u in users}` instead of the manual loop.
```

```
💬 QUESTION: Is there a reason we're not using the existing
`UserService.get_by_email()` here? Looks like it does the same thing.
```

### Bad Feedback (avoid these)

- ❌ "This is wrong." (no explanation)
- ❌ "I would have done it differently." (not actionable)
- ❌ "Why didn't you...?" (accusatory tone)
- ❌ Rewriting the entire approach in a comment (open a discussion instead)

---

## SECTION 4 — REVIEWER RESPONSIBILITIES

1. **Respond within 4 business hours** — don't block teammates.
2. **Review the PR description first** — understand intent before reading code.
3. **Pull and run locally** for non-trivial changes.
4. **Check the tests** — are they testing behavior or implementation?
5. **Approve when "good enough"** — don't pursue perfection on every PR.
6. **Escalate architectural concerns** — if the approach is fundamentally wrong, discuss synchronously before leaving 50 comments.

---

## SECTION 5 — AUTHOR RESPONSIBILITIES

1. **Keep PRs small** — under 400 lines changed (excluding generated files).
2. **Self-review before requesting** — read your own diff first.
3. **Write a clear PR description** — what, why, how to test.
4. **Respond to all comments** — even if just "done" or "won't fix because X".
5. **Don't take feedback personally** — reviews are about code, not you.
6. **Split large changes** — if a PR touches >3 concerns, break it up.

---

## SECTION 6 — WHEN TO REQUEST ADDITIONAL REVIEWERS

| Scenario | Who to add |
|----------|-----------|
| Security-sensitive changes (auth, crypto, permissions) | Security champion |
| Database migrations | DBA or senior backend |
| Infrastructure / deployment changes | DevOps lead |
| API contract changes | Frontend lead + API consumers |
| New architectural pattern | Tech lead / architect |

---

## SECTION 7 — REVIEW TURNAROUND SLA

| PR Size | Expected turnaround |
|---------|-------------------|
| < 100 lines | Same day (4 hours) |
| 100–400 lines | Next business day |
| > 400 lines | Author should split; reviewer may request split |
