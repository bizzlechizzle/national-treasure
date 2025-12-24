"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from national_treasure.core.database import init_database


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest_asyncio.fixture
async def test_db(temp_dir):
    """Create a test database."""
    db_path = temp_dir / "test.db"
    await init_database(str(db_path))
    yield str(db_path)


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/status/200",
    ]


@pytest.fixture
def sample_selectors():
    """Sample selectors for testing."""
    return {
        "title": ["h1", ".title", "#title", "[data-title]"],
        "content": [".content", "#content", "article", "main"],
        "image": ["img.main", ".hero img", "img[src*='large']"],
    }
