"""Unit tests for data ingestion service."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.domain.models import RawDataBatch, DataSourceType, IngestionStatus
from app.domain.repositories import RawDataBatchRepository
from app.application.services import DataIngestionService
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
async def test_ingest_data(test_db):
    """Test data ingestion."""
    service = DataIngestionService(test_db)

    batch = await service.ingest_data(
        source_type=DataSourceType.ERP,
        source_id="erp_001",
        batch_reference="batch_001",
        data={"item": "value"},
    )

    assert batch.id is not None
    assert batch.source_type == DataSourceType.ERP
    assert batch.status == IngestionStatus.PENDING


@pytest.mark.asyncio
async def test_duplicate_batch_raises_error(test_db):
    """Test duplicate batch detection."""
    service = DataIngestionService(test_db)

    # First ingest
    await service.ingest_data(
        source_type=DataSourceType.ERP,
        source_id="erp_001",
        batch_reference="batch_001",
        data={"item": "value"},
    )

    # Duplicate should fail
    with pytest.raises(ServiceError) as exc_info:
        await service.ingest_data(
            source_type=DataSourceType.ERP,
            source_id="erp_001",
            batch_reference="batch_001",
            data={"item": "value"},
        )

    assert exc_info.value.code == "DUPLICATE_BATCH"


@pytest.mark.asyncio
async def test_mark_batch_success(test_db):
    """Test marking batch as success."""
    service = DataIngestionService(test_db)

    batch = await service.ingest_data(
        source_type=DataSourceType.ERP,
        source_id="erp_001",
        batch_reference="batch_001",
        data={"item": "value"},
    )

    updated = await service.mark_batch_success(batch.id)
    assert updated.status == IngestionStatus.SUCCESS
    assert updated.processed_at is not None
