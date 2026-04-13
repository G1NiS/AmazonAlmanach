from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.keepa_client import KeepaClient
from services.amazon_client import AmazonClient

router = APIRouter(prefix="/api/products", tags=["products"])

keepa_client = KeepaClient()
amazon_client = AmazonClient()

COMPARE_MARKETPLACES = ["US", "GB", "DE", "FR", "IT", "ES", "CA", "JP", "AU", "IN", "MX", "BR"]


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    marketplace: str = Query("US"),
    category: str = Query("All"),
):
    return await amazon_client.search(q, marketplace=marketplace, category=category)


@router.get("/{asin}/price-history")
async def get_price_history(
    asin: str,
    marketplace: str = Query("US"),
    db: AsyncSession = Depends(get_db),
):
    data = await keepa_client.get_product(asin, marketplace=marketplace)
    if not data:
        raise HTTPException(status_code=404, detail="Product not found")
    return data


@router.get("/{asin}/compare")
async def compare_marketplaces(asin: str):
    """Get current price across all marketplaces, sorted cheapest total first."""
    import asyncio
    results = await asyncio.gather(
        *[amazon_client.get_item(asin, marketplace=mp) for mp in COMPARE_MARKETPLACES],
        return_exceptions=True,
    )
    items = [
        r for r in results
        if isinstance(r, dict) and r is not None
    ]
    return sorted(
        items,
        key=lambda x: (x.get("price") or float("inf")) + (x.get("shipping_price") or 0),
    )
