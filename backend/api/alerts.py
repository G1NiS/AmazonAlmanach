import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.alert import Alert
from models.user import User

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    asin: str
    target_price: float = Field(..., gt=0)
    marketplaces: list[str] = Field(..., min_length=1)
    channels: list[str] = Field(..., min_length=1)
    email: str | None = None
    telegram_chat_id: str | None = None


async def create_alert_in_db(payload: AlertCreate, db: AsyncSession) -> dict:
    user = User(email=payload.email, telegram_chat_id=payload.telegram_chat_id)
    db.add(user)
    await db.flush()

    alert = Alert(
        user_id=user.id,
        asin=payload.asin,
        target_price=payload.target_price,
        marketplaces=json.dumps(payload.marketplaces),
        channels=json.dumps(payload.channels),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return {"id": alert.id, "asin": alert.asin, "target_price": alert.target_price}


async def list_alerts_from_db(user_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Alert).where(Alert.user_id == user_id, Alert.active.is_(True))
    )
    alerts = result.scalars().all()
    return [
        {"id": a.id, "asin": a.asin, "target_price": a.target_price, "active": a.active}
        for a in alerts
    ]


async def deactivate_alert_in_db(alert_id: int, db: AsyncSession) -> bool:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        return False
    alert.active = False
    await db.commit()
    return True


@router.post("", status_code=201)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    return await create_alert_in_db(payload, db)


@router.get("")
async def list_alerts(user_id: int, db: AsyncSession = Depends(get_db)):
    return await list_alerts_from_db(user_id, db)


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await deactivate_alert_in_db(alert_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"deleted": True}
