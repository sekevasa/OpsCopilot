"""Schemas for forecast API."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class ForecastType(str, Enum):
    """Type of forecast."""
    DEMAND = "demand"
    INVENTORY = "inventory"
    SUPPLY = "supply"
    QUALITY = "quality"


class ForecastPeriod(str, Enum):
    """Forecast time period."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ForecastRequest(BaseModel):
    """Request to generate forecast."""

    forecast_type: ForecastType
    period: ForecastPeriod
    entity_id: str = Field(..., description="Entity to forecast")
    entity_type: str = Field(...,
                             description="Type of entity (item, warehouse, etc.)")
    lookback_days: int = Field(
        365, ge=30, le=3650, description="Days of history to use")


class ForecastResponse(BaseModel):
    """Response for forecast."""

    id: UUID
    forecast_type: ForecastType
    period: ForecastPeriod
    entity_id: str
    forecast_value: float
    forecast_lower_bound: Optional[float]
    forecast_upper_bound: Optional[float]
    confidence_level: Optional[float]
    model_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastAlertResponse(BaseModel):
    """Response for forecast alert."""

    id: UUID
    forecast_id: UUID
    alert_type: str
    severity: str
    description: str
    recommended_action: Optional[str]
    acknowledged: str
    created_at: datetime

    class Config:
        from_attributes = True
