---
name: new-endpoint
description: Scaffold a new API endpoint following standards
---

# Create New API Endpoint

## Steps

1. Read `rules/api-design.md` for URL and response conventions.
2. Read the framework skill (`skills/{framework}/SKILL.md`).
3. Create the endpoint file in `app/api/v1/`.
4. Create request/response schemas in `app/schemas/`.
5. Create service layer logic in `app/services/`.
6. Create repository layer if DB access needed in `app/repositories/`.
7. Register the router in `app/api/v1/router.py`.
8. Write tests in `tests/` mirroring source structure.
9. Run: `ruff check . && mypy app/ --strict && pytest`

## Conventions

- URL: `/api/v1/{resource}` — plural nouns, kebab-case
- Response: `{"data": {...}}` single, `{"data": [...], "pagination": {...}}` list
- Error: `{"error": {"code": "MACHINE_CODE", "message": "Human message"}}`
- Always paginate lists (default 20, max 100)
- All endpoints authenticated unless marked public
