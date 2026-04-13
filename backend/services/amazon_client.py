import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import httpx

from core.config import settings

MARKETPLACE_ENDPOINTS: dict[str, tuple[str, str]] = {
    "US": ("webservices.amazon.com", "us-east-1"),
    "GB": ("webservices.amazon.co.uk", "eu-west-1"),
    "DE": ("webservices.amazon.de", "eu-west-1"),
    "FR": ("webservices.amazon.fr", "eu-west-1"),
    "JP": ("webservices.amazon.co.jp", "us-west-2"),
    "CA": ("webservices.amazon.ca", "us-east-1"),
    "IT": ("webservices.amazon.it", "eu-west-1"),
    "ES": ("webservices.amazon.es", "eu-west-1"),
    "IN": ("webservices.amazon.in", "eu-west-1"),
    "AU": ("webservices.amazon.com.au", "us-west-2"),
    "MX": ("webservices.amazon.com.mx", "us-east-1"),
    "BR": ("webservices.amazon.com.br", "us-east-1"),
}

_SERVICE = "ProductAdvertisingAPI"
_TARGET_PREFIX = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1"
_PATH = "/paapi5/searchitems"
_GET_ITEMS_PATH = "/paapi5/getitems"

_RESOURCES = [
    "ItemInfo.Title",
    "ItemInfo.ByLineInfo",
    "Images.Primary.Large",
    "Offers.Listings.Price",
    "Offers.Listings.DeliveryInfo.IsAmazonFulfilled",
    "Offers.Listings.DeliveryInfo.IsPrimeEligible",
]


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signing_key(secret: str, date: str, region: str, service: str) -> bytes:
    k_date = _sign(("AWS4" + secret).encode("utf-8"), date)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def _build_headers(
    host: str,
    region: str,
    operation: str,
    payload: dict,
    access_key: str,
    secret_key: str,
    partner_tag: str,
) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    payload["PartnerTag"] = partner_tag
    payload["PartnerType"] = "Associates"
    payload["Marketplace"] = f"www.{host.replace('webservices.', '')}"

    body = json.dumps(payload, separators=(",", ":"))
    body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()

    canonical_headers = (
        f"content-encoding:amz-1.0\n"
        f"content-type:application/json; charset=utf-8\n"
        f"host:{host}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:{_TARGET_PREFIX}.{operation}\n"
    )
    signed_headers = "content-encoding;content-type;host;x-amz-date;x-amz-target"

    path = _PATH if operation == "SearchItems" else _GET_ITEMS_PATH
    canonical_request = "\n".join([
        "POST", path, "",
        canonical_headers, signed_headers, body_hash,
    ])

    credential_scope = f"{date_stamp}/{region}/{_SERVICE}/aws4_request"
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, credential_scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    signing_key = _get_signing_key(secret_key, date_stamp, region, _SERVICE)
    signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    authorization = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    return {
        "content-encoding": "amz-1.0",
        "content-type": "application/json; charset=utf-8",
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-target": f"{_TARGET_PREFIX}.{operation}",
        "Authorization": authorization,
    }


class AmazonClient:
    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=15.0)

    def _parse_item(self, item: dict, marketplace: str) -> dict[str, Any]:
        listings = (item.get("Offers") or {}).get("Listings") or []
        listing = listings[0] if listings else None

        price = None
        currency = "USD"
        is_prime = False
        shipping_price = None

        if listing:
            price_data = listing.get("Price") or {}
            price = price_data.get("Amount")
            currency = price_data.get("Currency", "USD")
            delivery = listing.get("DeliveryInfo") or {}
            is_prime = delivery.get("IsPrimeEligible", False)
            if is_prime:
                shipping_price = 0.0

        item_info = item.get("ItemInfo") or {}
        title = (item_info.get("Title") or {}).get("DisplayValue", "")
        brand = ((item_info.get("ByLineInfo") or {}).get("Brand") or {}).get("DisplayValue")

        images = item.get("Images") or {}
        primary = (images.get("Primary") or {}).get("Large") or {}
        image_url = primary.get("URL")

        return {
            "asin": item["ASIN"],
            "title": title,
            "brand": brand,
            "image_url": image_url,
            "price": price,
            "shipping_price": shipping_price,
            "currency": currency,
            "marketplace": marketplace,
            "is_prime": is_prime,
        }

    async def _post(self, host: str, region: str, operation: str, payload: dict) -> dict:
        path = _PATH if operation == "SearchItems" else _GET_ITEMS_PATH
        headers = _build_headers(
            host=host,
            region=region,
            operation=operation,
            payload=payload,
            access_key=settings.amazon_access_key,
            secret_key=settings.amazon_secret_key,
            partner_tag=settings.amazon_partner_tag,
        )
        url = f"https://{host}{path}"
        body = json.dumps(payload, separators=(",", ":"))
        response = await self._http.post(url, content=body, headers=headers)
        response.raise_for_status()
        return response.json()

    async def search(
        self,
        keywords: str,
        marketplace: str = "US",
        category: str = "All",
        item_count: int = 10,
    ) -> list[dict]:
        host, region = MARKETPLACE_ENDPOINTS.get(marketplace, MARKETPLACE_ENDPOINTS["US"])
        payload = {
            "Keywords": keywords,
            "SearchIndex": category,
            "Resources": _RESOURCES,
            "ItemCount": item_count,
        }
        try:
            data = await self._post(host, region, "SearchItems", payload)
        except httpx.HTTPError:
            return []
        items = (data.get("SearchResult") or {}).get("Items") or []
        return [self._parse_item(item, marketplace) for item in items]

    async def get_item(self, asin: str, marketplace: str = "US") -> dict | None:
        host, region = MARKETPLACE_ENDPOINTS.get(marketplace, MARKETPLACE_ENDPOINTS["US"])
        payload = {
            "ItemIds": [asin],
            "Resources": _RESOURCES,
        }
        try:
            data = await self._post(host, region, "GetItems", payload)
        except httpx.HTTPError:
            return None
        items = (data.get("ItemsResult") or {}).get("Items") or []
        return self._parse_item(items[0], marketplace) if items else None

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()
