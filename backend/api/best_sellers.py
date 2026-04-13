from fastapi import APIRouter, Query
from services.keepa_client import KeepaClient

router = APIRouter(prefix="/api/best-sellers", tags=["best-sellers"])
keepa_client = KeepaClient()

CATEGORIES: dict[str, int] = {
    "Electronics": 172282,
    "Books": 283155,
    "Toys": 165793011,
    "Kitchen": 284507,
    "Sports": 3375251,
    "Clothing": 7141123011,
    "Home": 1055398,
    "Beauty": 11055981,
    "Automotive": 15684181,
    "Garden": 2972638011,
}


@router.get("/categories")
async def list_categories() -> list[str]:
    return list(CATEGORIES.keys())


@router.get("")
async def get_best_sellers(
    category: str = Query("Electronics"),
    marketplace: str = Query("US"),
) -> dict:
    category_id = CATEGORIES.get(category, CATEGORIES["Electronics"])
    asins = await keepa_client.get_best_sellers(category_id, marketplace=marketplace)
    return {"category": category, "marketplace": marketplace, "asins": asins[:50]}
