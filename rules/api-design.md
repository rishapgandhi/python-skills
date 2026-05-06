# REST API Design Standards

> Consistent, predictable, versioned REST APIs.

---

## 1. URL Structure

```
/api/v1/{resource}              ← Collection
/api/v1/{resource}/{id}         ← Single item
/api/v1/{resource}/{id}/{sub}   ← Sub-resource
```

**Rules:**
- Use **nouns**, never verbs: `/api/v1/users` not `/api/v1/getUsers`
- Always **plural**: `/users`, `/orders`, `/products`
- **kebab-case** for multi-word resources: `/user-profiles`
- Always version with `/v1/` — never unversioned URLs in production

---

## 2. HTTP Methods

| Method | Use | Idempotent |
|---|---|---|
| `GET` | Read (list or single) | ✅ |
| `POST` | Create | ❌ |
| `PUT` | Full replacement | ✅ |
| `PATCH` | Partial update | ✅ |
| `DELETE` | Delete | ✅ |

Never use `GET` to modify data. Never use `POST` for search (use query params instead).

---

## 3. HTTP Status Codes

| Code | When |
|---|---|
| `200 OK` | Successful GET, PUT, PATCH |
| `201 Created` | Successful POST — include `Location` header |
| `204 No Content` | Successful DELETE or action with no response body |
| `400 Bad Request` | Malformed request syntax |
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | Authenticated but not authorised |
| `404 Not Found` | Resource doesn't exist |
| `409 Conflict` | Duplicate resource or state conflict |
| `422 Unprocessable Entity` | Schema/business validation failure |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server error |

---

## 4. Request / Response Shape

### Request (POST / PUT / PATCH)
```json
{
  "email": "user@example.com",
  "name": "Jane Doe",
  "role": "editor"
}
```

### Success Response (single item)
```json
{
  "data": {
    "id": 1,
    "public_id": "a1b2c3d4-...",
    "email": "user@example.com",
    "name": "Jane Doe",
    "created_at": "2026-01-15T10:30:00Z"
  }
}
```

### Success Response (list)
```json
{
  "data": [ ... ],
  "pagination": {
    "total": 250,
    "page": 2,
    "page_size": 20,
    "pages": 13
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      { "field": "email", "message": "Invalid email format." }
    ]
  }
}
```

---

## 5. Pagination

Always paginate list endpoints. Never return unbounded lists.

```
GET /api/v1/users?page=2&page_size=20
```

| Param | Default | Max |
|---|---|---|
| `page` | 1 | — |
| `page_size` | 20 | 100 |

---

## 6. Filtering, Sorting, Search

```
GET /api/v1/users?is_active=true&role=admin          ← filter
GET /api/v1/users?sort=created_at&order=desc         ← sort
GET /api/v1/users?search=jane                        ← full-text search
```

Never expose raw DB column names in filters — use a whitelist of allowed filter fields.

---

## 7. Versioning

- All breaking changes require a new version: `/api/v2/`.
- Old versions deprecated with `Sunset` and `Deprecation` headers before removal.
- Minimum 3 months deprecation window.

```
Deprecation: Sat, 31 Dec 2026 00:00:00 GMT
Sunset: Sat, 31 Mar 2027 00:00:00 GMT
Link: </api/v2/users>; rel="successor-version"
```

---

## 8. API Documentation

Every endpoint must have:
- Summary (one line)
- Description (when not obvious)
- All parameters documented
- All response schemas documented
- Example request/response

Use **drf-spectacular** (DRF) or **FastAPI's built-in OpenAPI** generation.

---

## 9. Datetime Format

Always ISO 8601 UTC: `"2026-01-15T10:30:00Z"`

Never return Unix timestamps to API consumers.

---

## 10. Sensitive Fields — Never Return

`password_hash`, `secret_key`, `internal_id`, `ssn`, `raw_token`, `salt`
