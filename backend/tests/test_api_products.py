import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app


@pytest.mark.asyncio
async def test_search_products_returns_results():
    mock_results = [
        {"asin": "B08N5WRWNW", "title": "Test Headphones", "price": 29.99,
         "currency": "USD", "marketplace": "US", "is_prime": True,
         "brand": None, "image_url": None, "shipping_price": 0.0}
    ]
    with patch("api.products.amazon_client.search", new_callable=AsyncMock, return_value=mock_results):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/products/search?q=headphones&marketplace=US")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["asin"] == "B08N5WRWNW"


@pytest.mark.asyncio
async def test_search_products_requires_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/products/search")
    assert resp.status_code == 422  # Missing required query param


@pytest.mark.asyncio
async def test_get_price_history_returns_data():
    mock_data = {
        "asin": "B08N5WRWNW",
        "title": "Test Product",
        "price_history": [{"timestamp": 1640000000, "price": 29.99}],
        "shipping_history": [],
    }
    with patch("api.products.keepa_client.get_product", new_callable=AsyncMock, return_value=mock_data):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/products/B08N5WRWNW/price-history?marketplace=US")
    assert resp.status_code == 200
    assert resp.json()["asin"] == "B08N5WRWNW"
    assert "price_history" in resp.json()


@pytest.mark.asyncio
async def test_get_price_history_404_on_empty():
    with patch("api.products.keepa_client.get_product", new_callable=AsyncMock, return_value=None):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/products/INVALID/price-history")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_compare_marketplaces_returns_sorted_list():
    # Simulate 2 marketplaces responding, sorted by total price
    de_item = {"asin": "B08N5WRWNW", "marketplace": "DE", "price": 25.0,
                "shipping_price": 3.0, "currency": "EUR", "is_prime": False,
                "title": "Test", "brand": None, "image_url": None}
    us_item = {"asin": "B08N5WRWNW", "marketplace": "US", "price": 30.0,
                "shipping_price": 0.0, "currency": "USD", "is_prime": True,
                "title": "Test", "brand": None, "image_url": None}

    async def mock_get_item(asin, marketplace):
        if marketplace == "DE":
            return de_item
        if marketplace == "US":
            return us_item
        return None

    with patch("api.products.amazon_client.get_item", side_effect=mock_get_item):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/products/B08N5WRWNW/compare")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 2
    # DE total = 28.0, US total = 30.0 — DE should be first
    assert results[0]["marketplace"] == "DE"
