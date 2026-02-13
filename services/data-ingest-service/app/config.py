"""Configuration for data-ingest service."""

from shared.config import Settings
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Shared module


class DataIngestSettings(Settings):
    """Data ingest service specific settings."""

    service_name: str = "data-ingest-service"
    batch_processing_timeout: int = 300  # 5 minutes
    max_batch_size: int = 10000
