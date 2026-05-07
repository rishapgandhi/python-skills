"""Tests for users API — demonstrates testing standards."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Async test client fixture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check_returns_healthy(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_user_returns_201(client: AsyncClient) -> None:
    response = await client.post("/api/v1/users/", json={"email": "test@example.com", "name": "Test User"})
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_nonexistent_user_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
