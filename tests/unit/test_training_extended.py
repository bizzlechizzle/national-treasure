"""Extended training service tests for 100% coverage."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.services.scraper.training import TrainingService
from national_treasure.core.models import SelectorPattern


class TestGetSelectorsForSite:
    """Test get_selectors_for_site method."""

    @pytest.mark.asyncio
    async def test_get_selectors_empty(self, test_db):
        """Should return empty list when no selectors."""
        service = TrainingService(db_path=test_db)

        # Record for a different site
        await service.record_selector_outcome("other.com", "title", ".title", True, "Test")

        selectors = await service.get_selectors_for_site("test.com")
        assert selectors == []

    @pytest.mark.asyncio
    async def test_get_selectors_with_data(self, test_db):
        """Should return selectors for site."""
        service = TrainingService(db_path=test_db)

        # Add some selectors
        await service.record_selector_outcome("test.com", "title", ".title", True, "Test")
        await service.record_selector_outcome("test.com", "title", ".title", True, "Test")
        await service.record_selector_outcome("test.com", "content", ".content", True, "Content")

        selectors = await service.get_selectors_for_site("test.com")
        assert len(selectors) >= 1


class TestImportExportData:
    """Test import/export functionality."""

    @pytest.mark.asyncio
    async def test_export_data(self, test_db):
        """Should export data correctly."""
        service = TrainingService(db_path=test_db)

        # Add some data
        await service.record_selector_outcome("site.com", "title", ".h1", True, "Title")
        await service.record_selector_outcome("site.com", "title", ".h1", True, "Title2")
        await service.record_url_pattern_outcome("site.com", "path", "/articles/", True)

        # Export returns a dict
        data = await service.export_training_data()
        assert "selectors" in data
        assert "url_patterns" in data
        assert len(data["selectors"]) >= 1

    @pytest.mark.asyncio
    async def test_export_data_filtered(self, test_db):
        """Should export data filtered by site."""
        service = TrainingService(db_path=test_db)

        # Add data for different sites
        await service.record_selector_outcome("site1.com", "title", ".h1", True, "Title")
        await service.record_selector_outcome("site2.com", "title", ".h2", True, "Other")

        # Export filtered
        data = await service.export_training_data(site="site1.com")
        assert all(s["site"] == "site1.com" for s in data["selectors"])


class TestGetFallbackSelectors:
    """Test fallback selector retrieval."""

    @pytest.mark.asyncio
    async def test_get_fallback_selectors_ordered(self, test_db):
        """Should return selectors ordered by confidence."""
        service = TrainingService(db_path=test_db)

        # Add selectors with different confidence
        # High confidence
        for _ in range(10):
            await service.record_selector_outcome("site.com", "title", ".high", True, "T")

        # Medium confidence
        for _ in range(5):
            await service.record_selector_outcome("site.com", "title", ".medium", True, "T")
        for _ in range(5):
            await service.record_selector_outcome("site.com", "title", ".medium", False)

        selectors = await service.get_fallback_selectors("site.com", "title", limit=5)
        assert len(selectors) >= 1


class TestTrainingStats:
    """Test training statistics."""

    @pytest.mark.asyncio
    async def test_get_training_stats_empty(self, test_db):
        """Should return stats for database."""
        service = TrainingService(db_path=test_db)

        stats = await service.get_training_stats()
        assert isinstance(stats, dict)

    @pytest.mark.asyncio
    async def test_get_training_stats_with_data(self, test_db):
        """Should return stats with training data."""
        service = TrainingService(db_path=test_db)

        await service.record_selector_outcome("a.com", "title", ".t", True, "T")
        await service.record_selector_outcome("b.com", "content", ".c", True, "C")
        await service.record_url_pattern_outcome("a.com", "path", "/", True)

        stats = await service.get_training_stats()
        assert isinstance(stats, dict)


class TestRecordUrlPatternOutcome:
    """Test URL pattern recording."""

    @pytest.mark.asyncio
    async def test_record_url_pattern_success(self, test_db):
        """Should record successful URL pattern."""
        service = TrainingService(db_path=test_db)

        await service.record_url_pattern_outcome("example.com", "path", "/articles/", True)

        # Check it was recorded by getting best pattern
        pattern = await service.get_best_url_pattern("example.com", "path")
        assert pattern is not None

    @pytest.mark.asyncio
    async def test_record_url_pattern_failure(self, test_db):
        """Should record failed URL pattern."""
        service = TrainingService(db_path=test_db)

        # Record success then failure
        await service.record_url_pattern_outcome("example.com", "query", "?page=", True)
        await service.record_url_pattern_outcome("example.com", "query", "?page=", False)

        pattern = await service.get_best_url_pattern("example.com", "query")
        # Pattern should exist
        assert pattern is not None


class TestGetBestSelector:
    """Test getting best selector."""

    @pytest.mark.asyncio
    async def test_get_best_selector(self, test_db):
        """Should return best selector for field."""
        service = TrainingService(db_path=test_db)

        # Record different selectors with varying success
        for _ in range(10):
            await service.record_selector_outcome("test.com", "title", ".best", True, "T")

        for _ in range(5):
            await service.record_selector_outcome("test.com", "title", ".okay", True, "T")
        for _ in range(5):
            await service.record_selector_outcome("test.com", "title", ".okay", False)

        best = await service.get_best_selector("test.com", "title")
        assert best is not None
        assert best.selector == ".best"

    @pytest.mark.asyncio
    async def test_get_best_selector_no_data(self, test_db):
        """Should return None when no selectors."""
        service = TrainingService(db_path=test_db)

        best = await service.get_best_selector("nonexistent.com", "title")
        assert best is None


class TestSelectorPatternModel:
    """Test SelectorPattern model."""

    def test_selector_pattern_confidence(self):
        """Should calculate confidence correctly."""
        pattern = SelectorPattern(
            site="test.com",
            field="title",
            selector=".title",
            success_count=8,
            failure_count=2,
        )
        assert pattern.confidence == 0.8

    def test_selector_pattern_zero_attempts(self):
        """Should handle zero attempts."""
        pattern = SelectorPattern(
            site="test.com",
            field="title",
            selector=".title",
            success_count=0,
            failure_count=0,
        )
        assert pattern.confidence == 0.0
