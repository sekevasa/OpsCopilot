"""Ledger extractor for Tally Prime 7.

Extracts ledger accounts and their balances from Tally.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class LedgerExtractor(BaseExtractor):
    """Extract ledger account data from Tally Prime 7."""

    async def extract(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract all ledger accounts from Tally.

        Args:
            from_date: Optional start date for balance calculation (YYYYMMDD).
            to_date: Optional end date for balance calculation (YYYYMMDD).
            **kwargs: Not used currently.

        Returns:
            List of ledger account dictionaries.
        """
        root = await self.connection.export_collection(
            collection_name="Ledgers",
            report_name="Ledger",
            from_date=from_date,
            to_date=to_date,
        )

        records: List[Dict[str, Any]] = []
        for ledger in self._iter_collection(root, "LEDGER"):
            record = {
                "record_type": "ledger",
                "name": self._text(ledger, "NAME") or ledger.get("NAME", ""),
                "parent": self._text(ledger, "PARENT"),
                "opening_balance": self._float(ledger, "OPENINGBALANCE"),
                "closing_balance": self._float(ledger, "CLOSINGBALANCE"),
                "is_revenue": self._bool(ledger, "ISREVENUE"),
                "gst_duty_head": self._text(ledger, "GSTDUTYHEAD"),
                "tax_classification": self._text(ledger, "TAXCLASSIFICATIONNAME"),
            }
            if not record["name"]:
                record["name"] = ledger.get("NAME", "unknown")
            records.append(record)

        logger.info("Extracted %d ledger records from Tally", len(records))
        return records[: self.batch_size]
