# Database Design — Enterprise Standard

**Applies to:** All Python projects using a relational database.
**ORMs covered:** SQLAlchemy 2.x (async), Django ORM.
**Migration tools:** Alembic (SQLAlchemy), Django migrations.

---

## SECTION 1 — MODEL FOUNDATION

### 1.1 Abstract Base Mixins — always use, never duplicate

```python
# app/models/base.py

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at audit fields to any model.

    These are set by the database server (server_default / onupdate)
    so they are always accurate regardless of application timezone config.
    All timestamps are stored in UTC. Convert to local time in the
    presentation layer only.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,          # commonly used in ORDER BY; index pays for itself
        doc="UTC timestamp when this record was first created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="UTC timestamp when this record was last modified.",
    )


class UUIDPublicIdMixin:
    """Adds a UUID public identifier alongside the integer primary key.

    Use public_id in all API responses and URLs.
    Use id (integer) for internal joins and foreign keys.

    Rationale:
    - Integer PK: fast joins, small storage, auto-increment simplicity.
    - UUID public_id: prevents sequential enumeration attacks in APIs,
      enables safe exposure to external systems without revealing record count.
    """

    public_id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
        doc="UUID used in public APIs. Never expose integer id externally.",
    )


class SoftDeleteMixin:
    """Adds soft-delete capability.

    Records are never physically deleted — deleted_at is set instead.
    Hard deletes require a separate archival / purge process.

    Use with care: soft-deleted records still consume storage and affect
    index performance. Implement a purge job for records older than N days.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,   # filtered queries: WHERE deleted_at IS NULL
        doc="UTC timestamp of soft deletion. NULL means the record is active.",
    )

    @property
    def is_deleted(self) -> bool:
        """Return True if this record has been soft-deleted."""
        return self.deleted_at is not None
```

### 1.2 Model Definition Standards

```python
# app/models/user.py

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPublicIdMixin

if TYPE_CHECKING:
    from app.models.order import Order


class User(Base, TimestampMixin, UUIDPublicIdMixin):
    """Application user with authentication and role information.

    Columns that hold encrypted or hashed data are named with a _hash or
    _encrypted suffix so the nature of the storage is always explicit.

    The email column has a case-insensitive unique constraint enforced
    at the DB level and normalised to lowercase in the service layer.
    """

    __tablename__ = "users"
    __table_args__ = (
        # Composite unique constraint — more efficient than separate indexes
        UniqueConstraint("email", "tenant_id", name="uq_users_email_tenant"),
        # Partial index — only index active users (common query pattern)
        Index(
            "ix_users_tenant_active",
            "tenant_id",
            "is_active",
            postgresql_where="is_active = true",   # DB-specific; document this
        ),
        {"comment": "Application users; includes auth credentials and role."},
    )

    # Primary key — always named id, always integer autoincrement
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Business columns
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,   # FK columns always indexed
    )

    # Relationships
    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",   # explicit cascade — never implicit
        lazy="select",                  # explicit loading strategy — never implicit
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r}, role={self.role!r})"
```

---

## SECTION 2 — NAMING CONVENTIONS

| Element | Convention | Example |
|---|---|---|
| Table name | `snake_case`, plural | `user_orders`, `product_categories` |
| Column name | `snake_case` | `created_at`, `is_active`, `tenant_id` |
| Primary key | Always `id` | `id INTEGER PRIMARY KEY` |
| Foreign key column | `{singular_table}_id` | `user_id`, `order_id` |
| Boolean columns | `is_` or `has_` prefix | `is_active`, `has_verified_email` |
| Timestamp columns | `_at` suffix | `created_at`, `deleted_at`, `published_at` |
| Hashed/encrypted | `_hash` or `_encrypted` suffix | `password_hash`, `ssn_encrypted` |
| Index | `ix_{table}_{columns}` | `ix_users_email`, `ix_orders_user_created` |
| Unique constraint | `uq_{table}_{columns}` | `uq_users_email_tenant` |
| Foreign key constraint | `fk_{table}_{col}_{ref_table}` | `fk_orders_user_id_users` |
| Check constraint | `ck_{table}_{rule}` | `ck_orders_amount_positive` |

---

## SECTION 3 — RELATIONSHIPS

### 3.1 Always specify cascade and lazy loading explicitly

```python
# ONE-TO-MANY
class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),   # explicit ondelete behaviour
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="orders",
        lazy="select",           # explicit: load when accessed
    )
    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",   # deleting order deletes its items
        lazy="select",
    )


# MANY-TO-MANY — use association table (not association object) unless extra data needed
from sqlalchemy import Table, Column

user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


# MANY-TO-MANY with extra data — association object pattern
class OrderItem(Base, TimestampMixin):
    """Association object: Order ↔ Product with quantity and unit price."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Storing price at purchase time is important — product prices change
```

---

## SECTION 4 — INDEXING STRATEGY

### 4.1 Always index these — no exceptions

```
- All foreign key columns (PostgreSQL does not auto-index FK columns)
- Columns used in WHERE clauses in high-frequency queries
- Columns used in JOIN conditions
- Columns used in ORDER BY on large tables
- Columns used in GROUP BY on aggregation queries
- Any column with a UNIQUE constraint (implicit index)
- Soft-delete column: WHERE deleted_at IS NULL (partial index)
```

### 4.2 Never index these

```
- Boolean columns (low cardinality — index hurts more than it helps)
- Columns with very high write volume and low read frequency
- Every column "just in case" — indexes cost on INSERT/UPDATE/DELETE
- Columns with fewer than 1000 rows in the table (sequential scan is faster)
```

### 4.3 Advanced indexing

```python
# Composite index — column order matters: most selective first
Index("ix_orders_user_created", "user_id", "created_at")
# Good for: WHERE user_id = ? ORDER BY created_at
# Bad for:  WHERE created_at > ? (does not use the index)

# Partial index — index only relevant rows (PostgreSQL / newer SQLite)
Index(
    "ix_orders_pending",
    "created_at",
    postgresql_where="status = 'pending'",
)

# GIN index for full-text search (PostgreSQL)
from sqlalchemy.dialects.postgresql import TSVECTOR
Index("ix_products_search", "search_vector", postgresql_using="gin")
```

---

## SECTION 5 — MIGRATION DISCIPLINE (ALEMBIC)

### 5.1 Migration commit message format

```
{verb}_{description}_{table}

Examples:
  add_column_phone_number_users
  create_table_order_items
  add_index_created_at_orders
  drop_column_legacy_token_sessions
  add_constraint_check_amount_positive_orders
  rename_column_name_to_full_name_users
```

### 5.2 Safe migration patterns

```python
# env.py — always use compare_type and compare_server_default
context.configure(
    connection=connection,
    target_metadata=Base.metadata,
    compare_type=True,              # detect column type changes
    compare_server_default=True,    # detect default value changes
    include_schemas=True,
)
```

```python
# Safe: adding a nullable column (no default required)
op.add_column("users", sa.Column("phone", sa.String(20), nullable=True))

# Safe: adding a NOT NULL column with a server default
op.add_column(
    "users",
    sa.Column(
        "is_verified",
        sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),  # backfills existing rows
    ),
)

# DANGEROUS: adding NOT NULL column without default to table with data
op.add_column("users", sa.Column("required_field", sa.String(), nullable=False))
# This will FAIL on a non-empty table. Always provide server_default for existing data.

# Safe column deprecation process (3-step):
# Step 1: Make nullable (backfill migration if needed)
op.alter_column("users", "old_column", nullable=True)
# Step 2: Stop writing to it (code change; let it sit one release cycle)
# Step 3: Drop the column (final migration)
op.drop_column("users", "old_column")
```

### 5.3 Migration rules

```
- Never edit a migration after it has been applied to any environment
- Never DELETE or TRUNCATE data in a migration — use a separate script
- Every migration must have a downgrade() implementation unless it is irreversible
- Review auto-generated migrations before applying — autogenerate misses: custom indexes,
  partial indexes, GIN/GiST indexes, triggers, stored procedures, RLS policies
- Test migrations on a production-like dataset before applying to prod
- Migrations are part of every PR that changes a model — no model changes without migrations
```

---

## SECTION 6 — QUERY PATTERNS

### 6.1 Avoid N+1 queries — always

```python
# N+1 PROBLEM — do not do this
orders = await session.execute(select(Order))
for order in orders.scalars():
    # This fires a separate query for EACH order — N+1 queries total
    user = await session.execute(select(User).where(User.id == order.user_id))

# CORRECT — eager loading with joinedload (one query with JOIN)
from sqlalchemy.orm import joinedload

orders = await session.execute(
    select(Order)
    .options(joinedload(Order.user))   # joined in single query
    .where(Order.status == "pending")
)

# CORRECT — selectin loading (two queries, better for many-to-many)
from sqlalchemy.orm import selectinload

users = await session.execute(
    select(User)
    .options(selectinload(User.orders))    # SELECT IN (user_ids); avoids cartesian product
    .where(User.is_active == True)
)
```

### 6.2 Pagination — always required for list queries

```python
from sqlalchemy import func, select

async def get_paginated_users(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    *,
    include_deleted: bool = False,
) -> tuple[list[User], int]:
    """Fetch a page of users with total count.

    Returns:
        Tuple of (users on this page, total user count).
    """
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")
    if not 1 <= page_size <= 100:
        raise ValueError(f"page_size must be 1-100, got {page_size}")

    base_query = select(User)
    if not include_deleted:
        base_query = base_query.where(User.deleted_at.is_(None))

    # Count query — uses COUNT(*) on same filters (no ORDER BY; faster)
    count_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    # Data query with pagination
    users_result = await session.execute(
        base_query
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    return users_result.scalars().all(), total
```

---

## SECTION 7 — DECIMAL HANDLING FOR MONETARY VALUES

```python
# NEVER use float for money — IEEE 754 float arithmetic loses precision
price: float = 0.1 + 0.2    # 0.30000000000000004 — WRONG

# ALWAYS use Decimal from Python's decimal module
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import Numeric

class Product(Base):
    # Numeric(precision, scale) — exact decimal storage in PostgreSQL
    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),   # up to 99,999,999.99
        nullable=False,
    )


def calculate_total(price: Decimal, quantity: int, tax_rate: Decimal) -> Decimal:
    """Calculate order total with tax, rounded to 2 decimal places."""
    subtotal = price * quantity
    tax = subtotal * tax_rate
    total = subtotal + tax
    # Always round with an explicit rounding mode for financial calculations
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```
