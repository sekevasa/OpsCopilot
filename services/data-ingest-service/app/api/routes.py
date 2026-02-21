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
from ..connectors.tally.models import (
    TallyConnectorConfig,
    TallyConnectionConfig,
    TallyDataType,
    TallySyncMode,
    TallySyncRequest,
    TallySyncResponse,
    TallySyncStats,
)
from ..connectors.tally.tally_connector import TallyConnector
from datetime import datetime
from uuid import UUID, uuid4


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


# ============================================================================
# TALLY CONNECTOR ENDPOINTS
# ============================================================================

@router.post(
    "/tally/validate",
    status_code=status.HTTP_200_OK,
    summary="Validate a Tally connector configuration",
)
async def validate_tally_config(config: TallyConnectorConfig) -> dict:
    """
    Validate a Tally connector configuration by attempting a connection.

    Sends a ping to the configured Tally server and returns the result
    without persisting any data.
    """
    connector = TallyConnector(config)
    try:
        connected = await connector.connect()
        if connected:
            return {"status": "ok", "message": "Successfully connected to Tally"}
        return {"status": "error", "message": "Could not connect to Tally"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TALLY_CONNECTION_FAILED", "message": str(exc)},
        )
    finally:
        await connector.disconnect()


@router.post(
    "/tally/sync",
    response_model=TallySyncResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a Tally sync operation",
)
async def trigger_tally_sync(request: TallySyncRequest) -> TallySyncResponse:
    """
    Trigger a Tally data sync operation.

    Connects to the Tally server, extracts and transforms the requested
    data types, and returns a job summary.  The sync runs synchronously
    within the request; for large datasets consider running it as a
    background task.
    """
    # Build a minimal connector config from the sync request
    # In production this would be loaded from the database by connector_name
    connection_config = TallyConnectionConfig()  # defaults to localhost:9000
    connector_config = TallyConnectorConfig(
        connector_name=request.connector_name,
        connection=connection_config,
        enabled_data_types=request.data_types or [],
        sync_mode=request.sync_mode or TallySyncMode.INCREMENTAL,
    )

    connector = TallyConnector(connector_config)
    try:
        await connector.connect()
        result = await connector.sync(
            sync_mode=request.sync_mode,
            from_date=request.from_date,
            to_date=request.to_date,
            data_types=request.data_types,
        )
        raw_stats = result.get("stats", {})
        by_type = raw_stats.get("by_type", {})
        stats = TallySyncStats(
            total_masters=by_type.get("item", 0) + by_type.get("party", 0),
            total_ledgers=by_type.get("ledger", 0),
            total_vouchers=by_type.get("transaction", 0),
            total_inventory_records=(
                by_type.get("inventory_movement", 0) + by_type.get("stock_balance", 0)
            ),
            duration_seconds=raw_stats.get("duration_seconds", 0.0),
        )
        return TallySyncResponse(
            job_id=uuid4(),
            connector_name=request.connector_name,
            status="COMPLETED",
            message=f"Sync completed – {raw_stats.get('total_records', 0)} records",
            sync_mode=request.sync_mode
            or connector_config.sync_mode,
            stats=stats,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "TALLY_SYNC_FAILED", "message": str(exc)},
        )
    finally:
        await connector.disconnect()
