# ADR-NNN: [Title — Short Decision Statement]

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Deciders:** [Names of people involved in the decision]
**Ticket:** [JIRA/Linear ticket reference]

---

## Context

What is the issue that we're seeing that is motivating this decision or change? What forces are at play (technical, business, team, timeline)?

## Decision

What is the change that we're proposing and/or doing? State it as an imperative: "We will..."

## Consequences

What becomes easier or more difficult to do because of this change?

### Positive
- ...

### Negative
- ...

### Risks
- ...

---

## Alternatives Considered

| Option | Pros | Cons | Why rejected |
|--------|------|------|--------------|
| Option A | ... | ... | ... |
| Option B | ... | ... | ... |

---

## References

- Links to relevant docs, RFCs, blog posts, benchmarks

---

---

# EXAMPLE: ADR-001 — Use PostgreSQL as Primary Database

**Status:** Accepted
**Date:** 2026-01-15
**Deciders:** Nishant, Arpit, Deepika
**Ticket:** PLAT-42

---

## Context

We need a primary database for the new order management service. The team has experience with both PostgreSQL and MySQL. We need JSONB support for flexible order metadata, strong transactional guarantees, and good async driver support for our FastAPI stack.

## Decision

We will use PostgreSQL 16 as the primary relational database for all new services, accessed via SQLAlchemy 2.x async with asyncpg driver.

## Consequences

### Positive
- Native JSONB with indexing for flexible schemas
- Excellent asyncpg driver performance
- Strong ecosystem (PostGIS, pg_trgm, full-text search)
- Team already has operational experience

### Negative
- Slightly more complex replication setup than MySQL
- Requires tuning for write-heavy workloads (autovacuum)

### Risks
- Vendor lock-in to PostgreSQL-specific features (JSONB, array types)

---

## Alternatives Considered

| Option | Pros | Cons | Why rejected |
|--------|------|------|--------------|
| MySQL 8 | Simpler replication, wide hosting support | Weaker JSONB, no asyncpg equivalent | Async driver ecosystem weaker |
| MongoDB | Native document model | No ACID across documents, eventual consistency | Need strong transactions for orders |

---

## References

- [asyncpg benchmarks](https://github.com/MagicStack/asyncpg)
- [SQLAlchemy 2.0 async guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

---

# HOW TO USE THIS TEMPLATE

1. Copy this file: `cp ADR-template.md ADR-NNN-short-title.md`
2. Number sequentially: ADR-001, ADR-002, etc.
3. Fill in all sections — "Alternatives Considered" is mandatory.
4. Submit as a PR for team review.
5. Once accepted, it's immutable — create a new ADR to supersede.

## When to Write an ADR

- Choosing a database, message broker, or major library
- Changing authentication/authorization approach
- Adopting a new architectural pattern
- Making a decision that's expensive to reverse
- Any decision where future-you will ask "why did we do this?"
