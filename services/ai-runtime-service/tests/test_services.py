"""Tests for AI runtime service."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.application.services import AIRuntimeService
from shared.database import Base
from shared.domain_models import ServiceError


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
async def test_register_model(test_db):
    """Test registering AI model."""
    service = AIRuntimeService(test_db)

    model = await service.register_model(
        name="test-model",
        version="1.0.0",
        model_type="linear_regression",
    )

    assert model.name == "test-model"
    assert model.version == "1.0.0"


@pytest.mark.asyncio
async def test_duplicate_model_fails(test_db):
    """Test duplicate model registration fails."""
    service = AIRuntimeService(test_db)

    await service.register_model(
        name="test-model",
        version="1.0.0",
        model_type="linear_regression",
    )

    with pytest.raises(ServiceError) as exc_info:
        await service.register_model(
            name="test-model",
            version="1.0.1",
            model_type="linear_regression",
        )

    assert exc_info.value.code == "DUPLICATE"


@pytest.mark.asyncio
async def test_run_inference(test_db):
    """Test running inference."""
    service = AIRuntimeService(test_db)

    model = await service.register_model(
        name="test-model",
        version="1.0.0",
        model_type="linear_regression",
    )

    job = await service.run_inference(
        model_name="test-model",
        input_data={"feature1": 10, "feature2": 20},
    )

    assert job.output_data is not None
    assert "prediction" in job.output_data
