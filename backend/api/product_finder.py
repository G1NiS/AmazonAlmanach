from fastapi import APIRouter, Query
from services.amazon_client import AmazonClient

router = APIRouter(prefix="/api/product-finder", tags=["product-finder"])
amazon_client = AmazonClient()


@router.get("")
async def find_products(
    q: str = Query(..., min_length=1),
    marketplace: str = Query("US"),
    category: str = Query("All"),
    min_price: float | None = Query(None, gt=0),
    max_price: float | None = Query(None, gt=0),
) -> list[dict]:
    results = await amazon_client.search(q, marketplace=marketplace, category=category)
    if min_price is not None:
        results = [r for r in results if r.get("price") is not None and r["price"] >= min_price]
    if max_price is not None:
        results = [r for r in results if r.get("price") is not None and r["price"] <= max_price]
    return results
