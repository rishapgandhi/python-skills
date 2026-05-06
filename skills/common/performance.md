# Performance — Enterprise Standard

**Applies to:** All Python projects. Specific sections tagged by project type.
**Sources:** RORO pattern, async best practices, caching strategies from awesome-cursorrules community audit.

---

## SECTION 1 — ASYNC PROGRAMMING

### 1.1 async def vs def — the decision rule

```python
# Use async def for: DB queries, HTTP calls, file I/O, message queues, any waiting
async def get_user(user_id: int) -> User | None:
    return await session.scalar(select(User).where(User.id == user_id))

async def fetch_exchange_rate(currency: str) -> Decimal:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.rates.example.com/{currency}")
        return Decimal(response.json()["rate"])

# Use def for: pure computation, data transformation, validation logic, formatting
def calculate_discount(price: Decimal, pct: Decimal) -> Decimal:
    """Pure function — no I/O, no side effects. def is correct."""
    return (price * pct / 100).quantize(Decimal("0.01"))

def format_currency(amount: Decimal, symbol: str = "$") -> str:
    return f"{symbol}{amount:,.2f}"
```

### 1.2 Blocking I/O inside async context — always wrap

```python
import asyncio
from pathlib import Path

# WRONG — blocks the event loop; all other coroutines freeze
async def read_config() -> dict:
    return json.loads(Path("config.json").read_text())   # blocking file read

# CORRECT — runs blocking call in a thread pool; event loop stays free
async def read_config() -> dict:
    def _read() -> dict:
        return json.loads(Path("config.json").read_text())
    return await asyncio.to_thread(_read)

# CORRECT — for CPU-bound work: use ProcessPoolExecutor
import concurrent.futures

async def run_heavy_computation(data: list[int]) -> int:
    loop = asyncio.get_event_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        return await loop.run_in_executor(pool, sum, data)
```

### 1.3 Concurrent I/O — asyncio.gather()

```python
# WRONG — sequential; total time = sum of all individual times
async def get_dashboard_data(user_id: int) -> DashboardData:
    profile = await get_user_profile(user_id)        # 50ms
    orders = await get_recent_orders(user_id)         # 80ms
    notifications = await get_notifications(user_id)  # 30ms
    # Total: 160ms

# CORRECT — concurrent; total time = max of individual times
async def get_dashboard_data(user_id: int) -> DashboardData:
    profile, orders, notifications = await asyncio.gather(
        get_user_profile(user_id),
        get_recent_orders(user_id),
        get_notifications(user_id),
    )
    # Total: 80ms

# When one failure should not cancel others — use return_exceptions=True
results = await asyncio.gather(
    task_one(),
    task_two(),
    task_three(),
    return_exceptions=True,   # returns exceptions as values rather than raising
)
errors = [r for r in results if isinstance(r, Exception)]
if errors:
    logger.error("partial_failure", failed_count=len(errors))
```

---

## SECTION 2 — CACHING

### 2.1 Function-level caching with functools

```python
import functools
from typing import Any

# lru_cache — bounded cache (version: Python 3.2+)
@functools.lru_cache(maxsize=128)
def get_country_code(country_name: str) -> str | None:
    """Cache up to 128 most-recently-used country lookups."""
    return COUNTRY_MAP.get(country_name.upper())

# functools.cache — unbounded LRU (version: Python 3.9+)
# Equivalent to lru_cache(maxsize=None); slightly faster due to no size tracking
@functools.cache
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# RULES for functools caching:
# - Only cache functions with HASHABLE arguments (str, int, tuple — not list, dict)
# - Only cache PURE functions (same input always produces same output, no side effects)
# - Never cache functions that access DB, network, or time — use Redis instead
# - Cache size should be bounded for production (lru_cache with maxsize) unless
#   the input domain is provably small and finite
```

### 2.2 Web-layer caching with Redis (async)

```python
# FastAPI — using fastapi-cache2 + Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis

# In lifespan / startup
redis = aioredis.from_url("redis://localhost", encoding="utf8")
FastAPICache.init(RedisBackend(redis), prefix="myapp:")

# On route handler
@router.get("/products/{id}", response_model=ProductResponse)
@cache(expire=300)   # cache response for 300 seconds
async def get_product(id: int) -> ProductResponse:
    return await product_service.get_product(id)

# Manual cache pattern for service-layer caching with custom key
async def get_config(tenant_id: int) -> TenantConfig:
    cache_key = f"config:{tenant_id}"
    cached = await redis.get(cache_key)
    if cached:
        return TenantConfig.model_validate_json(cached)

    config = await config_repo.find_by_tenant(tenant_id)
    await redis.setex(cache_key, 600, config.model_dump_json())  # 10min TTL
    return config
```

### 2.3 Cache invalidation rules

```python
# RULE 1 — Always set a TTL. Unbounded caches are memory leaks.
# RULE 2 — Invalidate on write — when data changes, evict the cache entry.
# RULE 3 — Namespace keys by entity + identifier: "user:42", "config:tenant:7"
# RULE 4 — Document TTL choice in comments with the reason.

async def update_user(user_id: int, data: UserUpdate) -> User:
    user = await user_repo.update(user_id, data)

    # Invalidate cache on write — stale reads are worse than cache misses
    await redis.delete(f"user:{user_id}")
    await redis.delete(f"user:email:{user.email}")

    return user
```

---

## SECTION 3 — N+1 QUERY PREVENTION

### 3.1 SQLAlchemy — joinedload vs selectinload

```python
from sqlalchemy.orm import joinedload, selectinload

# joinedload — single SQL with JOIN; best for FK / OneToOne (at most one related)
users = await session.scalars(
    select(User).options(joinedload(User.profile))   # one JOIN — one user has one profile
)

# selectinload — two queries (SELECT IN); best for collections (one-to-many)
# Avoids cartesian product that joinedload creates with collections
orders = await session.scalars(
    select(Order).options(
        selectinload(Order.items),           # one query: SELECT * FROM items WHERE order_id IN (...)
        joinedload(Order.user),              # one JOIN: user is always exactly one
    ).where(Order.status == "pending")
)

# NEVER access a relationship in a loop without pre-loading
for order in orders:
    print(order.user.email)   # OK — already joinedloaded above
    for item in order.items:  # OK — already selectinloaded above
        print(item.product_id)
```

### 3.2 Django — select_related vs prefetch_related

```python
# select_related — SQL JOIN; for FK and OneToOne (single related object)
orders = Order.objects.select_related("user", "user__profile").filter(status="pending")

# prefetch_related — separate query with WHERE IN; for ManyToMany and reverse FK
orders = Order.objects.prefetch_related(
    "items",                      # reverse FK: ORDER_items
    "items__product",             # follow through to product
).select_related("user")

# Annotations to avoid COUNT N+1
from django.db.models import Count
users = User.objects.annotate(order_count=Count("orders")).filter(is_active=True)
# Now user.order_count is available without extra queries
```

---

## SECTION 4 — PAGINATION (mandatory for all list endpoints)

```python
# NEVER return unbounded querysets
async def list_users() -> list[User]:
    return await session.scalars(select(User)).all()  # WRONG — could return millions

# ALWAYS paginate
async def list_users(page: int = 1, page_size: int = 20) -> PaginatedResponse[UserResponse]:
    if not 1 <= page_size <= 100:
        raise ValidationError("page_size must be between 1 and 100")

    offset = (page - 1) * page_size
    total = await session.scalar(select(func.count(User.id)))
    users = await session.scalars(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )
```

---

## SECTION 5 — RESOURCE MONITORING (production services)

```python
# Use psutil for resource monitoring in long-running services
import psutil
import os

def get_process_memory_mb() -> float:
    """Return current process RSS memory usage in megabytes."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

# Log resource usage periodically in background services
async def log_resource_metrics() -> None:
    logger.info(
        "resource_metrics",
        memory_mb=round(get_process_memory_mb(), 1),
        cpu_percent=psutil.cpu_percent(interval=1),
        open_files=len(psutil.Process(os.getpid()).open_files()),
    )
```
