"""Repositories for notifications."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.repository import BaseRepository
from .models import Notification, NotificationPreference, NotificationTemplate


class NotificationRepository(BaseRepository[Notification]):
    """Repository for notifications."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    async def get_pending(self) -> List[Notification]:
        """Get all pending notifications."""
        from .models import NotificationStatus
        stmt = select(Notification).where(
            Notification.status == NotificationStatus.PENDING)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_user(self, user_id: str) -> List[Notification]:
        """Get notifications for user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    """Repository for notification preferences."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, NotificationPreference)

    async def get_by_user_id(self, user_id: str) -> Optional[NotificationPreference]:
        """Get preferences for user."""
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class NotificationTemplateRepository(BaseRepository[NotificationTemplate]):
    """Repository for notification templates."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, NotificationTemplate)

    async def get_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get template by name."""
        stmt = select(NotificationTemplate).where(
            NotificationTemplate.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
