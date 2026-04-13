# Amazon Product Tracker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a full-stack Amazon product price tracker with price history charts, multi-marketplace comparison, price drop alerts (email/Telegram/push/screen), product finder, best sellers, and review analysis.

**Architecture:** API-first — Python FastAPI backend aggregates data from Keepa API + Amazon PA API, stores in PostgreSQL, caches in Redis, fires background Celery workers for alerts. Next.js frontend consumes the REST API.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Celery, PostgreSQL 16, Redis, Next.js 14, TypeScript, Recharts, Keepa API, Amazon PA API, Docker

---

## Phase 1 — Foundation

### Task 1: Project Scaffold

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/pyproject.toml`
- Create: `backend/main.py`
- Create: `backend/core/config.py`
- Create: `backend/core/database.py`
- Create: `.env.example`
- Create: `frontend/` (Next.js app)

**Step 1: Create root directory structure**

```bash
cd "C:\Users\edvinas.giniotis\CLAUDE\A tool"
mkdir -p backend/api backend/services backend/models backend/workers backend/core backend/tests
mkdir -p frontend
```

**Step 2: Create `.env.example`**

```env
# Amazon PA API
AMAZON_ACCESS_KEY=your_access_key
AMAZON_SECRET_KEY=your_secret_key
AMAZON_PARTNER_TAG=your_tag-20
AMAZON_HOST=webservices.amazon.com

# Keepa API
KEEPA_API_KEY=your_keepa_api_key

# Database
DATABASE_URL=postgresql+asyncpg://tracker:tracker@localhost:5432/amazon_tracker
REDIS_URL=redis://localhost:6379/0

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=your_bot_token
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_CLAIM_EMAIL=your@email.com
```

**Step 3: Create `docker-compose.yml`**

```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: tracker
      POSTGRES_PASSWORD: tracker
      POSTGRES_DB: amazon_tracker
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  celery:
    build: ./backend
    env_file: .env
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: celery -A workers.tasks worker --beat --loglevel=info

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: .env
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    command: npm run dev

volumes:
  postgres_data:
```

**Step 4: Create `backend/pyproject.toml`**

```toml
[project]
name = "amazon-tracker-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "redis>=5.0.0",
    "celery[redis]>=5.4.0",
    "httpx>=0.27.0",
    "pydantic-settings>=2.0.0",
    "python-dotenv>=1.0.0",
    "paapi5-python-sdk>=1.0.0",
    "pywebpush>=2.0.0",
    "python-telegram-bot>=21.0",
    "aiosmtplib>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
    "pytest-mock>=3.14.0",
]
```

**Step 5: Create `backend/core/config.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    amazon_access_key: str
    amazon_secret_key: str
    amazon_partner_tag: str
    amazon_host: str = "webservices.amazon.com"
    keepa_api_key: str
    database_url: str
    redis_url: str
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    telegram_bot_token: str = ""
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_claim_email: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 6: Create `backend/core/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

**Step 7: Create `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Amazon Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 8: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY . .
```

**Step 9: Scaffold Next.js frontend**

```bash
cd "C:\Users\edvinas.giniotis\CLAUDE\A tool"
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"
```

**Step 10: Start infrastructure and verify**

```bash
docker-compose up postgres redis -d
# Wait 5 seconds, then:
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**Step 11: Commit**

```bash
git init
git add .
git commit -m "feat: initial project scaffold — FastAPI + Next.js + Docker"
```

---

### Task 2: Database Models & Migrations

**Files:**
- Create: `backend/models/product.py`
- Create: `backend/models/price_history.py`
- Create: `backend/models/user.py`
- Create: `backend/models/alert.py`
- Create: `backend/models/__init__.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

**Step 1: Create `backend/models/product.py`**

```python
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    asin: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(200))
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

**Step 2: Create `backend/models/price_history.py`**

```python
from sqlalchemy import String, Float, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_asin_marketplace_ts", "asin", "marketplace", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    asin: Mapped[str] = mapped_column(String(10), index=True)
    marketplace: Mapped[str] = mapped_column(String(10))  # US, DE, UK, etc.
    price: Mapped[float | None] = mapped_column(Float)
    shipping_price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3))
    source: Mapped[str] = mapped_column(String(20))  # keepa, amazon
    timestamp: Mapped[DateTime] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

**Step 3: Create `backend/models/user.py`**

```python
from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(200), unique=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50))
    push_subscription: Mapped[str | None] = mapped_column(Text)  # JSON string
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

**Step 4: Create `backend/models/alert.py`**

```python
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
    triggered_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

**Step 5: Create `backend/models/__init__.py`**

```python
from models.product import Product
from models.price_history import PriceHistory
from models.user import User
from models.alert import Alert

__all__ = ["Product", "PriceHistory", "User", "Alert"]
```

**Step 6: Setup Alembic and create initial migration**

```bash
cd backend
pip install -e ".[dev]"
alembic init alembic
# Edit alembic/env.py to use async engine and import models
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
```

**Step 7: Commit**

```bash
git add backend/models/ backend/alembic/
git commit -m "feat: add database models and initial migration"
```

---

### Task 3: Keepa API Client

**Files:**
- Create: `backend/services/keepa_client.py`
- Create: `backend/tests/test_keepa_client.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_keepa_client.py
import pytest
from unittest.mock import AsyncMock, patch
from services.keepa_client import KeepaClient


@pytest.mark.asyncio
async def test_get_product_returns_price_history():
    client = KeepaClient(api_key="test_key")
    mock_response = {
        "products": [{
            "asin": "B08N5WRWNW",
            "title": "Test Product",
            "csv": [[1640000000, 9999], [1641000000, 8999]],  # keepa time, cents
        }]
    }
    with patch.object(client._http, "get", return_value=AsyncMock(json=lambda: mock_response)):
        result = await client.get_product("B08N5WRWNW", marketplace="US")
    assert result["asin"] == "B08N5WRWNW"
    assert len(result["price_history"]) == 2


@pytest.mark.asyncio
async def test_keepa_time_converts_to_unix():
    client = KeepaClient(api_key="test_key")
    keepa_time = 1640000000
    unix_time = client.keepa_time_to_unix(keepa_time)
    assert isinstance(unix_time, int)
    assert unix_time > 1609459200  # after 2021-01-01
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_keepa_client.py -v
# Expected: FAIL — ImportError: cannot import name 'KeepaClient'
```

**Step 3: Create `backend/services/keepa_client.py`**

```python
import httpx
from typing import Any
from core.config import settings

# Keepa time: minutes since 2011-01-01 00:00 UTC
KEEPA_EPOCH_OFFSET = 1293840000

MARKETPLACE_IDS = {
    "US": 1, "GB": 2, "DE": 3, "FR": 4, "JP": 5,
    "CA": 6, "IT": 8, "ES": 9, "IN": 10, "MX": 11,
    "BR": 12, "AU": 13,
}


class KeepaClient:
    BASE_URL = "https://api.keepa.com"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.keepa_api_key
        self._http = httpx.AsyncClient(timeout=30.0)

    def keepa_time_to_unix(self, keepa_time: int) -> int:
        return KEEPA_EPOCH_OFFSET + keepa_time * 60

    def _parse_csv(self, csv: list[int]) -> list[dict]:
        """Convert flat [time, price, time, price, ...] list to dicts."""
        result = []
        for i in range(0, len(csv) - 1, 2):
            if csv[i] != -1 and csv[i + 1] != -1:
                result.append({
                    "timestamp": self.keepa_time_to_unix(csv[i]),
                    "price": csv[i + 1] / 100,  # cents to dollars
                })
        return result

    async def get_product(self, asin: str, marketplace: str = "US") -> dict[str, Any]:
        domain = MARKETPLACE_IDS.get(marketplace, 1)
        resp = await self._http.get(
            f"{self.BASE_URL}/product",
            params={"key": self.api_key, "domain": domain, "asin": asin, "history": 1},
        )
        resp.raise_for_status()
        data = resp.json()
        product = data["products"][0]
        csv = product.get("csv", [])
        # csv[0] = Amazon price history, csv[7] = new price, csv[11] = shipping
        price_csv = csv[0] if csv else []
        shipping_csv = csv[11] if len(csv) > 11 else []
        return {
            "asin": product["asin"],
            "title": product.get("title", ""),
            "brand": product.get("brand", ""),
            "category": product.get("categoryTree", [{}])[-1].get("name", ""),
            "image_url": f"https://images-na.ssl-images-amazon.com/images/I/{product.get('imagesCSV', '').split(',')[0]}" if product.get("imagesCSV") else None,
            "price_history": self._parse_csv(price_csv),
            "shipping_history": self._parse_csv(shipping_csv),
            "sales_rank": product.get("salesRanks", {}),
        }

    async def get_best_sellers(self, category_id: int, marketplace: str = "US") -> list[str]:
        domain = MARKETPLACE_IDS.get(marketplace, 1)
        resp = await self._http.get(
            f"{self.BASE_URL}/bestsellers",
            params={"key": self.api_key, "domain": domain, "category": category_id},
        )
        resp.raise_for_status()
        return resp.json().get("asinList", [])

    async def close(self):
        await self._http.aclose()
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_keepa_client.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add backend/services/keepa_client.py backend/tests/test_keepa_client.py
git commit -m "feat: add Keepa API client with price history parsing"
```

---

### Task 4: Amazon PA API Client

**Files:**
- Create: `backend/services/amazon_client.py`
- Create: `backend/tests/test_amazon_client.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_amazon_client.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.amazon_client import AmazonClient


@pytest.mark.asyncio
async def test_search_products_returns_list():
    client = AmazonClient()
    mock_item = MagicMock()
    mock_item.asin = "B08N5WRWNW"
    mock_item.item_info.title.display_value = "Test Product"
    mock_item.offers.listings[0].price.amount = 29.99
    mock_item.offers.listings[0].price.currency = "USD"
    mock_item.offers.listings[0].delivery_info.is_prime_eligible = True

    with patch.object(client, "_search_raw", return_value=[mock_item]):
        results = await client.search("wireless headphones", marketplace="US")

    assert len(results) == 1
    assert results[0]["asin"] == "B08N5WRWNW"
    assert results[0]["price"] == 29.99
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_amazon_client.py -v
# Expected: FAIL — ImportError
```

**Step 3: Create `backend/services/amazon_client.py`**

```python
import asyncio
from typing import Any
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.get_items_request import GetItemsRequest
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException
from core.config import settings

MARKETPLACE_ENDPOINTS = {
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
}

RESOURCES = [
    "ItemInfo.Title", "ItemInfo.ByLineInfo", "ItemInfo.Classifications",
    "Images.Primary.Large",
    "Offers.Listings.Price", "Offers.Listings.DeliveryInfo.IsAmazonFulfilled",
    "Offers.Listings.DeliveryInfo.IsPrimeEligible",
    "Offers.Listings.SavingBasis",
    "BrowseNodeInfo.BrowseNodes",
]


def _get_api(marketplace: str) -> DefaultApi:
    host, region = MARKETPLACE_ENDPOINTS.get(marketplace, MARKETPLACE_ENDPOINTS["US"])
    return DefaultApi(
        access_key=settings.amazon_access_key,
        secret_key=settings.amazon_secret_key,
        host=host,
        region=region,
    )


def _parse_item(item: Any, marketplace: str) -> dict:
    listing = item.offers.listings[0] if item.offers and item.offers.listings else None
    return {
        "asin": item.asin,
        "title": item.item_info.title.display_value if item.item_info and item.item_info.title else "",
        "brand": item.item_info.by_line_info.brand.display_value if item.item_info and item.item_info.by_line_info and item.item_info.by_line_info.brand else None,
        "image_url": item.images.primary.large.url if item.images and item.images.primary else None,
        "price": listing.price.amount if listing and listing.price else None,
        "shipping_price": 0.0 if listing and listing.delivery_info and listing.delivery_info.is_prime_eligible else None,
        "currency": listing.price.currency if listing and listing.price else "USD",
        "marketplace": marketplace,
        "is_prime": listing.delivery_info.is_prime_eligible if listing and listing.delivery_info else False,
    }


class AmazonClient:
    async def search(self, keywords: str, marketplace: str = "US", category: str = "All") -> list[dict]:
        api = _get_api(marketplace)
        request = SearchItemsRequest(
            partner_tag=settings.amazon_partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            keywords=keywords,
            search_index=category,
            resources=RESOURCES,
            item_count=10,
        )
        try:
            response = await asyncio.to_thread(api.search_items, request)
            items = response.search_result.items if response.search_result else []
            return [_parse_item(item, marketplace) for item in items]
        except ApiException:
            return []

    async def _search_raw(self, keywords: str, marketplace: str) -> list:
        api = _get_api(marketplace)
        request = SearchItemsRequest(
            partner_tag=settings.amazon_partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            keywords=keywords,
            search_index="All",
            resources=RESOURCES,
            item_count=10,
        )
        response = await asyncio.to_thread(api.search_items, request)
        return response.search_result.items if response.search_result else []

    async def get_item(self, asin: str, marketplace: str = "US") -> dict | None:
        api = _get_api(marketplace)
        request = GetItemsRequest(
            partner_tag=settings.amazon_partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            item_ids=[asin],
            resources=RESOURCES,
        )
        try:
            response = await asyncio.to_thread(api.get_items, request)
            items = list(response.items_result.items.values()) if response.items_result else []
            return _parse_item(items[0], marketplace) if items else None
        except ApiException:
            return None
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_amazon_client.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add backend/services/amazon_client.py backend/tests/test_amazon_client.py
git commit -m "feat: add Amazon PA API client for search and item lookup"
```

---

## Phase 2 — Price Tracker API

### Task 5: Products API Endpoints

**Files:**
- Create: `backend/api/products.py`
- Create: `backend/tests/test_api_products.py`
- Modify: `backend/main.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_api_products.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app


@pytest.mark.asyncio
async def test_search_products():
    mock_results = [{"asin": "B08N5WRWNW", "title": "Test", "price": 29.99, "marketplace": "US"}]
    with patch("api.products.amazon_client.search", return_value=mock_results):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/products/search?q=headphones&marketplace=US")
    assert resp.status_code == 200
    assert resp.json()[0]["asin"] == "B08N5WRWNW"


@pytest.mark.asyncio
async def test_get_price_history():
    mock_history = {"asin": "B08N5WRWNW", "price_history": [{"timestamp": 1640000000, "price": 29.99}]}
    with patch("api.products.keepa_client.get_product", return_value=mock_history):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/products/B08N5WRWNW/price-history?marketplace=US")
    assert resp.status_code == 200
    assert "price_history" in resp.json()
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_products.py -v
# Expected: FAIL
```

**Step 3: Create `backend/api/products.py`**

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services.keepa_client import KeepaClient
from services.amazon_client import AmazonClient

router = APIRouter(prefix="/api/products", tags=["products"])
keepa_client = KeepaClient()
amazon_client = AmazonClient()


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    marketplace: str = Query("US"),
    category: str = Query("All"),
):
    results = await amazon_client.search(q, marketplace=marketplace, category=category)
    return results


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
    """Get current price across all marketplaces."""
    marketplaces = ["US", "GB", "DE", "FR", "IT", "ES", "CA", "JP", "AU"]
    results = []
    for mp in marketplaces:
        item = await amazon_client.get_item(asin, marketplace=mp)
        if item:
            results.append(item)
    return sorted(results, key=lambda x: (x.get("price") or float("inf")))
```

**Step 4: Register router in `backend/main.py`**

```python
from api.products import router as products_router
app.include_router(products_router)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api_products.py -v
# Expected: PASS
```

**Step 6: Commit**

```bash
git add backend/api/products.py backend/tests/test_api_products.py backend/main.py
git commit -m "feat: add product search and price history API endpoints"
```

---

### Task 6: Alerts API

**Files:**
- Create: `backend/api/alerts.py`
- Create: `backend/tests/test_api_alerts.py`
- Modify: `backend/main.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_api_alerts.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app


@pytest.mark.asyncio
async def test_create_alert():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/alerts", json={
            "asin": "B08N5WRWNW",
            "target_price": 20.0,
            "marketplaces": ["US", "DE"],
            "channels": ["email"],
            "email": "test@example.com",
        })
    assert resp.status_code == 201
    assert resp.json()["asin"] == "B08N5WRWNW"


@pytest.mark.asyncio
async def test_list_alerts():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/alerts?user_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_api_alerts.py -v
# Expected: FAIL
```

**Step 3: Create `backend/api/alerts.py`**

```python
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from core.database import get_db
from models.alert import Alert
from models.user import User

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class AlertCreate(BaseModel):
    asin: str
    target_price: float
    marketplaces: list[str]
    channels: list[str]
    email: str | None = None
    telegram_chat_id: str | None = None


@router.post("", status_code=201)
async def create_alert(payload: AlertCreate, db: AsyncSession = Depends(get_db)):
    # Upsert user
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


@router.get("")
async def list_alerts(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.user_id == user_id, Alert.active == True))
    alerts = result.scalars().all()
    return [{"id": a.id, "asin": a.asin, "target_price": a.target_price} for a in alerts]


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.active = False
    await db.commit()
    return {"deleted": True}
```

**Step 4: Register router in `main.py`**

```python
from api.alerts import router as alerts_router
app.include_router(alerts_router)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_api_alerts.py -v
# Expected: PASS
```

**Step 6: Commit**

```bash
git add backend/api/alerts.py backend/tests/test_api_alerts.py backend/main.py
git commit -m "feat: add alerts CRUD API"
```

---

### Task 7: Best Sellers & Product Finder API

**Files:**
- Create: `backend/api/best_sellers.py`
- Create: `backend/api/product_finder.py`
- Modify: `backend/main.py`

**Step 1: Create `backend/api/best_sellers.py`**

```python
from fastapi import APIRouter, Query
from services.keepa_client import KeepaClient

router = APIRouter(prefix="/api/best-sellers", tags=["best-sellers"])
keepa_client = KeepaClient()

# Common Keepa category IDs
CATEGORIES = {
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


@router.get("")
async def get_best_sellers(
    category: str = Query("Electronics"),
    marketplace: str = Query("US"),
):
    category_id = CATEGORIES.get(category, CATEGORIES["Electronics"])
    asins = await keepa_client.get_best_sellers(category_id, marketplace=marketplace)
    return {"category": category, "marketplace": marketplace, "asins": asins[:50]}


@router.get("/categories")
async def list_categories():
    return list(CATEGORIES.keys())
```

**Step 2: Create `backend/api/product_finder.py`**

```python
from fastapi import APIRouter, Query
from services.amazon_client import AmazonClient

router = APIRouter(prefix="/api/product-finder", tags=["product-finder"])
amazon_client = AmazonClient()


@router.get("")
async def find_products(
    q: str = Query(...),
    marketplace: str = Query("US"),
    category: str = Query("All"),
    min_price: float | None = Query(None),
    max_price: float | None = Query(None),
    min_rating: float | None = Query(None),
):
    results = await amazon_client.search(q, marketplace=marketplace, category=category)
    if min_price is not None:
        results = [r for r in results if r.get("price") and r["price"] >= min_price]
    if max_price is not None:
        results = [r for r in results if r.get("price") and r["price"] <= max_price]
    return results
```

**Step 3: Register routers in `main.py`**

```python
from api.best_sellers import router as best_sellers_router
from api.product_finder import router as product_finder_router
app.include_router(best_sellers_router)
app.include_router(product_finder_router)
```

**Step 4: Commit**

```bash
git add backend/api/best_sellers.py backend/api/product_finder.py backend/main.py
git commit -m "feat: add best sellers and product finder endpoints"
```

---

## Phase 3 — Notifications

### Task 8: Notifier Service

**Files:**
- Create: `backend/services/notifier.py`
- Create: `backend/tests/test_notifier.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_notifier.py
import pytest
from unittest.mock import AsyncMock, patch
from services.notifier import Notifier


@pytest.mark.asyncio
async def test_send_email_called_with_correct_args():
    notifier = Notifier()
    with patch.object(notifier, "_send_email", new_callable=AsyncMock) as mock_email:
        await notifier.notify(
            channels=["email"],
            email="test@example.com",
            asin="B08N5WRWNW",
            product_title="Test Product",
            current_price=19.99,
            target_price=20.00,
            marketplace="US",
        )
    mock_email.assert_called_once()
    call_args = mock_email.call_args[1]
    assert call_args["to"] == "test@example.com"
    assert "B08N5WRWNW" in call_args["body"]


@pytest.mark.asyncio
async def test_notify_skips_unknown_channel():
    notifier = Notifier()
    # Should not raise
    await notifier.notify(
        channels=["unknown_channel"],
        asin="B08N5WRWNW",
        product_title="Test",
        current_price=10.0,
        target_price=15.0,
        marketplace="US",
    )
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_notifier.py -v
# Expected: FAIL
```

**Step 3: Create `backend/services/notifier.py`**

```python
import json
import asyncio
import aiosmtplib
from email.message import EmailMessage
from typing import Any
from core.config import settings

try:
    from telegram import Bot as TelegramBot
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False

try:
    from pywebpush import webpush, WebPushException
    HAS_WEBPUSH = True
except ImportError:
    HAS_WEBPUSH = False


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
                tasks.append(self._send_email(
                    to=email,
                    subject=f"Price Drop: {product_title}",
                    body=self._email_body(asin, product_title, current_price, target_price, marketplace),
                ))
            elif channel == "telegram" and telegram_chat_id and HAS_TELEGRAM:
                tasks.append(self._send_telegram(
                    chat_id=telegram_chat_id,
                    message=f"Price drop! {product_title}\n${current_price} (target: ${target_price})\nASIN: {asin}",
                ))
            elif channel == "push" and push_subscription and HAS_WEBPUSH:
                tasks.append(self._send_push(push_subscription, product_title, current_price))
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

    async def _send_email(self, to: str, subject: str, body: str) -> None:
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

    async def _send_telegram(self, chat_id: str, message: str) -> None:
        bot = TelegramBot(token=settings.telegram_bot_token)
        await bot.send_message(chat_id=chat_id, text=message)

    async def _send_push(self, subscription_json: str, title: str, price: float) -> None:
        subscription = json.loads(subscription_json)
        await asyncio.to_thread(
            webpush,
            subscription_info=subscription,
            data=json.dumps({"title": f"Price Drop!", "body": f"{title} — ${price:.2f}"}),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": f"mailto:{settings.vapid_claim_email}"},
        )
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_notifier.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add backend/services/notifier.py backend/tests/test_notifier.py
git commit -m "feat: add multi-channel notifier (email, Telegram, Web Push)"
```

---

### Task 9: Celery Alert Worker

**Files:**
- Create: `backend/workers/tasks.py`
- Create: `backend/tests/test_tasks.py`

**Step 1: Write failing test**

```python
# backend/tests/test_tasks.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from workers.tasks import check_price_alerts


@pytest.mark.asyncio
async def test_check_price_alerts_triggers_notification_when_price_drops():
    mock_alert = MagicMock()
    mock_alert.id = 1
    mock_alert.asin = "B08N5WRWNW"
    mock_alert.target_price = 30.0
    mock_alert.marketplaces = '["US"]'
    mock_alert.channels = '["email"]'
    mock_alert.user_id = 1

    mock_user = MagicMock()
    mock_user.email = "test@example.com"

    mock_item = {"price": 25.0, "title": "Test Product", "marketplace": "US"}

    with patch("workers.tasks.get_active_alerts", return_value=[mock_alert]), \
         patch("workers.tasks.get_user", return_value=mock_user), \
         patch("workers.tasks.amazon_client.get_item", return_value=mock_item), \
         patch("workers.tasks.notifier.notify", new_callable=AsyncMock) as mock_notify:
        await check_price_alerts()

    mock_notify.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_tasks.py -v
# Expected: FAIL
```

**Step 3: Create `backend/workers/tasks.py`**

```python
import json
import asyncio
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select
from core.config import settings
from core.database import AsyncSessionLocal
from models.alert import Alert
from models.user import User
from services.amazon_client import AmazonClient
from services.notifier import Notifier

celery_app = Celery("tasks", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "check-alerts-every-hour": {
        "task": "workers.tasks.run_check_alerts",
        "schedule": crontab(minute=0),
    },
}

amazon_client = AmazonClient()
notifier = Notifier()


async def get_active_alerts() -> list[Alert]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Alert).where(Alert.active == True))
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
            if item and item.get("price") and item["price"] <= alert.target_price:
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
def run_check_alerts():
    asyncio.run(check_price_alerts())
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_tasks.py -v
# Expected: PASS
```

**Step 5: Commit**

```bash
git add backend/workers/tasks.py backend/tests/test_tasks.py
git commit -m "feat: add Celery price alert worker with hourly schedule"
```

---

### Task 10: WebSocket Screen Notifications

**Files:**
- Create: `backend/api/websocket.py`
- Modify: `backend/main.py`
- Modify: `backend/services/notifier.py`

**Step 1: Create `backend/api/websocket.py`**

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# In-memory connection manager (single user MVP)
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in self.active[:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.active.remove(ws)


manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Step 2: Add WebSocket broadcast to notifier**

In `backend/services/notifier.py`, add to the `notify` method:

```python
elif channel == "screen":
    tasks.append(self._send_screen(asin, product_title, current_price))
```

And add the method:

```python
async def _send_screen(self, asin: str, title: str, price: float) -> None:
    from api.websocket import manager
    await manager.broadcast({
        "type": "price_alert",
        "asin": asin,
        "title": title,
        "price": price,
    })
```

**Step 3: Register WebSocket router in `main.py`**

```python
from api.websocket import router as ws_router
app.include_router(ws_router)
```

**Step 4: Commit**

```bash
git add backend/api/websocket.py backend/main.py backend/services/notifier.py
git commit -m "feat: add WebSocket screen notification channel"
```

---

## Phase 4 — Frontend

### Task 11: Next.js API Client & Layout

**Files:**
- Create: `frontend/lib/api.ts`
- Create: `frontend/lib/websocket.ts`
- Modify: `frontend/app/layout.tsx`

**Step 1: Create `frontend/lib/api.ts`**

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function searchProducts(q: string, marketplace = "US") {
  const res = await fetch(`${API_BASE}/api/products/search?q=${encodeURIComponent(q)}&marketplace=${marketplace}`);
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function getPriceHistory(asin: string, marketplace = "US") {
  const res = await fetch(`${API_BASE}/api/products/${asin}/price-history?marketplace=${marketplace}`);
  if (!res.ok) throw new Error("Price history fetch failed");
  return res.json();
}

export async function compareMarketplaces(asin: string) {
  const res = await fetch(`${API_BASE}/api/products/${asin}/compare`);
  if (!res.ok) throw new Error("Compare fetch failed");
  return res.json();
}

export async function createAlert(payload: {
  asin: string; target_price: number; marketplaces: string[];
  channels: string[]; email?: string; telegram_chat_id?: string;
}) {
  const res = await fetch(`${API_BASE}/api/alerts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Alert creation failed");
  return res.json();
}

export async function getBestSellers(category = "Electronics", marketplace = "US") {
  const res = await fetch(`${API_BASE}/api/best-sellers?category=${category}&marketplace=${marketplace}`);
  if (!res.ok) throw new Error("Best sellers fetch failed");
  return res.json();
}

export async function findProducts(params: {
  q: string; marketplace?: string; category?: string;
  min_price?: number; max_price?: number;
}) {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null).map(([k, v]) => [k, String(v)]));
  const res = await fetch(`${API_BASE}/api/product-finder?${qs}`);
  if (!res.ok) throw new Error("Product finder failed");
  return res.json();
}
```

**Step 2: Create `frontend/lib/websocket.ts`**

```typescript
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/notifications";

type AlertMessage = { type: string; asin: string; title: string; price: number };
type Handler = (msg: AlertMessage) => void;

let socket: WebSocket | null = null;
const handlers: Handler[] = [];

export function connectWebSocket() {
  if (socket) return;
  socket = new WebSocket(WS_URL);
  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data) as AlertMessage;
    handlers.forEach((h) => h(msg));
  };
  socket.onclose = () => {
    socket = null;
    setTimeout(connectWebSocket, 5000); // reconnect
  };
}

export function onAlert(handler: Handler) {
  handlers.push(handler);
  return () => { const i = handlers.indexOf(handler); if (i > -1) handlers.splice(i, 1); };
}
```

**Step 3: Install frontend dependencies**

```bash
cd frontend
npm install recharts lucide-react
```

**Step 4: Commit**

```bash
git add frontend/lib/
git commit -m "feat: add frontend API client and WebSocket utility"
```

---

### Task 12: Price History Chart Component

**Files:**
- Create: `frontend/components/PriceChart.tsx`
- Create: `frontend/components/MarketplaceComparison.tsx`

**Step 1: Create `frontend/components/PriceChart.tsx`**

```tsx
"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";

type DataPoint = { timestamp: number; price: number };
type Props = { priceHistory: DataPoint[]; shippingHistory?: DataPoint[]; currency?: string };

function formatDate(ts: number) {
  return new Date(ts * 1000).toLocaleDateString();
}

export default function PriceChart({ priceHistory, shippingHistory = [], currency = "USD" }: Props) {
  const merged = priceHistory.map((p) => {
    const shipping = shippingHistory.find((s) => Math.abs(s.timestamp - p.timestamp) < 86400);
    return {
      date: formatDate(p.timestamp),
      price: p.price,
      total: shipping ? +(p.price + shipping.price).toFixed(2) : undefined,
    };
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={merged}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tickFormatter={(v) => `${currency === "USD" ? "$" : "€"}${v}`} />
        <Tooltip formatter={(v) => [`${v}`, ""]} />
        <Legend />
        <Line type="monotone" dataKey="price" stroke="#2563eb" name="Price" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="total" stroke="#16a34a" name="Price + Shipping" dot={false} strokeWidth={2} strokeDasharray="4 2" />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

**Step 2: Create `frontend/components/MarketplaceComparison.tsx`**

```tsx
type Item = { marketplace: string; price: number | null; shipping_price: number | null; currency: string; is_prime: boolean };
type Props = { items: Item[] };

export default function MarketplaceComparison({ items }: Props) {
  const sorted = [...items].sort((a, b) => {
    const totalA = (a.price ?? Infinity) + (a.shipping_price ?? 0);
    const totalB = (b.price ?? Infinity) + (b.shipping_price ?? 0);
    return totalA - totalB;
  });

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2 text-left">Marketplace</th>
            <th className="p-2 text-right">Price</th>
            <th className="p-2 text-right">Shipping</th>
            <th className="p-2 text-right font-bold">Total</th>
            <th className="p-2 text-center">Prime</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((item, i) => {
            const total = (item.price ?? 0) + (item.shipping_price ?? 0);
            return (
              <tr key={item.marketplace} className={i === 0 ? "bg-green-50 font-medium" : "border-t"}>
                <td className="p-2">{i === 0 ? "⭐ " : ""}{item.marketplace}</td>
                <td className="p-2 text-right">{item.price != null ? `${item.price.toFixed(2)} ${item.currency}` : "—"}</td>
                <td className="p-2 text-right">{item.shipping_price != null ? `${item.shipping_price.toFixed(2)} ${item.currency}` : "—"}</td>
                <td className="p-2 text-right">{total.toFixed(2)} {item.currency}</td>
                <td className="p-2 text-center">{item.is_prime ? "✓" : ""}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/components/
git commit -m "feat: add price history chart and marketplace comparison components"
```

---

### Task 13: Product Detail Page

**Files:**
- Create: `frontend/app/product/[asin]/page.tsx`
- Create: `frontend/components/AlertForm.tsx`

**Step 1: Create `frontend/components/AlertForm.tsx`**

```tsx
"use client";
import { useState } from "react";
import { createAlert } from "@/lib/api";

type Props = { asin: string };

export default function AlertForm({ asin }: Props) {
  const [targetPrice, setTargetPrice] = useState("");
  const [email, setEmail] = useState("");
  const [marketplaces, setMarketplaces] = useState(["US"]);
  const [channels, setChannels] = useState(["email", "screen"]);
  const [status, setStatus] = useState<"idle" | "saved" | "error">("idle");

  const allMarketplaces = ["US", "GB", "DE", "FR", "IT", "ES", "CA", "JP", "AU"];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createAlert({ asin, target_price: parseFloat(targetPrice), marketplaces, channels, email });
      setStatus("saved");
    } catch {
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 border rounded-lg p-4">
      <h3 className="font-semibold text-lg">Set Price Alert</h3>
      <div>
        <label className="block text-sm mb-1">Target Price ($)</label>
        <input type="number" step="0.01" required value={targetPrice} onChange={e => setTargetPrice(e.target.value)}
          className="border rounded px-3 py-1 w-full" />
      </div>
      <div>
        <label className="block text-sm mb-1">Email (for email alerts)</label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="border rounded px-3 py-1 w-full" />
      </div>
      <div>
        <label className="block text-sm mb-1">Marketplaces</label>
        <div className="flex flex-wrap gap-2">
          {allMarketplaces.map(mp => (
            <label key={mp} className="flex items-center gap-1 text-sm">
              <input type="checkbox" checked={marketplaces.includes(mp)}
                onChange={e => setMarketplaces(e.target.checked ? [...marketplaces, mp] : marketplaces.filter(m => m !== mp))} />
              {mp}
            </label>
          ))}
        </div>
      </div>
      <div>
        <label className="block text-sm mb-1">Notify via</label>
        <div className="flex gap-4">
          {["email", "telegram", "push", "screen"].map(ch => (
            <label key={ch} className="flex items-center gap-1 text-sm">
              <input type="checkbox" checked={channels.includes(ch)}
                onChange={e => setChannels(e.target.checked ? [...channels, ch] : channels.filter(c => c !== ch))} />
              {ch}
            </label>
          ))}
        </div>
      </div>
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        Save Alert
      </button>
      {status === "saved" && <p className="text-green-600 text-sm">Alert saved!</p>}
      {status === "error" && <p className="text-red-600 text-sm">Failed to save alert.</p>}
    </form>
  );
}
```

**Step 2: Create `frontend/app/product/[asin]/page.tsx`**

```tsx
import { getPriceHistory, compareMarketplaces } from "@/lib/api";
import PriceChart from "@/components/PriceChart";
import MarketplaceComparison from "@/components/MarketplaceComparison";
import AlertForm from "@/components/AlertForm";

type Props = { params: { asin: string }; searchParams: { marketplace?: string } };

export default async function ProductPage({ params, searchParams }: Props) {
  const marketplace = searchParams.marketplace || "US";
  const [history, comparison] = await Promise.all([
    getPriceHistory(params.asin, marketplace),
    compareMarketplaces(params.asin),
  ]);

  return (
    <main className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="flex items-start gap-4">
        {history.image_url && <img src={history.image_url} alt={history.title} className="w-32 h-32 object-contain" />}
        <div>
          <h1 className="text-2xl font-bold">{history.title}</h1>
          {history.brand && <p className="text-gray-500">{history.brand}</p>}
          <p className="text-sm text-gray-400">ASIN: {params.asin}</p>
        </div>
      </div>

      <section>
        <h2 className="text-xl font-semibold mb-3">Price History ({marketplace})</h2>
        <PriceChart priceHistory={history.price_history} shippingHistory={history.shipping_history} />
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Price Comparison — All Marketplaces</h2>
        <MarketplaceComparison items={comparison} />
      </section>

      <AlertForm asin={params.asin} />
    </main>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/app/product/ frontend/components/AlertForm.tsx
git commit -m "feat: add product detail page with price chart and alert form"
```

---

### Task 14: Search Page & Dashboard

**Files:**
- Create: `frontend/app/page.tsx` (dashboard / search)
- Create: `frontend/components/ProductCard.tsx`
- Create: `frontend/components/NotificationToast.tsx`

**Step 1: Create `frontend/components/ProductCard.tsx`**

```tsx
import Link from "next/link";

type Props = {
  asin: string; title: string; price: number | null;
  currency?: string; image_url?: string; marketplace?: string;
};

export default function ProductCard({ asin, title, price, currency = "USD", image_url, marketplace = "US" }: Props) {
  return (
    <Link href={`/product/${asin}?marketplace=${marketplace}`}
      className="border rounded-lg p-4 flex gap-3 hover:shadow-md transition-shadow">
      {image_url && <img src={image_url} alt={title} className="w-16 h-16 object-contain flex-shrink-0" />}
      <div className="min-w-0">
        <p className="font-medium text-sm line-clamp-2">{title}</p>
        <p className="text-blue-600 font-bold mt-1">
          {price != null ? `${price.toFixed(2)} ${currency}` : "Price unavailable"}
        </p>
        <p className="text-xs text-gray-400">{asin}</p>
      </div>
    </Link>
  );
}
```

**Step 2: Create `frontend/components/NotificationToast.tsx`**

```tsx
"use client";
import { useEffect, useState } from "react";
import { connectWebSocket, onAlert } from "@/lib/websocket";

type Toast = { id: number; title: string; price: number; asin: string };

export default function NotificationToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    connectWebSocket();
    const unsub = onAlert((msg) => {
      const toast = { id: Date.now(), title: msg.title, price: msg.price, asin: msg.asin };
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== toast.id)), 5000);
    });
    return unsub;
  }, []);

  return (
    <div className="fixed bottom-4 right-4 space-y-2 z-50">
      {toasts.map((t) => (
        <div key={t.id} className="bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg max-w-sm">
          <p className="font-semibold">Price Drop Alert!</p>
          <p className="text-sm">{t.title}</p>
          <p className="font-bold">${t.price.toFixed(2)}</p>
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Create `frontend/app/page.tsx`**

```tsx
"use client";
import { useState } from "react";
import { searchProducts } from "@/lib/api";
import ProductCard from "@/components/ProductCard";
import NotificationToast from "@/components/NotificationToast";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [marketplace, setMarketplace] = useState("US");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const marketplaces = ["US", "GB", "DE", "FR", "IT", "ES", "CA", "JP", "AU", "IN", "MX", "BR"];

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchProducts(query, marketplace);
      setResults(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Amazon Price Tracker</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-8">
        <input type="text" placeholder="Search products or paste ASIN..." value={query}
          onChange={e => setQuery(e.target.value)}
          className="flex-1 border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <select value={marketplace} onChange={e => setMarketplace(e.target.value)}
          className="border rounded-lg px-3 py-2 text-sm">
          {marketplaces.map(mp => <option key={mp}>{mp}</option>)}
        </select>
        <button type="submit" disabled={loading}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {loading ? "..." : "Search"}
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map((r) => (
          <ProductCard key={r.asin} {...r} marketplace={marketplace} />
        ))}
      </div>

      <NotificationToast />
    </main>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/app/page.tsx frontend/components/
git commit -m "feat: add search page, product cards, and screen notification toast"
```

---

### Task 15: Best Sellers & Product Finder Pages

**Files:**
- Create: `frontend/app/best-sellers/page.tsx`
- Create: `frontend/app/finder/page.tsx`
- Create: `frontend/app/layout.tsx` (nav)

**Step 1: Update `frontend/app/layout.tsx` with navigation**

```tsx
import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = { title: "Amazon Tracker" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="border-b px-6 py-3 flex gap-6 text-sm font-medium">
          <Link href="/" className="text-blue-600">Search</Link>
          <Link href="/best-sellers" className="hover:text-blue-600">Best Sellers</Link>
          <Link href="/finder" className="hover:text-blue-600">Product Finder</Link>
          <Link href="/alerts" className="hover:text-blue-600">Alerts</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
```

**Step 2: Create `frontend/app/best-sellers/page.tsx`**

```tsx
"use client";
import { useState, useEffect } from "react";
import { getBestSellers } from "@/lib/api";
import Link from "next/link";

const CATEGORIES = ["Electronics", "Books", "Toys", "Kitchen", "Sports", "Clothing", "Home", "Beauty"];
const MARKETPLACES = ["US", "GB", "DE", "FR", "IT", "ES", "CA", "JP", "AU"];

export default function BestSellersPage() {
  const [category, setCategory] = useState("Electronics");
  const [marketplace, setMarketplace] = useState("US");
  const [asins, setAsins] = useState<string[]>([]);

  useEffect(() => {
    getBestSellers(category, marketplace).then(d => setAsins(d.asins || []));
  }, [category, marketplace]);

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Best Sellers</h1>
      <div className="flex gap-3 mb-6">
        <select value={category} onChange={e => setCategory(e.target.value)} className="border rounded px-3 py-1 text-sm">
          {CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <select value={marketplace} onChange={e => setMarketplace(e.target.value)} className="border rounded px-3 py-1 text-sm">
          {MARKETPLACES.map(m => <option key={m}>{m}</option>)}
        </select>
      </div>
      <ol className="space-y-2">
        {asins.map((asin, i) => (
          <li key={asin} className="flex items-center gap-3 border rounded p-3 hover:bg-gray-50">
            <span className="text-gray-400 w-6 text-right">{i + 1}.</span>
            <Link href={`/product/${asin}?marketplace=${marketplace}`} className="text-blue-600 font-mono text-sm hover:underline">
              {asin}
            </Link>
          </li>
        ))}
      </ol>
    </main>
  );
}
```

**Step 3: Create `frontend/app/finder/page.tsx`**

```tsx
"use client";
import { useState } from "react";
import { findProducts } from "@/lib/api";
import ProductCard from "@/components/ProductCard";

const MARKETPLACES = ["US", "GB", "DE", "FR", "IT", "ES", "CA", "JP", "AU"];
const CATEGORIES = ["All", "Electronics", "Books", "Toys", "Kitchen", "Sports", "Clothing"];

export default function FinderPage() {
  const [q, setQ] = useState("");
  const [marketplace, setMarketplace] = useState("US");
  const [category, setCategory] = useState("All");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await findProducts({
        q, marketplace, category,
        min_price: minPrice ? parseFloat(minPrice) : undefined,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
      });
      setResults(data);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Product Finder</h1>
      <form onSubmit={handleSearch} className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        <input placeholder="Keywords" value={q} onChange={e => setQ(e.target.value)}
          className="col-span-2 md:col-span-3 border rounded px-3 py-2 text-sm" required />
        <select value={marketplace} onChange={e => setMarketplace(e.target.value)} className="border rounded px-3 py-1 text-sm">
          {MARKETPLACES.map(m => <option key={m}>{m}</option>)}
        </select>
        <select value={category} onChange={e => setCategory(e.target.value)} className="border rounded px-3 py-1 text-sm">
          {CATEGORIES.map(c => <option key={c}>{c}</option>)}
        </select>
        <div className="flex gap-1">
          <input placeholder="Min $" type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)}
            className="border rounded px-2 py-1 text-sm w-full" />
          <input placeholder="Max $" type="number" value={maxPrice} onChange={e => setMaxPrice(e.target.value)}
            className="border rounded px-2 py-1 text-sm w-full" />
        </div>
        <button type="submit" disabled={loading}
          className="col-span-2 md:col-span-3 bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
          {loading ? "Searching..." : "Find Products"}
        </button>
      </form>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {results.map(r => <ProductCard key={r.asin} {...r} marketplace={marketplace} />)}
      </div>
    </main>
  );
}
```

**Step 4: Commit**

```bash
git add frontend/app/
git commit -m "feat: add best sellers, product finder pages and nav layout"
```

---

## Phase 5 — Docker & Polish

### Task 16: Frontend Dockerfile & docker-compose final

**Files:**
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.yml`
- Create: `.env.example` (already done in Task 1)

**Step 1: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

**Step 2: Verify full stack starts**

```bash
cd "C:\Users\edvinas.giniotis\CLAUDE\A tool"
docker-compose up --build -d
# Wait ~30s for all services to start
curl http://localhost:8000/health
# Expected: {"status":"ok"}
# Open http://localhost:3000 in browser — search page should load
```

**Step 3: Run all backend tests**

```bash
docker-compose exec backend pytest tests/ -v
# Expected: all PASS
```

**Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete MVP — Amazon tracker with price history, alerts, product finder, best sellers"
```

---

## Verification Checklist

- [ ] `docker-compose up` starts all 5 services without errors
- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] Search "wireless headphones" on US marketplace returns results
- [ ] Clicking a product shows price history chart with shipping overlay
- [ ] Marketplace comparison table shows all available marketplaces sorted by total price
- [ ] Creating an alert saves to DB and appears in alerts list
- [ ] Celery worker runs `run_check_alerts` task (visible in Celery logs)
- [ ] WebSocket connects and screen toast appears when alert triggers
- [ ] Best Sellers page loads ASINs for Electronics/US
- [ ] Product Finder with price filter returns filtered results

---

## Environment Setup Notes

Before running, populate `.env` from `.env.example`:
1. **Keepa API key** — get at keepa.com/api (paid, starts ~$17/mo)
2. **Amazon PA API** — requires Amazon Associates account (free with affiliate signup)
3. **Telegram Bot** — create via @BotFather on Telegram
4. **VAPID keys** — generate with: `python -c "from py_vapid import Vapid; v=Vapid(); v.generate_keys(); print(v.private_key, v.public_key)"`
5. **Gmail SMTP** — use App Password (not main password) with 2FA enabled
