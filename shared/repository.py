"""Repository pattern base classes."""

from typing import TypeVar, Generic, List, Optional, Type
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Base
from .domain_models import PagedResponse, PaginationParams


T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository implementing generic CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def create(self, obj: T) -> T:
        """Create a new entity."""
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def get_by_id(self, obj_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        return await self.session.get(self.model, obj_id)

    async def get_all(self) -> List[T]:
        """Get all entities."""
        stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_paginated(self, params: PaginationParams) -> PagedResponse:
        """Get paginated entities."""
        # Get total count
        count_stmt = select(func.count()).select_from(self.model)
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get paginated items
        stmt = select(self.model).offset(params.skip).limit(params.limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()

        return PagedResponse(
            items=items,
            total=total,
            skip=params.skip,
            limit=params.limit,
        )

    async def update(self, obj_id: UUID, update_data: dict) -> Optional[T]:
        """Update an entity."""
        obj = await self.get_by_id(obj_id)
        if not obj:
            return None

        for key, value in update_data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)

        await self.session.flush()
        return obj

    async def delete(self, obj_id: UUID) -> bool:
        """Delete an entity."""
        obj = await self.get_by_id(obj_id)
        if not obj:
            return False

        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def exists(self, obj_id: UUID) -> bool:
        """Check if entity exists."""
        stmt = select(func.count()).select_from(
            self.model).where(self.model.id == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar() > 0
