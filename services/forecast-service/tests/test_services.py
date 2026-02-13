"""Tests for forecast service."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.domain.models import ForecastType, ForecastPeriod
from app.application.services import ForecastingService
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
async def test_generate_forecast(test_db):
    """Test generating forecast."""
    service = ForecastingService(test_db)

    forecast = await service.generate_forecast(
        forecast_type=ForecastType.DEMAND,
        period=ForecastPeriod.MONTHLY,
        entity_id="ITEM-001",
        entity_type="item",
    )

    assert forecast.forecast_value > 0
    assert forecast.confidence_level > 0
    assert forecast.model_name is not None


@pytest.mark.asyncio
async def test_get_latest_forecast(test_db):
    """Test getting latest forecast."""
    service = ForecastingService(test_db)

    # Create forecast
    created = await service.generate_forecast(
        forecast_type=ForecastType.DEMAND,
        period=ForecastPeriod.MONTHLY,
        entity_id="ITEM-002",
        entity_type="item",
    )

    # Retrieve forecast
    retrieved = await service.get_latest_forecast("ITEM-002", "demand")

    assert retrieved.id == created.id
