# Incident Response

**Applies to:** All production services.
**Owner:** Engineering leads + on-call rotation.

---

## SECTION 1 — SEVERITY DEFINITIONS

| Severity | Definition | Examples | Response time |
|----------|-----------|----------|---------------|
| **P0 — Critical** | Complete outage, data loss, security breach | Service down, DB corruption, credentials leaked | Immediate (< 15 min) |
| **P1 — High** | Major feature broken, significant user impact | Payments failing, auth broken, >5% error rate | < 30 min |
| **P2 — Medium** | Degraded performance, minor feature broken | Slow responses (p99 > 5s), non-critical feature down | < 2 hours |
| **P3 — Low** | Cosmetic, minor inconvenience, workaround exists | UI glitch, non-blocking error in logs | Next business day |

---

## SECTION 2 — ESCALATION PATH

```
Alert fires
  → On-call engineer acknowledges (< 5 min)
    → P0/P1: Page team lead + notify stakeholders
      → No resolution in 30 min: Escalate to engineering manager
        → No resolution in 1 hour: Escalate to CTO
    → P2: On-call investigates, updates ticket
    → P3: Create ticket, handle in next sprint
```

### Communication Channels

| Channel | Use for |
|---------|---------|
| PagerDuty / Opsgenie | P0/P1 alerts, on-call paging |
| #incidents Slack channel | Real-time coordination during incident |
| Status page | External communication to customers |
| Email | Post-incident summary to stakeholders |

---

## SECTION 3 — INCIDENT COMMANDER ROLE

For P0/P1 incidents, designate an Incident Commander (IC):

**IC responsibilities:**
1. Coordinate response — assign tasks, prevent duplication
2. Communicate status updates every 15 minutes
3. Decide when to escalate
4. Decide when incident is resolved
5. Ensure postmortem is scheduled

**IC does NOT:**
- Debug the issue themselves (unless they're the only one available)
- Make unilateral architectural decisions under pressure

---

## SECTION 4 — RESPONSE PLAYBOOK

### Step 1: Assess
- What's broken? Check dashboards, error rates, alerts.
- Who's affected? All users, subset, internal only?
- When did it start? Correlate with recent deploys.

### Step 2: Mitigate (stop the bleeding)
- **Recent deploy?** → Rollback immediately.
- **External dependency down?** → Enable circuit breaker / fallback.
- **Traffic spike?** → Scale up, enable rate limiting.
- **Data issue?** → Stop writes, assess damage scope.

### Step 3: Fix
- Identify root cause.
- Implement fix with test.
- Deploy through normal pipeline (unless P0 hotfix).

### Step 4: Verify
- Confirm error rates back to baseline.
- Check affected users can access the service.
- Monitor for 30 minutes post-fix.

### Step 5: Close
- Update status page.
- Notify stakeholders.
- Schedule postmortem within 48 hours.

---

## SECTION 5 — POSTMORTEM TEMPLATE

```markdown
# Postmortem: [Incident Title]

**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Severity:** P0 / P1 / P2
**Incident Commander:** [Name]
**Author:** [Name]

## Summary
One paragraph: what happened, who was affected, how long.

## Timeline (UTC)
| Time | Event |
|------|-------|
| 14:00 | Alert fired: error rate > 5% |
| 14:05 | On-call acknowledged |
| 14:15 | Root cause identified: bad migration |
| 14:20 | Rollback initiated |
| 14:25 | Service restored |

## Root Cause
What actually broke and why.

## Impact
- Users affected: X
- Revenue impact: $Y (if applicable)
- Data loss: None / describe

## What Went Well
- Fast detection (alert fired within 2 min)
- Rollback procedure worked as documented

## What Went Wrong
- Migration wasn't tested against production-sized data
- No canary deployment caught the issue

## Action Items
| Action | Owner | Due date | Ticket |
|--------|-------|----------|--------|
| Add migration load test to CI | @dev | 2026-05-15 | PLAT-123 |
| Implement canary deploys | @devops | 2026-06-01 | PLAT-124 |

## Lessons Learned
What should we change to prevent this class of incident?
```

---

## SECTION 6 — ON-CALL RULES

| Rule | Rationale |
|------|-----------|
| Rotate weekly | Prevent burnout |
| Maximum 1 week on-call per month | Sustainable pace |
| On-call has authority to rollback without approval | Speed > process during incidents |
| Handoff document at rotation | Context transfer |
| Compensate on-call (time off or pay) | Respect people's time |
| No on-call for junior devs (< 6 months) | Need experience to handle incidents |
| Runbooks for every alert | On-call shouldn't need to reverse-engineer at 3am |
