# Testing — Enterprise Standard

**Applies to:** All Python projects.
**Philosophy:** Tests are not verification — they are specification. Write them first when possible.

---

## SECTION 0 — TESTING PRINCIPLES (The Hitchhiker's Rules)

These principles apply regardless of framework (pytest, unittest, Django TestCase).
They represent the community consensus on what makes a test suite genuinely useful.

**One thing per test.** A test unit should focus on one tiny bit of functionality and prove it correct.
Multiple assertions are fine when they all verify the same behaviour — but a test that checks
registration *and* login *and* profile update is three tests masquerading as one.

**Independence is imperative.** Every test must run correctly in isolation and in any order.
No test may depend on the side effects of a previous test. Use fixtures and factories
to build fresh state for each test; never share mutable state across tests.

**Long, descriptive names.** Test functions are never called explicitly — their names appear only
in failure output. `test_square_of_negative_number_returns_positive()` beats `test_square()`.
State the expected behaviour: `"Returns 404 when post is unpublished"` not `"Tests 404"`.

**Speed matters.** Slow tests don't get run. If a test takes more than a few hundred milliseconds,
it will be skipped during development, defeating its purpose. Isolate slow integration tests
into a separate suite run only in CI.

**Write a failing test before fixing a bug.** The first step when debugging is to write a test
that reproduces the bug. This test becomes the most valuable permanent addition to the suite —
it prevents the bug from regressing silently.

**Test at session boundaries.** Run the full suite before a coding session and again after.
CI hooks that block merges on failing tests are not optional — they are the enforcement mechanism.

**If a test is hard to explain, the code is probably wrong.** A unit test whose purpose is
unclear usually means the code under test has too many responsibilities. Refactor the code,
not the test.

**If a test is easy to explain, it's probably a good idea.** New contributors learn the codebase
by reading tests. Well-named, readable tests are onboarding documentation.

**Debug using a test.** In the face of an ambiguous bug: don't add `print()` — write a test
that isolates the failing case. The test documents the fix permanently.

---

## SECTION 1 — TOOLCHAIN

| Tool | Role |
|---|---|
| `pytest` | Test runner and assertion framework |
| `pytest-asyncio` | async test support; `asyncio_mode = "auto"` |
| `pytest-cov` | Coverage measurement; blocks CI below threshold |
| `factory_boy` | Model/schema factories; never hardcode test data inline |
| `faker` | Fake data generation used inside factories |
| `httpx[asyncio]` | Async HTTP test client for FastAPI/Starlette |
| `testcontainers` | Real PostgreSQL/Redis containers in integration tests |
| `pytest-mock` | Mocker fixture wrapping `unittest.mock` |
| `freezegun` | Freeze/travel time in tests that touch datetime |
| `respx` | Mock httpx calls in unit tests |
| `time-machine` | Faster alternative to freezegun (Python 3.8+) |

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
    "--cov=app",
    "--cov-report=term-missing",
    "--cov-report=xml",
    "--cov-fail-under=80",
    "-x",                    # stop on first failure (remove in CI for full picture)
    "--tb=short",
]

[tool.coverage.run]
source = ["app"]
omit = [
    "app/core/config.py",    # config loading, no logic
    "migrations/*",
    "scripts/*",
    "tests/*",
]
branch = true                # branch coverage, not just line coverage

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "@(abc\\.)?abstractmethod",
]
```

---

## SECTION 2 — TEST CATEGORIES AND SCOPE

### 2.1 Unit Tests

- Test a **single function or method** in complete isolation.
- All dependencies replaced with mocks/fakes.
- No network, no filesystem, no DB — zero I/O.
- Should run in < 1ms each; entire unit suite in < 5 seconds.
- Location: `tests/unit/`

### 2.2 Integration Tests

- Test a **real interaction between two or more components**.
- Use `testcontainers` for a real PostgreSQL/Redis (not SQLite).
- May hit real filesystem; no real network (external APIs are mocked).
- Location: `tests/integration/`

### 2.3 End-to-End Tests

- Test a **complete user-visible flow** against a running service.
- Only in `tests/e2e/` — never run in unit or integration CI.
- Location: `tests/e2e/`

### 2.4 Performance / Load Tests (Locust / k6)

- Separate from pytest; in `tests/performance/` or dedicated repo.
- Never mixed with unit or integration tests.

---

## SECTION 3 — TEST STRUCTURE AND NAMING

### 3.1 File and class naming

```
Source:   app/services/order_service.py
Tests:    tests/unit/services/test_order_service.py
          tests/integration/services/test_order_service_integration.py

Test class:   class TestOrderService:
Test method:  def test_{method}_{scenario}_{expected_outcome}(self):
              def test_create_order_with_valid_data_returns_order(self):
              def test_create_order_when_product_not_found_raises_not_found_error(self):
              def test_get_orders_for_inactive_user_raises_authorization_error(self):
```

### 3.2 AAA Pattern — every test is three sections

```python
async def test_create_order_with_valid_data_returns_persisted_order(
    self,
    order_service: OrderService,
    mock_order_repo: AsyncMock,
    mock_product_repo: AsyncMock,
) -> None:
    # Arrange — set up inputs and mock behaviours
    product = ProductFactory.build(id=1, price=Decimal("49.99"), is_active=True)
    mock_product_repo.find_by_id.return_value = product
    expected_order = OrderFactory.build(product_id=1, quantity=2)
    mock_order_repo.create.return_value = expected_order

    request = OrderCreateFactory.build(product_id=1, quantity=2)

    # Act — call the unit under test; one call only
    result = await order_service.create_order(user_id=42, data=request)

    # Assert — verify outcome; be specific
    assert result == expected_order
    mock_order_repo.create.assert_called_once()
    call_args = mock_order_repo.create.call_args[0][0]
    assert call_args.product_id == 1
    assert call_args.quantity == 2
    assert call_args.user_id == 42
```

---

## SECTION 4 — FIXTURES AND CONFTEST

### 4.1 Conftest hierarchy

```python
# tests/conftest.py — session-scoped; available everywhere
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest.fixture(scope="session")
def app():
    """Create application once per test session."""
    return create_app()


@pytest.fixture
async def client(app) -> AsyncClient:
    """Async HTTP client for API endpoint tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# tests/unit/services/conftest.py — fixtures scoped to unit/services/
@pytest.fixture
def mock_order_repo(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(spec=OrderRepository)

@pytest.fixture
def mock_product_repo(mocker: MockerFixture) -> AsyncMock:
    return mocker.AsyncMock(spec=ProductRepository)

@pytest.fixture
def order_service(
    mock_order_repo: AsyncMock,
    mock_product_repo: AsyncMock,
) -> OrderService:
    return OrderService(
        order_repo=mock_order_repo,
        product_repo=mock_product_repo,
    )
```

### 4.2 Fixture scope — choose carefully

```python
# scope="function" (default) — new fixture per test; always safe
# scope="class"    — shared within a test class
# scope="module"   — shared within a test file
# scope="session"  — shared for the entire test run

# Database containers are session-scoped (expensive to create)
@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

# DB engine is session-scoped (one engine per run)
@pytest.fixture(scope="session")
async def db_engine(postgres_container):
    engine = create_async_engine(postgres_container.get_connection_url())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

# DB session is function-scoped — each test gets a fresh, rolled-back transaction
@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(db_engine) as session:
        async with session.begin():
            yield session
            await session.rollback()   # rollback after each test — DB stays clean
```

---

## SECTION 5 — FACTORIES

Never hardcode test data inline. Always use factory_boy factories.

```python
# tests/factories.py

import factory
from decimal import Decimal
from factory import LazyAttribute, SubFactory, fuzzy
from faker import Faker

fake = Faker()
Faker.seed(0)  # deterministic fake data


class UserFactory(factory.Factory):
    """Factory for User ORM model instances."""

    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    email = LazyAttribute(lambda obj: f"user{obj.id}@example.com")
    name = LazyAttribute(lambda _: fake.name())
    is_active = True
    role = "viewer"
    created_at = LazyAttribute(lambda _: fake.date_time_this_year(tzinfo=timezone.utc))


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.Sequence(lambda n: n + 100)
    name = LazyAttribute(lambda _: fake.catch_phrase())
    price = fuzzy.FuzzyDecimal(low=Decimal("0.01"), high=Decimal("999.99"), precision=2)
    is_active = True
    sku = LazyAttribute(lambda obj: f"SKU-{obj.id:05d}")


class OrderCreateFactory(factory.Factory):
    """Factory for OrderCreate Pydantic schema."""

    class Meta:
        model = OrderCreate

    product_id = factory.Sequence(lambda n: n + 100)
    quantity = fuzzy.FuzzyInteger(1, 10)


# Traits — predefined variations
class InactiveUserFactory(UserFactory):
    is_active = False

class AdminUserFactory(UserFactory):
    role = "admin"

class ExpensiveProductFactory(ProductFactory):
    price = Decimal("999.99")
```

---

## SECTION 6 — WHAT MUST BE TESTED

| Must test | Why |
|---|---|
| All service methods — happy path | Verifies the contract |
| All service methods — every error branch | Verifies exception types and messages |
| All API endpoints — correct status codes | Contract with consumers |
| All API endpoints — response schema shape | Prevents breaking changes |
| All custom validators | Input sanitisation |
| All repository constraint violations | DB error handling |
| Permission / auth enforcement | Security |
| Edge cases: empty input, None, max values | Real-world resilience |
| All background tasks (unit level) | Often missed |

| Skip | Why |
|---|---|
| Auto-generated migration files | Not production code |
| Third-party library internals | Not your code |
| Trivial property accessors with no logic | No branch to test |
| `__repr__` and `__str__` | Unless they contain logic |

---

## SECTION 7 — MOCKING GUIDELINES

```python
# Mock at the boundary closest to the test — not at the framework level
# CORRECT — mock the repository, not the database driver
mock_repo.find_by_id.return_value = UserFactory.build(id=1)

# CORRECT — mock external HTTP with respx, not the application code
import respx
import httpx

@respx.mock
async def test_stripe_charge_success():
    respx.post("https://api.stripe.com/v1/charges").mock(
        return_value=httpx.Response(200, json={"id": "ch_123", "status": "succeeded"})
    )
    result = await stripe_client.charge(amount=100, token="tok_test")
    assert result.charge_id == "ch_123"

# CORRECT — freeze time for datetime-dependent code
from freezegun import freeze_time

@freeze_time("2026-01-15 10:30:00")
def test_token_expiry():
    token = create_access_token(user_id=1)
    payload = decode_token(token)
    assert payload["exp"] == datetime(2026, 1, 15, 10, 45, 0, tzinfo=timezone.utc)

# WRONG — mocking too deep (implementation detail)
mocker.patch("sqlalchemy.engine.Engine.connect")   # too internal; breaks on SQLAlchemy update

# WRONG — not mocking at all in a unit test (real DB)
async def test_get_user_unit():  # this is an integration test, not a unit test
    user = await real_db_session.execute(select(User).where(User.id == 1))
    ...
```

---

## SECTION 8 — COVERAGE RULES

```
Minimum overall coverage:              80% (CI fails below this)
Business logic (services):             90% target
Authentication / security paths:       95% — non-negotiable
Payment / financial logic:             95% — non-negotiable
Happy paths only is not enough:        every raise statement needs a test
```

**Coverage is a floor, not a goal.** 100% coverage with weak assertions is useless. 85% coverage with strong assertions that test real behaviour is far more valuable.

---

## SECTION 9 — INTEGRATION TEST PATTERN

```python
# tests/integration/api/test_users_endpoint.py

import pytest
from httpx import AsyncClient


class TestCreateUserEndpoint:
    """Integration tests for POST /api/v1/users."""

    async def test_create_user_returns_201_with_user_data(
        self,
        client: AsyncClient,
        db_session,    # real DB session; rolled back after test
    ) -> None:
        payload = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "SecurePass1!",
        }

        response = await client.post("/api/v1/users/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "id" in data
        assert "password" not in data      # never expose password in response
        assert "password_hash" not in data

    async def test_create_user_with_duplicate_email_returns_409(
        self,
        client: AsyncClient,
        db_session,
    ) -> None:
        existing_user = UserFactory.build()
        db_session.add(User(**existing_user.__dict__))
        await db_session.flush()

        payload = {"email": existing_user.email, "name": "Another", "password": "Pass1!"}

        response = await client.post("/api/v1/users/", json=payload)

        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == "CONFLICT"

    async def test_create_user_with_invalid_email_returns_422(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.post(
            "/api/v1/users/",
            json={"email": "not-an-email", "name": "A", "password": "Pass1!"},
        )
        assert response.status_code == 422

    async def test_unauthenticated_access_to_protected_endpoint_returns_401(
        self,
        client: AsyncClient,
    ) -> None:
        response = await client.get("/api/v1/users/1")  # no auth header
        assert response.status_code == 401
```

---

## SECTION 10 — DJANGO-SPECIFIC TESTING

### 10.1 TestCase vs TransactionTestCase

| Class | When to use |
|---|---|
| `django.test.TestCase` | Default — wraps each test in a savepoint, rolled back after. Fast. |
| `django.test.TransactionTestCase` | Only when testing signals, raw transactions, or `on_commit` hooks. Slow. |
| `django.test.SimpleTestCase` | No DB at all — pure logic, no model access. Fastest. |

```python
from django.test import TestCase, TransactionTestCase

class TestOrderService(TestCase):
    """Standard test case — DB state rolled back automatically."""

    def test_create_order_success(self) -> None:
        ...

class TestOrderSignals(TransactionTestCase):
    """Signals fire after commit — needs TransactionTestCase."""

    def test_order_created_signal_fires(self) -> None:
        ...
```

### 10.2 Preferred Django Assertion Methods

Use these over the generic `assertEqual` / `assertTrue` equivalents — they produce
better failure messages and catch more subtle bugs.

```python
from django.test import TestCase

class TestMyView(TestCase):

    # Exception + message assertions — always check the message too
    def test_validation_error_message(self) -> None:
        with self.assertRaisesMessage(ValidationError, "User not found"):
            service.get_user(user_id=9999)

    # assertWarns with message check
    def test_deprecated_api_warning(self) -> None:
        with self.assertWarnsMessage(DeprecationWarning, "use new_api()"):
            old_api()

    # Boolean — check the actual bool, not truthiness
    def test_user_is_active(self) -> None:
        user = User.objects.get(pk=1)
        self.assertIs(user.is_active, True)   # ✅ — checks bool identity
        # NOT: self.assertTrue(user.is_active) — passes for any truthy value

    # Regex — only when you genuinely need pattern matching
    def test_error_includes_field_name(self) -> None:
        with self.assertRaisesRegex(ValidationError, r"email.*invalid"):
            ...
```

**Rules:**
- Use `assertRaisesMessage()` over `assertRaises()` whenever you care about the message (you almost always should).
- Use `assertIs(result, True)` / `assertIs(result, False)` over `assertTrue()` / `assertFalse()` to verify the actual bool value, not just truthiness.
- In test docstrings, state the **expected behaviour**: `"Returns 404 when post is unpublished"` not `"Tests that 404 is returned"`.

### 10.3 Conditional Version Pragmas

When code branches on Python or Django version, mark the branch so coverage reports
exclude the irrelevant side on each version:

```python
import sys
import django

# Python version branches
if sys.version_info >= (3, 11):  # pragma: only py>=3.11
    from tomllib import loads
else:  # pragma: only py<3.11
    from tomli import loads  # third-party backport

# Django version branches
if django.VERSION[:2] >= (4, 2):  # pragma: django>=4.2 branch
    from django.db import connection
    connection.ensure_connection()

# Supported operators: <, <=, ==, !=, >, >=
# Supported prefixes: py, django (add others in conftest if needed)
# Correct pragma always: no cover = exclude whole block; branch = exclude branch only
```

**Rules:**
- Always use specific pragmas, never blanket `# pragma: no cover` on version branches.
- `# pragma: only py>=X.Y` — excludes the entire block on non-matching versions.
- `# pragma: py>=X.Y branch` — excludes just the branch (not the condition check).
- Add pragma support for your `cryptography`, `celery`, or other dep versions in
  `conftest.py` if you branch on those.

---

## SECTION 11 — PARAMETRIZE FOR COVERAGE BREADTH

```python
@pytest.mark.parametrize("invalid_email", [
    "",
    "not-an-email",
    "@example.com",
    "user@",
    "user @example.com",
    "a" * 255 + "@example.com",   # too long
])
async def test_create_user_with_invalid_email_raises_validation_error(
    self,
    order_service: OrderService,
    invalid_email: str,
) -> None:
    data = UserCreateFactory.build(email=invalid_email)
    with pytest.raises(ValidationError) as exc_info:
        await user_service.create_user(data)
    assert exc_info.value.field == "email"


@pytest.mark.parametrize("quantity,expected_total", [
    (1, Decimal("49.99")),
    (2, Decimal("99.98")),
    (10, Decimal("499.90")),
])
async def test_order_total_calculation(
    self,
    quantity: int,
    expected_total: Decimal,
) -> None:
    product = ProductFactory.build(price=Decimal("49.99"))
    total = calculate_order_total(product, quantity)
    assert total == expected_total
```

---

## SECTION 12 — ASSERT METHOD SELECTION GUIDE

Choosing the wrong assert method gives poor failure messages. Always pick the most
specific method available. This table is the reference used by agents when generating tests.

### 12.1 Equality & Identity

| Situation | Use | Not |
|---|---|---|
| Two values are equal | `assertEqual(a, b)` | `assertTrue(a == b)` |
| Two values are not equal | `assertNotEqual(a, b)` | `assertFalse(a == b)` |
| Same object (`is`) | `assertIs(a, b)` | `assertEqual(a, b)` |
| Not same object (`is not`) | `assertIsNot(a, b)` | |
| Value is `None` | `assertIsNone(x)` | `assertEqual(x, None)` |
| Value is not `None` | `assertIsNotNone(x)` | `assertFalse(x is None)` |
| Boolean is literally `True` | `assertIs(result, True)` | `assertTrue(result)` |
| Boolean is literally `False` | `assertIs(result, False)` | `assertFalse(result)` |
| Expression is truthy | `assertTrue(expr)` | — (only for non-bool truthiness) |
| Expression is falsy | `assertFalse(expr)` | — (only for non-bool falsiness) |

```python
# ✅ Correct — assertIs checks identity, catches non-bool truthy values
self.assertIs(user.is_verified, True)

# ❌ Wrong — passes for any truthy return, misses bugs where is_verified = 1
self.assertTrue(user.is_verified)
```

### 12.2 Type & Membership

| Situation | Use |
|---|---|
| Object is instance of a class | `assertIsInstance(obj, SomeClass)` |
| Object is NOT instance | `assertNotIsInstance(obj, SomeClass)` |
| Exact type (no subclasses) | `assertIs(type(obj), SomeClass)` |
| Value in collection | `assertIn(member, container)` |
| Value not in collection | `assertNotIn(member, container)` |
| Class is subclass of another | `assertIsSubclass(cls, Base)` *(Python 3.14+)* |
| Object has an attribute | `assertHasAttr(obj, "name")` *(Python 3.14+)* |

### 12.3 Numeric & Approximate

```python
# Floating point — never assertEqual; always assertAlmostEqual
self.assertAlmostEqual(result, 3.14159, places=4)   # rounds to 4 decimal places
self.assertAlmostEqual(total, expected, delta=0.01)  # within ±0.01

# Ordered comparisons
self.assertGreater(response_time_ms, 0)
self.assertLessEqual(response_time_ms, 200)
self.assertGreaterEqual(items_processed, 1)
```

### 12.4 Sequences (order-independent)

```python
# assertCountEqual — same elements regardless of order, duplicates counted
self.assertCountEqual(result_tags, ["python", "django", "api"])

# assertListEqual / assertTupleEqual — same elements AND same order
self.assertListEqual(sorted_items, [1, 2, 3])

# assertSetEqual — set equality
self.assertSetEqual(set(result), {"read", "write"})

# assertDictEqual — dictionary equality with rich diff on failure
self.assertDictEqual(response.json(), {"status": "ok", "count": 3})
```

### 12.5 Strings & Patterns

```python
# assertMultiLineEqual — best for comparing long strings; shows diff on failure
self.assertMultiLineEqual(rendered_html, expected_html)

# assertRegex — when exact match isn't needed
self.assertRegex(error_message, r"User \d+ not found")
self.assertNotRegex(log_output, r"password|secret|token")

# Python 3.14+ string helpers
self.assertStartsWith(response_body, '{"status"')
self.assertEndsWith(filename, ".csv")
```

### 12.6 Exceptions & Warnings

```python
# Basic exception — always prefer context manager form
with self.assertRaises(ValueError):
    parse_age("not-a-number")

# With message check — ALWAYS check message when it matters for users/API consumers
with self.assertRaisesMessage(ValidationError, "Email is required"):
    UserService.create(email="", name="Test")

# Access the exception object for deeper inspection
with self.assertRaises(OrderError) as ctx:
    order_service.cancel(order_id=999)
self.assertEqual(ctx.exception.error_code, "ORDER_NOT_FOUND")
self.assertIs(ctx.exception.retryable, False)

# Regex on exception message — only when exact text is variable
with self.assertRaisesRegex(PermissionError, r"User \d+ lacks 'admin' permission"):
    admin_service.delete_user(user_id=42)

# Warning assertions
with self.assertWarns(DeprecationWarning):
    legacy_api_call()

with self.assertWarnsMessage(DeprecationWarning, "use new_create() instead"):
    old_create_user(email="x@y.com")
```

### 12.7 Log Assertions

Test that code emits (or does NOT emit) log messages — essential for monitoring paths:

```python
import logging

class TestOrderService(TestCase):

    def test_retry_logs_warning_on_first_failure(self) -> None:
        """Service logs a warning before first retry attempt."""
        with self.assertLogs("myapp.orders", level="WARNING") as log_ctx:
            order_service.process_with_retry(order_id=1)

        self.assertIn("WARNING:myapp.orders:Retrying order 1", log_ctx.output)

    def test_successful_order_emits_no_errors(self) -> None:
        """Happy path produces no ERROR or CRITICAL log messages."""
        with self.assertNoLogs("myapp.orders", level="ERROR"):
            order_service.process(order_id=2)
```

**Rules:**
- `assertLogs(logger, level)` — at least one message at that level must be emitted; fails otherwise.
- `assertNoLogs(logger, level)` — no messages at or above that level must be emitted *(Python 3.10+)*.
- Always specify both `logger` (name string) and `level` — never rely on root logger defaults.
- `log_ctx.output` is a list of strings in format `"LEVEL:logger_name:message"`.
- `log_ctx.records` gives raw `LogRecord` objects for deeper inspection.

---

## SECTION 13 — SKIPPING TESTS & EXPECTED FAILURES

### 13.1 Skip Decorators

```python
import sys
import unittest

class TestPaymentGateway(TestCase):

    @unittest.skip("Stripe sandbox is down — restore after INFRA-442")
    def test_card_charge(self) -> None:
        ...

    @unittest.skipIf(
        settings.ENVIRONMENT == "ci",
        "External payment calls disabled in CI"
    )
    def test_live_webhook(self) -> None:
        ...

    @unittest.skipUnless(
        sys.platform.startswith("linux"),
        "File permission test only valid on Linux"
    )
    def test_file_permissions(self) -> None:
        ...
```

**Skip in setUp — when a shared resource is unavailable:**
```python
class TestElasticsearchIndexing(TestCase):

    def setUp(self) -> None:
        if not es_client.ping():
            self.skipTest("Elasticsearch not reachable — skipping index tests")
        self.index = es_client.indices.create(index="test_products")

    def test_product_indexed_after_save(self) -> None:
        ...
```

**Skip entire class:**
```python
@unittest.skip("Feature flag ORDERS_V2 not yet deployed")
class TestOrdersV2(TestCase):
    ...
```

### 13.2 Expected Failures

Mark tests that are **known broken** and tracked — they pass (silently) when broken,
and fail the suite when they unexpectedly start passing:

```python
class TestKnownBugs(TestCase):

    @unittest.expectedFailure
    def test_pagination_with_filters_returns_correct_count(self) -> None:
        """BUG-291: Filter + pagination count is off by one. Remove decorator when fixed."""
        result = product_service.list(category="books", page=2, page_size=10)
        self.assertEqual(result.total_count, 47)
```

**Rules:**
- `@unittest.skip` — use for environmental reasons (external service down, platform-specific).
- `@unittest.skipIf` — use for version or config conditions evaluated at import time.
- `@unittest.skipUnless` — inverse of `skipIf`; use when condition must be true to run.
- `@unittest.expectedFailure` — use only for tracked bugs with a ticket reference. Never use to hide
  flaky tests. Remove the decorator the moment the bug is fixed.
- Every `skip` call must include a reason string. Never: `@unittest.skip("")`.

---

## SECTION 14 — FIXTURE LIFECYCLE & CLEANUP

### 14.1 Fixture Scope Hierarchy

```
setUpModule()          ← runs once for the whole module
  setUpClass()         ← runs once per class
    setUp()            ← runs before each test method
      test_method()
    tearDown()         ← runs after each test method (if setUp succeeded)
    addCleanup(fn)     ← runs after tearDown, even if setUp/test failed — LIFO order
  tearDownClass()      ← runs once per class
  addClassCleanup(fn)  ← runs after tearDownClass — LIFO order
tearDownModule()       ← runs once for the whole module
addModuleCleanup(fn)   ← runs after tearDownModule — LIFO order
```

### 14.2 setUp / tearDown — Per-Test Fixtures

```python
class TestUserRepository(TestCase):

    def setUp(self) -> None:
        """Create a fresh DB connection before each test."""
        self.conn = create_test_db_connection()
        self.repo = UserRepository(self.conn)

    def tearDown(self) -> None:
        """Close connection after each test — only called if setUp succeeded."""
        self.conn.close()
```

**Important:** `tearDown` is only called when `setUp` succeeded. If `setUp` raises,
`tearDown` is skipped — use `addCleanup` for guaranteed cleanup.

### 14.3 addCleanup — Guaranteed Cleanup (Prefer Over tearDown)

`addCleanup` runs in **LIFO order** regardless of whether `setUp` or the test itself failed.
Prefer it over `tearDown` for resource cleanup:

```python
class TestFileProcessor(TestCase):

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir)   # ✅ always runs, even if setUp fails mid-way

        self.config_file = create_config(self.tmp_dir)
        self.addCleanup(self.config_file.close)          # ✅ LIFO: file closed before dir removed

    def test_processes_csv(self) -> None:
        ...
```

### 14.4 setUpClass / tearDownClass — Expensive Shared Resources

Use for resources that are slow to create and safe to share across tests in a class
(DB connections, test servers, loaded ML models):

```python
class TestReportGenerator(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        """Spin up a test database once for all tests in this class."""
        super().setUpClass()  # always call super — required
        cls.db = create_test_database()
        cls.addClassCleanup(cls.db.drop)  # cleaner than tearDownClass

    def test_monthly_report(self) -> None:
        result = ReportGenerator(self.db).generate(period="monthly")
        self.assertIsNotNone(result)
```

**Rules:**
- Always call `super().setUpClass()` — required by Django's `TestCase` and other subclasses.
- Prefer `addClassCleanup()` over `tearDownClass()` for the same reason as `addCleanup` over `tearDown`.
- Never put mutable shared state in class fixtures if tests modify it — use `setUp` per-test instead.
- Shared class fixtures break test isolation. Use sparingly; document clearly.

### 14.5 setUpModule / tearDownModule

For truly global one-time setup (starting a server process, loading a fixture file):

```python
# At module level — no class

def setUpModule() -> None:
    """Start a mock external API server for all tests in this module."""
    global _mock_server
    _mock_server = MockAPIServer.start(port=18080)
    unittest.addModuleCleanup(_mock_server.stop)  # guaranteed cleanup

def tearDownModule() -> None:
    pass  # prefer addModuleCleanup above instead
```

---

## SECTION 15 — SUBTEST: MULTIPLE ASSERTIONS IN ONE TEST

`self.subTest()` lets you run multiple related assertions in a single test method while
still reporting each failure independently. This is the `unittest` equivalent of
`@pytest.mark.parametrize` for use inside `TestCase` classes:

```python
class TestAgeValidator(TestCase):

    def test_invalid_ages_raise_validation_error(self) -> None:
        """All invalid age values must raise ValidationError with a useful message."""
        invalid_cases = [
            (-1,   "Age cannot be negative"),
            (0,    "Age must be at least 1"),
            (151,  "Age cannot exceed 150"),
            (None, "Age is required"),
        ]
        for age, expected_fragment in invalid_cases:
            with self.subTest(age=age):          # ← each iteration reported separately
                with self.assertRaisesMessage(ValidationError, expected_fragment):
                    validate_age(age)
```

**Without `subTest`:** First failure stops all remaining iterations — you only see one failure.
**With `subTest`:** All iterations run; each failure is reported individually with the parameter value.

```python
# Also works for output assertions across multiple inputs
class TestSlugifier(TestCase):

    def test_slugify(self) -> None:
        cases = [
            ("Hello World",   "hello-world"),
            ("  spaces  ",    "spaces"),
            ("Héllo",         "hello"),
            ("a--b",          "a-b"),
        ]
        for text, expected in cases:
            with self.subTest(input=text):
                self.assertEqual(slugify(text), expected)
```

**Rules:**
- Use `subTest` when testing multiple related inputs/outputs inside one logical test.
- Prefer `@pytest.mark.parametrize` for new pytest-native code — `subTest` is the equivalent
  for code that must use `unittest.TestCase` (Django tests, legacy code).
- Always pass meaningful keyword args to `subTest` — they appear in failure output.

---

## SECTION 16 — ASYNC TESTS (IsolatedAsyncioTestCase)

For testing async code without pytest-asyncio:

```python
from unittest import IsolatedAsyncioTestCase
import asyncio


class TestAsyncOrderService(IsolatedAsyncioTestCase):
    """Use IsolatedAsyncioTestCase for async service/repository tests."""

    async def asyncSetUp(self) -> None:
        """Async setUp — runs after setUp(), before test method."""
        self.conn = await create_async_db_connection()
        self.service = AsyncOrderService(self.conn)

    async def asyncTearDown(self) -> None:
        """Async tearDown — runs before tearDown()."""
        await self.conn.close()

    async def test_create_order_returns_id(self) -> None:
        """create_order returns a positive integer order ID."""
        order_id = await self.service.create_order(
            user_id=1, items=[{"product_id": 10, "qty": 2}]
        )
        self.assertIsInstance(order_id, int)
        self.assertGreater(order_id, 0)

    async def test_get_nonexistent_order_raises(self) -> None:
        """Fetching a missing order raises OrderNotFoundError."""
        with self.assertRaises(OrderNotFoundError):
            await self.service.get_order(order_id=99999)
```

**Execution order inside `IsolatedAsyncioTestCase`:**
```
setUp()  →  asyncSetUp()  →  test_method()  →  asyncTearDown()  →  tearDown()  →  cleanups
```

**Rules:**
- Use `IsolatedAsyncioTestCase` when the class must inherit from `unittest.TestCase`
  (e.g., Django project with async views/services).
- For pytest-native async tests, prefer `pytest-asyncio` with `@pytest.mark.asyncio`.
- `addAsyncCleanup(coro_func)` is the async equivalent of `addCleanup` — use it for
  guaranteed async resource teardown.
- Each test gets a **fresh event loop** — no cross-test async state leakage.

