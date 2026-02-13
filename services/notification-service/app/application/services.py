"""Application services for notifications."""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from shared.domain_models import ServiceError
from ..domain.models import (
    Notification,
    NotificationPreference,
    NotificationChannel,
    NotificationStatus,
)
from ..domain.repositories import (
    NotificationRepository,
    NotificationPreferenceRepository,
)


class NotificationService:
    """Service for sending notifications."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(session)
        self.preference_repo = NotificationPreferenceRepository(session)

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        severity: str,
        channel: NotificationChannel,
        metadata: Dict[str, Any] | None = None,
    ) -> Notification:
        """
        Send notification to user.

        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            severity: Severity level
            channel: Delivery channel
            metadata: Additional metadata

        Returns:
            Created notification
        """
        # Get user preferences
        preferences = await self.preference_repo.get_by_user_id(user_id)

        # Check if user has enabled this channel
        if preferences:
            channel_enabled_map = {
                NotificationChannel.EMAIL: preferences.email_enabled,
                NotificationChannel.SMS: preferences.sms_enabled,
                NotificationChannel.SLACK: preferences.slack_enabled,
                NotificationChannel.WEBHOOK: preferences.webhook_enabled,
            }

            if not channel_enabled_map.get(channel, True):
                raise ServiceError(
                    "CHANNEL_DISABLED",
                    f"Channel {channel} is disabled for user {user_id}",
                    {"user_id": user_id, "channel": channel}
                )

        # Create notification record
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            severity=severity,
            channel=channel.value,
            status=NotificationStatus.PENDING.value,
            metadata=metadata,
        )

        notification = await self.notification_repo.create(notification)

        # Queue for delivery (in production, would push to message queue)
        await self._queue_for_delivery(notification, preferences)

        return notification

    async def set_preferences(
        self,
        user_id: str,
        email: str | None = None,
        phone: str | None = None,
        email_enabled: bool = True,
        sms_enabled: bool = False,
        notify_on_critical: bool = True,
        notify_on_high: bool = True,
        notify_on_medium: bool = False,
    ) -> NotificationPreference:
        """
        Set notification preferences for user.

        Args:
            user_id: User ID
            email: Email address
            phone: Phone number
            email_enabled: Enable email notifications
            sms_enabled: Enable SMS notifications
            notify_on_critical: Notify on critical alerts
            notify_on_high: Notify on high alerts
            notify_on_medium: Notify on medium alerts

        Returns:
            Notification preferences
        """
        existing = await self.preference_repo.get_by_user_id(user_id)

        if existing:
            # Update existing
            await self.preference_repo.update(
                existing.id,
                {
                    "email": email or existing.email,
                    "phone": phone or existing.phone,
                    "email_enabled": email_enabled,
                    "sms_enabled": sms_enabled,
                    "notify_on_critical": notify_on_critical,
                    "notify_on_high": notify_on_high,
                    "notify_on_medium": notify_on_medium,
                }
            )
            return existing

        # Create new
        preferences = NotificationPreference(
            id=uuid4(),
            user_id=user_id,
            email=email,
            phone=phone,
            email_enabled=email_enabled,
            sms_enabled=sms_enabled,
            notify_on_critical=notify_on_critical,
            notify_on_high=notify_on_high,
            notify_on_medium=notify_on_medium,
        )

        return await self.preference_repo.create(preferences)

    async def get_pending_notifications(self) -> list[Notification]:
        """Get all pending notifications for delivery."""
        return await self.notification_repo.get_pending()

    async def mark_delivered(self, notification_id: UUID) -> Notification:
        """Mark notification as delivered."""
        notification = await self.notification_repo.update(
            notification_id,
            {
                "status": NotificationStatus.DELIVERED.value,
                "delivered_at": datetime.utcnow(),
            }
        )
        if not notification:
            raise ServiceError(
                "NOT_FOUND",
                f"Notification {notification_id} not found",
                {"notification_id": str(notification_id)}
            )
        return notification

    async def _queue_for_delivery(
        self,
        notification: Notification,
        preferences: NotificationPreference | None,
    ) -> None:
        """Queue notification for delivery."""
        # In production, would push to Redis or message queue
        # For now, just mark as sent
        await self.notification_repo.update(
            notification.id,
            {
                "status": NotificationStatus.SENT.value,
                "sent_at": datetime.utcnow(),
            }
        )
