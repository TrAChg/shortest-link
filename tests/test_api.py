from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    """Verifies that the /health endpoint reports healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


async def test_shorten_url_auto_code(client: AsyncClient) -> None:
    """Verifies standard URL shortening with auto-generated short code."""
    payload = {"url": "https://fastapi.tiangolo.com"}
    response = await client.post("/api/v1/shorten", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert len(data["short_code"]) > 0
    assert "short_url" in data
    assert data["original_url"].startswith("https://fastapi.tiangolo.com")


async def test_shorten_url_custom_alias_and_duplicate(client: AsyncClient) -> None:
    """Verifies custom alias assignment and 409 Conflict when alias is taken."""
    payload = {"url": "https://python.org", "custom_alias": "python-docs"}
    res1 = await client.post("/api/v1/shorten", json=payload)
    assert res1.status_code == 201
    assert res1.json()["short_code"] == "python-docs"
    res2 = await client.post("/api/v1/shorten", json=payload)
    assert res2.status_code == 409


async def test_redirect_not_found(client: AsyncClient) -> None:
    """Verifies 404 Not Found for unregistered short code."""
    response = await client.get("/non-existent-code-xyz")
    assert response.status_code == 404


async def test_redirect_to_target(client: AsyncClient) -> None:
    """Verifies HTTP 307 temporary redirect to destination URL."""
    await client.post(
        "/api/v1/shorten",
        json={"url": "https://python.org", "custom_alias": "python-redirect"},
    )
    response = await client.get("/python-redirect", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://python.org")


async def test_get_url_analytics(client: AsyncClient) -> None:
    """Verifies analytics retrieval for total clicks and history."""
    await client.post(
        "/api/v1/shorten",
        json={"url": "https://python.org", "custom_alias": "python-analytics"},
    )
    await client.get("/python-analytics", follow_redirects=False)

    response = await client.get("/api/v1/analytics/python-analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "python-analytics"
    assert data["total_clicks"] >= 1
    assert "recent_clicks" in data
