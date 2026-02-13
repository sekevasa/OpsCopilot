"""Repositories for AI runtime."""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.repository import BaseRepository
from .models import AIModel, InferenceJob


class AIModelRepository(BaseRepository[AIModel]):
    """Repository for AI models."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AIModel)

    async def get_by_name(self, name: str) -> Optional[AIModel]:
        """Get model by name."""
        stmt = select(AIModel).where(AIModel.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_available_models(self):
        """Get all available models."""
        from .models import ModelStatus
        stmt = select(AIModel).where(AIModel.status == ModelStatus.AVAILABLE)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class InferenceJobRepository(BaseRepository[InferenceJob]):
    """Repository for inference jobs."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, InferenceJob)
