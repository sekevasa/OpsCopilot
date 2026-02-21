"""Tally Prime 7 connector – main connector class.

Implements the :class:`BaseConnector` interface and orchestrates extraction
and transformation of data from Tally Prime 7.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..base import BaseConnector
from .models import (
    TallyConnectorConfig,
    TallyConnectionConfig,
    TallyDataType,
    TallySyncMode,
)
from .tally_connection import TallyConnection, TallyConnectionError
from .extractors import (
    MasterExtractor,
    LedgerExtractor,
    VoucherExtractor,
    InventoryExtractor,
)
from .transformers import MasterTransformer, TransactionTransformer

logger = logging.getLogger(__name__)


class TallyConnector(BaseConnector):
    """Connector for Tally Prime 7 ERP software.

    Provides extraction and transformation of master data (stock items,
    parties), ledger accounts, vouchers (sales/purchase/payment/receipt)
    and inventory movements from Tally Prime 7 via its XML HTTP gateway.

    Usage::

        config = TallyConnectorConfig(
            connector_name="my-tally",
            connection=TallyConnectionConfig(host="localhost", port=9000),
        )
        connector = TallyConnector(config)
        await connector.connect()
        records = await connector.fetch_all(from_date="20240101", to_date="20240131")
        await connector.disconnect()
    """

    def __init__(self, config: TallyConnectorConfig):
        """Initialise the Tally connector.

        Args:
            config: Full connector configuration including connection details
                and sync preferences.
        """
        conn_str = f"{config.connection.host}:{config.connection.port}"
        super().__init__(
            connection_string=conn_str,
            timeout_seconds=config.connection.timeout_seconds,
        )
        self.config = config
        self._tally_conn = TallyConnection(config.connection)

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        """Connect to Tally Prime 7.

        Returns:
            ``True`` on success.

        Raises:
            TallyConnectionError: If the Tally server is unreachable.
        """
        result = await self._tally_conn.connect()
        self._is_connected = result
        return result

    async def disconnect(self) -> None:
        """Disconnect from Tally."""
        await self._tally_conn.disconnect()
        self._is_connected = False

    async def fetch_data(self, query: str) -> List[Dict[str, Any]]:
        """Fetch data using a query string.

        The *query* string maps to a Tally data type keyword:
        ``"masters"``, ``"ledgers"``, ``"vouchers"``, ``"inventory"``, or
        ``"all"`` (default).

        Args:
            query: Data type keyword.

        Returns:
            List of raw record dictionaries.
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to Tally. Call connect() first.")

        data_type = query.lower().strip()
        return await self._extract_by_type(data_type)

    async def validate_connection(self) -> bool:
        """Validate that the Tally connection is healthy.

        Returns:
            ``True`` if Tally responds to a ping.
        """
        return await self._tally_conn.ping()

    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    async def fetch_all(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        data_types: Optional[List[TallyDataType]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract and transform all requested data types from Tally.

        Args:
            from_date: Start date for time-scoped data (YYYYMMDD).
            to_date: End date (YYYYMMDD).
            data_types: Override the connector's configured data types.

        Returns:
            List of unified schema records.
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to Tally. Call connect() first.")

        types_to_fetch = data_types or self.config.enabled_data_types
        if TallyDataType.ALL in types_to_fetch:
            types_to_fetch = [
                TallyDataType.MASTERS,
                TallyDataType.LEDGERS,
                TallyDataType.VOUCHERS,
                TallyDataType.INVENTORY,
            ]

        all_records: List[Dict[str, Any]] = []
        for data_type in types_to_fetch:
            try:
                raw = await self._extract_by_type(
                    data_type.value, from_date=from_date, to_date=to_date
                )
                transformed = self._transform(raw, data_type)
                all_records.extend(transformed)
                logger.info(
                    "Tally sync: extracted and transformed %d records for type '%s'",
                    len(transformed),
                    data_type.value,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Error extracting Tally data for type '%s': %s",
                    data_type.value,
                    exc,
                )

        return all_records

    async def sync(
        self,
        sync_mode: Optional[TallySyncMode] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        data_types: Optional[List[TallyDataType]] = None,
    ) -> Dict[str, Any]:
        """Run a complete sync operation and return statistics.

        Args:
            sync_mode: Override the connector's sync mode.
            from_date: Start date (YYYYMMDD) – required for incremental mode.
            to_date: End date (YYYYMMDD).
            data_types: Override connector data types.

        Returns:
            Dictionary with sync statistics (counts per type, duration, etc.).
        """
        mode = sync_mode or self.config.sync_mode
        start_time = datetime.utcnow()

        logger.info(
            "Starting Tally %s sync for connector '%s'",
            mode.value,
            self.config.connector_name,
        )

        if mode == TallySyncMode.FULL:
            # Full sync ignores date filters
            from_date = None
            to_date = None

        records = await self.fetch_all(
            from_date=from_date,
            to_date=to_date,
            data_types=data_types,
        )

        duration = (datetime.utcnow() - start_time).total_seconds()

        stats = self._compute_stats(records, duration)
        logger.info(
            "Tally sync completed in %.2fs – %d total records",
            duration,
            len(records),
        )
        return {"records": records, "stats": stats}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _extract_by_type(
        self,
        data_type: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Dispatch extraction to the correct extractor.

        Args:
            data_type: One of ``masters``, ``ledgers``, ``vouchers``,
                ``inventory``.
            from_date: Optional start date.
            to_date: Optional end date.

        Returns:
            Raw records list.
        """
        batch_size = self.config.batch_size

        if data_type == TallyDataType.MASTERS.value:
            extractor = MasterExtractor(self._tally_conn, batch_size)
            return await extractor.extract(from_date=from_date, to_date=to_date)

        if data_type == TallyDataType.LEDGERS.value:
            extractor = LedgerExtractor(self._tally_conn, batch_size)
            return await extractor.extract(from_date=from_date, to_date=to_date)

        if data_type == TallyDataType.VOUCHERS.value:
            extractor = VoucherExtractor(self._tally_conn, batch_size)
            return await extractor.extract(from_date=from_date, to_date=to_date)

        if data_type == TallyDataType.INVENTORY.value:
            extractor = InventoryExtractor(self._tally_conn, batch_size)
            return await extractor.extract(from_date=from_date, to_date=to_date)

        logger.warning("Unknown data type '%s', skipping extraction", data_type)
        return []

    def _transform(
        self, raw_records: List[Dict[str, Any]], data_type: TallyDataType
    ) -> List[Dict[str, Any]]:
        """Apply the appropriate transformer to raw records.

        Args:
            raw_records: Extracted raw records.
            data_type: Type of data to determine transformer selection.

        Returns:
            Transformed records.
        """
        if data_type == TallyDataType.MASTERS:
            return MasterTransformer().transform(raw_records)
        # Ledgers, vouchers, inventory all use the transaction transformer
        return TransactionTransformer().transform(raw_records)

    @staticmethod
    def _compute_stats(records: List[Dict[str, Any]], duration: float) -> Dict[str, Any]:
        """Compute sync statistics from the transformed records list.

        Args:
            records: Transformed records.
            duration: Sync duration in seconds.

        Returns:
            Statistics dictionary.
        """
        counts: Dict[str, int] = {}
        for record in records:
            unified_type = record.get("unified_type", "unknown")
            counts[unified_type] = counts.get(unified_type, 0) + 1

        return {
            "total_records": len(records),
            "duration_seconds": round(duration, 3),
            "by_type": counts,
        }
