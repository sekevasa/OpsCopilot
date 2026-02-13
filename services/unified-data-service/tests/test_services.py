"""Tests for unified data service."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.domain.models import ManufacturingItem
from app.application.services import DataNormalizationService
from shared.database import Base


@pytest.fixture
async def test_db():
    """Create in-memory test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session


@pytest.mark.asyncio
async def test_normalize_manufacturing_item(test_db):
    """Test normalizing manufacturing item."""
    service = DataNormalizationService(test_db)

    item = await service.normalize_manufacturing_item(
        sku="ITEM-001",
        name="Test Item",
        uom="EA",
        standard_cost=100.0,
    )

    assert item.sku == "ITEM-001"
    assert item.name == "Test Item"
    assert item.standard_cost == 100.0


@pytest.mark.asyncio
async def test_normalize_inventory(test_db):
    """Test normalizing inventory snapshot."""
    service = DataNormalizationService(test_db)

    item = await service.normalize_manufacturing_item(
        sku="ITEM-002",
        name="Inventory Test",
        uom="EA",
    )

    snapshot = await service.normalize_inventory_snapshot(
        item_id=item.id,
        warehouse_id="WH001",
        quantity_on_hand=100,
        quantity_reserved=10,
    )

    assert snapshot.quantity_on_hand == 100
    assert snapshot.quantity_available == 90
