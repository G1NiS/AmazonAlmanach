from datetime import datetime
from sqlalchemy import String, Float, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_asin_marketplace_ts", "asin", "marketplace", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    asin: Mapped[str] = mapped_column(String(10))
    marketplace: Mapped[str] = mapped_column(String(10))
    price: Mapped[float | None] = mapped_column(Float)
    shipping_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
