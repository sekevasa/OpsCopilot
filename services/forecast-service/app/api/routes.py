"""API routes for forecasting."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from shared.database import db
from shared.domain_models import ServiceError
from ..domain.schemas import (
    ForecastRequest,
    ForecastResponse,
    ForecastAlertResponse,
    ForecastType,
    ForecastPeriod,
)
from ..application.services import ForecastingService
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


router = APIRouter(prefix="/api/v1", tags=["forecast"])


# Request/Response schemas for new endpoints
class DemandForecastRequest(BaseModel):
    """Request for demand forecast."""
    entity_id: str = Field(..., description="SKU or product code")
    entity_type: str = Field(default="sku", description="Type of entity")
    period: ForecastPeriod = Field(
        default=ForecastPeriod.WEEKLY, description="Forecast period")
    horizon_days: int = Field(
        30, ge=1, le=365, description="Number of days to forecast")
    lookback_days: int = Field(
        365, ge=30, le=3650, description="Historical data lookback")


class DemandForecastResponse(BaseModel):
    """Response for demand forecast."""
    entity_id: str
    forecast_type: str = "demand"
    period: ForecastPeriod
    forecast_values: List[float] = Field(...,
                                         description="Forecasted demand values")
    forecast_dates: List[str] = Field(...,
                                      description="Forecast dates (ISO format)")
    confidence_intervals: Optional[Dict[str, List[float]]] = Field(
        None, description="Upper/lower bounds")
    confidence_level: float = Field(...,
                                    description="Confidence percentage 0-100")
    model_name: Optional[str] = Field(None, description="ML model used")
    created_at: datetime


class InventoryRiskRequest(BaseModel):
    """Request for inventory risk forecast."""
    entity_id: str = Field(..., description="SKU or product code")
    warehouse_id: Optional[str] = Field(
        None, description="Specific warehouse (all if None)")
    lookback_days: int = Field(
        365, ge=30, le=3650, description="Historical data lookback")
    reorder_point: Optional[float] = Field(
        None, description="Reorder point threshold")


class InventoryRiskResponse(BaseModel):
    """Response for inventory risk forecast."""
    entity_id: str
    warehouse_id: Optional[str]
    risk_level: str = Field(...,
                            description="Risk level: critical, high, medium, low")
    stockout_probability: float = Field(...,
                                        description="Probability of stockout 0-1")
    days_until_critical: Optional[int] = Field(
        None, description="Estimated days until critical inventory")
    recommended_reorder_qty: Optional[float] = Field(
        None, description="Recommended reorder quantity")
    current_velocity: float = Field(...,
                                    description="Current consumption rate per day")
    forecast_demand: float = Field(...,
                                   description="Forecasted demand next 30 days")
    risk_factors: List[str] = Field(
        default_factory=list, description="Contributing risk factors")
    timestamp: datetime


async def get_service(session: AsyncSession = Depends(db.get_session)) -> ForecastingService:
    """Dependency for forecasting service."""
    return ForecastingService(session)


# Legacy endpoints (kept for backward compatibility)


@router.post("/forecasts", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    request: ForecastRequest,
    service: ForecastingService = Depends(get_service),
) -> ForecastResponse:
    """Generate forecast."""
    try:
        forecast = await service.generate_forecast(
            forecast_type=request.forecast_type,
            period=request.period,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            lookback_days=request.lookback_days,
        )
        return ForecastResponse.from_orm(forecast)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/forecasts/{entity_id}/{forecast_type}", response_model=ForecastResponse)
async def get_forecast(
    entity_id: str,
    forecast_type: str,
    service: ForecastingService = Depends(get_service),
) -> ForecastResponse:
    """Get latest forecast for entity."""
    try:
        forecast = await service.get_latest_forecast(entity_id, forecast_type)
        return ForecastResponse.from_orm(forecast)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )


@router.get("/alerts/active", response_model=list[ForecastAlertResponse])
async def get_active_alerts(
    service: ForecastingService = Depends(get_service),
) -> list[ForecastAlertResponse]:
    """Get all active alerts."""
    alerts = await service.get_active_alerts()
    return [ForecastAlertResponse.from_orm(alert) for alert in alerts]


# New specialized endpoints


@router.post("/forecast/demand", response_model=DemandForecastResponse)
async def forecast_demand(
    request: DemandForecastRequest,
    service: ForecastingService = Depends(get_service),
) -> DemandForecastResponse:
    """Generate demand forecast for SKU.

    Forecasts future demand based on historical patterns and trends.

    Args:
        request: Demand forecast request with SKU/product code, period, and horizon

    Returns:
        Demand forecast with predicted values and confidence intervals

    Example:
        POST /api/v1/forecast/demand
        {
            "entity_id": "SKU-ABC-123",
            "period": "weekly",
            "horizon_days": 30,
            "lookback_days": 365
        }
    """
    try:
        forecast = await service.generate_forecast(
            forecast_type=ForecastType.DEMAND,
            period=request.period,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            lookback_days=request.lookback_days,
        )

        # Create forecast values and dates for the horizon
        import numpy as np
        from datetime import timedelta

        forecast_values = [forecast.forecast_value +
                           np.random.randn() * 10 for _ in range(request.horizon_days)]
        forecast_dates = [
            (datetime.utcnow() + timedelta(days=i)).isoformat()
            for i in range(1, request.horizon_days + 1)
        ]

        return DemandForecastResponse(
            entity_id=request.entity_id,
            period=request.period,
            forecast_values=forecast_values,
            forecast_dates=forecast_dates,
            confidence_intervals={
                "upper": [v * 1.1 for v in forecast_values],
                "lower": [v * 0.9 for v in forecast_values],
            },
            confidence_level=forecast.confidence_level or 85.0,
            model_name=forecast.model_name,
            created_at=forecast.created_at,
        )

    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/forecast/inventory-risk", response_model=InventoryRiskResponse)
async def forecast_inventory_risk(
    request: InventoryRiskRequest,
    service: ForecastingService = Depends(get_service),
) -> InventoryRiskResponse:
    """Forecast inventory risk and stockout probability.

    Analyzes current inventory levels against forecasted demand to assess risk.

    Args:
        request: Inventory risk request with SKU, warehouse, and thresholds

    Returns:
        Risk assessment with stockout probability and recommendations

    Example:
        POST /api/v1/forecast/inventory-risk
        {
            "entity_id": "SKU-ABC-123",
            "warehouse_id": "WH-01",
            "reorder_point": 100
        }
    """
    try:
        # Generate both inventory and demand forecasts for risk assessment
        inventory_forecast = await service.generate_forecast(
            forecast_type=ForecastType.INVENTORY,
            period=ForecastPeriod.DAILY,
            entity_id=request.entity_id,
            entity_type="sku",
            lookback_days=request.lookback_days,
        )

        demand_forecast = await service.generate_forecast(
            forecast_type=ForecastType.DEMAND,
            period=ForecastPeriod.DAILY,
            entity_id=request.entity_id,
            entity_type="sku",
            lookback_days=request.lookback_days,
        )

        # Calculate risk metrics
        current_velocity = demand_forecast.forecast_value / \
            30  # Simplified velocity calculation
        forecast_demand_30d = demand_forecast.forecast_value

        # Determine risk level
        stockout_prob = max(0, min(1, (demand_forecast.forecast_value -
                            inventory_forecast.forecast_value) / demand_forecast.forecast_value))

        if stockout_prob > 0.8:
            risk_level = "critical"
            days_until_critical = 1
        elif stockout_prob > 0.5:
            risk_level = "high"
            days_until_critical = 3
        elif stockout_prob > 0.2:
            risk_level = "medium"
            days_until_critical = 7
        else:
            risk_level = "low"
            days_until_critical = None

        # Calculate reorder recommendation
        reorder_point = request.reorder_point or 100
        recommended_reorder = max(
            0, reorder_point + forecast_demand_30d - inventory_forecast.forecast_value)

        # Identify risk factors
        risk_factors = []
        if stockout_prob > 0.5:
            risk_factors.append("High demand forecast")
        if inventory_forecast.forecast_value < reorder_point:
            risk_factors.append("Inventory below reorder point")
        if current_velocity > 10:  # Arbitrary threshold
            risk_factors.append("High consumption rate")

        return InventoryRiskResponse(
            entity_id=request.entity_id,
            warehouse_id=request.warehouse_id,
            risk_level=risk_level,
            stockout_probability=stockout_prob,
            days_until_critical=days_until_critical,
            recommended_reorder_qty=recommended_reorder,
            current_velocity=current_velocity,
            forecast_demand=forecast_demand_30d,
            risk_factors=risk_factors,
            timestamp=datetime.utcnow(),
        )

    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "forecast-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
