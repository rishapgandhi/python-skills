# Error Handling — Enterprise Standard

**Applies to:** All Python projects.
**Authority:** PEP 8 §Programming Recommendations, PEP 3151, Python 3.3+ exception hierarchy.
**Python 3.11+:** ExceptionGroup and `except*` noted separately.

---

## SECTION 1 — EXCEPTION HIERARCHY DESIGN

### 1.1 Always derive from Exception, not BaseException

```python
# BaseException is reserved for:
#   - SystemExit (raised by sys.exit())
#   - KeyboardInterrupt (Ctrl+C)
#   - GeneratorExit (generator.close())
# Catching these accidentally is almost always a bug.

class AppError(Exception):          # CORRECT — top of your app hierarchy
    """Base for all application-level errors."""

class DatabaseError(BaseException): # WRONG — will swallow Ctrl+C
    pass
```

### 1.2 Build a purposeful domain hierarchy

Design the hierarchy around what CATCHING code needs to distinguish — not where errors are raised.

```python
# app/core/exceptions.py

class AppError(Exception):
    """Root exception for all application errors.

    All custom exceptions must inherit from AppError.
    Third-party exceptions are wrapped before being re-raised as AppError subclasses.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code for API consumers and monitoring.
        details: Optional structured additional context.
    """

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: dict | None = None,  # Python 3.10+; use Optional[dict] for 3.7-3.9
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"


# ── Domain exceptions — one per distinct failure mode ─────────────────────

class NotFoundError(AppError):
    """Requested resource does not exist."""

    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )
        self.resource = resource
        self.identifier = identifier


class ValidationError(AppError):
    """Input data failed business-rule validation.

    Distinct from schema validation (Pydantic handles that).
    This is for domain-level rules: "order total cannot exceed credit limit".
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        violations: list[dict] | None = None,
    ) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")
        self.field = field
        self.violations = violations or []


class AuthenticationError(AppError):
    """Authentication credentials are missing or invalid."""

    def __init__(self, message: str = "Authentication is required.") -> None:
        super().__init__(message=message, code="UNAUTHENTICATED")


class AuthorizationError(AppError):
    """Authenticated user lacks permission for this operation."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        required_permission: str | None = None,
    ) -> None:
        super().__init__(message=message, code="FORBIDDEN")
        self.required_permission = required_permission


class ConflictError(AppError):
    """Resource already exists or state conflict prevents the operation."""

    def __init__(self, message: str, conflicting_field: str | None = None) -> None:
        super().__init__(message=message, code="CONFLICT")
        self.conflicting_field = conflicting_field


class RateLimitError(AppError):
    """Operation exceeds configured rate limits."""

    def __init__(self, retry_after_seconds: int = 60) -> None:
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after_seconds} seconds.",
            code="RATE_LIMITED",
            details={"retry_after_seconds": retry_after_seconds},
        )
        self.retry_after_seconds = retry_after_seconds


class ExternalServiceError(AppError):
    """Third-party service call failed.

    Always wrap third-party exceptions in this before propagating.
    Never let requests.HTTPError, httpx.HTTPError, etc. leak into callers.
    """

    def __init__(
        self,
        service: str,
        message: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message=f"External service '{service}' failed: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "status_code": status_code},
        )
        self.service = service
        self.status_code = status_code


class ConfigurationError(AppError):
    """Application misconfiguration detected at startup or runtime."""

    def __init__(self, message: str, config_key: str | None = None) -> None:
        super().__init__(message=message, code="CONFIGURATION_ERROR")
        self.config_key = config_key


class DataIntegrityError(AppError):
    """Data invariant violated — indicates a bug or corrupted data."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="DATA_INTEGRITY_ERROR")
```

---

## SECTION 2 — WHERE EXCEPTIONS ARE RAISED AND CAUGHT

### 2.1 The golden rule: raise domain exceptions; catch in one place

```python
# CORRECT — service raises domain exception; knows nothing about HTTP
class OrderService:
    async def get_order(self, order_id: int, user_id: int) -> Order:
        order = await self._repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError("Order", order_id)
        if order.user_id != user_id:
            raise AuthorizationError("You can only view your own orders.")
        return order

# WRONG — service raises HTTP exception; couples domain to transport layer
from fastapi import HTTPException

class OrderService:
    async def get_order(self, order_id: int, user_id: int) -> Order:
        order = await self._repo.find_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")   # WRONG
```

### 2.2 Exception-to-HTTP mapping (FastAPI / Flask / DRF)

Map in exactly ONE place — a global exception handler. Never scatter HTTP status codes through service code.

```python
# app/core/exception_handlers.py

EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ConflictError: 409,
    RateLimitError: 429,
    ExternalServiceError: 502,
    ConfigurationError: 500,
    DataIntegrityError: 500,
    AppError: 500,   # fallback for any unmapped AppError subclass
}

# FastAPI handler
from fastapi import Request
from fastapi.responses import JSONResponse

async def app_exception_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": getattr(request.state, "request_id", None),
            }
        },
    )

# Registration in main.py
app.add_exception_handler(AppError, app_exception_handler)
```

---

## SECTION 3 — RAISING EXCEPTIONS CORRECTLY

### 3.1 Exception chaining — always preserve context

```python
# raise X from Y — explicit chaining; preserves original traceback in __cause__
try:
    result = await httpx_client.post(url, json=payload)
    result.raise_for_status()
except httpx.HTTPStatusError as exc:
    raise ExternalServiceError(
        service="payment-gateway",
        message=str(exc),
        status_code=exc.response.status_code,
    ) from exc           # CORRECT — traceback shows both errors

# raise X from None — intentional suppression; use only when original is noise
try:
    value = config["database_url"]
except KeyError:
    raise ConfigurationError(
        "DATABASE_URL environment variable is not set.",
        config_key="database_url",
    ) from None          # OK — KeyError detail adds no value to user

# WRONG — raise without from loses the original context
try:
    result = await call_api()
except requests.HTTPError:
    raise ExternalServiceError("api", "call failed")   # original traceback lost
```

### 3.2 Repository layer — wrap DB exceptions

```python
class UserRepository:
    async def create(self, data: UserCreate) -> User:
        try:
            user = User(**data.model_dump())
            self._session.add(user)
            await self._session.commit()
            await self._session.refresh(user)
            return user
        except IntegrityError as exc:
            await self._session.rollback()
            # Check constraint name to give precise error
            if "uq_users_email" in str(exc.orig):
                raise ConflictError(
                    f"A user with email '{data.email}' already exists.",
                    conflicting_field="email",
                ) from exc
            raise DataIntegrityError(
                f"Database constraint violated: {exc.orig}"
            ) from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            logger.error("db_create_failed", model="User", error=str(exc), exc_info=True)
            raise ExternalServiceError("database", str(exc)) from exc
```

---

## SECTION 4 — CATCHING EXCEPTIONS CORRECTLY

### 4.1 Always catch the most specific exception

```python
# CORRECT — narrow, specific
try:
    value = collection[key]
except KeyError:
    return default_value

# CORRECT — multiple specific types
try:
    connect(host, port)
except (ConnectionRefusedError, TimeoutError, OSError) as exc:
    logger.warning("connection_failed", host=host, port=port, error=str(exc))
    raise ExternalServiceError("db", str(exc)) from exc

# WRONG — too broad; masks unrelated bugs
try:
    result = process(data)
except Exception:
    return None

# WRONG — bare except catches SystemExit and KeyboardInterrupt
try:
    do_something()
except:            # catches EVERYTHING including Ctrl+C
    pass
```

### 4.2 Minimal try blocks

```python
# WRONG — too much code in try; KeyError from process() would be caught
try:
    return process(collection[key])
except KeyError:
    return default_value

# CORRECT — minimal scope; only the operation that can raise KeyError is in try
try:
    value = collection[key]
except KeyError:
    return default_value
else:
    return process(value)  # else clause: runs only if no exception was raised
```

### 4.3 The else clause — underused, valuable

```python
# try / except / else / finally — all four clauses together
def load_config(path: str) -> dict:
    try:
        f = open(path)
    except FileNotFoundError:
        logger.warning("config_not_found", path=path)
        return {}
    else:
        # Only runs if open() succeeded — cannot be confused with FileNotFoundError
        try:
            return json.load(f)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(f"Invalid JSON in {path}") from exc
    finally:
        # Always runs — whether or not an exception was raised
        # Note: if f is not defined (FileNotFoundError raised), this would NameError
        # Use contextlib.suppress or check with hasattr in complex cases
        pass
```

### 4.4 OS errors — use exception hierarchy, not errno

```python
# CORRECT — Python 3.3+ exception hierarchy
import os

try:
    os.remove(path)
except FileNotFoundError:
    pass  # already gone — that's fine
except PermissionError as exc:
    raise AuthorizationError(f"Cannot delete {path}: permission denied") from exc

# WRONG — errno introspection is fragile and platform-specific
import errno
try:
    os.remove(path)
except OSError as exc:
    if exc.errno == errno.ENOENT:   # fragile; don't do this in Python 3.3+
        pass
```

---

## SECTION 5 — LOGGING AND EXCEPTIONS

```python
# Log BEFORE re-raising — context is preserved, stack trace attached
try:
    result = await external_service.call()
except httpx.HTTPStatusError as exc:
    logger.error(
        "external_call_failed",
        service="payment",
        status_code=exc.response.status_code,
        url=str(exc.request.url),
        exc_info=True,      # attaches full stack trace to log entry
    )
    raise ExternalServiceError("payment", str(exc)) from exc

# WRONG — log after raising is unreachable; log instead of raising loses the error
try:
    result = await external_service.call()
except httpx.HTTPStatusError as exc:
    raise ExternalServiceError("payment", str(exc)) from exc
    logger.error("failed", error=str(exc))  # UNREACHABLE

# WRONG — logging swallows the exception; calling code cannot react
try:
    result = await external_service.call()
except httpx.HTTPStatusError as exc:
    logger.error("failed", error=str(exc))  # error is swallowed — caller gets None
```

---

## SECTION 6 — PYTHON 3.11+ EXCEPTION GROUPS

Python 3.11 introduced `ExceptionGroup` and `except*` for concurrent error handling. Only use when actually handling concurrent failures.

```python
# Python 3.11+ only — guard with version check or minimum version constraint
import sys

if sys.version_info >= (3, 11):
    # Raising multiple exceptions from concurrent operations
    exceptions = []
    for task_result in results:
        if task_result.error:
            exceptions.append(task_result.error)

    if exceptions:
        raise ExceptionGroup("Batch processing failed", exceptions)

    # Catching specific types from an ExceptionGroup
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(task_one())
            tg.create_task(task_two())
    except* ValidationError as eg:
        for exc in eg.exceptions:
            logger.warning("validation_failed", error=str(exc))
    except* ExternalServiceError as eg:
        for exc in eg.exceptions:
            logger.error("service_failed", error=str(exc))
```

---

## SECTION 7 — STANDARD ERROR RESPONSE SHAPE

All HTTP APIs must return errors in exactly this shape — no exceptions.

```json
{
    "error": {
        "code": "NOT_FOUND",
        "message": "Order with identifier '42' was not found.",
        "details": {
            "resource": "Order",
            "identifier": "42"
        },
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

For validation errors with multiple field violations:
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed.",
        "details": {
            "violations": [
                {"field": "email", "message": "Invalid email format."},
                {"field": "age", "message": "Must be at least 18."}
            ]
        },
        "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

---

## SECTION 8 — ANTI-PATTERNS REFERENCE

```python
# 1. Silent swallowing — the worst pattern in production code
try:
    process()
except Exception:
    pass              # error disappears; system continues in unknown state

# 2. Catching and only printing — no re-raise means caller thinks it succeeded
try:
    process()
except Exception as exc:
    print(exc)        # print() is not logging; nothing is alerted; caller gets None

# 3. Over-broad re-raise — you lose the specific type
try:
    process()
except Exception as exc:
    raise AppError(str(exc))   # original type (ValidationError, etc.) is lost

# 4. Raising generic Exception — use custom hierarchy
raise Exception("something went wrong")   # WRONG — untyped; uncatchable precisely

# 5. Using exception message strings for control flow — fragile
try:
    connect()
except Exception as exc:
    if "duplicate" in str(exc):   # WRONG — message format can change; DB-vendor specific
        handle_duplicate()

# 6. Catching then re-raising same exception unnecessarily
try:
    process()
except ValueError as exc:
    raise exc         # WRONG — just don't catch it; or use bare `raise`

try:
    process()
except ValueError:
    raise             # CORRECT — bare raise preserves original traceback
```
