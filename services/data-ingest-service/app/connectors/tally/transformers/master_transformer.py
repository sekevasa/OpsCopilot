"""Master data transformer for Tally Prime 7.

Transforms raw Tally master records (stock items, parties) to the unified
platform schema.
"""

import logging
from typing import Any, Dict, List

from .base_transformer import BaseTransformer

logger = logging.getLogger(__name__)


class MasterTransformer(BaseTransformer):
    """Transform Tally master records (stock items and parties) to unified schema."""

    def transform(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of master records.

        Args:
            records: Raw master records from :class:`MasterExtractor`.

        Returns:
            List of unified schema dictionaries.
        """
        return self.transform_batch(records)

    def _transform_one(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to the correct transformer based on ``record_type``."""
        record_type = record.get("record_type", "")
        if record_type == "stock_item":
            return self._transform_stock_item(record)
        if record_type == "party":
            return self._transform_party(record)
        logger.debug("Unknown master record_type '%s', skipping", record_type)
        return {}

    def _transform_stock_item(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Tally stock item to the unified item schema.

        Args:
            record: Raw stock item dictionary.

        Returns:
            Unified item dictionary.
        """
        name = record.get("name", "")
        if not name:
            raise ValueError("Stock item has no name")
        return {
            "unified_type": "item",
            "source_id": name,
            "sku_code": self._slugify(name),
            "product_name": name,
            "description": record.get("description") or None,
            "uom": record.get("uom") or "EA",
            "category": record.get("parent") or "Uncategorized",
            "unit_cost": self._safe_float(record.get("opening_rate")),
            "hsn_code": record.get("hsn_code") or None,
            "is_active": True,
            "raw": record,
        }

    def _transform_party(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Tally party to the unified party schema.

        Args:
            record: Raw party dictionary.

        Returns:
            Unified party dictionary.
        """
        name = record.get("name", "")
        if not name:
            raise ValueError("Party has no name")

        # Determine party type
        if record.get("is_customer") and record.get("is_supplier"):
            party_type = "both"
        elif record.get("is_customer"):
            party_type = "customer"
        elif record.get("is_supplier"):
            party_type = "supplier"
        else:
            party_type = "other"

        return {
            "unified_type": "party",
            "source_id": name,
            "party_code": self._slugify(name),
            "party_name": name,
            "party_type": party_type,
            "email": record.get("email") or None,
            "phone": record.get("mobile") or None,
            "address": record.get("address") or None,
            "gstin": record.get("gstin") or None,
            "is_active": True,
            "raw": record,
        }
