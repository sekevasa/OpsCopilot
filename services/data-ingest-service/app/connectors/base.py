"""Data source connectors for various ERP/accounting systems."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base connector for all data sources."""

    def __init__(self, connection_string: str, timeout_seconds: int = 30):
        """Initialize connector.

        Args:
            connection_string: Connection details
            timeout_seconds: Connection timeout
        """
        self.connection_string = connection_string
        self.timeout_seconds = timeout_seconds
        self._is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to data source."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from data source."""
        pass

    @abstractmethod
    async def fetch_data(self, query: str) -> List[Dict[str, Any]]:
        """Fetch data from source."""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate connection is healthy."""
        pass

    @property
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._is_connected


class ERPConnector(BaseConnector):
    """Connector for ERP systems (SAP, NetSuite, Odoo)."""

    async def connect(self) -> bool:
        """Connect to ERP system."""
        logger.info(f"Connecting to ERP: {self.connection_string[:20]}...")
        # Simulate connection
        self._is_connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from ERP."""
        logger.info("Disconnecting from ERP")
        self._is_connected = False

    async def fetch_data(self, query: str) -> List[Dict[str, Any]]:
        """Fetch data from ERP system."""
        if not self._is_connected:
            raise ConnectionError("Not connected to ERP")

        logger.info(f"Fetching ERP data: {query[:50]}...")
        # Simulate data fetch
        return []

    async def validate_connection(self) -> bool:
        """Validate ERP connection."""
        if not self._is_connected:
            return False
        logger.debug("ERP connection validated")
        return True


class AccountingConnector(BaseConnector):
    """Connector for accounting systems (QuickBooks, Xero, FreshBooks)."""

    async def connect(self) -> bool:
        """Connect to accounting system."""
        logger.info(
            f"Connecting to Accounting: {self.connection_string[:20]}...")
        self._is_connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from accounting system."""
        logger.info("Disconnecting from Accounting")
        self._is_connected = False

    async def fetch_data(self, query: str) -> List[Dict[str, Any]]:
        """Fetch accounting data."""
        if not self._is_connected:
            raise ConnectionError("Not connected to Accounting")

        logger.info(f"Fetching accounting data: {query[:50]}...")
        return []

    async def validate_connection(self) -> bool:
        """Validate accounting connection."""
        if not self._is_connected:
            return False
        logger.debug("Accounting connection validated")
        return True


class InventoryConnector(BaseConnector):
    """Connector for inventory management systems."""

    async def connect(self) -> bool:
        """Connect to inventory system."""
        logger.info(
            f"Connecting to Inventory: {self.connection_string[:20]}...")
        self._is_connected = True
        return True

    async def disconnect(self) -> None:
        """Disconnect from inventory system."""
        logger.info("Disconnecting from Inventory")
        self._is_connected = False

    async def fetch_data(self, query: str) -> List[Dict[str, Any]]:
        """Fetch inventory data."""
        if not self._is_connected:
            raise ConnectionError("Not connected to Inventory")

        logger.info(f"Fetching inventory data: {query[:50]}...")
        return []

    async def validate_connection(self) -> bool:
        """Validate inventory connection."""
        if not self._is_connected:
            return False
        logger.debug("Inventory connection validated")
        return True


class ConnectorFactory:
    """Factory for creating appropriate connectors."""

    _connectors = {
        "erp": ERPConnector,
        "accounting": AccountingConnector,
        "inventory_system": InventoryConnector,
        "quality_control": InventoryConnector,
        "production": InventoryConnector,
    }

    @classmethod
    def create_connector(
        cls,
        source_type: str,
        connection_string: str,
        timeout_seconds: int = 30,
    ) -> BaseConnector:
        """Create appropriate connector based on source type.

        Args:
            source_type: Type of data source
            connection_string: Connection details
            timeout_seconds: Connection timeout

        Returns:
            Connector instance

        Raises:
            ValueError: If source type not supported
        """
        connector_class = cls._connectors.get(source_type.lower())
        if not connector_class:
            raise ValueError(f"Unsupported source type: {source_type}")

        logger.info(f"Creating connector for {source_type}")
        return connector_class(connection_string, timeout_seconds)
