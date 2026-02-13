"""Repositories for unified data."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.repository import BaseRepository
from .models import ManufacturingItem, ManufacturingProcess, InventorySnapshot


class ManufacturingItemRepository(BaseRepository[ManufacturingItem]):
    """Repository for manufacturing items."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ManufacturingItem)

    async def get_by_sku(self, sku: str) -> Optional[ManufacturingItem]:
        """Get item by SKU."""
        stmt = select(ManufacturingItem).where(ManufacturingItem.sku == sku)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_id: str, source: str) -> Optional[ManufacturingItem]:
        """Get item by external ID and source."""
        stmt = select(ManufacturingItem).where(
            (ManufacturingItem.external_id == external_id) &
            (ManufacturingItem.external_source == source)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ManufacturingProcessRepository(BaseRepository[ManufacturingProcess]):
    """Repository for manufacturing processes."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ManufacturingProcess)

    async def get_by_process_id(self, process_id: str) -> Optional[ManufacturingProcess]:
        """Get process by process ID."""
        stmt = select(ManufacturingProcess).where(
            ManufacturingProcess.process_id == process_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class InventorySnapshotRepository(BaseRepository[InventorySnapshot]):
    """Repository for inventory snapshots."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, InventorySnapshot)

    async def get_latest_for_item(self, item_id: UUID) -> Optional[InventorySnapshot]:
        """Get latest inventory snapshot for item."""
        stmt = select(InventorySnapshot).where(
            InventorySnapshot.item_id == item_id
        ).order_by(InventorySnapshot.snapshot_date.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_warehouse(self, warehouse_id: str) -> List[InventorySnapshot]:
        """Get inventory snapshots for warehouse."""
        stmt = select(InventorySnapshot).where(
            InventorySnapshot.warehouse_id == warehouse_id
        ).order_by(InventorySnapshot.snapshot_date.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
