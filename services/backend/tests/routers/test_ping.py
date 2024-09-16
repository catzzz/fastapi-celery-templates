"""Test the ping router."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_from_fixture(async_client: AsyncClient):
    """Test the test client fixture."""
    response = await async_client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}
