"""Base transformer for Tally data transformation."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseTransformer(ABC):
    """Abstract base class for Tally data transformers.

    Transformers convert raw Tally records (as produced by the extractors)
    into the unified platform schema.
    """

    @abstractmethod
    def transform(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a list of raw Tally records to unified schema.

        Args:
            records: Raw records from a Tally extractor.

        Returns:
            Transformed records ready for ingestion into the unified platform.
        """

    def transform_batch(
        self, records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Transform records and skip any that raise errors.

        Wraps :meth:`transform` and logs individual record failures so that a
        single bad record does not abort the whole batch.

        Args:
            records: Raw records to transform.

        Returns:
            List of successfully transformed records.
        """
        results: List[Dict[str, Any]] = []
        failed = 0
        for record in records:
            try:
                transformed = self._transform_one(record)
                if transformed:
                    results.append(transformed)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                logger.warning(
                    "Failed to transform record %s: %s",
                    record.get("name", record.get("voucher_number", "?")),
                    exc,
                )
        if failed:
            logger.warning("Skipped %d records due to transformation errors", failed)
        return results

    def _transform_one(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single record.  Override in subclasses if needed."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Shared helper utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _slugify(name: str) -> str:
        """Convert a Tally name to a safe slug for use as a code/ID.

        Args:
            name: Raw Tally name string.

        Returns:
            Slugified string (uppercase, spaces → underscores).
        """
        return name.strip().upper().replace(" ", "_").replace("/", "_")

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        """Coerce *value* to float, returning *default* on failure."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
