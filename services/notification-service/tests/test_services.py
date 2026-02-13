"""Tests for notification service."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.domain.models import NotificationChannel
from app.application.services import NotificationService
from shared.database import Base


@pytest.fixture
async def test_db():
    """Create in-memory test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        yield session


@pytest.mark.asyncio
async def test_send_notification(test_db):
    """Test sending notification."""
    service = NotificationService(test_db)

    notification = await service.send_notification(
        user_id="user123",
        title="Test Alert",
        message="This is a test message",
        notification_type="alert",
        severity="high",
        channel=NotificationChannel.EMAIL,
    )

    assert notification.id is not None
    assert notification.user_id == "user123"


@pytest.mark.asyncio
async def test_set_preferences(test_db):
    """Test setting notification preferences."""
    service = NotificationService(test_db)

    prefs = await service.set_preferences(
        user_id="user456",
        email="user@example.com",
        email_enabled=True,
    )

    assert prefs.user_id == "user456"
    assert prefs.email == "user@example.com"
