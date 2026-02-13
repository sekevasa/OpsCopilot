"""Pytest configuration for async tests."""

import pytest
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"
