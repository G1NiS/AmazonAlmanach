import json
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from main import app


@pytest.mark.asyncio
async def test_create_alert_returns_201():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("api.alerts.create_alert_in_db", new_callable=AsyncMock, return_value={"id": 1, "asin": "B08N5WRWNW", "target_price": 20.0}):
            resp = await client.post("/api/alerts", json={
                "asin": "B08N5WRWNW",
                "target_price": 20.0,
                "marketplaces": ["US", "DE"],
                "channels": ["email", "screen"],
                "email": "test@example.com",
            })
    assert resp.status_code == 201
    assert resp.json()["asin"] == "B08N5WRWNW"


@pytest.mark.asyncio
async def test_create_alert_validates_target_price():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/alerts", json={
            "asin": "B08N5WRWNW",
            "target_price": -1.0,  # negative price invalid
            "marketplaces": ["US"],
            "channels": ["email"],
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_alerts_returns_list():
    mock_alerts = [{"id": 1, "asin": "B08N5WRWNW", "target_price": 20.0, "active": True}]
    with patch("api.alerts.list_alerts_from_db", new_callable=AsyncMock, return_value=mock_alerts):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/alerts?user_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert resp.json()[0]["asin"] == "B08N5WRWNW"


@pytest.mark.asyncio
async def test_delete_alert_returns_200():
    with patch("api.alerts.deactivate_alert_in_db", new_callable=AsyncMock, return_value=True):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/api/alerts/1")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


@pytest.mark.asyncio
async def test_delete_alert_404_on_missing():
    with patch("api.alerts.deactivate_alert_in_db", new_callable=AsyncMock, return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/api/alerts/999")
    assert resp.status_code == 404
