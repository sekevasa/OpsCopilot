"""Schemas for AI runtime API."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


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


class AIModelResponse(BaseModel):
    """Response for AI model."""

    id: UUID
    name: str
    version: str
    model_type: str
    status: ModelStatus
    accuracy_score: Optional[float]
    last_trained: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class InferenceRequest(BaseModel):
    """Request for inference."""

    model_name: str = Field(..., description="Name of model to use")
    input_data: Dict[str, Any] = Field(...,
                                       description="Input features for inference")
    timeout_seconds: int = Field(
        30, ge=1, le=300, description="Inference timeout")


class InferenceResponse(BaseModel):
    """Response for inference."""

    job_id: UUID
    model_name: str
    status: InferenceStatus
    output_data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
