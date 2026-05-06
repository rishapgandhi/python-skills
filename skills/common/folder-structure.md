# Python Project Structure — Enterprise Standard

**Applies to:** All Python project types. Each section tagged with project archetype.
**Version:** Python 3.7+. Version-specific options noted per section.

---

## SECTION 1 — THE CORE PRINCIPLE

There is no universal folder structure — there are structures suited to the problem. This skill defines invariant rules that govern any structure, plus canonical layouts for the five most common Python project archetypes:

1. **Web service** (FastAPI / Flask / Django)
2. **Library / package** (PyPI or internal registry)
3. **Data pipeline / ETL**
4. **CLI tool**
5. **ML / AI project**

**Invariants — apply to every project regardless of archetype:**
- One `pyproject.toml` at root. No `setup.py`, `setup.cfg`, `tox.ini`, `.flake8`.
- `src/` layout for libraries; flat `app/` layout acceptable for applications.
- `tests/` always at root, mirroring source structure exactly.
- `.env.example` committed, `.env` never committed.
- No business logic in `__init__.py` — only re-exports or empty.
- No circular imports — enforced architecturally by layer discipline.

---

## SECTION 2 — SRC LAYOUT vs FLAT LAYOUT

### 2.1 src/ Layout — for libraries and installable packages

```
my-project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       └── ...
├── tests/
└── pyproject.toml
```

**Why:** Prevents accidental import of the package from root during testing. Without it, `import mypackage` in tests resolves to `./mypackage/` rather than the installed package, hiding installation bugs.

**Use when:** Libraries, packages published to PyPI or internal registries.

### 2.2 Flat Layout — for deployed applications

```
my-app/
├── app/
│   ├── __init__.py
│   └── ...
├── tests/
└── pyproject.toml
```

**Use when:** Web services, CLIs, data pipelines — deployed rather than installed.

---

## SECTION 3 — WEB SERVICE LAYOUT

```
my-service/
├── app/
│   ├── __init__.py
│   ├── main.py                     ← application factory / ASGI entrypoint
│   ├── core/                       ← cross-cutting concerns; no domain logic
│   │   ├── config.py               ← pydantic-settings config
│   │   ├── database.py             ← engine, session factory, Base
│   │   ├── security.py             ← token, password hashing
│   │   ├── exceptions.py           ← exception hierarchy
│   │   ├── logging.py              ← structlog configuration
│   │   └── middleware.py
│   │
│   ├── models/                     ← ORM models (one file per domain entity)
│   │   ├── base.py                 ← TimestampMixin, UUIDMixin, SoftDeleteMixin
│   │   ├── user.py
│   │   └── order.py
│   │
│   ├── schemas/                    ← Pydantic request/response models
│   │   ├── common.py               ← PaginatedResponse, ErrorResponse
│   │   ├── user.py                 ← UserCreate, UserUpdate, UserResponse
│   │   └── order.py
│   │
│   ├── repositories/               ← DB queries only; no business logic
│   │   ├── base.py                 ← generic CRUD base
│   │   ├── user_repository.py
│   │   └── order_repository.py
│   │
│   ├── services/                   ← business logic; orchestrates repositories
│   │   ├── user_service.py
│   │   └── order_service.py
│   │
│   ├── api/                        ← HTTP layer; routes, deps, serialisation
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── router.py
│   │       ├── users.py
│   │       ├── orders.py
│   │       └── health.py
│   │
│   ├── workers/                    ← Celery / ARQ tasks
│   │   ├── celery_app.py
│   │   └── tasks/
│   │       └── email_tasks.py
│   │
│   └── utils/                      ← pure stateless helpers; no layer dependencies
│       ├── pagination.py
│       └── date_utils.py
│
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   │   └── services/
│   │       └── test_user_service.py
│   ├── integration/
│   │   └── api/
│   │       └── test_users_endpoint.py
│   └── e2e/
│
├── migrations/
├── scripts/
├── docker/
├── .github/workflows/
├── docs/
│   ├── adr/                        ← Architecture Decision Records
│   └── runbooks/
├── pyproject.toml
├── .env.example
├── .pre-commit-config.yaml
└── README.md
```

### Layer Responsibility Contract

| Layer | Location | Sole Responsibility | May import from | Must NOT import from |
|---|---|---|---|---|
| API / Routes | `app/api/` | HTTP, validation, serialisation | Services, Schemas, core | Repositories, Models directly |
| Services | `app/services/` | Business logic, domain rules | Repositories, Models, core | API, DB session |
| Repositories | `app/repositories/` | DB queries, ORM operations | Models, DB session | Services, API, Schemas |
| Models | `app/models/` | DB schema definition | `app/models/base` only | Nothing above |
| Schemas | `app/schemas/` | Request/response shapes | Models (for ORM mode) | Services, Repositories |
| Core | `app/core/` | Config, exceptions, logging | stdlib, third-party | Nothing in app/ |
| Utils | `app/utils/` | Pure stateless helpers | stdlib, third-party | Anything in app/ |

**Canonical violations to never generate:**
```python
# VIOLATION — API calling repository directly (skips service; bypasses business logic)
@router.get("/users/{id}")
async def get_user(id: int, repo: UserRepository = Depends()):
    return await repo.find_by_id(id)

# VIOLATION — Service importing from API layer (inverted dependency)
from app.api.deps import get_current_user

# VIOLATION — Repository containing business logic
class UserRepository:
    async def get_eligible_discount_users(self):   # business logic; belongs in service
        ...
```

---

## SECTION 4 — LIBRARY / PACKAGE LAYOUT

```
my-library/
├── src/
│   └── mylibrary/
│       ├── __init__.py             ← public API + __all__ + __version__
│       ├── py.typed                ← PEP 561 marker; signals type info ships with package
│       ├── _internal/              ← private implementation; underscore = not public API
│       │   ├── __init__.py
│       │   ├── parser.py
│       │   └── validator.py
│       ├── exceptions.py
│       └── client.py
├── tests/
├── docs/
├── CHANGELOG.md
├── pyproject.toml
└── README.md
```

**Library-specific rules:**
- `__init__.py` must define `__all__` — makes the public API explicit and stable.
- `__version__` defined in `__init__.py` and matches `pyproject.toml`.
- `py.typed` required for PEP 561 compliance.
- Private implementation in `_internal/` — never documented or imported externally.

---

## SECTION 5 — DATA PIPELINE / ETL LAYOUT

```
my-pipeline/
├── pipeline/
│   ├── extract/                    ← data source connectors
│   │   ├── base.py                 ← abstract Extractor
│   │   ├── postgres_extractor.py
│   │   └── s3_extractor.py
│   ├── transform/                  ← pure transformation functions
│   │   ├── normalise.py
│   │   └── validate.py
│   ├── load/                       ← data sink connectors
│   │   ├── base.py
│   │   └── warehouse_loader.py
│   ├── models/                     ← data contracts (dataclasses or Pydantic)
│   │   ├── raw.py
│   │   └── processed.py
│   └── orchestrator.py
├── dags/                           ← Airflow DAGs or Prefect flows
├── tests/
├── data/
│   ├── samples/                    ← small samples for tests
│   └── schemas/                    ← JSON Schema / Avro
└── pyproject.toml
```

---

## SECTION 6 — CLI TOOL LAYOUT

```
my-cli/
├── src/
│   └── mycli/
│       ├── __init__.py
│       ├── __main__.py             ← enables `python -m mycli`
│       ├── cli.py                  ← Click / Typer root group
│       ├── commands/               ← one file per command group
│       │   ├── deploy.py
│       │   └── status.py
│       ├── core/
│       │   ├── config.py
│       │   └── exceptions.py
│       └── utils/
│           └── output.py           ← formatters: plain text, JSON, table
├── tests/
└── pyproject.toml

# pyproject.toml entry point
[project.scripts]
mycli = "mycli.cli:main"
```

---

## SECTION 7 — ML / AI PROJECT LAYOUT

```
my-ml-project/
├── src/
│   └── mymodel/
│       ├── data/
│       │   ├── dataset.py
│       │   ├── preprocessing.py
│       │   └── augmentation.py
│       ├── models/
│       │   ├── base.py
│       │   └── transformer.py
│       ├── training/
│       │   ├── trainer.py
│       │   ├── loss.py
│       │   └── metrics.py
│       ├── inference/
│       │   ├── predictor.py
│       │   └── postprocessing.py
│       └── config/
│           └── model_config.py
├── experiments/                    ← experiment configs (YAML) — version controlled
├── notebooks/                      ← exploration only; NOT production code paths
├── artifacts/                      ← gitignored; weights, checkpoints (use DVC)
├── tests/
└── pyproject.toml
```

**ML-specific rules:**
- Notebooks are exploration tools — all production logic lives in importable modules.
- Model configs are Pydantic models or dataclasses — never bare dicts.
- Artifacts are gitignored; use DVC or artifact storage (MLflow, W&B).

---

## SECTION 8 — FILE AND MODULE NAMING RULES

```
Modules:     short, all_lowercase, underscores if necessary
             user_service.py ✓   UserService.py ✗   userservice.py ✓

Packages:    short, lowercase, no underscores preferred
             mypackage ✓   my_package acceptable   MyPackage ✗

Test files:  mirror source with test_ prefix
             app/services/user_service.py → tests/unit/services/test_user_service.py

One domain per file: user.py, product.py, order.py — not a 20-class models.py

__init__.py: re-exports only or empty; never business logic

Never name a file the same as a stdlib module:
             email.py, io.py, types.py, logging.py will shadow stdlib imports
```

---

## SECTION 9 — WHAT NEVER GOES WHERE

| Location | Forbidden |
|---|---|
| `api/` routes | SQL queries, business rules, role-check logic |
| `services/` | Direct DB sessions, HTTP response objects, SQLAlchemy imports |
| `repositories/` | Business validation, external API calls, email sending |
| `models/` | Business methods; imports from services or api |
| `schemas/` | DB queries, service calls |
| `core/` | Domain logic; framework-specific code |
| `utils/` | Stateful code, DB access, external services |
| `__init__.py` | Business logic, side effects on import |
| `tests/` | Any production code path |
| `scripts/` | Any code imported by the application |

---

## SECTION 10 — MODULE & PACKAGE DESIGN RULES (Hitchhiker's Guide)

### Import Style: Explicitness Over Brevity

```python
# WORST — namespace pollution; reader cannot tell where sqrt came from
from math import *
x = sqrt(4)

# BETTER — explicit names imported, but origin unclear if many imports
from math import sqrt, pi
x = sqrt(4)

# BEST — always visible where the attribute comes from; zero ambiguity
import math
x = math.sqrt(4)
```

**Rule:** Prefer `import module` over `from module import name` in all but the simplest
single-file scripts. The verbosity of `math.sqrt(4)` is worthwhile; readability > brevity.
`from module import *` is prohibited everywhere except `__init__.py` re-exports.

### `__init__.py` — Keep It Lean

```
# CORRECT __init__.py patterns:

# 1. Empty — cleanest; package is a namespace only
# (nothing in the file)

# 2. Version only
__version__ = "1.2.3"

# 3. Public API re-export only
from .user import User
from .order import Order
__all__ = ["User", "Order"]
```

**Rules:**
- Never put business logic in `__init__.py`.
- Never trigger side effects on import (no DB connections, no file reads).
- The bigger the project, the leaner the `__init__.py`. Deep packages should have
  empty `__init__.py` files; only the top-level package exposes a public API.

### Project Pitfalls to Avoid

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **Circular dependencies** | `ImportError` or `import inside a method` | Restructure — A → B → A means one of them does too much |
| **Hidden coupling** | Changing Table breaks unrelated Carpenter tests | Make dependencies explicit; inject them as arguments |
| **Heavy global state** | Functions read/write module-level variables | Pass state as arguments; avoid mutable module globals |
| **Spaghetti code** | Pages of nested `if/for` with copy-pasted logic | Extract named functions; apply SRP |
| **Ravioli code** | Can't remember which of 8 "User" classes to use | Collect unrelated utilities in `utils.py`; name things unambiguously |

### Pure Functions vs Classes — When to Use Each

Use **pure functions** (no external state, no side effects, deterministic) when:
- Transforming data: parsing, formatting, calculating
- I/O handlers for file formats (read CSV → Dataset, write Dataset → CSV)
- Validation logic
- Business rules that take inputs and return outputs

Use **classes** when you need to **bundle state with behaviour**:
- Persisting session data across multiple method calls (HTTP session, DB connection pool)
- Modelling domain objects with lifecycle (Order, User, Product)
- Implementing the Repository or Service pattern with shared dependencies

```python
# Pure function — no class needed
def calculate_vat(amount: Decimal, rate: Decimal) -> Decimal:
    """Return VAT amount for given price and rate."""
    return (amount * rate).quantize(Decimal("0.01"))

# Class — bundles session state (cookies, auth) with HTTP behaviour
class APIClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._session = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    def get_user(self, user_id: int) -> dict:
        return self._session.get(f"/users/{user_id}").json()
```

**Warning for web apps:** In multi-process WSGI/ASGI deployments, class instances
holding mutable state are **not shared across workers**. Never use class-level or
module-level mutable variables to cache data that must be consistent across requests.
Use Redis, the database, or a proper cache layer instead.
