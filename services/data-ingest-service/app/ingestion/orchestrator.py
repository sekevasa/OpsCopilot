"""Core ingestion service and orchestration."""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime

from shared.domain_models import DataSourceType, IngestionStatus, ServiceError
from app.domain.models import IngestionJob, StagingData
from app.domain.repositories import IngestionJobRepository, StagingDataRepository

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Orchestrates the ingestion process - fetch, transform, load."""

    def __init__(
        self,
        job_repo: IngestionJobRepository,
        staging_repo: StagingDataRepository,
    ):
        """Initialize orchestrator.

        Args:
            job_repo: Ingestion job repository
            staging_repo: Staging data repository
        """
        self.job_repo = job_repo
        self.staging_repo = staging_repo

    async def start_ingestion_job(
        self,
        source_type: DataSourceType,
        source_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """Start a new ingestion job.

        Args:
            source_type: Type of data source
            source_id: External system identifier
            metadata: Optional metadata

        Returns:
            Job ID
        """
        job_reference = f"{source_type.value}_{source_id}_{datetime.utcnow().timestamp()}"

        job = IngestionJob(
            id=uuid4(),
            job_reference=job_reference,
            source_type=source_type,
            source_id=source_id,
            status=IngestionStatus.PENDING,
            metadata=metadata,
        )

        created_job = await self.job_repo.create(job)
        logger.info(f"Started ingestion job: {created_job.id}")
        return created_job.id

    async def process_job(
        self,
        job_id: UUID,
        raw_records: List[Dict[str, Any]],
    ) -> None:
        """Process ingestion job with raw records.

        Args:
            job_id: Job ID
            raw_records: List of raw data records
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ServiceError("JOB_NOT_FOUND", f"Job {job_id} not found")

        # Update job status
        job.status = IngestionStatus.PROCESSING
        job.started_at = datetime.utcnow()
        job.total_records = len(raw_records)
        await self.job_repo.update(job)

        logger.info(f"Processing {len(raw_records)} records for job {job_id}")

        successful = 0
        failed = 0
        errors = []

        # Store records in staging
        for idx, record in enumerate(raw_records, 1):
            try:
                staging = StagingData(
                    id=uuid4(),
                    batch_id=job_id,
                    source_type=job.source_type,
                    source_id=job.source_id,
                    record_number=idx,
                    raw_data=record,
                    transformation_status="pending",
                )
                await self.staging_repo.create(staging)
                successful += 1
            except Exception as e:
                failed += 1
                error_msg = str(e)
                errors.append(f"Record {idx}: {error_msg}")
                logger.error(f"Failed to store record {idx}: {error_msg}")

        # Update job with results
        job.successful_records = successful
        job.failed_records = failed
        job.status = (
            IngestionStatus.COMPLETED if failed == 0
            else IngestionStatus.PARTIALLY_FAILED
        )
        job.completed_at = datetime.utcnow()
        if errors:
            job.error_summary = "\n".join(errors[:100])  # First 100 errors

        await self.job_repo.update(job)
        logger.info(
            f"Job {job_id} completed: {successful} successful, {failed} failed")

    async def get_job_status(self, job_id: UUID) -> Optional[IngestionJob]:
        """Get current job status.

        Args:
            job_id: Job ID

        Returns:
            Job details or None
        """
        return await self.job_repo.get_by_id(job_id)

    async def get_staging_records(
        self,
        job_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StagingData]:
        """Get staging records for a job.

        Args:
            job_id: Job ID
            skip: Number to skip
            limit: Maximum records

        Returns:
            List of staging records
        """
        return await self.staging_repo.get_by_batch(job_id, skip, limit)

    async def mark_records_transformed(self, job_id: UUID) -> int:
        """Mark all records as transformed for a job.

        Args:
            job_id: Job ID

        Returns:
            Number of records updated
        """
        logger.info(f"Marking records as transformed for job {job_id}")
        # Implementation would update transformation_status in batch
        return 0
