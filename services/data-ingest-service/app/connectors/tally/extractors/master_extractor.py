"""Master data extractor for Tally Prime 7.

Extracts stock items (SKUs) and party masters (customers/suppliers) from Tally.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class MasterExtractor(BaseExtractor):
    """Extract master data (stock items and parties) from Tally Prime 7."""

    async def extract(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract all masters (stock items + parties) from Tally.

        Args:
            from_date: Unused for master data (masters are not date-filtered).
            to_date: Unused for master data.
            **kwargs: Optionally pass ``include_items=False`` or
                ``include_parties=False`` to skip a category.

        Returns:
            Combined list of stock item and party records.
        """
        records: List[Dict[str, Any]] = []

        if kwargs.get("include_items", True):
            items = await self.extract_stock_items()
            records.extend(items)
            logger.info("Extracted %d stock items from Tally", len(items))

        if kwargs.get("include_parties", True):
            parties = await self.extract_parties()
            records.extend(parties)
            logger.info("Extracted %d parties from Tally", len(parties))

        return records

    async def extract_stock_items(self) -> List[Dict[str, Any]]:
        """Fetch all stock items from Tally.

        Returns:
            List of stock item dictionaries.
        """
        root = await self.connection.export_collection(
            collection_name="Stock Items",
            report_name="Stock Items",
        )

        records: List[Dict[str, Any]] = []
        for item in self._iter_collection(root, "STOCKITEM"):
            record = {
                "record_type": "stock_item",
                "name": self._text(item, "NAME") or item.get("NAME", ""),
                "alias": self._text(item, "LANGUAGENAME.LIST/NAME.LIST/NAME"),
                "parent": self._text(item, "PARENT"),
                "uom": self._text(item, "BASEUNITS"),
                "opening_balance": self._float(item, "OPENINGBALANCE"),
                "opening_rate": self._float(item, "OPENINGRATE"),
                "opening_value": self._float(item, "OPENINGVALUE"),
                "is_batch_enabled": self._bool(item, "ISBATCHWISEON"),
                "gst_applicable": self._bool(item, "ISGSTAPPLICABLE"),
                "hsn_code": self._text(item, "HSNDETAILS.LIST/HSNCODE"),
                "description": self._text(item, "DESCRIPTION"),
            }
            # Prefer attribute NAME over child element
            if not record["name"]:
                record["name"] = item.get("NAME", "unknown")
            records.append(record)

        return records[: self.batch_size]

    async def extract_parties(self) -> List[Dict[str, Any]]:
        """Fetch all sundry debtors and creditors from Tally.

        Returns:
            List of party dictionaries.
        """
        root = await self.connection.export_collection(
            collection_name="Ledgers",
            report_name="Ledger",
            filters={"PARENT": "Sundry Debtors,Sundry Creditors"},
        )

        records: List[Dict[str, Any]] = []
        for ledger in self._iter_collection(root, "LEDGER"):
            parent = self._text(ledger, "PARENT")
            record = {
                "record_type": "party",
                "name": self._text(ledger, "NAME") or ledger.get("NAME", ""),
                "parent": parent,
                "address": self._text(ledger, "ADDRESS.LIST/ADDRESS"),
                "state": self._text(ledger, "COUNTRYNAME"),
                "country": self._text(ledger, "LEDGERCONTACT"),
                "mobile": self._text(ledger, "LEDMOBILE"),
                "email": self._text(ledger, "EMAIL"),
                "gstin": self._text(ledger, "PARTYGSTIN"),
                "pan": self._text(ledger, "INCOMETAXNUMBER"),
                "credit_limit": self._float(ledger, "CREDITLIMIT"),
                "credit_days": int(self._float(ledger, "BILLCREDITPERIOD")),
                "is_customer": "debtor" in parent.lower(),
                "is_supplier": "creditor" in parent.lower(),
                "opening_balance": self._float(ledger, "OPENINGBALANCE"),
            }
            if not record["name"]:
                record["name"] = ledger.get("NAME", "unknown")
            records.append(record)

        return records[: self.batch_size]
