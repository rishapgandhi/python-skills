# Data Migrations — Enterprise Standard

**Applies to:** All Python projects with relational databases.
**Tools:** Alembic (SQLAlchemy), Django migrations.
**Principle:** Every migration must be deployable without downtime.

---

## SECTION 1 — ZERO-DOWNTIME MIGRATION RULES

| Rule | Rationale |
|------|-----------|
| Never rename a column in one step | Old code still reads the old name during rollout |
| Never drop a column in the same release that stops using it | Rolling deploys mean old pods still reference it |
| Never add a NOT NULL column without a default | Existing rows will fail INSERT from old code |
| Always make migrations reversible | `downgrade()` must work for rollback |
| Separate schema migrations from data migrations | Schema = fast DDL; data = slow backfill |
| Test migrations against a production-sized dataset | A 2-second migration on dev can be 2-hour lock on prod |

---

## SECTION 2 — EXPAND-CONTRACT PATTERN

The safe way to make breaking schema changes:

### Phase 1: Expand (deploy with old + new)

```python
# alembic/versions/001_add_new_column.py
def upgrade():
    op.add_column("users", sa.Column("full_name", sa.String(255), nullable=True))

def downgrade():
    op.drop_column("users", "full_name")
```

- Add new column as **nullable** (no lock on existing rows).
- Deploy code that writes to BOTH old and new columns.
- Old code still works — it ignores the new column.

### Phase 2: Migrate (backfill data)

```python
# alembic/versions/002_backfill_full_name.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Batch update to avoid long-running transactions
    connection = op.get_bind()
    while True:
        result = connection.execute(
            sa.text("""
                UPDATE users
                SET full_name = first_name || ' ' || last_name
                WHERE full_name IS NULL
                LIMIT 1000
            """)
        )
        if result.rowcount == 0:
            break

def downgrade():
    pass  # Data backfill — no meaningful downgrade
```

### Phase 3: Contract (remove old)

```python
# alembic/versions/003_drop_old_columns.py
def upgrade():
    op.drop_column("users", "first_name")
    op.drop_column("users", "last_name")

def downgrade():
    op.add_column("users", sa.Column("first_name", sa.String(100)))
    op.add_column("users", sa.Column("last_name", sa.String(100)))
```

- Deploy ONLY after all code references the new column.
- Minimum 1 release cycle between expand and contract.

---

## SECTION 3 — BACKFILL STRATEGIES

### Batch Processing (preferred)

```python
BATCH_SIZE = 1000

def backfill_in_batches(session):
    """Process records in batches to avoid locking and memory issues."""
    last_id = 0
    while True:
        rows = session.execute(
            select(User).where(User.id > last_id, User.full_name.is_(None))
            .order_by(User.id).limit(BATCH_SIZE)
        ).scalars().all()

        if not rows:
            break

        for row in rows:
            row.full_name = f"{row.first_name} {row.last_name}"

        session.commit()
        last_id = rows[-1].id
        logger.info("backfill_progress", last_id=last_id)
```

### Rules for Backfills

- Always process in batches (1000–5000 rows).
- Commit per batch — don't hold a transaction open for millions of rows.
- Log progress so you can resume if interrupted.
- Run backfills as background tasks (Celery), not inside migration files for large tables.
- Add a progress column or flag to track completion.

---

## SECTION 4 — DANGEROUS OPERATIONS REFERENCE

| Operation | Risk | Safe Alternative |
|-----------|------|-----------------|
| `DROP COLUMN` | Breaks old code during rolling deploy | Expand-contract (3 releases) |
| `RENAME COLUMN` | Same as drop | Add new → backfill → drop old |
| `ALTER COLUMN type` | Table rewrite, locks | Add new column → backfill → swap |
| `ADD NOT NULL` | Fails for existing rows | Add nullable → backfill → add constraint |
| `ADD UNIQUE constraint` | Fails if duplicates exist | Clean data first, then add |
| `CREATE INDEX` | Locks table on large datasets | `CREATE INDEX CONCURRENTLY` (Postgres) |
| `DROP TABLE` | Data loss | Rename to `_deprecated_X`, drop after 30 days |

---

## SECTION 5 — ALEMBIC BEST PRACTICES

```python
# alembic/env.py — always include
def run_migrations_online():
    # Use a transaction per migration for safety
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,  # Each migration in its own transaction
        )
        with context.begin_transaction():
            context.run_migrations()
```

### Migration File Rules

- One logical change per migration file.
- Descriptive revision message: `add_full_name_to_users`, not `update_schema`.
- Always implement `downgrade()`.
- Never import application models in migrations — use raw SQL or `op.*` only.
- Pin the migration to a specific schema state (don't reference `models.py`).

---

## SECTION 6 — DJANGO MIGRATIONS SPECIFICS

```python
# Safe: RunSQL with reverse
from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            sql="CREATE INDEX CONCURRENTLY idx_users_email ON users (email);",
            reverse_sql="DROP INDEX idx_users_email;",
            state_operations=[],  # Don't affect Django's state
        ),
    ]
```

### Django `SeparateDatabaseAndState`

```python
# When you need Django to think the schema changed without actually running DDL
migrations.SeparateDatabaseAndState(
    database_operations=[
        migrations.RunSQL("ALTER TABLE ..."),
    ],
    state_operations=[
        migrations.AlterField(...),
    ],
)
```
