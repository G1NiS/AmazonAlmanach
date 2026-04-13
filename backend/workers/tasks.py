import asyncio
import json

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select

from core.config import settings
from core.database import AsyncSessionLocal
from models.alert import Alert
from models.user import User
from services.amazon_client import AmazonClient
from services.notifier import Notifier

celery_app = Celery("amazon_tracker", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.beat_schedule = {
    "check-price-alerts-hourly": {
        "task": "workers.tasks.run_check_alerts",
        "schedule": crontab(minute=0),  # every hour on the hour
    },
}
celery_app.conf.timezone = "UTC"

amazon_client = AmazonClient()
notifier = Notifier()


async def get_active_alerts() -> list[Alert]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Alert).where(Alert.active.is_(True)))
        return result.scalars().all()


async def get_user(user_id: int) -> User | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


async def check_price_alerts() -> None:
    alerts = await get_active_alerts()
    for alert in alerts:
        marketplaces = json.loads(alert.marketplaces)
        channels = json.loads(alert.channels)
        user = await get_user(alert.user_id)

        for marketplace in marketplaces:
            item = await amazon_client.get_item(alert.asin, marketplace=marketplace)
            if not item or item.get("price") is None:
                continue
            if item["price"] <= alert.target_price:
                await notifier.notify(
                    channels=channels,
                    asin=alert.asin,
                    product_title=item.get("title", alert.asin),
                    current_price=item["price"],
                    target_price=alert.target_price,
                    marketplace=marketplace,
                    email=user.email if user else None,
                    telegram_chat_id=user.telegram_chat_id if user else None,
                    push_subscription=user.push_subscription if user else None,
                )


@celery_app.task(name="workers.tasks.run_check_alerts")
def run_check_alerts() -> None:
    asyncio.run(check_price_alerts())
