import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app


@pytest.mark.asyncio
async def test_get_best_sellers_returns_data():
    mock_asins = ["B001", "B002", "B003"]
    with patch("api.best_sellers.keepa_client.get_best_sellers", new_callable=AsyncMock, return_value=mock_asins):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/best-sellers?category=Electronics&marketplace=US")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "Electronics"
    assert data["marketplace"] == "US"
    assert "B001" in data["asins"]


@pytest.mark.asyncio
async def test_get_best_sellers_unknown_category_uses_default():
    with patch("api.best_sellers.keepa_client.get_best_sellers", new_callable=AsyncMock, return_value=[]) as mock_fn:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/api/best-sellers?category=UnknownCategory")
    # Should still call get_best_sellers (with Electronics fallback)
    mock_fn.assert_called_once()


@pytest.mark.asyncio
async def test_list_categories_returns_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/best-sellers/categories")
    assert resp.status_code == 200
    categories = resp.json()
    assert isinstance(categories, list)
    assert "Electronics" in categories
