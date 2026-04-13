from datetime import datetime
from sqlalchemy import String, Float, DateTime, Boolean, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    asin: Mapped[str] = mapped_column(String(10), index=True)
    target_price: Mapped[float] = mapped_column(Float)
    marketplaces: Mapped[str] = mapped_column(Text)   # JSON: ["US","DE"]
    channels: Mapped[str] = mapped_column(Text)        # JSON: ["email","telegram"]
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
