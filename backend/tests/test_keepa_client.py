import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.keepa_client import KeepaClient


@pytest.fixture
async def client():
    c = KeepaClient(api_key="test_key")
    yield c
    await c.close()


@pytest.mark.asyncio
async def test_keepa_time_converts_to_unix(client):
    result = client.keepa_time_to_unix(0)
    assert result == 1293840000


@pytest.mark.asyncio
async def test_keepa_time_nonzero(client):
    result = client.keepa_time_to_unix(1)
    assert result == 1293840000 + 60


@pytest.mark.asyncio
async def test_parse_csv_converts_cents_to_dollars(client):
    csv = [100, 2999, 200, 1999]
    result = client._parse_csv(csv)
    assert len(result) == 2
    assert result[0]["price"] == 29.99
    assert result[1]["price"] == 19.99


@pytest.mark.asyncio
async def test_parse_csv_skips_negative_values(client):
    csv = [100, -1, 200, 1999]
    result = client._parse_csv(csv)
    assert len(result) == 1
    assert result[0]["price"] == 19.99


@pytest.mark.asyncio
async def test_get_product_returns_structured_data(client):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock(return_value=None)
    mock_response.json.return_value = {
        "products": [{
            "asin": "B08N5WRWNW",
            "title": "Test Headphones",
            "brand": "TestBrand",
            "categoryTree": [{"name": "Electronics"}],
            "imagesCSV": "img1.jpg,img2.jpg",
            "csv": [
                [100, 2999, 200, 1999],  # index 0: amazon price history
                [], [], [], [], [], [], [], [], [], [], [],
                [100, 500, 200, 0],      # index 11: shipping history
            ],
            "salesRanks": {},
        }]
    }

    with patch.object(client._http, "get", new_callable=AsyncMock, return_value=mock_response):
        result = await client.get_product("B08N5WRWNW", marketplace="US")

    assert result["asin"] == "B08N5WRWNW"
    assert result["title"] == "Test Headphones"
    assert result["brand"] == "TestBrand"
    assert result["category"] == "Electronics"
    assert len(result["price_history"]) == 2
    assert result["price_history"][0]["price"] == 29.99
    assert "timestamp" in result["price_history"][0]


@pytest.mark.asyncio
async def test_marketplace_ids_coverage(client):
    assert "US" in client.MARKETPLACE_IDS
    assert "DE" in client.MARKETPLACE_IDS
    assert "GB" in client.MARKETPLACE_IDS
    assert "JP" in client.MARKETPLACE_IDS
    assert client.MARKETPLACE_IDS["US"] == 1
