"""Tests for training service."""

import pytest

from national_treasure.services.scraper.training import TrainingService


class TestTrainingService:
    """Tests for TrainingService."""

    @pytest.mark.asyncio
    async def test_record_selector_success(self, test_db):
        """Should record successful selector outcome."""
        service = TrainingService(db_path=test_db)

        await service.record_selector_outcome(
            site="example.com",
            field="title",
            selector="h1",
            success=True,
            extracted_value="Example Title",
        )

        # Get best selector
        pattern = await service.get_best_selector("example.com", "title")
        assert pattern is not None
        assert pattern.selector == "h1"
        assert pattern.success_count == 1
        assert pattern.failure_count == 0

    @pytest.mark.asyncio
    async def test_record_selector_failure(self, test_db):
        """Should record failed selector outcome."""
        service = TrainingService(db_path=test_db)

        await service.record_selector_outcome(
            site="example.com",
            field="title",
            selector="h1",
            success=False,
        )

        pattern = await service.get_best_selector(
            "example.com", "title", min_confidence=0.0
        )
        assert pattern is not None
        assert pattern.success_count == 0
        assert pattern.failure_count == 1

    @pytest.mark.asyncio
    async def test_confidence_threshold(self, test_db):
        """Should respect minimum confidence threshold."""
        service = TrainingService(db_path=test_db)

        # Record mostly failures
        for _ in range(8):
            await service.record_selector_outcome(
                "example.com", "title", "h1", success=False
            )
        for _ in range(2):
            await service.record_selector_outcome(
                "example.com", "title", "h1", success=True
            )

        # 20% confidence - below threshold
        pattern = await service.get_best_selector(
            "example.com", "title", min_confidence=0.5
        )
        assert pattern is None

    @pytest.mark.asyncio
    async def test_get_fallback_selectors(self, test_db):
        """Should return selectors ordered by confidence."""
        service = TrainingService(db_path=test_db)

        # Add selectors with different success rates
        for _ in range(10):
            await service.record_selector_outcome(
                "example.com", "title", ".best-selector", success=True
            )
        for _ in range(5):
            await service.record_selector_outcome(
                "example.com", "title", ".good-selector", success=True
            )
        for _ in range(5):
            await service.record_selector_outcome(
                "example.com", "title", ".good-selector", success=False
            )

        patterns = await service.get_fallback_selectors("example.com", "title")
        assert len(patterns) == 2
        assert patterns[0].selector == ".best-selector"  # 100% confidence
        assert patterns[1].selector == ".good-selector"  # 50% confidence

    @pytest.mark.asyncio
    async def test_url_pattern_outcome(self, test_db):
        """Should record URL pattern outcomes."""
        service = TrainingService(db_path=test_db)

        await service.record_url_pattern_outcome(
            site="bandcamp.com",
            pattern_type="image_url",
            pattern=r"_\d+\.jpg$",
            success=True,
            source_url="https://f4.bcbits.com/img/a123_10.jpg",
            result_url="https://f4.bcbits.com/img/a123_0.jpg",
        )

        pattern = await service.get_best_url_pattern(
            "bandcamp.com", "image_url"
        )
        assert pattern is not None
        assert pattern.success_count == 1

    @pytest.mark.asyncio
    async def test_export_training_data(self, test_db):
        """Should export training data."""
        service = TrainingService(db_path=test_db)

        await service.record_selector_outcome(
            "example.com", "title", "h1", success=True
        )

        data = await service.export_training_data()
        assert "selectors" in data
        assert len(data["selectors"]) == 1
        assert data["selectors"][0]["site"] == "example.com"

    @pytest.mark.asyncio
    async def test_import_training_data(self, test_db):
        """Should import training data."""
        service = TrainingService(db_path=test_db)

        data = {
            "selectors": [
                {
                    "site": "imported.com",
                    "field": "title",
                    "selector": ".imported",
                    "success_count": 5,
                    "failure_count": 1,
                }
            ],
            "url_patterns": [],
        }

        counts = await service.import_training_data(data)
        assert counts["selectors"] == 1

        pattern = await service.get_best_selector("imported.com", "title")
        assert pattern is not None
        assert pattern.success_count == 5

    @pytest.mark.asyncio
    async def test_training_stats(self, test_db):
        """Should return training statistics."""
        service = TrainingService(db_path=test_db)

        # Add some data
        for _ in range(5):
            await service.record_selector_outcome(
                "example.com", "title", "h1", success=True
            )
        for _ in range(3):
            await service.record_selector_outcome(
                "other.com", "content", ".content", success=True
            )

        stats = await service.get_training_stats()
        assert stats["selectors"]["total_patterns"] == 2
        assert stats["selectors"]["unique_sites"] == 2
        assert stats["selectors"]["total_successes"] == 8
