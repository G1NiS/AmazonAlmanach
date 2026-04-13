from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.products import router as products_router
from api.alerts import router as alerts_router
from api.best_sellers import router as best_sellers_router
from api.product_finder import router as product_finder_router

app = FastAPI(title="AmazonAlmanach API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(products_router)
app.include_router(alerts_router)
app.include_router(best_sellers_router)
app.include_router(product_finder_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
