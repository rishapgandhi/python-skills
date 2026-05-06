# Logging — Enterprise Standard

**Applies to:** All Python projects in all deployment environments.
**No print() in production code. Ever.**

---

## SECTION 1 — LIBRARY CHOICE AND RATIONALE

Use **structlog** for all application logging. It wraps Python's stdlib `logging` and adds:
- Structured key-value output (JSON in production, colored console in dev)
- Context binding: attach request_id, user_id once per request; all log entries carry it automatically
- Processor pipeline: consistent timestamping, log level, caller info
- Zero performance penalty for disabled log levels

```
pip install structlog
```

**When to use stdlib `logging` directly:** Only in library code that cannot impose structlog on consumers. In that case, use `logging.getLogger(__name__)` and emit only to a NullHandler.

```python
# In a reusable library (not an application)
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
```

---

## SECTION 2 — CONFIGURATION

```python
# app/core/logging.py

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(
    log_level: str = "INFO",
    json_output: bool = False,
    *,
    include_caller_info: bool = False,
) -> None:
    """Configure structlog for the application.

    Must be called once at application startup, before any other code
    creates loggers. Calling it multiple times is safe but the second
    call wins.

    Args:
        log_level: Minimum severity level. Case-insensitive.
            Valid: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        json_output: If True, emit JSON lines (use in production and CI).
            If False, emit human-readable coloured output (use in development).
        include_caller_info: If True, add filename and line number to every
            log entry. Useful for debugging; adds overhead in hot paths.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,    # merges request-scoped context
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if include_caller_info:
        shared_processors.append(structlog.processors.CallsiteParameterAdder([
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.LINENO,
            structlog.processors.CallsiteParameter.FUNC_NAME,
        ]))

    shared_processors.append(structlog.processors.StackInfoRenderer())
    shared_processors.append(structlog.processors.format_exc_info)

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True, sort_keys=False)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,   # performance: bind once
    )

    # Also configure stdlib logging for third-party libraries that use it
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(log_level.upper()),
    )
```

---

## SECTION 3 — GETTING A LOGGER

```python
# Every module declares its own logger — never pass logger instances around
import structlog

logger = structlog.get_logger(__name__)

# In a class — module-level logger is preferred over instance logger
class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        # NO: self.logger = structlog.get_logger(__name__)  — redundant; use module logger

    async def create_user(self, data: UserCreate) -> User:
        logger.info("user_create_started", email=data.email)
        ...
```

---

## SECTION 4 — LOG LEVELS — WHEN TO USE EACH

| Level | Use when | Examples |
|---|---|---|
| `DEBUG` | Detailed trace for debugging. Never enabled in production. | Query parameters, intermediate values, loop iterations |
| `INFO` | Normal operational events. Default production level. | Request received, user created, job completed |
| `WARNING` | Unexpected but recoverable. Ops team should be aware. | Deprecated API called, retry attempt, config fallback used |
| `ERROR` | Failure that affected a user or operation. Requires investigation. | Payment declined, DB connection lost, file not found |
| `CRITICAL` | System cannot function. Immediate human response required. | Config missing at startup, unrecoverable crash, data corruption detected |

```python
# DEBUG — rich detail; only useful when debugging a specific problem
logger.debug(
    "cache_lookup",
    key=cache_key,
    hit=result is not None,
    ttl_remaining=ttl,
)

# INFO — confirms the system is working as expected
logger.info(
    "user_created",
    user_id=user.id,
    tenant_id=tenant_id,
    source="api",
)

# WARNING — something unusual happened but we recovered
logger.warning(
    "retry_attempt",
    service="payment_gateway",
    attempt=attempt_number,
    max_attempts=MAX_RETRIES,
    error=str(last_error),
)

# ERROR — something failed; a user or operation was affected
logger.error(
    "payment_failed",
    order_id=order_id,
    user_id=user_id,
    gateway_response_code=response.status_code,
    exc_info=True,   # attaches full stack trace to the log entry
)

# CRITICAL — system is in a non-recoverable state
logger.critical(
    "database_unreachable_at_startup",
    database_url=settings.database_url.split("@")[-1],  # safe: no credentials
    error=str(exc),
)
```

---

## SECTION 5 — STRUCTURED FIELDS — CONSISTENCY ACROSS THOUSANDS OF LOGS

All log entries for a given event type must use identical field names. Inconsistent field names make log aggregation (Datadog, Splunk, CloudWatch Insights) impossible at scale.

### 5.1 Standard Field Vocabulary

| Field | Type | Description |
|---|---|---|
| `request_id` | str (UUID) | Trace ID — attached at middleware, carried through all layers |
| `user_id` | int or str | Authenticated user performing the action |
| `tenant_id` | int or str | Tenant in a multi-tenant system |
| `session_id` | str | User session identifier |
| `entity` | str | Entity type being operated on: `"User"`, `"Order"` |
| `entity_id` | int or str | Entity primary key |
| `action` | str | What happened: `"created"`, `"updated"`, `"deleted"` |
| `duration_ms` | float | Operation duration in milliseconds |
| `http_method` | str | HTTP method: `"GET"`, `"POST"` |
| `http_path` | str | Request path: `"/api/v1/users"` |
| `http_status` | int | Response status code |
| `service` | str | External service name when calling third parties |
| `error` | str | Exception message (use `exc_info=True` for stack trace) |
| `error_code` | str | Machine-readable error code |

```python
# CORRECT — structured, consistent, searchable
logger.info(
    "order_created",          # event name: snake_case, past-tense verb-noun
    entity="Order",
    entity_id=order.id,
    user_id=current_user.id,
    tenant_id=tenant_id,
    total_amount=order.total,
    item_count=len(order.items),
    duration_ms=round((time.monotonic() - start) * 1000, 2),
)

# WRONG — unstructured string; impossible to query in log aggregation
logger.info(f"Order {order.id} created by user {current_user.id} for ${order.total}")
```

### 5.2 Event Naming Convention

```
Pattern:  {entity}_{action}_{modifier}
Examples:
  user_created
  user_login_failed
  order_payment_processed
  cache_lookup_hit
  cache_lookup_miss
  retry_attempt_succeeded
  rate_limit_exceeded
  db_query_slow             # with duration_ms field
```

---

## SECTION 6 — REQUEST-SCOPED CONTEXT BINDING

Bind context once per request; structlog carries it automatically to all log calls within that request — no need to pass fields manually.

```python
# app/core/middleware.py

import uuid
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Binds request-scoped context to structlog context vars.

    All log entries within a request will automatically include:
    request_id, http_method, http_path.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.monotonic()

        # Clear any context left from previous request (connection reuse)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
        )

        logger.info("request_received")

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.error("request_failed", duration_ms=duration_ms, exc_info=True)
            raise
        else:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.info(
                "request_completed",
                http_status=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response


# Binding authenticated user after auth middleware runs
def bind_user_context(user_id: int, tenant_id: int) -> None:
    """Call this once authentication succeeds in a request."""
    structlog.contextvars.bind_contextvars(
        user_id=user_id,
        tenant_id=tenant_id,
    )
```

---

## SECTION 7 — LOGGING EXCEPTIONS

```python
# CORRECT — log before re-raising; exc_info=True attaches full traceback
try:
    result = await payment_gateway.charge(amount, card_token)
except PaymentGatewayTimeout as exc:
    logger.error(
        "payment_timeout",
        order_id=order_id,
        amount=amount,
        gateway="stripe",
        error=str(exc),
        exc_info=True,      # includes traceback in JSON output as "exception" field
    )
    raise ExternalServiceError("stripe", str(exc)) from exc

# CORRECT — WARNING level for retryable failures (not yet an error)
for attempt in range(MAX_RETRIES):
    try:
        return await call_with_retry()
    except RetryableError as exc:
        logger.warning(
            "retry_attempt",
            attempt=attempt + 1,
            max_attempts=MAX_RETRIES,
            error=str(exc),
        )
        await asyncio.sleep(backoff_seconds(attempt))

# WRONG — logging after raising (unreachable code)
try:
    process()
except SomeError as exc:
    raise AppError("failed") from exc
    logger.error("failed", error=str(exc))   # NEVER reached

# WRONG — swallowing exception by only logging
try:
    process()
except SomeError as exc:
    logger.error("failed", error=str(exc))   # error silently swallowed; caller gets None
```

---

## SECTION 8 — WHAT NEVER TO LOG

These are security requirements — violations can cause compliance incidents.

| Never log | Reason | Alternative |
|---|---|---|
| Passwords, secret keys, API tokens | Credentials in logs = breach | Log that auth occurred, not the credential |
| Full credit card numbers | PCI DSS violation | Log last 4 digits only: `card_last4=card[-4:]` |
| Full SSN / national ID | PII / GDPR | Log presence/absence, not value |
| JWT token contents | Token is a credential | Log `token_type`, not the token itself |
| Email addresses in body | GDPR data minimisation | Log `user_id` instead |
| Full request body | May contain PII or credentials | Log specific safe fields only |
| Full response body from external APIs | May contain sensitive data + bloat | Log status code and duration only |
| Database connection strings | Contains credentials | Log only the host portion |

```python
# WRONG — credentials in log
logger.info("connecting_to_db", url=settings.database_url)

# CORRECT — credentials stripped
db_host = settings.database_url.split("@")[-1]  # strips user:password@
logger.info("connecting_to_db", host=db_host)

# WRONG — full PAN in log
logger.info("payment_attempted", card_number=card.number)

# CORRECT — last 4 only
logger.info("payment_attempted", card_last4=card.number[-4:])
```

---

## SECTION 9 — SLOW QUERY LOGGING

Always instrument database operations for slow query detection.

```python
import time
import structlog

SLOW_QUERY_THRESHOLD_MS = 100   # flag any query taking longer than 100ms

async def execute_with_logging(
    session: AsyncSession,
    statement: Any,
    *,
    operation: str,
    entity: str,
) -> Any:
    """Execute a SQLAlchemy statement with timing and slow-query detection.

    Args:
        session: Active async database session.
        statement: SQLAlchemy select/insert/update/delete statement.
        operation: Human-readable operation name for log entries.
        entity: Entity type being queried for log context.

    Returns:
        Raw SQLAlchemy result object.
    """
    start = time.monotonic()
    try:
        result = await session.execute(statement)
        duration_ms = round((time.monotonic() - start) * 1000, 2)

        log_kwargs = dict(
            operation=operation,
            entity=entity,
            duration_ms=duration_ms,
        )

        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            logger.warning("db_query_slow", **log_kwargs)
        else:
            logger.debug("db_query_completed", **log_kwargs)

        return result
    except Exception as exc:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        logger.error(
            "db_query_failed",
            operation=operation,
            entity=entity,
            duration_ms=duration_ms,
            error=str(exc),
            exc_info=True,
        )
        raise
```
