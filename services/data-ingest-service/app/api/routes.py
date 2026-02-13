"""API routes for data ingestion service."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import db
from shared.domain_models import ServiceError
from ..domain.schemas import (
    SyncRunRequest,
    SyncStartResponse,
    SyncStatusResponse,
    IngestionJobResponse,
    HealthResponse,
)
from ..application.services import DataIngestionService
from ..ingestion.orchestrator import IngestionOrchestrator
from ..domain.repositories import IngestionJobRepository, StagingDataRepository
from datetime import datetime
from uuid import UUID


router = APIRouter(prefix="/api/v1", tags=["data-ingest"])


async def get_session() -> AsyncSession:
    """Get database session."""
    return db.get_session()


async def get_ingestion_service(
    session: AsyncSession = Depends(get_session),
) -> DataIngestionService:
    """Dependency for data ingestion service."""
    return DataIngestionService(session)


async def get_orchestrator(
    session: AsyncSession = Depends(get_session),
) -> IngestionOrchestrator:
    """Dependency for ingestion orchestrator."""
    job_repo = IngestionJobRepository(session)
    staging_repo = StagingDataRepository(session)
    return IngestionOrchestrator(job_repo, staging_repo)


# ============================================================================
# SYNC / INGESTION ENDPOINTS
# ============================================================================

@router.post(
    "/sync/run",
    response_model=SyncStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_sync(
    request: SyncRunRequest,
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
) -> SyncStartResponse:
    """
    Start a new sync run from a data source.

    Creates a new ingestion job and begins fetching data.
    Returns immediately with job ID for polling.
    """
    try:
        job_id = await orchestrator.start_ingestion_job(
            source_type=request.source_type,
            source_id=request.source_id,
            metadata=request.metadata,
        )

        return SyncStartResponse(
            job_id=job_id,
            job_reference=f"{request.source_type.value}_{request.source_id}",
            status="PENDING",
            message="Sync job started",
        )
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/sync/status/{job_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    job_id: UUID,
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
) -> SyncStatusResponse:
    """
    Get status of a sync job.

    Poll this endpoint to check progress of an ingestion job.
    """
    job = await orchestrator.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Calculate progress percentage
    progress = 0.0
    if job.total_records > 0:
        progress = ((job.successful_records + job.failed_records) /
                    job.total_records) * 100

    return SyncStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=progress,
        total_records=job.total_records,
        successful_records=job.successful_records,
        failed_records=job.failed_records,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/sync/job/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    job_id: UUID,
    orchestrator: IngestionOrchestrator = Depends(get_orchestrator),
) -> IngestionJobResponse:
    """Get detailed information about an ingestion job."""
    job = await orchestrator.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return IngestionJobResponse.from_orm(job)


# ============================================================================
# HEALTH & DIAGNOSTIC ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> HealthResponse:
    """Health check endpoint."""
    db_status = "connected"
    try:
        # Try a simple query
        await session.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="data-ingest-service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        database=db_status,
    )


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe for Kubernetes."""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check():
    """Liveness probe for Kubernetes."""
    return {"status": "alive"}
