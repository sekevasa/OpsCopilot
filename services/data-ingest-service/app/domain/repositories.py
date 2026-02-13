"""Repositories for data ingest service - staging layer."""

from .models import RawDataBatch
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.repository import BaseRepository
from shared.domain_models import DataSourceType, IngestionStatus
from .models import IngestionJob, StagingData, DataConnectorConfig


class IngestionJobRepository(BaseRepository[IngestionJob]):
    """Repository for ingestion jobs."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, IngestionJob)

    async def get_by_reference(self, job_reference: str) -> Optional[IngestionJob]:
        """Get job by reference."""
        stmt = select(IngestionJob).where(
            IngestionJob.job_reference == job_reference)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_jobs(self) -> List[IngestionJob]:
        """Get all pending ingestion jobs."""
        stmt = select(IngestionJob).where(
            IngestionJob.status == IngestionStatus.PENDING
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_source(
        self,
        source_type: DataSourceType,
        source_id: str,
    ) -> List[IngestionJob]:
        """Get jobs by source."""
        stmt = select(IngestionJob).where(
            (IngestionJob.source_type == source_type) &
            (IngestionJob.source_id == source_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class StagingDataRepository(BaseRepository[StagingData]):
    """Repository for staging data."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, StagingData)

    async def get_by_batch(
        self,
        batch_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StagingData]:
        """Get staging records for a batch."""
        stmt = select(StagingData).where(
            StagingData.batch_id == batch_id
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_records(
        self,
        batch_id: UUID,
    ) -> List[StagingData]:
        """Get pending records for transformation."""
        stmt = select(StagingData).where(
            (StagingData.batch_id == batch_id) &
            (StagingData.transformation_status == "pending")
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_batch(self, batch_id: UUID) -> int:
        """Count records in a batch."""
        stmt = select(func.count(StagingData.id)).where(
            StagingData.batch_id == batch_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class DataConnectorConfigRepository(BaseRepository[DataConnectorConfig]):
    """Repository for connector configurations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, DataConnectorConfig)

    async def get_by_name(self, connector_name: str) -> Optional[DataConnectorConfig]:
        """Get connector config by name."""
        stmt = select(DataConnectorConfig).where(
            DataConnectorConfig.connector_name == connector_name
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_connectors(self) -> List[DataConnectorConfig]:
        """Get all active connectors."""
        stmt = select(DataConnectorConfig).where(
            DataConnectorConfig.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()


# Legacy for compatibility


class RawDataBatchRepository(BaseRepository[RawDataBatch]):
    """Legacy repository - for compatibility."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, RawDataBatch)

    async def get_by_batch_reference(self, batch_reference: str) -> Optional[RawDataBatch]:
        """Get batch by reference."""
        stmt = select(RawDataBatch).where(
            RawDataBatch.batch_reference == batch_reference)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_batches(self) -> List[RawDataBatch]:
        """Get all pending batches for processing."""
        stmt = select(RawDataBatch).where(
            RawDataBatch.status == IngestionStatus.PENDING)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_source(self, source_type: str, source_id: str) -> List[RawDataBatch]:
        """Get batches by source."""
        stmt = select(RawDataBatch).where(
            (RawDataBatch.source_type == DataSourceType(source_type)) &
            (RawDataBatch.source_id == source_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
