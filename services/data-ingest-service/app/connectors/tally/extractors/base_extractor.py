"""Base extractor for Tally data extraction."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

from ..tally_connection import TallyConnection

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for all Tally data extractors.

    Subclasses implement :meth:`extract` to pull a specific category of data
    (masters, ledgers, vouchers, inventory) from Tally via XML requests.
    """

    def __init__(
        self,
        connection: TallyConnection,
        batch_size: int = 500,
    ):
        """Initialise the extractor.

        Args:
            connection: An active :class:`TallyConnection`.
            batch_size: Maximum records to return per extraction call.
        """
        self.connection = connection
        self.batch_size = batch_size

    @abstractmethod
    async def extract(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Extract data from Tally.

        Args:
            from_date: Optional start date (``YYYYMMDD``).
            to_date: Optional end date (``YYYYMMDD``).
            **kwargs: Extractor-specific parameters.

        Returns:
            List of raw record dictionaries.
        """

    # ------------------------------------------------------------------
    # XML parsing helpers shared by all extractors
    # ------------------------------------------------------------------

    @staticmethod
    def _text(element: Optional[ET.Element], tag: str, default: str = "") -> str:
        """Safely get text content of a child element.

        Args:
            element: Parent XML element.
            tag: Child tag name.
            default: Fallback value if not found.

        Returns:
            Stripped text content or *default*.
        """
        if element is None:
            return default
        child = element.find(tag)
        if child is None or child.text is None:
            return default
        return child.text.strip()

    @staticmethod
    def _float(element: Optional[ET.Element], tag: str, default: float = 0.0) -> float:
        """Safely parse a float from a child element's text.

        Args:
            element: Parent XML element.
            tag: Child tag name.
            default: Fallback value.

        Returns:
            Parsed float or *default*.
        """
        if element is None:
            return default
        child = element.find(tag)
        if child is None or not child.text:
            return default
        try:
            return float(child.text.strip().replace(",", ""))
        except ValueError:
            return default

    @staticmethod
    def _bool(element: Optional[ET.Element], tag: str, default: bool = False) -> bool:
        """Safely parse a boolean from a child element's text.

        Tally represents booleans as ``"Yes"``/``"No"`` or ``"TRUE"``/``"FALSE"``.

        Args:
            element: Parent XML element.
            tag: Child tag name.
            default: Fallback value.

        Returns:
            Parsed boolean or *default*.
        """
        if element is None:
            return default
        child = element.find(tag)
        if child is None or not child.text:
            return default
        return child.text.strip().lower() in ("yes", "true", "1")

    @staticmethod
    def _iter_collection(root: ET.Element, item_tag: str) -> List[ET.Element]:
        """Return all elements with *item_tag* anywhere under *root*.

        Args:
            root: Root XML element to search.
            item_tag: Tag name of the items to collect.

        Returns:
            List of matching elements.
        """
        return root.findall(f".//{item_tag}")
