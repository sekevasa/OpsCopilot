"""Schemas for notification API."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class NotificationChannel(str, Enum):
    """Notification delivery channel."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Status of notification."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"
    DELIVERED = "delivered"


class SendNotificationRequest(BaseModel):
    """Request to send notification."""

    user_id: str = Field(..., description="User to notify")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    notification_type: str = Field(..., description="Type of notification")
    severity: str = Field(..., description="Severity level")
    channel: NotificationChannel = Field(..., description="Delivery channel")
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    """Response for notification."""

    id: UUID
    user_id: str
    title: str
    message: str
    channel: NotificationChannel
    status: NotificationStatus
    severity: str
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceRequest(BaseModel):
    """Request to set notification preferences."""

    user_id: str = Field(..., description="User ID")
    email: Optional[str] = None
    phone: Optional[str] = None
    email_enabled: bool = True
    sms_enabled: bool = False
    notify_on_critical: bool = True
    notify_on_high: bool = True
    notify_on_medium: bool = False


class NotificationPreferenceResponse(BaseModel):
    """Response for notification preference."""

    id: UUID
    user_id: str
    email: Optional[str]
    phone: Optional[str]
    email_enabled: bool
    sms_enabled: bool
    notify_on_critical: bool
    notify_on_high: bool

    class Config:
        from_attributes = True
