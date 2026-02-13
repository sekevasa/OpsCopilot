"""Application services for forecasting."""

from uuid import UUID, uuid4
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from shared.domain_models import ServiceError
from ..domain.models import Forecast, ForecastAlert, ForecastType, ForecastPeriod
from ..domain.repositories import ForecastRepository, ForecastAlertRepository


class ForecastingService:
    """Service for generating and managing forecasts."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.forecast_repo = ForecastRepository(session)
        self.alert_repo = ForecastAlertRepository(session)

    async def generate_forecast(
        self,
        forecast_type: ForecastType,
        period: ForecastPeriod,
        entity_id: str,
        entity_type: str,
        lookback_days: int = 365,
    ) -> Forecast:
        """
        Generate forecast for entity.

        Args:
            forecast_type: Type of forecast
            period: Forecast period
            entity_id: Entity ID
            entity_type: Entity type
            lookback_days: Days of history to use

        Returns:
            Generated forecast
        """
        # Mock forecast generation
        forecast_value = self._generate_forecast_value(
            entity_type, lookback_days)

        # Calculate valid period
        valid_from = datetime.utcnow()
        valid_to = self._calculate_valid_to(valid_from, period)

        forecast = Forecast(
            id=uuid4(),
            forecast_type=forecast_type.value,
            period=period.value,
            entity_id=entity_id,
            entity_type=entity_type,
            forecast_value=forecast_value,
            forecast_lower_bound=forecast_value * 0.8,
            forecast_upper_bound=forecast_value * 1.2,
            confidence_level=0.85,
            forecast_date=datetime.utcnow(),
            valid_from=valid_from,
            valid_to=valid_to,
            model_name="exponential_smoothing",
            model_version="1.0.0",
        )

        return await self.forecast_repo.create(forecast)

    async def create_alert_from_forecast(
        self,
        forecast_id: UUID,
        alert_type: str,
        severity: str,
        description: str,
        recommended_action: str | None = None,
        threshold_value: float | None = None,
    ) -> ForecastAlert:
        """
        Create alert from forecast.

        Args:
            forecast_id: Forecast ID
            alert_type: Type of alert
            severity: Alert severity
            description: Alert description
            recommended_action: Recommended action
            threshold_value: Threshold value

        Returns:
            Created alert
        """
        forecast = await self.forecast_repo.get_by_id(forecast_id)
        if not forecast:
            raise ServiceError(
                "NOT_FOUND",
                f"Forecast {forecast_id} not found",
                {"forecast_id": str(forecast_id)}
            )

        alert = ForecastAlert(
            id=uuid4(),
            forecast_id=forecast_id,
            alert_type=alert_type,
            severity=severity,
            description=description,
            recommended_action=recommended_action,
            threshold_value=threshold_value,
            forecast_value=forecast.forecast_value,
        )

        return await self.alert_repo.create(alert)

    async def get_latest_forecast(
        self,
        entity_id: str,
        forecast_type: str,
    ) -> Forecast:
        """Get latest forecast for entity."""
        forecast = await self.forecast_repo.get_latest_for_entity(entity_id, forecast_type)
        if not forecast:
            raise ServiceError(
                "NOT_FOUND",
                f"No forecast found for {entity_id}",
                {"entity_id": entity_id}
            )
        return forecast

    async def get_active_alerts(self) -> list[ForecastAlert]:
        """Get all active alerts."""
        return await self.alert_repo.get_pending_alerts()

    def _generate_forecast_value(self, entity_type: str, lookback_days: int) -> float:
        """Mock forecast value generation."""
        # Simple mock - return value based on entity type
        base_values = {
            "item": 1000,
            "warehouse": 5000,
            "process": 100,
        }
        base = base_values.get(entity_type, 1000)
        # Add some variance
        return base * (1 + (lookback_days / 365) * 0.1)

    def _calculate_valid_to(self, valid_from: datetime, period: ForecastPeriod) -> datetime:
        """Calculate forecast valid_to date."""
        period_days = {
            ForecastPeriod.DAILY: 1,
            ForecastPeriod.WEEKLY: 7,
            ForecastPeriod.MONTHLY: 30,
            ForecastPeriod.QUARTERLY: 90,
        }
        days = period_days.get(period, 30)
        return valid_from + timedelta(days=days)
