"""Application services for unified data."""

import json
from typing import Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from shared.domain_models import ServiceError
from ..domain.models import (
    ManufacturingItem,
    ManufacturingProcess,
    InventorySnapshot,
)
from ..domain.repositories import (
    ManufacturingItemRepository,
    ManufacturingProcessRepository,
    InventorySnapshotRepository,
)


class DataNormalizationService:
    """Service for normalizing and transforming raw data."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.item_repo = ManufacturingItemRepository(session)
        self.process_repo = ManufacturingProcessRepository(session)
        self.inventory_repo = InventorySnapshotRepository(session)

    async def normalize_manufacturing_item(
        self,
        sku: str,
        name: str,
        description: str | None = None,
        uom: str = "EA",
        standard_cost: float | None = None,
        supplier_id: str | None = None,
        supplier_name: str | None = None,
        external_id: str | None = None,
        external_source: str | None = None,
        external_data: Dict[str, Any] | None = None,
    ) -> ManufacturingItem:
        """
        Normalize and create/update manufacturing item.

        Args:
            sku: Stock keeping unit
            name: Item name
            description: Item description
            uom: Unit of measure
            standard_cost: Standard cost
            supplier_id: Supplier ID
            supplier_name: Supplier name
            external_id: External system ID
            external_source: Source system
            external_data: Raw external data

        Returns:
            Normalized manufacturing item
        """
        # Check for existing item
        existing = await self.item_repo.get_by_sku(sku)

        if existing:
            # Update existing
            existing.name = name
            existing.description = description or existing.description
            existing.uom = uom
            existing.standard_cost = standard_cost or existing.standard_cost
            existing.supplier_id = supplier_id or existing.supplier_id
            existing.supplier_name = supplier_name or existing.supplier_name
            existing.updated_at = datetime.utcnow()

            await self.session.flush()
            return existing

        # Create new
        item = ManufacturingItem(
            id=uuid4(),
            sku=sku,
            name=name,
            description=description,
            uom=uom,
            standard_cost=standard_cost,
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            external_id=external_id,
            external_source=external_source,
            external_data=external_data,
        )

        return await self.item_repo.create(item)

    async def normalize_inventory_snapshot(
        self,
        item_id: UUID,
        warehouse_id: str,
        quantity_on_hand: float,
        quantity_reserved: float = 0,
        quantity_available: float | None = None,
        reorder_point: float | None = None,
        reorder_quantity: float | None = None,
        snapshot_date: datetime | None = None,
    ) -> InventorySnapshot:
        """
        Normalize inventory snapshot.

        Args:
            item_id: Manufacturing item ID
            warehouse_id: Warehouse identifier
            quantity_on_hand: Quantity available
            quantity_reserved: Quantity reserved
            quantity_available: Quantity available (calculated if not provided)
            reorder_point: Reorder point
            reorder_quantity: Reorder quantity
            snapshot_date: Snapshot timestamp

        Returns:
            Inventory snapshot
        """
        if quantity_available is None:
            quantity_available = max(0, quantity_on_hand - quantity_reserved)

        snapshot = InventorySnapshot(
            id=uuid4(),
            item_id=item_id,
            warehouse_id=warehouse_id,
            quantity_on_hand=quantity_on_hand,
            quantity_reserved=quantity_reserved,
            quantity_available=quantity_available,
            reorder_point=reorder_point,
            reorder_quantity=reorder_quantity,
            snapshot_date=snapshot_date or datetime.utcnow(),
        )

        return await self.inventory_repo.create(snapshot)

    async def get_item_by_sku(self, sku: str) -> ManufacturingItem:
        """Get manufacturing item by SKU."""
        item = await self.item_repo.get_by_sku(sku)
        if not item:
            raise ServiceError(
                "NOT_FOUND",
                f"Item with SKU '{sku}' not found",
                {"sku": sku}
            )
        return item

    async def get_latest_inventory(self, item_id: UUID) -> InventorySnapshot:
        """Get latest inventory snapshot for item."""
        snapshot = await self.inventory_repo.get_latest_for_item(item_id)
        if not snapshot:
            raise ServiceError(
                "NOT_FOUND",
                f"No inventory records for item {item_id}",
                {"item_id": str(item_id)}
            )
        return snapshot
