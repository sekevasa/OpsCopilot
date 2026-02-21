"""Voucher extractor for Tally Prime 7.

Extracts sales and purchase vouchers (and other transaction types) from Tally.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

# Voucher types to extract by default
DEFAULT_VOUCHER_TYPES = [
    "Sales",
    "Purchase",
    "Receipt",
    "Payment",
    "Journal",
    "Contra",
    "Credit Note",
    "Debit Note",
]


class VoucherExtractor(BaseExtractor):
    """Extract voucher (transaction) data from Tally Prime 7."""

    async def extract(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract vouchers from Tally.

        Args:
            from_date: Start date in YYYYMMDD format.
            to_date: End date in YYYYMMDD format.
            **kwargs: Optionally pass ``voucher_types`` (list[str]) to filter.

        Returns:
            List of voucher dictionaries.
        """
        voucher_types: List[str] = kwargs.get("voucher_types", DEFAULT_VOUCHER_TYPES)

        root = await self.connection.export_collection(
            collection_name="Vouchers",
            report_name="Voucher Register",
            from_date=from_date,
            to_date=to_date,
        )

        records: List[Dict[str, Any]] = []
        for voucher in self._iter_collection(root, "VOUCHER"):
            v_type = self._text(voucher, "VOUCHERTYPENAME")
            if voucher_types and v_type not in voucher_types:
                continue

            ledger_entries = self._extract_ledger_entries(voucher)
            inventory_entries = self._extract_inventory_entries(voucher)

            record = {
                "record_type": "voucher",
                "voucher_number": self._text(voucher, "VOUCHERNUMBER") or voucher.get("VCHNO", ""),
                "voucher_type": v_type,
                "date": self._text(voucher, "DATE"),
                "party_name": self._text(voucher, "PARTYLEDGERNAME"),
                "narration": self._text(voucher, "NARRATION"),
                "reference": self._text(voucher, "REFERENCE"),
                "amount": self._float(voucher, "AMOUNT"),
                "ledger_entries": ledger_entries,
                "inventory_entries": inventory_entries,
                "is_cancelled": self._bool(voucher, "ISCANCELLED"),
                "guid": voucher.get("GUID", ""),
            }
            records.append(record)

            if len(records) >= self.batch_size:
                break

        logger.info("Extracted %d vouchers from Tally", len(records))
        return records

    def _extract_ledger_entries(self, voucher_elem: Any) -> List[Dict[str, Any]]:
        """Parse all ledger entries from a VOUCHER element."""
        entries = []
        for entry in self._iter_collection(voucher_elem, "ALLLEDGERENTRIES.LIST"):
            entries.append({
                "ledger_name": self._text(entry, "LEDGERNAME"),
                "amount": self._float(entry, "AMOUNT"),
                "cost_centre": self._text(entry, "COSTCENTRENAME"),
                "narration": self._text(entry, "NARRATION"),
            })
        return entries

    def _extract_inventory_entries(self, voucher_elem: Any) -> List[Dict[str, Any]]:
        """Parse all inventory entries from a VOUCHER element."""
        entries = []
        for entry in self._iter_collection(voucher_elem, "INVENTORYENTRIES.LIST"):
            actual_qty_str = self._text(entry, "ACTUALQTY")
            entries.append({
                "item_name": self._text(entry, "STOCKITEMNAME"),
                "quantity": self._float(entry, "ACTUALQTY"),
                "rate": self._float(entry, "RATE"),
                "amount": self._float(entry, "AMOUNT"),
                "uom": actual_qty_str.split()[-1] if actual_qty_str else None,
                "batch_name": self._text(entry, "BATCHNAME"),
            })
        return entries
