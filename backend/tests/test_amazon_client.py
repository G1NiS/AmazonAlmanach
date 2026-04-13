import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from services.amazon_client import AmazonClient, MARKETPLACE_ENDPOINTS


def test_marketplace_endpoints_coverage():
    assert "US" in MARKETPLACE_ENDPOINTS
    assert "DE" in MARKETPLACE_ENDPOINTS
    assert "GB" in MARKETPLACE_ENDPOINTS
    assert "JP" in MARKETPLACE_ENDPOINTS
    for mp, (host, region) in MARKETPLACE_ENDPOINTS.items():
        assert "amazon" in host
        assert region in ("us-east-1", "eu-west-1", "us-west-2")


def test_parse_item_returns_structured_dict():
    client = AmazonClient()
    mock_item = {
        "ASIN": "B08N5WRWNW",
        "ItemInfo": {
            "Title": {"DisplayValue": "Test Headphones"},
            "ByLineInfo": {"Brand": {"DisplayValue": "TestBrand"}},
        },
        "Images": {
            "Primary": {"Large": {"URL": "https://example.com/img.jpg"}}
        },
        "Offers": {
            "Listings": [{
                "Price": {"Amount": 29.99, "Currency": "USD"},
                "DeliveryInfo": {"IsPrimeEligible": True},
            }]
        },
    }
    result = client._parse_item(mock_item, "US")
    assert result["asin"] == "B08N5WRWNW"
    assert result["title"] == "Test Headphones"
    assert result["brand"] == "TestBrand"
    assert result["price"] == 29.99
    assert result["currency"] == "USD"
    assert result["is_prime"] is True
    assert result["marketplace"] == "US"


def test_parse_item_handles_missing_offers():
    client = AmazonClient()
    mock_item = {
        "ASIN": "B08N5WRWNW",
        "ItemInfo": {"Title": {"DisplayValue": "Test"}},
        "Offers": {"Listings": []},
    }
    result = client._parse_item(mock_item, "US")
    assert result["price"] is None
    assert result["is_prime"] is False


def test_parse_item_handles_missing_images():
    client = AmazonClient()
    mock_item = {
        "ASIN": "B00001",
        "ItemInfo": {"Title": {"DisplayValue": "Test"}},
        "Offers": {"Listings": []},
    }
    result = client._parse_item(mock_item, "DE")
    assert result["image_url"] is None


@pytest.mark.asyncio
async def test_search_returns_list():
    client = AmazonClient()
    mock_response_data = {
        "SearchResult": {
            "Items": [
                {
                    "ASIN": "B08N5WRWNW",
                    "ItemInfo": {"Title": {"DisplayValue": "Headphones"}},
                    "Offers": {"Listings": [{"Price": {"Amount": 49.99, "Currency": "USD"}, "DeliveryInfo": {"IsPrimeEligible": False}}]},
                }
            ]
        }
    }
    with patch.object(client, "_post", new_callable=AsyncMock, return_value=mock_response_data):
        results = await client.search("headphones", marketplace="US")
    assert len(results) == 1
    assert results[0]["asin"] == "B08N5WRWNW"
    assert results[0]["price"] == 49.99


@pytest.mark.asyncio
async def test_search_returns_empty_on_no_results():
    client = AmazonClient()
    with patch.object(client, "_post", new_callable=AsyncMock, return_value={}):
        results = await client.search("xyznotexist", marketplace="US")
    assert results == []


@pytest.mark.asyncio
async def test_get_item_returns_none_on_missing():
    client = AmazonClient()
    with patch.object(client, "_post", new_callable=AsyncMock, return_value={"ItemsResult": {"Items": []}}):
        result = await client.get_item("INVALID", marketplace="US")
    assert result is None


@pytest.mark.asyncio
async def test_search_returns_empty_on_http_error():
    async with AmazonClient() as client:
        with patch.object(client, "_post", new_callable=AsyncMock, side_effect=httpx.HTTPError("error")):
            results = await client.search("headphones", marketplace="US")
    assert results == []


@pytest.mark.asyncio
async def test_get_item_returns_none_on_http_error():
    async with AmazonClient() as client:
        with patch.object(client, "_post", new_callable=AsyncMock, side_effect=httpx.HTTPError("error")):
            result = await client.get_item("B08N5WRWNW", marketplace="US")
    assert result is None


@pytest.mark.asyncio
async def test_async_context_manager():
    async with AmazonClient() as client:
        assert client._http is not None
    # After exit, the client should be closed (aclose called)
    assert client._http.is_closed
