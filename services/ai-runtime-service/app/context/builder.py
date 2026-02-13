"""Context building for copilot conversations."""

from typing import Any, Dict, List, Optional
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build context for copilot operations from external data."""

    def __init__(self):
        """Initialize context builder."""
        self.context_cache: Dict[str, Any] = {}

    async def build_context(
        self,
        entity_type: str,
        entity_id: str,
        include_inventory: bool = True,
        include_orders: bool = True,
        include_production: bool = False,
    ) -> Dict[str, Any]:
        """Build rich context for an entity.

        Args:
            entity_type: Type of entity (sku, warehouse, customer, etc.)
            entity_id: Entity identifier
            include_inventory: Include inventory data
            include_orders: Include sales order data
            include_production: Include production data

        Returns:
            Context dictionary with all relevant data
        """
        logger.info(f"Building context for {entity_type}:{entity_id}")

        context = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "timestamp": "2025-02-13T15:30:45Z",
        }

        # Fetch inventory context
        if include_inventory:
            context["inventory"] = await self._get_inventory_context(entity_id)

        # Fetch order context
        if include_orders:
            context["orders"] = await self._get_orders_context(entity_id)

        # Fetch production context
        if include_production:
            context["production"] = await self._get_production_context(entity_id)

        # Calculate insights
        context["insights"] = self._calculate_insights(context)

        return context

    async def _get_inventory_context(self, entity_id: str) -> Dict[str, Any]:
        """Get inventory context for entity."""
        # Mock implementation - would call unified-data-service
        return {
            "sku_code": entity_id,
            "product_name": f"Product {entity_id}",
            "quantity_on_hand": 500,
            "quantity_available": 250,
            "reorder_point": 100,
            "status": "OPTIMAL",
            "warehouses": [
                {"location": "WH_SOUTH", "qty": 300},
                {"location": "WH_NORTH", "qty": 200},
            ],
        }

    async def _get_orders_context(self, entity_id: str) -> Dict[str, Any]:
        """Get sales order context for entity."""
        # Mock implementation
        return {
            "customer_id": entity_id,
            "open_orders": 3,
            "total_value": 45000.00,
            "oldest_order_date": "2025-02-10",
            "latest_required_date": "2025-02-25",
            "on_time_percentage": 95.5,
        }

    async def _get_production_context(self, entity_id: str) -> Dict[str, Any]:
        """Get production context."""
        # Mock implementation
        return {
            "work_order_id": entity_id,
            "status": "IN_PROGRESS",
            "progress_percentage": 65.0,
            "scheduled_completion": "2025-02-16",
            "quantity_produced": 650,
            "quantity_remaining": 350,
        }

    def _calculate_insights(self, context: Dict[str, Any]) -> List[str]:
        """Calculate business insights from context."""
        insights = []

        # Inventory insights
        if "inventory" in context:
            inv = context["inventory"]
            if inv["quantity_available"] <= inv["reorder_point"]:
                insights.append(
                    f"⚠️ Inventory at reorder point ({inv['quantity_available']} units)")
            if inv["status"] == "CRITICAL":
                insights.append(
                    "🚨 Critical inventory level - immediate action needed")

        # Order insights
        if "orders" in context:
            orders = context["orders"]
            if orders["open_orders"] > 5:
                insights.append(
                    f"📦 High order volume: {orders['open_orders']} open orders")
            if orders["total_value"] > 50000:
                insights.append(
                    f"💰 High order value: ${orders['total_value']:,.0f}")

        # Production insights
        if "production" in context:
            prod = context["production"]
            if prod["progress_percentage"] < 50:
                insights.append("⏱️ Production behind schedule")
            elif prod["progress_percentage"] > 80:
                insights.append("✅ Production on track")

        return insights

    def clear_cache(self):
        """Clear context cache."""
        self.context_cache.clear()
        logger.info("Context cache cleared")
