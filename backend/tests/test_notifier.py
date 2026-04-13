import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.notifier import Notifier


@pytest.fixture
def notifier():
    return Notifier()


@pytest.mark.asyncio
async def test_notify_calls_email_when_channel_is_email(notifier):
    with patch.object(notifier, "_send_email", new_callable=AsyncMock) as mock_email:
        await notifier.notify(
            channels=["email"],
            asin="B08N5WRWNW",
            product_title="Test Product",
            current_price=19.99,
            target_price=25.00,
            marketplace="US",
            email="test@example.com",
        )
    mock_email.assert_called_once()
    call_kwargs = mock_email.call_args[1]
    assert call_kwargs["to"] == "test@example.com"
    assert "B08N5WRWNW" in call_kwargs["body"]


@pytest.mark.asyncio
async def test_notify_calls_telegram_when_channel_is_telegram(notifier):
    with patch.object(notifier, "_send_telegram", new_callable=AsyncMock) as mock_tg:
        await notifier.notify(
            channels=["telegram"],
            asin="B08N5WRWNW",
            product_title="Test Product",
            current_price=19.99,
            target_price=25.00,
            marketplace="US",
            telegram_chat_id="123456",
        )
    mock_tg.assert_called_once()


@pytest.mark.asyncio
async def test_notify_skips_email_when_no_email_provided(notifier):
    with patch.object(notifier, "_send_email", new_callable=AsyncMock) as mock_email:
        await notifier.notify(
            channels=["email"],
            asin="B08N5WRWNW",
            product_title="Test Product",
            current_price=19.99,
            target_price=25.00,
            marketplace="US",
            # email=None intentionally omitted
        )
    mock_email.assert_not_called()


@pytest.mark.asyncio
async def test_notify_skips_unknown_channels(notifier):
    # Should not raise, just skip unknown channels
    await notifier.notify(
        channels=["unknown_channel", "another_unknown"],
        asin="B08N5WRWNW",
        product_title="Test Product",
        current_price=19.99,
        target_price=25.00,
        marketplace="US",
    )


@pytest.mark.asyncio
async def test_notify_handles_multiple_channels(notifier):
    with patch.object(notifier, "_send_email", new_callable=AsyncMock) as mock_email, \
         patch.object(notifier, "_send_telegram", new_callable=AsyncMock) as mock_tg:
        await notifier.notify(
            channels=["email", "telegram"],
            asin="B08N5WRWNW",
            product_title="Test Product",
            current_price=19.99,
            target_price=25.00,
            marketplace="US",
            email="test@example.com",
            telegram_chat_id="123456",
        )
    mock_email.assert_called_once()
    mock_tg.assert_called_once()


@pytest.mark.asyncio
async def test_email_body_contains_key_info(notifier):
    body = notifier._email_body(
        asin="B08N5WRWNW",
        title="Test Product",
        price=19.99,
        target=25.00,
        marketplace="US",
    )
    assert "B08N5WRWNW" in body
    assert "19.99" in body
    assert "25.00" in body
    assert "US" in body
