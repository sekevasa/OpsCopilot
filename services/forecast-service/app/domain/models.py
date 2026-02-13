"""Domain models for forecasting."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, String, Float, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from shared.database import Base


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


class Forecast(Base):
    """Forecast prediction."""

    __tablename__ = "forecasts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    forecast_type = Column(String(50), nullable=False, index=True)
    period = Column(String(50), nullable=False)

    # Entity being forecasted
    entity_id = Column(String(255), nullable=False, index=True)
    # item, warehouse, process, etc.
    entity_type = Column(String(100), nullable=False)

    # Forecast values
    forecast_value = Column(Float, nullable=False)
    forecast_lower_bound = Column(Float, nullable=True)
    forecast_upper_bound = Column(Float, nullable=True)
    confidence_level = Column(Float, nullable=True)

    # Metadata
    forecast_date = Column(DateTime, nullable=False, index=True)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)

    model_name = Column(String(255), nullable=True)
    model_version = Column(String(50), nullable=True)

    # Accuracy after actual data arrives
    actual_value = Column(Float, nullable=True)
    accuracy_error = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class ForecastAlert(Base):
    """Alert triggered by forecast."""

    __tablename__ = "forecast_alerts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    forecast_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)

    # stockout_risk, demand_spike, etc.
    alert_type = Column(String(100), nullable=False)
    # low, medium, high, critical
    severity = Column(String(50), nullable=False)

    description = Column(String, nullable=False)
    recommended_action = Column(String, nullable=True)

    # Alert metadata
    threshold_value = Column(Float, nullable=True)
    forecast_value = Column(Float, nullable=True)

    # pending, acknowledged, resolved
    acknowledged = Column(String(50), default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
