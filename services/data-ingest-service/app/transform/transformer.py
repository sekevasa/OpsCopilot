"""Data transformation rules and validators."""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    """Abstract base transformer."""

    @abstractmethod
    async def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single record.

        Args:
            record: Raw record

        Returns:
            Transformed record
        """
        pass

    @abstractmethod
    def validate(self, record: Dict[str, Any]) -> List[str]:
        """Validate a record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        pass


class SKUTransformer(BaseTransformer):
    """Transform SKU data from external sources."""

    async def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform SKU record."""
        return {
            "sku_code": record.get("product_code", ""),
            "product_name": record.get("product_name", ""),
            "uom": record.get("unit_of_measure", "EA"),
            "category": record.get("category", "UNCATEGORIZED"),
            "supplier_id": record.get("vendor_id"),
            "unit_cost": float(record.get("cost", 0)),
            "lead_time_days": int(record.get("lead_time", 0)),
            "is_active": record.get("is_active", True),
        }

    def validate(self, record: Dict[str, Any]) -> List[str]:
        """Validate SKU record."""
        errors = []
        if not record.get("sku_code"):
            errors.append("Missing sku_code")
        if not record.get("product_name"):
            errors.append("Missing product_name")
        try:
            float(record.get("unit_cost", 0))
        except (ValueError, TypeError):
            errors.append("Invalid unit_cost - must be numeric")
        return errors


class InventoryTransformer(BaseTransformer):
    """Transform inventory data."""

    async def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform inventory record."""
        qty_on_hand = float(record.get("quantity_on_hand", 0))
        qty_reserved = float(record.get("quantity_reserved", 0))

        return {
            "sku_code": record.get("sku_code", ""),
            "warehouse_location": record.get("warehouse", ""),
            "quantity_on_hand": qty_on_hand,
            "quantity_reserved": qty_reserved,
            "quantity_available": max(qty_on_hand - qty_reserved, 0),
            "reorder_point": float(record.get("reorder_point", 0)),
            "reorder_quantity": float(record.get("reorder_qty", 0)),
            "last_stock_count": record.get("last_count_date"),
        }

    def validate(self, record: Dict[str, Any]) -> List[str]:
        """Validate inventory record."""
        errors = []
        if not record.get("sku_code"):
            errors.append("Missing sku_code")
        if not record.get("warehouse"):
            errors.append("Missing warehouse")
        try:
            float(record.get("quantity_on_hand", 0))
            float(record.get("quantity_reserved", 0))
        except (ValueError, TypeError):
            errors.append("Invalid quantity - must be numeric")
        return errors


class WorkOrderTransformer(BaseTransformer):
    """Transform work order data."""

    async def transform(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform work order record."""
        return {
            "work_order_number": record.get("work_order_id", ""),
            "sku_code": record.get("product_code", ""),
            "quantity_ordered": float(record.get("quantity", 0)),
            "quantity_produced": float(record.get("completed_qty", 0)),
            "status": record.get("status", "PENDING").upper(),
            "scheduled_start": record.get("start_date"),
            "scheduled_end": record.get("end_date"),
            "priority": int(record.get("priority", 5)),
            "notes": record.get("notes"),
        }

    def validate(self, record: Dict[str, Any]) -> List[str]:
        """Validate work order record."""
        errors = []
        if not record.get("work_order_id"):
            errors.append("Missing work_order_id")
        if not record.get("product_code"):
            errors.append("Missing product_code")
        try:
            float(record.get("quantity", 0))
        except (ValueError, TypeError):
            errors.append("Invalid quantity")
        return errors


class TransformerFactory:
    """Factory for creating appropriate transformers."""

    _transformers = {
        "sku": SKUTransformer,
        "inventory": InventoryTransformer,
        "work_order": WorkOrderTransformer,
    }

    @classmethod
    def get_transformer(cls, entity_type: str) -> BaseTransformer:
        """Get transformer for entity type.

        Args:
            entity_type: Type of entity (sku, inventory, work_order)

        Returns:
            Transformer instance

        Raises:
            ValueError: If entity type not supported
        """
        transformer_class = cls._transformers.get(entity_type.lower())
        if not transformer_class:
            raise ValueError(f"Unsupported entity type: {entity_type}")

        logger.info(f"Creating transformer for {entity_type}")
        return transformer_class()

    @classmethod
    async def transform_record(
        cls,
        entity_type: str,
        record: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Transform a record.

        Args:
            entity_type: Type of entity
            record: Raw record

        Returns:
            Transformed record or None if invalid
        """
        transformer = cls.get_transformer(entity_type)

        # Validate first
        errors = transformer.validate(record)
        if errors:
            logger.warning(f"Validation errors for {entity_type}: {errors}")
            return None

        # Transform
        return await transformer.transform(record)
