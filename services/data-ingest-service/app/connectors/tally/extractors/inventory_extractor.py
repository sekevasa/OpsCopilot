"""Inventory extractor for Tally Prime 7.

Extracts inventory movements and current stock balances from Tally.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

# Inward voucher types (increase stock)
_INWARD_TYPES = {"Purchase", "Receipt Note", "Sales Return", "Stock Journal"}


class InventoryExtractor(BaseExtractor):
    """Extract inventory movements and stock balance data from Tally Prime 7."""

    async def extract(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract inventory data from Tally.

        Fetches both stock movements (voucher-level) and current stock balances.

        Args:
            from_date: Start date for movements (YYYYMMDD).
            to_date: End date for movements (YYYYMMDD).
            **kwargs: Optionally pass ``include_movements=False`` or
                ``include_balances=False``.

        Returns:
            Combined list of movement and balance records.
        """
        records: List[Dict[str, Any]] = []

        if kwargs.get("include_movements", True):
            movements = await self.extract_movements(from_date, to_date)
            records.extend(movements)
            logger.info("Extracted %d inventory movements from Tally", len(movements))

        if kwargs.get("include_balances", True):
            balances = await self.extract_stock_balances()
            records.extend(balances)
            logger.info("Extracted %d stock balance records from Tally", len(balances))

        return records

    async def extract_movements(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Extract inventory movement records from Tally vouchers.

        Returns:
            List of movement dictionaries.
        """
        root = await self.connection.export_collection(
            collection_name="Vouchers",
            report_name="Inventory Vouchers",
            from_date=from_date,
            to_date=to_date,
        )

        records: List[Dict[str, Any]] = []
        for voucher in self._iter_collection(root, "VOUCHER"):
            v_type = self._text(voucher, "VOUCHERTYPENAME")
            v_number = self._text(voucher, "VOUCHERNUMBER")
            v_date = self._text(voucher, "DATE")

            for entry in self._iter_collection(voucher, "INVENTORYENTRIES.LIST"):
                item_name = self._text(entry, "STOCKITEMNAME")
                if not item_name:
                    continue
                qty_str = self._text(entry, "ACTUALQTY")
                qty_parts = qty_str.split() if qty_str else []
                qty = float(qty_parts[0]) if qty_parts else self._float(entry, "ACTUALQTY")
                uom = qty_parts[1] if len(qty_parts) > 1 else None

                record = {
                    "record_type": "inventory_movement",
                    "item_name": item_name,
                    "voucher_number": v_number,
                    "voucher_type": v_type,
                    "date": v_date,
                    "quantity": abs(qty),
                    "rate": self._float(entry, "RATE"),
                    "uom": uom,
                    "batch_name": self._text(entry, "BATCHNAME"),
                    "godown": self._text(entry, "GODOWNNAME"),
                    "is_inward": v_type in _INWARD_TYPES,
                    "net_value": self._float(entry, "AMOUNT"),
                }
                records.append(record)

            if len(records) >= self.batch_size:
                break

        return records

    async def extract_stock_balances(self) -> List[Dict[str, Any]]:
        """Extract current closing stock balances from Tally.

        Returns:
            List of stock balance dictionaries.
        """
        root = await self.connection.export_collection(
            collection_name="Stock Items",
            report_name="Stock Summary",
        )

        records: List[Dict[str, Any]] = []
        for item in self._iter_collection(root, "STOCKITEM"):
            name = self._text(item, "NAME") or item.get("NAME", "")
            if not name:
                continue
            record = {
                "record_type": "stock_balance",
                "item_name": name,
                "godown": self._text(item, "GODOWNNAME"),
                "quantity": self._float(item, "CLOSINGBALANCE"),
                "rate": self._float(item, "CLOSINGRATE"),
                "value": self._float(item, "CLOSINGVALUE"),
                "uom": self._text(item, "BASEUNITS"),
            }
            records.append(record)

        return records[: self.batch_size]
