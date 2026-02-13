"""Repositories for forecasting."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.repository import BaseRepository
from .models import Forecast, ForecastAlert


class ForecastRepository(BaseRepository[Forecast]):
    """Repository for forecasts."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Forecast)

    async def get_latest_for_entity(
        self,
        entity_id: str,
        forecast_type: str,
    ) -> Optional[Forecast]:
        """Get latest forecast for entity."""
        stmt = select(Forecast).where(
            (Forecast.entity_id == entity_id) &
            (Forecast.forecast_type == forecast_type)
        ).order_by(Forecast.forecast_date.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_forecasts(
        self,
        as_of: datetime | None = None,
    ) -> List[Forecast]:
        """Get all active forecasts."""
        if as_of is None:
            as_of = datetime.utcnow()

        stmt = select(Forecast).where(
            (Forecast.valid_from <= as_of) &
            (Forecast.valid_to > as_of)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ForecastAlertRepository(BaseRepository[ForecastAlert]):
    """Repository for forecast alerts."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ForecastAlert)

    async def get_pending_alerts(self) -> List[ForecastAlert]:
        """Get all pending alerts."""
        stmt = select(ForecastAlert).where(
            ForecastAlert.acknowledged == "pending")
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_critical_alerts(self) -> List[ForecastAlert]:
        """Get all critical alerts."""
        stmt = select(ForecastAlert).where(
            ForecastAlert.severity == "critical")
        result = await self.session.execute(stmt)
        return result.scalars().all()
