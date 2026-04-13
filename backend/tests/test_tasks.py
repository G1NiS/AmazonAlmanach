import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_check_price_alerts_triggers_notification_when_price_below_target():
    from workers.tasks import check_price_alerts

    mock_alert = MagicMock()
    mock_alert.id = 1
    mock_alert.asin = "B08N5WRWNW"
    mock_alert.target_price = 30.0
    mock_alert.marketplaces = json.dumps(["US"])
    mock_alert.channels = json.dumps(["email"])
    mock_alert.user_id = 1

    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    mock_user.telegram_chat_id = None
    mock_user.push_subscription = None

    mock_item = {
        "asin": "B08N5WRWNW",
        "title": "Test Product",
        "price": 25.0,
        "marketplace": "US",
    }

    with patch("workers.tasks.get_active_alerts", new_callable=AsyncMock, return_value=[mock_alert]), \
         patch("workers.tasks.get_user", new_callable=AsyncMock, return_value=mock_user), \
         patch("workers.tasks.amazon_client.get_item", new_callable=AsyncMock, return_value=mock_item), \
         patch("workers.tasks.notifier.notify", new_callable=AsyncMock) as mock_notify:
        await check_price_alerts()

    mock_notify.assert_called_once()
    call_kwargs = mock_notify.call_args[1]
    assert call_kwargs["asin"] == "B08N5WRWNW"
    assert call_kwargs["current_price"] == 25.0
    assert call_kwargs["target_price"] == 30.0


@pytest.mark.asyncio
async def test_check_price_alerts_no_notification_when_price_above_target():
    from workers.tasks import check_price_alerts

    mock_alert = MagicMock()
    mock_alert.id = 1
    mock_alert.asin = "B08N5WRWNW"
    mock_alert.target_price = 20.0
    mock_alert.marketplaces = json.dumps(["US"])
    mock_alert.channels = json.dumps(["email"])
    mock_alert.user_id = 1

    mock_user = MagicMock()
    mock_user.email = "test@example.com"

    mock_item = {"asin": "B08N5WRWNW", "title": "Test", "price": 25.0, "marketplace": "US"}

    with patch("workers.tasks.get_active_alerts", new_callable=AsyncMock, return_value=[mock_alert]), \
         patch("workers.tasks.get_user", new_callable=AsyncMock, return_value=mock_user), \
         patch("workers.tasks.amazon_client.get_item", new_callable=AsyncMock, return_value=mock_item), \
         patch("workers.tasks.notifier.notify", new_callable=AsyncMock) as mock_notify:
        await check_price_alerts()

    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_check_price_alerts_skips_when_item_unavailable():
    from workers.tasks import check_price_alerts

    mock_alert = MagicMock()
    mock_alert.asin = "B08N5WRWNW"
    mock_alert.target_price = 30.0
    mock_alert.marketplaces = json.dumps(["US"])
    mock_alert.channels = json.dumps(["email"])
    mock_alert.user_id = 1

    with patch("workers.tasks.get_active_alerts", new_callable=AsyncMock, return_value=[mock_alert]), \
         patch("workers.tasks.get_user", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("workers.tasks.amazon_client.get_item", new_callable=AsyncMock, return_value=None), \
         patch("workers.tasks.notifier.notify", new_callable=AsyncMock) as mock_notify:
        await check_price_alerts()

    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_check_price_alerts_skips_when_price_is_none():
    from workers.tasks import check_price_alerts

    mock_alert = MagicMock()
    mock_alert.asin = "B08N5WRWNW"
    mock_alert.target_price = 30.0
    mock_alert.marketplaces = json.dumps(["US"])
    mock_alert.channels = json.dumps(["email"])
    mock_alert.user_id = 1

    mock_item = {"asin": "B08N5WRWNW", "title": "Test", "price": None, "marketplace": "US"}

    with patch("workers.tasks.get_active_alerts", new_callable=AsyncMock, return_value=[mock_alert]), \
         patch("workers.tasks.get_user", new_callable=AsyncMock, return_value=MagicMock()), \
         patch("workers.tasks.amazon_client.get_item", new_callable=AsyncMock, return_value=mock_item), \
         patch("workers.tasks.notifier.notify", new_callable=AsyncMock) as mock_notify:
        await check_price_alerts()

    mock_notify.assert_not_called()
