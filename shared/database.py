"""Database connectivity and session management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        self.engine = None
        self.session_maker = None

    async def initialize(self) -> None:
        """Initialize database engine and session maker."""
        settings = get_settings()

        self.engine = create_async_engine(
            settings.database.url,
            echo=settings.database.echo,
            poolclass=NullPool,  # Better for microservices
            connect_args={"timeout": 10},
        )

        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()

    async def create_tables(self) -> None:
        """Create all tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            # Silently handle database connection errors in dev mode
            import os
            if os.getenv("SKIP_DB_INIT") != "1":
                raise
            print(f"[DATABASE] Skipping table creation: {type(e).__name__}")

    async def drop_tables(self) -> None:
        """Drop all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global instance
db = DatabaseManager()
