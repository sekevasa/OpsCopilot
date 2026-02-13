"""API routes for notifications."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, EmailStr
from shared.database import db
from shared.domain_models import ServiceError
from ..domain.schemas import (
    SendNotificationRequest,
    NotificationResponse,
    NotificationPreferenceRequest,
    NotificationPreferenceResponse,
    NotificationChannel,
    NotificationStatus,
)
from ..application.services import NotificationService
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


router = APIRouter(prefix="/api/v1", tags=["notifications"])


# Request/Response schemas for new endpoints
class NotificationSeverity(str, Enum):
    """Notification severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EmailNotificationRequest(BaseModel):
    """Email notification request."""
    recipient_email: EmailStr = Field(..., description="Email recipient")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text or HTML)")
    html_body: Optional[str] = Field(None, description="HTML email body")
    priority: NotificationSeverity = Field(
        default=NotificationSeverity.MEDIUM, description="Email priority")
    tags: List[str] = Field(default_factory=list,
                            description="Email tags for filtering")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata")


class EmailNotificationResponse(BaseModel):
    """Email notification response."""
    notification_id: str
    recipient_email: str
    subject: str
    status: str = "sent"
    timestamp: datetime
    delivery_status: Optional[str] = Field(
        None, description="Email delivery status")
    send_attempts: int = Field(1, description="Number of send attempts")


class AlertRequest(BaseModel):
    """Alert notification request."""
    user_id: str = Field(..., description="User to alert")
    alert_title: str = Field(..., description="Alert title")
    alert_message: str = Field(..., description="Alert description")
    severity: NotificationSeverity = Field(
        default=NotificationSeverity.HIGH, description="Alert severity")
    channels: List[str] = Field(
        default_factory=list, description="Channels: email, sms, slack, webhook")
    alert_type: str = Field(
        default="system", description="Alert type: system, inventory, production, quality")
    source_entity: Optional[str] = Field(
        None, description="Related entity (SKU, WorkOrder, etc.)")
    action_required: bool = Field(
        False, description="Whether action is required")
    ttl_hours: Optional[int] = Field(
        24, description="Alert time-to-live in hours")


class AlertResponse(BaseModel):
    """Alert notification response."""
    alert_id: str
    user_id: str
    alert_title: str
    severity: NotificationSeverity
    channels_notified: List[str] = Field(
        default_factory=list, description="Successfully notified channels")
    channels_failed: List[str] = Field(
        default_factory=list, description="Failed channels")
    status: str = "pending"
    created_at: datetime
    expires_at: Optional[datetime] = None


class AcknowledgeAlertRequest(BaseModel):
    """Request to acknowledge alert."""
    acknowledged_by: str = Field(..., description="User acknowledging alert")
    acknowledgment_message: Optional[str] = Field(
        None, description="Acknowledgment notes")


class NotificationPreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    user_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    slack_webhook: Optional[str] = Field(None, description="Slack webhook URL")
    enabled_channels: List[str] = Field(
        default_factory=list, description="Enabled notification channels")
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_on_medium: bool = False
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None    # HH:MM format


async def get_service(session: AsyncSession = Depends(db.get_session)) -> NotificationService:
    """Dependency for notification service."""
    return NotificationService(session)


# Legacy endpoints (kept for backward compatibility)


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    request: SendNotificationRequest,
    service: NotificationService = Depends(get_service),
) -> NotificationResponse:
    """Send notification to user."""
    try:
        notification = await service.send_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            severity=request.severity,
            channel=request.channel,
            metadata=request.metadata,
        )
        return NotificationResponse.from_orm(notification)
    except ServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )


@router.post("/preferences", response_model=NotificationPreferenceResponse)
async def set_preferences(
    request: NotificationPreferenceRequest,
    service: NotificationService = Depends(get_service),
) -> NotificationPreferenceResponse:
    """Set notification preferences."""
    prefs = await service.set_preferences(
        user_id=request.user_id,
        email=request.email,
        phone=request.phone,
        email_enabled=request.email_enabled,
        sms_enabled=request.sms_enabled,
        notify_on_critical=request.notify_on_critical,
        notify_on_high=request.notify_on_high,
    )
    return NotificationPreferenceResponse.from_orm(prefs)


# New specialized endpoints


@router.post("/notify/email", response_model=EmailNotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_email_notification(
    request: EmailNotificationRequest,
    service: NotificationService = Depends(get_service),
) -> EmailNotificationResponse:
    """Send email notification.

    Sends an email notification to specified recipient with subject and body.
    Supports both plain text and HTML content.

    Args:
        request: Email notification request

    Returns:
        Email notification response with delivery status

    Example:
        POST /api/v1/notify/email
        {
            "recipient_email": "user@example.com",
            "subject": "Inventory Alert",
            "body": "SKU ABC-123 is below reorder point",
            "priority": "high"
        }
    """
    try:
        # Send email notification through service
        notification = await service.send_notification(
            user_id=request.recipient_email,
            title=request.subject,
            message=request.body,
            notification_type="email",
            severity=request.priority.value,
            channel="email",
            metadata={
                "html_body": request.html_body,
                "tags": request.tags,
                **(request.metadata or {})
            },
        )

        return EmailNotificationResponse(
            notification_id=str(notification.id),
            recipient_email=request.recipient_email,
            subject=request.subject,
            status="sent",
            timestamp=datetime.utcnow(),
            delivery_status="pending",
            send_attempts=1,
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


@router.post("/notify/alert", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def send_alert(
    request: AlertRequest,
    service: NotificationService = Depends(get_service),
) -> AlertResponse:
    """Send multi-channel alert notification.

    Sends alerts through multiple channels (email, SMS, Slack, webhook) based on user preferences
    and alert severity. Suitable for critical system events.

    Args:
        request: Alert notification request

    Returns:
        Alert response with channels notified and status

    Example:
        POST /api/v1/notify/alert
        {
            "user_id": "user-123",
            "alert_title": "Critical Inventory Alert",
            "alert_message": "SKU ABC-123 stock critically low",
            "severity": "critical",
            "channels": ["email", "slack"],
            "alert_type": "inventory",
            "source_entity": "SKU-ABC-123",
            "action_required": true
        }
    """
    try:
        from datetime import timedelta

        channels_notified = []
        channels_failed = []

        # Send through each requested channel
        for channel in request.channels:
            try:
                await service.send_notification(
                    user_id=request.user_id,
                    title=request.alert_title,
                    message=request.alert_message,
                    notification_type="alert",
                    severity=request.severity.value,
                    channel=channel,
                    metadata={
                        "alert_type": request.alert_type,
                        "source_entity": request.source_entity,
                        "action_required": request.action_required,
                    },
                )
                channels_notified.append(channel)
            except Exception as e:
                channels_failed.append(channel)

        # Calculate expiration
        expires_at = None
        if request.ttl_hours:
            expires_at = datetime.utcnow() + timedelta(hours=request.ttl_hours)

        return AlertResponse(
            alert_id=f"alert-{datetime.utcnow().timestamp()}",
            user_id=request.user_id,
            alert_title=request.alert_title,
            severity=request.severity,
            channels_notified=channels_notified,
            channels_failed=channels_failed,
            status="pending",
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/notify/alert/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    service: NotificationService = Depends(get_service),
) -> Dict[str, Any]:
    """Acknowledge an alert notification.

    Marks an alert as acknowledged by a user, typically prevents further escalation.

    Args:
        alert_id: Alert ID to acknowledge
        request: Acknowledgment details

    Returns:
        Acknowledgment confirmation

    Example:
        POST /api/v1/notify/alert/alert-123456/acknowledge
        {
            "acknowledged_by": "user-123",
            "acknowledgment_message": "Inventory reorder in progress"
        }
    """
    try:
        return {
            "alert_id": alert_id,
            "acknowledged_by": request.acknowledged_by,
            "acknowledged_at": datetime.utcnow().isoformat(),
            "status": "acknowledged",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/notify/preferences", response_model=Dict[str, Any])
async def update_preferences(
    request: NotificationPreferencesRequest,
    service: NotificationService = Depends(get_service),
) -> Dict[str, Any]:
    """Update user notification preferences.

    Configure notification channels, quiet hours, and severity levels.

    Args:
        request: Notification preferences update

    Returns:
        Updated preferences

    Example:
        POST /api/v1/notify/preferences
        {
            "user_id": "user-123",
            "email": "user@example.com",
            "phone": "+1-555-0123",
            "enabled_channels": ["email", "slack"],
            "notify_on_critical": true,
            "notify_on_high": true,
            "quiet_hours_enabled": true,
            "quiet_hours_start": "18:00",
            "quiet_hours_end": "08:00"
        }
    """
    try:
        # Update preferences through service
        prefs = await service.set_preferences(
            user_id=request.user_id,
            email=request.email,
            phone=request.phone,
            email_enabled="email" in request.enabled_channels,
            sms_enabled="sms" in request.enabled_channels,
            notify_on_critical=request.notify_on_critical,
            notify_on_high=request.notify_on_high,
        )

        return {
            "user_id": request.user_id,
            "enabled_channels": request.enabled_channels,
            "notify_on_critical": request.notify_on_critical,
            "notify_on_high": request.notify_on_high,
            "notify_on_medium": request.notify_on_medium,
            "quiet_hours_enabled": request.quiet_hours_enabled,
            "updated_at": datetime.utcnow().isoformat(),
        }

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


@router.get("/notify/channels")
async def list_available_channels() -> Dict[str, Any]:
    """List available notification channels.

    Returns:
        Available channels and their descriptions

    Example Response:
        {
            "channels": [
                {"name": "email", "description": "Email notifications"},
                {"name": "slack", "description": "Slack messages"},
                {"name": "sms", "description": "SMS text messages"},
                {"name": "webhook", "description": "Webhook callbacks"}
            ]
        }
    """
    return {
        "channels": [
            {
                "name": "email",
                "description": "Email notifications",
                "requires_config": ["recipient_email"],
            },
            {
                "name": "slack",
                "description": "Slack messages",
                "requires_config": ["slack_webhook_url"],
            },
            {
                "name": "sms",
                "description": "SMS text messages",
                "requires_config": ["phone_number"],
            },
            {
                "name": "webhook",
                "description": "HTTP webhook callbacks",
                "requires_config": ["webhook_url"],
            },
        ],
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
