import pytest
from models.product import Product
from models.price_history import PriceHistory
from models.user import User
from models.alert import Alert


def test_product_tablename():
    assert Product.__tablename__ == "products"


def test_price_history_tablename():
    assert PriceHistory.__tablename__ == "price_history"


def test_user_tablename():
    assert User.__tablename__ == "users"


def test_alert_tablename():
    assert Alert.__tablename__ == "alerts"


def test_price_history_has_composite_index():
    index_names = [idx.name for idx in PriceHistory.__table__.indexes]
    assert "ix_price_history_asin_marketplace_ts" in index_names


def test_alert_has_active_field():
    col = Alert.__table__.c["active"]
    assert col is not None
