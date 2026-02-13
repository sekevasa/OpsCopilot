"""Application services for data ingestion."""

import json
from uuid import UUID
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from shared.domain_models import ServiceError
from ..domain.models import RawDataBatch, IngestionStatus, DataSourceType
from ..domain.repositories import RawDataBatchRepository


class DataIngestionService:
    """Service for handling data ingestion operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = RawDataBatchRepository(session)

    async def ingest_data(
        self,
        source_type: DataSourceType,
        source_id: str,
        batch_reference: str,
        data: Dict[str, Any],
    ) -> RawDataBatch:
        """
        Ingest raw data from external source.

        Args:
            source_type: Type of data source
            source_id: External system ID
            batch_reference: Unique batch reference
            data: Raw data payload

        Returns:
            Created raw data batch

        Raises:
            ServiceError: If batch already exists
        """
        # Check for duplicates
        existing = await self.batch_repo.get_by_batch_reference(batch_reference)
        if existing:
            raise ServiceError(
                "DUPLICATE_BATCH",
                f"Batch {batch_reference} already exists",
                {"batch_reference": batch_reference}
            )

        # Create batch
        batch = RawDataBatch(
            source_type=source_type,
            source_id=source_id,
            batch_reference=batch_reference,
            status=IngestionStatus.PENDING,
            raw_data=json.dumps(data),
            record_count=len(data) if isinstance(data, (list, dict)) else 1,
        )

        batch = await self.batch_repo.create(batch)
        return batch

    async def get_batch_by_id(self, batch_id: UUID) -> RawDataBatch:
        """Get batch by ID."""
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise ServiceError(
                "NOT_FOUND",
                f"Batch {batch_id} not found",
                {"batch_id": str(batch_id)}
            )
        return batch

    async def get_pending_batches(self) -> list[RawDataBatch]:
        """Get all pending batches."""
        return await self.batch_repo.get_pending_batches()

    async def mark_batch_processing(self, batch_id: UUID) -> RawDataBatch:
        """Mark batch as in progress."""
        batch = await self.batch_repo.update(
            batch_id,
            {"status": IngestionStatus.IN_PROGRESS}
        )
        if not batch:
            raise ServiceError(
                "NOT_FOUND",
                f"Batch {batch_id} not found",
                {"batch_id": str(batch_id)}
            )
        return batch

    async def mark_batch_success(self, batch_id: UUID) -> RawDataBatch:
        """Mark batch as successfully processed."""
        batch = await self.batch_repo.update(
            batch_id,
            {
                "status": IngestionStatus.SUCCESS,
                "processed_at": datetime.utcnow(),
            }
        )
        if not batch:
            raise ServiceError(
                "NOT_FOUND",
                f"Batch {batch_id} not found",
                {"batch_id": str(batch_id)}
            )
        return batch

    async def mark_batch_failed(
        self,
        batch_id: UUID,
        error_message: str,
    ) -> RawDataBatch:
        """Mark batch as failed."""
        batch = await self.batch_repo.update(
            batch_id,
            {
                "status": IngestionStatus.FAILED,
                "error_message": error_message,
                "processed_at": datetime.utcnow(),
            }
        )
        if not batch:
            raise ServiceError(
                "NOT_FOUND",
                f"Batch {batch_id} not found",
                {"batch_id": str(batch_id)}
            )
        return batch
