"""Pydantic schemas for API requests/responses."""

from datetime import datetime
from typing import Optional, Any, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field
from shared.domain_models import DataSourceType, IngestionStatus


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SyncRunRequest(BaseModel):
    """Request to start a sync run."""

    source_type: DataSourceType = Field(..., description="Type of data source")
    source_id: str = Field(..., description="External system identifier")
    connector_name: Optional[str] = Field(
        None, description="Named connector config")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata")


class SyncDataRequest(BaseModel):
    """Request with raw data to sync."""

    records: List[Dict[str, Any]
                  ] = Field(..., description="List of records to ingest")
    entity_type: Optional[str] = Field(
        None, description="Type of entity (sku, inventory, etc)")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class IngestionJobResponse(BaseModel):
    """Response for ingestion job."""

    id: UUID
    job_reference: str
    source_type: DataSourceType
    source_id: str
    status: IngestionStatus
    total_records: int
    successful_records: int
    failed_records: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SyncStatusResponse(BaseModel):
    """Response for sync status check."""

    job_id: UUID
    status: IngestionStatus
    progress: float = Field(..., ge=0, le=100,
                            description="Progress percentage")
    total_records: int
    successful_records: int
    failed_records: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SyncStartResponse(BaseModel):
    """Response when sync is started."""

    job_id: UUID
    job_reference: str
    status: IngestionStatus
    message: str


class StagingDataResponse(BaseModel):
    """Response for staging data record."""

    id: UUID
    batch_id: UUID
    record_number: int
    raw_data: Dict[str, Any]
    transformation_status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConnectorConfigResponse(BaseModel):
    """Response for connector configuration."""

    id: UUID
    connector_name: str
    source_type: DataSourceType
    is_active: bool
    last_sync_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(...,
                        description="Service status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime
    database: str = Field("unknown", description="Database connection status")


# Legacy schemas for compatibility

class IngestRequest(BaseModel):
    """Legacy: Request to ingest data."""

    source_type: DataSourceType
    source_id: str = Field(..., description="External system identifier")
    batch_reference: str = Field(...,
                                 description="Unique batch reference from source")
    data: Dict[str, Any] = Field(..., description="Raw data payload")


class RawDataBatchResponse(BaseModel):
    """Legacy: Response for raw data batch."""

    id: UUID
    source_type: DataSourceType
    source_id: str
    batch_reference: str
    status: IngestionStatus
    record_count: int
    ingested_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class IngestionResponse(BaseModel):
    """Legacy: Response to ingestion request."""

    batch_id: UUID
    status: IngestionStatus
    message: str
