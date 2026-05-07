# Feature Flags — Enterprise Standard

**Applies to:** All Python services releasing features incrementally.
**Tools:** LaunchDarkly, Unleash, Flagsmith, or custom implementation.

---

## SECTION 1 — FLAG TYPES

| Type | Purpose | Lifetime | Example |
|------|---------|----------|---------|
| Release flag | Gradual rollout of new feature | Days to weeks | `enable_new_checkout` |
| Experiment flag | A/B test | Weeks | `experiment_pricing_v2` |
| Ops flag | Kill switch for degraded mode | Permanent | `disable_external_payments` |
| Permission flag | Feature gating per plan/tier | Permanent | `feature_advanced_analytics` |

---

## SECTION 2 — IMPLEMENTATION PATTERN

### Simple Flag Service

```python
# app/core/feature_flags.py
from app.core.config import settings


class FeatureFlags:
    """Feature flag evaluation. Replace with LaunchDarkly/Unleash SDK in production."""

    def __init__(self) -> None:
        self._overrides: dict[str, bool] = {}

    def is_enabled(self, flag: str, user_id: str | None = None, default: bool = False) -> bool:
        """Check if a feature flag is enabled."""
        # Local override (for testing)
        if flag in self._overrides:
            return self._overrides[flag]

        # Percentage rollout
        if user_id and flag in _ROLLOUT_FLAGS:
            return _hash_user_to_percentage(user_id, flag) < _ROLLOUT_FLAGS[flag]

        # Static flags from config
        return getattr(settings, f"flag_{flag}", default)

    def override(self, flag: str, value: bool) -> None:
        """Override for testing only."""
        self._overrides[flag] = value

    def clear_overrides(self) -> None:
        self._overrides.clear()


def _hash_user_to_percentage(user_id: str, flag: str) -> int:
    """Deterministic hash: same user always gets same result for a flag."""
    import hashlib
    h = hashlib.md5(f"{flag}:{user_id}".encode()).hexdigest()
    return int(h[:8], 16) % 100


# Rollout configuration: flag_name -> percentage (0-100)
_ROLLOUT_FLAGS: dict[str, int] = {
    "new_checkout": 25,  # 25% of users
}

feature_flags = FeatureFlags()
```

### Usage in Code

```python
# In service layer
async def get_pricing(user_id: str, product_id: int) -> PricingResponse:
    if feature_flags.is_enabled("experiment_pricing_v2", user_id=user_id):
        return await new_pricing_engine.calculate(product_id)
    return await legacy_pricing.calculate(product_id)
```

### Usage in Endpoints

```python
@router.get("/dashboard")
async def get_dashboard(user: User = Depends(get_current_user)):
    data = await dashboard_service.get_base_data(user.id)

    if feature_flags.is_enabled("feature_advanced_analytics", user_id=str(user.id)):
        data["analytics"] = await analytics_service.get_advanced(user.id)

    return data
```

---

## SECTION 3 — GRADUAL ROLLOUT STRATEGY

```
Day 1:   1% (internal team only)
Day 3:   5% (early adopters / beta users)
Day 5:  25% (monitor error rates, latency)
Day 7:  50% (watch for edge cases at scale)
Day 10: 100% (full rollout)
Day 14: Remove flag (cleanup)
```

### Rollout Rules

| Rule | Rationale |
|------|-----------|
| Monitor error rate at each stage before increasing | Catch issues early |
| Have a kill switch — instant rollback to 0% | Faster than code revert |
| Use deterministic hashing (not random) | Same user gets consistent experience |
| Log which variant a user received | Debug issues per-variant |
| Never nest flags (flag inside flag) | Combinatorial explosion |

---

## SECTION 4 — FLAG LIFECYCLE

```
CREATED → ACTIVE → ROLLED_OUT → CLEANUP → REMOVED
```

| Phase | Action | Owner |
|-------|--------|-------|
| Created | Flag added to code + config | Developer |
| Active | Gradual rollout in progress | Developer + PM |
| Rolled out | 100% enabled, monitoring stable | Developer |
| Cleanup | Remove flag checks from code | Developer (scheduled) |
| Removed | Flag deleted from config/service | Developer |

### Cleanup Rules

- **Release flags:** Remove within 2 weeks of 100% rollout.
- **Experiment flags:** Remove within 1 week of experiment conclusion.
- **Ops flags:** Keep permanently (they're kill switches).
- **Permission flags:** Keep permanently (they're business logic).

**Anti-pattern:** Flags that live for months. They become tech debt and make code unreadable.

---

## SECTION 5 — TESTING WITH FLAGS

```python
# tests/test_pricing.py
import pytest
from app.core.feature_flags import feature_flags


@pytest.fixture(autouse=True)
def reset_flags():
    """Reset flag overrides between tests."""
    yield
    feature_flags.clear_overrides()


def test_new_pricing_when_flag_enabled():
    feature_flags.override("experiment_pricing_v2", True)
    result = await get_pricing(user_id="user-1", product_id=1)
    assert result.engine == "v2"


def test_legacy_pricing_when_flag_disabled():
    feature_flags.override("experiment_pricing_v2", False)
    result = await get_pricing(user_id="user-1", product_id=1)
    assert result.engine == "legacy"
```

---

## SECTION 6 — FLAG HYGIENE TRACKING

Maintain a flag registry (spreadsheet, Notion, or in-code):

```python
# app/core/flag_registry.py
"""
Active feature flags — review monthly for cleanup candidates.

| Flag                      | Type       | Owner   | Created    | Target removal |
|---------------------------|------------|---------|------------|----------------|
| new_checkout              | release    | @arpit  | 2026-04-01 | 2026-04-15     |
| experiment_pricing_v2     | experiment | @nishant| 2026-04-10 | 2026-05-01     |
| disable_external_payments | ops        | @deepika| 2026-01-01 | permanent      |
| feature_advanced_analytics| permission | @arpit  | 2026-03-01 | permanent      |
"""
```
