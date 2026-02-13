"""Domain models for data ingest service - staging schema."""

from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from shared.database import Base
from shared.domain_models import DataSourceType, IngestionStatus


class StagingData(Base):
    """Raw data staging table - holds unprocessed data from sources."""

    __tablename__ = "staging_data"
    __table_args__ = {"schema": "staging"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True)
    batch_id = Column(PG_UUID(as_uuid=True), index=True, nullable=False)
    source_type = Column(SQLEnum(DataSourceType), nullable=False)
    source_id = Column(String(255), nullable=False)
    record_number = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    transformation_status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class IngestionJob(Base):
    """Ingestion job tracking - one job per sync run."""

    __tablename__ = "ingestion_jobs"
    __table_args__ = {"schema": "staging"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True)
    job_reference = Column(String(255), unique=True,
                           nullable=False, index=True)
    source_type = Column(SQLEnum(DataSourceType), nullable=False)
    source_id = Column(String(255), nullable=False)
    status = Column(SQLEnum(IngestionStatus),
                    default=IngestionStatus.PENDING, nullable=False)

    total_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    job_metadata = Column(JSON, nullable=True)
    error_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class DataConnectorConfig(Base):
    """Configuration for data connectors."""

    __tablename__ = "connector_configs"
    __table_args__ = {"schema": "staging"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True)
    connector_name = Column(String(100), unique=True,
                            nullable=False, index=True)
    source_type = Column(SQLEnum(DataSourceType), nullable=False)

    connection_string = Column(Text, nullable=False)
    auth_credentials = Column(JSON, nullable=True)
    connection_timeout_seconds = Column(Integer, default=30)

    is_active = Column(Boolean, default=True)
    last_sync_timestamp = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


# Legacy audit trail table for compatibility
class PriMasterAudit(Base):
    """Audit trail for data modifications."""

    __tablename__ = "prim_master_audits"
    __table_args__ = {"schema": "staging"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    batch_id = Column(PG_UUID(as_uuid=True), nullable=False)
    operation = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(255), nullable=False)

    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class RawDataBatch(Base):
    """Raw data batch - represents a batch of ingest data."""

    __tablename__ = "raw_data_batches"
    __table_args__ = {"schema": "staging"}

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True)
    batch_reference = Column(String(255), unique=True,
                             nullable=False, index=True)
    source_type = Column(SQLEnum(DataSourceType), nullable=False)
    source_id = Column(String(255), nullable=False)
    status = Column(SQLEnum(IngestionStatus),
                    default=IngestionStatus.PENDING, nullable=False)
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
