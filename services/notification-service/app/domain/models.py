"""Domain models for notifications."""

from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from shared.database import Base


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


class NotificationPreference(Base):
    """User notification preferences."""

    __tablename__ = "notification_preferences"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)

    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    slack_webhook_url = Column(String(500), nullable=True)

    # Preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    slack_enabled = Column(Boolean, default=False)
    webhook_enabled = Column(Boolean, default=False)

    # Alert preferences
    notify_on_critical = Column(Boolean, default=True)
    notify_on_high = Column(Boolean, default=True)
    notify_on_medium = Column(Boolean, default=False)

    daily_digest_enabled = Column(Boolean, default=True)
    digest_time = Column(String(5), default="08:00")  # HH:MM format

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class Notification(Base):
    """Sent notification record."""

    __tablename__ = "notifications"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)

    # Content
    title = Column(String(255), nullable=False)
    message = Column(String, nullable=False)
    # alert, forecast, update, etc.
    notification_type = Column(String(100), nullable=False)
    # critical, high, medium, low
    severity = Column(String(50), nullable=False)

    # Delivery
    channel = Column(String(50), nullable=False)
    status = Column(String(50), default=NotificationStatus.PENDING)

    # Content metadata
    notification_metadata = Column(JSON, nullable=True)
    recipient_address = Column(String(500), nullable=True)

    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class NotificationTemplate(Base):
    """Notification message templates."""

    __tablename__ = "notification_templates"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    notification_type = Column(String(100), nullable=False)

    # Template content
    title_template = Column(String(500), nullable=False)
    message_template = Column(String, nullable=False)

    # Template variables documentation
    variables = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
