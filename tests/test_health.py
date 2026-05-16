from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timelineCacheHits" in data
    assert "timelineCacheMisses" in data
    assert isinstance(data["timelineCacheHits"], int)
    assert isinstance(data["timelineCacheMisses"], int)
