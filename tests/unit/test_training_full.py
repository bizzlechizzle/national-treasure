"""Full training service tests for 100% coverage."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.services.scraper.training import TrainingService


class TestImportTrainingData:
    """Test import_training_data functionality."""

    @pytest.mark.asyncio
    async def test_import_with_merge_false(self, test_db):
        """Should clear existing data when merge=False."""
        service = TrainingService(db_path=test_db)

        # Add initial data
        await service.record_selector_outcome("old.com", "title", ".old", True, "Old")
        await service.record_url_pattern_outcome("old.com", "path", "/old/", True)

        # Import with merge=False (should clear old data)
        new_data = {
            "selectors": [
                {
                    "site": "new.com",
                    "field": "title",
                    "selector": ".new",
                    "success_count": 5,
                    "failure_count": 1,
                }
            ],
            "url_patterns": [
                {
                    "site": "new.com",
                    "pattern_type": "path",
                    "pattern": "/new/",
                    "success_count": 3,
                    "failure_count": 0,
                }
            ],
        }

        counts = await service.import_training_data(new_data, merge=False)

        assert counts["selectors"] == 1
        assert counts["url_patterns"] == 1

        # Old data should be gone
        old_selectors = await service.get_selectors_for_site("old.com")
        assert len(old_selectors) == 0

    @pytest.mark.asyncio
    async def test_import_with_merge_true(self, test_db):
        """Should merge with existing data when merge=True."""
        service = TrainingService(db_path=test_db)

        # Add initial data
        await service.record_selector_outcome("site.com", "title", ".title", True, "Title")

        # Import with merge=True
        new_data = {
            "selectors": [
                {
                    "site": "site.com",
                    "field": "title",
                    "selector": ".title",
                    "success_count": 5,
                    "failure_count": 1,
                }
            ],
            "url_patterns": [],
        }

        counts = await service.import_training_data(new_data, merge=True)
        assert counts["selectors"] == 1

        # Original + imported counts should combine
        selectors = await service.get_selectors_for_site("site.com")
        assert len(selectors) >= 1

    @pytest.mark.asyncio
    async def test_import_url_patterns_merge(self, test_db):
        """Should merge URL patterns correctly."""
        service = TrainingService(db_path=test_db)

        # Import URL patterns with merge
        data = {
            "selectors": [],
            "url_patterns": [
                {
                    "site": "test.com",
                    "pattern_type": "path",
                    "pattern": "/articles/",
                    "success_count": 10,
                    "failure_count": 2,
                }
            ],
        }

        counts = await service.import_training_data(data, merge=True)
        assert counts["url_patterns"] == 1

        # Import again - should merge
        counts2 = await service.import_training_data(data, merge=True)
        assert counts2["url_patterns"] == 1

    @pytest.mark.asyncio
    async def test_import_url_patterns_no_merge(self, test_db):
        """Should replace URL patterns when not merging."""
        service = TrainingService(db_path=test_db)

        # Add initial pattern
        await service.record_url_pattern_outcome("old.com", "query", "?page=", True)

        # Import without merge
        data = {
            "selectors": [],
            "url_patterns": [
                {
                    "site": "new.com",
                    "pattern_type": "path",
                    "pattern": "/new/",
                    "success_count": 5,
                    "failure_count": 0,
                }
            ],
        }

        counts = await service.import_training_data(data, merge=False)
        assert counts["url_patterns"] == 1

        # Old pattern should be gone
        old_pattern = await service.get_best_url_pattern("old.com", "query")
        assert old_pattern is None


class TestRecordUrlPatternSuccess:
    """Test URL pattern success recording."""

    @pytest.mark.asyncio
    async def test_record_url_pattern_update_success(self, test_db):
        """Should update success count for existing pattern."""
        service = TrainingService(db_path=test_db)

        # Record initial
        await service.record_url_pattern_outcome("site.com", "path", "/test/", True)

        # Record another success - should hit the update branch
        await service.record_url_pattern_outcome(
            "site.com", "path", "/test/", True,
            source_url="https://site.com/articles/1",
            result_url="https://site.com/test/1"
        )

        pattern = await service.get_best_url_pattern("site.com", "path")
        assert pattern is not None
        assert pattern.success_count >= 2


class TestGetBestUrlPatternNone:
    """Test get_best_url_pattern returning None."""

    @pytest.mark.asyncio
    async def test_get_best_url_pattern_no_data(self, test_db):
        """Should return None when no patterns exist."""
        service = TrainingService(db_path=test_db)

        result = await service.get_best_url_pattern("nonexistent.com", "path")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_best_url_pattern_different_type(self, test_db):
        """Should return None for different pattern type."""
        service = TrainingService(db_path=test_db)

        await service.record_url_pattern_outcome("site.com", "query", "?id=", True)

        # Request different type
        result = await service.get_best_url_pattern("site.com", "path")
        assert result is None
