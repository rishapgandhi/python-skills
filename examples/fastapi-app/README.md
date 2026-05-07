# Example FastAPI App

Minimal reference implementation of `python-agent-standards`.

## Demonstrates

- App factory pattern (`create_app()`)
- pydantic-settings configuration
- Domain exception hierarchy with HTTP mapping
- Structured logging (structlog)
- Service layer separation
- Health check endpoint
- Async test client (httpx + pytest-asyncio)

## Run

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```
