# Technical Debt Management

**Applies to:** All engineering teams.
**Owner:** Tech leads, reviewed during sprint planning.

---

## SECTION 1 — WHAT COUNTS AS TECH DEBT

| Category | Examples |
|----------|---------|
| **Code debt** | Duplicated logic, god classes, missing abstractions, no tests |
| **Architecture debt** | Monolith that should be split, wrong DB choice, missing caching layer |
| **Dependency debt** | Outdated libraries, deprecated APIs, unsupported Python version |
| **Infrastructure debt** | Manual deployments, no monitoring, missing IaC |
| **Documentation debt** | Missing ADRs, outdated README, no runbooks |
| **Test debt** | Low coverage, flaky tests, missing integration tests |

### What is NOT tech debt

- Intentional simplicity (YAGNI) — choosing not to build something you don't need yet
- Learning — code written by juniors that works correctly but isn't elegant
- Feature requests disguised as debt — "we should rewrite this in Rust"

---

## SECTION 2 — TRACKING

### Ticket Format

Every tech debt item gets a ticket with:

```
Title: [DEBT] Short description of the problem
Labels: tech-debt, severity/{critical|high|medium|low}

## Problem
What's wrong and where (file paths, module names).

## Impact
- Developer productivity: How much time is wasted per week?
- Risk: What could go wrong if we don't fix this?
- Scope: How many files/services are affected?

## Proposed Solution
Brief description of the fix approach.

## Effort Estimate
T-shirt size: S (< 1 day) | M (1-3 days) | L (3-5 days) | XL (> 1 week)
```

### Debt Registry

Maintain a living document or board view:

| Item | Category | Severity | Effort | Impact | Score |
|------|----------|----------|--------|--------|-------|
| No tests on payment service | Test | Critical | L | High (risk of regression) | 9 |
| Python 3.9 → 3.11 upgrade | Dependency | High | M | Medium (perf + features) | 7 |
| Duplicated auth logic in 3 services | Code | Medium | M | Medium (maintenance cost) | 5 |
| Manual deployment scripts | Infra | High | L | High (error-prone, slow) | 8 |

---

## SECTION 3 — PRIORITIZATION FRAMEWORK

### Scoring (1-10)

```
Score = (Impact × 2 + Risk × 2 + Frequency) / 5
```

| Factor | 1 (low) | 5 (medium) | 10 (high) |
|--------|---------|------------|-----------|
| **Impact** | Minor annoyance | Slows team weekly | Blocks features |
| **Risk** | Unlikely to cause issues | Could cause outage | Will cause outage |
| **Frequency** | Encountered rarely | Hit weekly | Hit daily |

### Priority Matrix

| Score | Priority | Action |
|-------|----------|--------|
| 8-10 | Critical | Fix this sprint, block new features if needed |
| 5-7 | High | Schedule within 2 sprints |
| 3-4 | Medium | Allocate in quarterly planning |
| 1-2 | Low | Fix opportunistically (boy scout rule) |

---

## SECTION 4 — SCHEDULING STRATEGIES

### The 20% Rule

Reserve 20% of sprint capacity for tech debt. Non-negotiable.

```
Sprint capacity: 10 story points per dev × 5 devs = 50 points
Feature work: 40 points (80%)
Tech debt: 10 points (20%)
```

### Debt Sprints

Every 6th sprint is a dedicated "health sprint":
- No new features
- Focus on highest-priority debt items
- Upgrade dependencies
- Improve test coverage
- Write missing documentation

### Boy Scout Rule (Continuous)

"Leave the code better than you found it."

When touching a file for a feature:
- Fix one small debt item in that file
- Add missing type annotations
- Add a missing test
- Remove dead code

**Rule:** Boy scout improvements go in the same PR as the feature — don't create separate PRs for trivial fixes.

---

## SECTION 5 — PREVENTING DEBT ACCUMULATION

| Practice | How it prevents debt |
|----------|---------------------|
| Code review with standards | Catches shortcuts before merge |
| CI enforcement (lint, types, coverage) | Automated quality gate |
| ADRs for architectural decisions | Prevents "why is this like this?" confusion |
| Spike tickets before large features | Explore before committing to an approach |
| Refactoring as part of feature work | Don't let debt compound |
| Regular dependency updates (Renovate) | Prevents "big bang" upgrades |

---

## SECTION 6 — COMMUNICATING DEBT TO STAKEHOLDERS

Leads must translate tech debt into business language:

| Technical framing (bad) | Business framing (good) |
|------------------------|------------------------|
| "We need to refactor the auth module" | "Auth changes take 3 days instead of 3 hours — fixing this saves 2 dev-weeks per quarter" |
| "We should upgrade Python" | "We're on an unsupported version — security patches stop in 6 months" |
| "The test suite is flaky" | "We deploy 2 days late per sprint because tests fail randomly" |
| "We need to split the monolith" | "We can't scale the payment system independently — Black Friday will be a problem" |

**Rule:** Always quantify debt in time, money, or risk. "It's messy" is not a business case.
