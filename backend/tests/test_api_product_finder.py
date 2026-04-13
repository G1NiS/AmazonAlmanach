import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app


@pytest.mark.asyncio
async def test_find_products_returns_results():
    mock_results = [
        {"asin": "B001", "title": "Product A", "price": 25.0, "marketplace": "US",
         "brand": None, "image_url": None, "shipping_price": 0.0, "currency": "USD", "is_prime": True},
        {"asin": "B002", "title": "Product B", "price": 75.0, "marketplace": "US",
         "brand": None, "image_url": None, "shipping_price": 0.0, "currency": "USD", "is_prime": False},
    ]
    with patch("api.product_finder.amazon_client.search", new_callable=AsyncMock, return_value=mock_results):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/product-finder?q=laptop")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_find_products_filters_by_min_price():
    mock_results = [
        {"asin": "B001", "price": 25.0, "title": "Cheap", "marketplace": "US",
         "brand": None, "image_url": None, "shipping_price": None, "currency": "USD", "is_prime": False},
        {"asin": "B002", "price": 75.0, "title": "Expensive", "marketplace": "US",
         "brand": None, "image_url": None, "shipping_price": None, "currency": "USD", "is_prime": False},
    ]
    with patch("api.product_finder.amazon_client.search", new_callable=AsyncMock, return_value=mock_results):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/product-finder?q=laptop&min_price=50")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["asin"] == "B002"


@pytest.mark.asyncio
async def test_find_products_filters_by_max_price():
    mock_results = [
        {"asin": "B001", "price": 25.0, "title": "Cheap", "marketplace": "US",
         "brand": None, "image_url": None, "shipping_price": None, "currency": "USD", "is_prime": False},
        {"asin": "B002", "price": 75.0, "title": "Expensive", "marketplace": "US",
         "brand": None, "image_url": None, "shipping_price": None, "currency": "USD", "is_prime": False},
    ]
    with patch("api.product_finder.amazon_client.search", new_callable=AsyncMock, return_value=mock_results):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/product-finder?q=laptop&max_price=50")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["asin"] == "B001"


@pytest.mark.asyncio
async def test_find_products_requires_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/product-finder")
    assert resp.status_code == 422
