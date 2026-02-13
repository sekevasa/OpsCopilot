"""Repositories for unified data service."""

from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.repository import BaseRepository
from ..domain.models import SKUModel, BOMModel, WorkOrderModel, SupplierModel, InventorySnapshotModel, SalesOrderModel


class SKURepository(BaseRepository[SKUModel]):
    """Repository for SKU master data."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SKUModel)

    async def get_by_sku_code(self, sku_code: str) -> Optional[SKUModel]:
        """Get SKU by code."""
        stmt = select(SKUModel).where(SKUModel.sku_code == sku_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_skus(self) -> List[SKUModel]:
        """Get all active SKUs."""
        stmt = select(SKUModel).where(SKUModel.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_category(self, category: str) -> List[SKUModel]:
        """Get SKUs by category."""
        stmt = select(SKUModel).where(SKUModel.category == category)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class BOMRepository(BaseRepository[BOMModel]):
    """Repository for Bill of Materials."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, BOMModel)

    async def get_by_bom_number(self, bom_number: str) -> Optional[BOMModel]:
        """Get BOM by number."""
        stmt = select(BOMModel).where(BOMModel.bom_number == bom_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku_id(self, sku_id: UUID) -> List[BOMModel]:
        """Get all BOMs for an SKU."""
        stmt = select(BOMModel).where(
            (BOMModel.sku_id == sku_id) & (BOMModel.is_active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class WorkOrderRepository(BaseRepository[WorkOrderModel]):
    """Repository for work orders."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkOrderModel)

    async def get_by_work_order_number(self, wo_number: str) -> Optional[WorkOrderModel]:
        """Get work order by number."""
        stmt = select(WorkOrderModel).where(
            WorkOrderModel.work_order_number == wo_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_work_orders(self) -> List[WorkOrderModel]:
        """Get all open work orders."""
        from shared.domain_models import WorkOrderStatus
        stmt = select(WorkOrderModel).where(
            WorkOrderModel.status.in_([
                WorkOrderStatus.CREATED,
                WorkOrderStatus.SCHEDULED,
                WorkOrderStatus.IN_PROGRESS,
            ])
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SupplierRepository(BaseRepository[SupplierModel]):
    """Repository for supplier master data."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SupplierModel)

    async def get_by_supplier_code(self, supplier_code: str) -> Optional[SupplierModel]:
        """Get supplier by code."""
        stmt = select(SupplierModel).where(
            SupplierModel.supplier_code == supplier_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_suppliers(self) -> List[SupplierModel]:
        """Get all active suppliers."""
        stmt = select(SupplierModel).where(SupplierModel.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class InventorySnapshotRepository(BaseRepository[InventorySnapshotModel]):
    """Repository for inventory snapshots."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, InventorySnapshotModel)

    async def get_latest_for_sku(
        self,
        sku_id: UUID,
        warehouse_location: Optional[str] = None,
    ) -> Optional[InventorySnapshotModel]:
        """Get latest inventory snapshot for SKU."""
        query = select(InventorySnapshotModel).where(
            InventorySnapshotModel.sku_id == sku_id
        )
        if warehouse_location:
            query = query.where(
                InventorySnapshotModel.warehouse_location == warehouse_location
            )
        query = query.order_by(InventorySnapshotModel.created_at.desc())
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_critical_inventory(self) -> List[InventorySnapshotModel]:
        """Get inventory at critical levels."""
        from shared.domain_models import InventoryStatus
        stmt = select(InventorySnapshotModel).where(
            InventorySnapshotModel.status == InventoryStatus.CRITICAL
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SalesOrderRepository(BaseRepository[SalesOrderModel]):
    """Repository for sales orders."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SalesOrderModel)

    async def get_by_sales_order_number(self, so_number: str) -> Optional[SalesOrderModel]:
        """Get sales order by number."""
        stmt = select(SalesOrderModel).where(
            SalesOrderModel.sales_order_number == so_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_orders(self) -> List[SalesOrderModel]:
        """Get all open sales orders."""
        from shared.domain_models import SalesOrderStatus
        stmt = select(SalesOrderModel).where(
            SalesOrderModel.status.in_([
                SalesOrderStatus.CONFIRMED,
                SalesOrderStatus.PARTIAL,
            ])
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_customer(self, customer_id: str) -> List[SalesOrderModel]:
        """Get all orders for a customer."""
        stmt = select(SalesOrderModel).where(
            SalesOrderModel.customer_id == customer_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
