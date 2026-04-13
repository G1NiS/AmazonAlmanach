import asyncio
import json
from core.config import settings


class Notifier:
    async def notify(
        self,
        channels: list[str],
        asin: str,
        product_title: str,
        current_price: float,
        target_price: float,
        marketplace: str,
        email: str | None = None,
        telegram_chat_id: str | None = None,
        push_subscription: str | None = None,
    ) -> None:
        tasks = []
        for channel in channels:
            if channel == "email" and email:
                tasks.append(
                    self._send_email(
                        to=email,
                        subject=f"Price Drop: {product_title}",
                        body=self._email_body(asin, product_title, current_price, target_price, marketplace),
                    )
                )
            elif channel == "telegram" and telegram_chat_id:
                tasks.append(
                    self._send_telegram(
                        chat_id=telegram_chat_id,
                        message=self._telegram_message(product_title, asin, current_price, marketplace),
                    )
                )
            elif channel == "push" and push_subscription:
                tasks.append(self._send_push(push_subscription, product_title, current_price))
            elif channel == "screen":
                tasks.append(self._send_screen(asin, product_title, current_price))
            # Unknown channels are silently skipped

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _email_body(self, asin: str, title: str, price: float, target: float, marketplace: str) -> str:
        return (
            f"Good news! The price dropped below your target.\n\n"
            f"Product: {title}\n"
            f"ASIN: {asin}\n"
            f"Marketplace: {marketplace}\n"
            f"Current Price: ${price:.2f}\n"
            f"Your Target: ${target:.2f}\n\n"
            f"https://www.amazon.com/dp/{asin}"
        )

    def _telegram_message(self, title: str, asin: str, price: float, marketplace: str) -> str:
        return (
            f"Price Drop Alert!\n"
            f"{title}\n"
            f"${price:.2f} on {marketplace}\n"
            f"ASIN: {asin}"
        )

    async def _send_email(self, to: str, subject: str, body: str) -> None:
        try:
            import aiosmtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg["From"] = settings.smtp_user
            msg["To"] = to
            msg["Subject"] = subject
            msg.set_content(body)
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
        except Exception:
            pass  # Don't crash the alert flow if email fails

    async def _send_telegram(self, chat_id: str, message: str) -> None:
        try:
            from telegram import Bot
            bot = Bot(token=settings.telegram_bot_token)
            await bot.send_message(chat_id=chat_id, text=message)
        except Exception:
            pass

    async def _send_push(self, subscription_json: str, title: str, price: float) -> None:
        try:
            from pywebpush import webpush
            subscription = json.loads(subscription_json)
            await asyncio.to_thread(
                webpush,
                subscription_info=subscription,
                data=json.dumps({"title": "Price Drop!", "body": f"{title} — ${price:.2f}"}),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_claim_email}"},
            )
        except Exception:
            pass

    async def _send_screen(self, asin: str, title: str, price: float) -> None:
        try:
            from api.websocket import manager
            await manager.broadcast({
                "type": "price_alert",
                "asin": asin,
                "title": title,
                "price": price,
            })
        except Exception:
            pass
