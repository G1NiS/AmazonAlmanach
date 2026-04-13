import httpx
from typing import Any
from core.config import settings

# Keepa time epoch: minutes since 2011-01-01 00:00 UTC
KEEPA_EPOCH_OFFSET = 1293840000


class KeepaClient:
    BASE_URL = "https://api.keepa.com"

    MARKETPLACE_IDS = {
        "US": 1,
        "GB": 2,
        "DE": 3,
        "FR": 4,
        "JP": 5,
        "CA": 6,
        "IT": 8,
        "ES": 9,
        "IN": 10,
        "MX": 11,
        "BR": 12,
        "AU": 13,
    }

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.keepa_api_key
        self._http = httpx.AsyncClient(timeout=30.0)

    def keepa_time_to_unix(self, keepa_time: int) -> int:
        """Convert Keepa time (minutes since 2011-01-01) to Unix timestamp."""
        return KEEPA_EPOCH_OFFSET + keepa_time * 60

    def _parse_csv(self, csv: list[int]) -> list[dict]:
        """Convert flat [keepa_time, price_cents, keepa_time, price_cents, ...] to dicts.

        Keepa uses -1 to indicate unavailable prices — these are skipped.
        """
        result = []
        for i in range(0, len(csv) - 1, 2):
            keepa_time = csv[i]
            price_cents = csv[i + 1]
            if keepa_time != -1 and price_cents != -1:
                result.append({
                    "timestamp": self.keepa_time_to_unix(keepa_time),
                    "price": round(price_cents / 100, 2),
                })
        return result

    async def get_product(self, asin: str, marketplace: str = "US") -> dict[str, Any]:
        """Fetch product data including full price history from Keepa."""
        domain = self.MARKETPLACE_IDS.get(marketplace, 1)
        response = await self._http.get(
            f"{self.BASE_URL}/product",
            params={
                "key": self.api_key,
                "domain": domain,
                "asin": asin,
                "history": 1,
            },
        )
        response.raise_for_status()
        data = response.json()
        product = data["products"][0]

        csv = product.get("csv") or []
        # csv[0] = Amazon price history (new), csv[11] = shipping cost history
        price_csv = csv[0] if len(csv) > 0 and csv[0] else []
        shipping_csv = csv[11] if len(csv) > 11 and csv[11] else []

        images = product.get("imagesCSV", "")
        first_image = images.split(",")[0] if images else None
        image_url = (
            f"https://images-na.ssl-images-amazon.com/images/I/{first_image}"
            if first_image
            else None
        )

        category_tree = product.get("categoryTree") or []
        category = category_tree[-1].get("name", "") if category_tree else ""

        return {
            "asin": product["asin"],
            "title": product.get("title", ""),
            "brand": product.get("brand"),
            "category": category,
            "image_url": image_url,
            "price_history": self._parse_csv(price_csv),
            "shipping_history": self._parse_csv(shipping_csv),
            "sales_rank": product.get("salesRanks", {}),
        }

    async def get_best_sellers(self, category_id: int, marketplace: str = "US") -> list[str]:
        """Fetch best seller ASINs for a given Keepa category ID."""
        domain = self.MARKETPLACE_IDS.get(marketplace, 1)
        response = await self._http.get(
            f"{self.BASE_URL}/bestsellers",
            params={
                "key": self.api_key,
                "domain": domain,
                "category": category_id,
            },
        )
        response.raise_for_status()
        return response.json().get("asinList", [])

    async def close(self) -> None:
        await self._http.aclose()
