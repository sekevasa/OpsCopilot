"""Business services for unified data operations."""

from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.domain.models import (
    SKUModel, BOMModel, WorkOrderModel, SupplierModel,
    InventorySnapshotModel, SalesOrderModel,
)
from app.repositories import (
    SKURepository, BOMRepository, WorkOrderRepository,
    SupplierRepository, InventorySnapshotRepository, SalesOrderRepository,
)
from shared.domain_models import ServiceError, InventoryStatus

logger = logging.getLogger(__name__)


class ManufacturingDataService:
    """Service for manufacturing data operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.sku_repo = SKURepository(session)
        self.bom_repo = BOMRepository(session)
        self.work_order_repo = WorkOrderRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.inventory_repo = InventorySnapshotRepository(session)
        self.sales_order_repo = SalesOrderRepository(session)

    # ========================================================================
    # SKU OPERATIONS
    # ========================================================================

    async def get_inventory_current(self, warehouse: Optional[str] = None) -> List[dict]:
        """Get current inventory across all locations or specific warehouse.

        Args:
            warehouse: Optional warehouse location to filter by

        Returns:
            List of current inventory records
        """
        snapshots = await self.inventory_repo.get_all(skip=0, limit=10000)

        if warehouse:
            snapshots = [
                s for s in snapshots if s.warehouse_location == warehouse]

        result = []
        for snapshot in snapshots:
            # Get SKU details
            sku = await self.sku_repo.get_by_id(snapshot.sku_id)
            if not sku:
                continue

            result.append({
                "sku_code": sku.sku_code,
                "product_name": sku.product_name,
                "warehouse": snapshot.warehouse_location,
                "quantity_on_hand": snapshot.quantity_on_hand,
                "quantity_reserved": snapshot.quantity_reserved,
                "quantity_available": snapshot.quantity_available,
                "status": snapshot.status,
                "reorder_point": snapshot.reorder_point,
                "reorder_needed": snapshot.quantity_available <= snapshot.reorder_point,
            })

        logger.info(f"Retrieved current inventory for {len(result)} items")
        return result

    # ========================================================================
    # SALES ORDER OPERATIONS
    # ========================================================================

    async def get_orders_open(self) -> List[dict]:
        """Get all open sales orders.

        Returns:
            List of open sales orders
        """
        orders = await self.sales_order_repo.get_open_orders()

        result = []
        for order in orders:
            result.append({
                "sales_order_number": order.sales_order_number,
                "customer_name": order.customer_name,
                "order_date": order.order_date,
                "required_date": order.required_date,
                "status": order.status,
                "total_amount": order.total_amount,
                "line_count": len(order.line_items) if order.line_items else 0,
            })

        logger.info(f"Retrieved {len(result)} open sales orders")
        return result

    # ========================================================================
    # SUPPLIER OPERATIONS
    # ========================================================================

    async def get_suppliers(self, active_only: bool = True) -> List[dict]:
        """Get supplier list.

        Args:
            active_only: Only return active suppliers

        Returns:
            List of suppliers
        """
        if active_only:
            suppliers = await self.supplier_repo.get_active_suppliers()
        else:
            suppliers = await self.supplier_repo.get_all()

        result = []
        for supplier in suppliers:
            result.append({
                "supplier_code": supplier.supplier_code,
                "supplier_name": supplier.supplier_name,
                "contact_person": supplier.contact_person,
                "email": supplier.email,
                "phone": supplier.phone,
                "country": supplier.country,
                "rating": supplier.rating,
                "is_active": supplier.is_active,
            })

        logger.info(f"Retrieved {len(result)} suppliers")
        return result

    # ========================================================================
    # WORK ORDER OPERATIONS
    # ========================================================================

    async def get_production_status(self) -> dict:
        """Get overall production status.

        Returns:
            Production status summary
        """
        all_work_orders = await self.work_order_repo.get_all()
        open_work_orders = await self.work_order_repo.get_open_work_orders()

        total_quantity_ordered = sum(
            wo.quantity_ordered for wo in all_work_orders)
        total_quantity_produced = sum(
            wo.quantity_produced for wo in all_work_orders)

        return {
            "total_work_orders": len(all_work_orders),
            "open_work_orders": len(open_work_orders),
            "total_quantity_ordered": total_quantity_ordered,
            "total_quantity_produced": total_quantity_produced,
            "production_rate": (
                (total_quantity_produced / total_quantity_ordered * 100)
                if total_quantity_ordered > 0 else 0
            ),
        }

    # ========================================================================
    # DATA QUALITY & VALIDATION
    # ========================================================================

    async def validate_inventory_consistency(self) -> dict:
        """Validate inventory data consistency.

        Returns:
            Validation report
        """
        snapshots = await self.inventory_repo.get_all()

        issues = []
        for snapshot in snapshots:
            # Quantity available should = on_hand - reserved
            expected_available = snapshot.quantity_on_hand - snapshot.quantity_reserved
            if abs(snapshot.quantity_available - expected_available) > 0.01:
                issues.append({
                    "sku_id": str(snapshot.sku_id),
                    "warehouse": snapshot.warehouse_location,
                    "issue": "Quantity available mismatch",
                    "expected": expected_available,
                    "actual": snapshot.quantity_available,
                })

            # Check if reserved > on_hand
            if snapshot.quantity_reserved > snapshot.quantity_on_hand:
                issues.append({
                    "sku_id": str(snapshot.sku_id),
                    "warehouse": snapshot.warehouse_location,
                    "issue": "Reserved quantity exceeds on-hand",
                })

        logger.info(f"Inventory validation found {len(issues)} issues")
        return {
            "total_records_checked": len(snapshots),
            "issues_found": len(issues),
            "issues": issues[:100],  # First 100 issues
        }
