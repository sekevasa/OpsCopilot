"""Domain models for AI runtime."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from shared.database import Base


class ModelStatus(str, Enum):
    """Status of AI model."""
    AVAILABLE = "available"
    TRAINING = "training"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class InferenceStatus(str, Enum):
    """Status of inference execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AIModel(Base):
    """AI/ML model definition."""

    __tablename__ = "ai_models"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    version = Column(String(50), nullable=False)
    # linear_regression, xgboost, etc.
    model_type = Column(String(100), nullable=False)
    status = Column(String(50), default=ModelStatus.AVAILABLE)

    # Model metadata
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)

    # Performance metrics
    accuracy_score = Column(Float, nullable=True)
    last_trained = Column(DateTime, nullable=True)

    # Model location
    model_path = Column(String(1000), nullable=True)
    model_checksum = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class InferenceJob(Base):
    """Inference execution job."""

    __tablename__ = "inference_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    model_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    model_name = Column(String(255), nullable=False)

    status = Column(String(50), default=InferenceStatus.PENDING)

    # Input/output
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)

    # Execution metadata
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
