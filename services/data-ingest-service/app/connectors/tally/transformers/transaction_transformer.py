"""Transaction transformer for Tally Prime 7.

Transforms raw Tally voucher records to the unified transaction schema.
"""

import logging
from typing import Any, Dict, List

from .base_transformer import BaseTransformer

logger = logging.getLogger(__name__)


class TransactionTransformer(BaseTransformer):
    """Transform Tally voucher records to the unified transaction schema."""

    def transform(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of voucher/inventory records.

        Args:
            records: Raw records from :class:`VoucherExtractor` or
                :class:`InventoryExtractor`.

        Returns:
            List of unified transaction/inventory dictionaries.
        """
        return self.transform_batch(records)

    def _transform_one(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch based on ``record_type``."""
        record_type = record.get("record_type", "")
        if record_type == "voucher":
            return self._transform_voucher(record)
        if record_type == "inventory_movement":
            return self._transform_inventory_movement(record)
        if record_type == "stock_balance":
            return self._transform_stock_balance(record)
        if record_type == "ledger":
            return self._transform_ledger(record)
        logger.debug("Unknown transaction record_type '%s', skipping", record_type)
        return {}

    def _transform_voucher(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Tally voucher to the unified transaction schema.

        Args:
            record: Raw voucher dictionary.

        Returns:
            Unified transaction dictionary.
        """
        voucher_number = record.get("voucher_number", "")
        if not voucher_number:
            raise ValueError("Voucher has no voucher_number")

        line_items = []
        for entry in record.get("ledger_entries", []):
            line_items.append({
                "ledger_name": entry.get("ledger_name"),
                "amount": self._safe_float(entry.get("amount")),
                "cost_centre": entry.get("cost_centre"),
            })
        for entry in record.get("inventory_entries", []):
            line_items.append({
                "item_name": entry.get("item_name"),
                "quantity": self._safe_float(entry.get("quantity")),
                "rate": self._safe_float(entry.get("rate")),
                "amount": self._safe_float(entry.get("amount")),
                "uom": entry.get("uom"),
                "batch_name": entry.get("batch_name"),
            })

        return {
            "unified_type": "transaction",
            "source_id": voucher_number,
            "transaction_type": record.get("voucher_type", ""),
            "transaction_date": self._normalise_date(record.get("date", "")),
            "party_name": record.get("party_name") or None,
            "amount": self._safe_float(record.get("amount")),
            "currency": "INR",
            "reference": record.get("reference") or None,
            "narration": record.get("narration") or None,
            "line_items": line_items,
            "is_cancelled": bool(record.get("is_cancelled")),
            "raw": record,
        }

    def _transform_inventory_movement(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Tally inventory movement to the unified schema."""
        return {
            "unified_type": "inventory_movement",
            "source_id": f"{record.get('voucher_number', '')}_{record.get('item_name', '')}",
            "item_name": record.get("item_name", ""),
            "voucher_number": record.get("voucher_number", ""),
            "voucher_type": record.get("voucher_type", ""),
            "transaction_date": self._normalise_date(record.get("date", "")),
            "quantity": self._safe_float(record.get("quantity")),
            "rate": self._safe_float(record.get("rate")),
            "uom": record.get("uom"),
            "batch_name": record.get("batch_name"),
            "godown": record.get("godown"),
            "is_inward": bool(record.get("is_inward")),
            "net_value": self._safe_float(record.get("net_value")),
            "raw": record,
        }

    def _transform_stock_balance(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Tally stock balance to the unified schema."""
        return {
            "unified_type": "stock_balance",
            "source_id": f"{record.get('item_name', '')}_{record.get('godown', 'main')}",
            "item_name": record.get("item_name", ""),
            "godown": record.get("godown"),
            "quantity": self._safe_float(record.get("quantity")),
            "rate": self._safe_float(record.get("rate")),
            "value": self._safe_float(record.get("value")),
            "uom": record.get("uom"),
            "raw": record,
        }

    def _transform_ledger(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Map a Tally ledger to the unified schema."""
        name = record.get("name", "")
        if not name:
            raise ValueError("Ledger has no name")
        return {
            "unified_type": "ledger",
            "source_id": name,
            "ledger_name": name,
            "parent_group": record.get("parent", ""),
            "opening_balance": self._safe_float(record.get("opening_balance")),
            "closing_balance": self._safe_float(record.get("closing_balance")),
            "is_revenue": bool(record.get("is_revenue")),
            "raw": record,
        }

    @staticmethod
    def _normalise_date(date_str: str) -> str:
        """Normalise Tally date strings to ISO format (YYYY-MM-DD).

        Tally may return dates as ``YYYYMMDD`` or ``DD-MM-YYYY``.

        Args:
            date_str: Raw date string.

        Returns:
            ISO-formatted date string, or original if parsing fails.
        """
        if not date_str:
            return date_str
        cleaned = date_str.strip()
        if len(cleaned) == 8 and cleaned.isdigit():
            # YYYYMMDD
            return f"{cleaned[:4]}-{cleaned[4:6]}-{cleaned[6:8]}"
        if "-" in cleaned and len(cleaned) == 10:
            parts = cleaned.split("-")
            if len(parts) == 3 and len(parts[0]) == 2:
                # DD-MM-YYYY → YYYY-MM-DD
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        return cleaned
