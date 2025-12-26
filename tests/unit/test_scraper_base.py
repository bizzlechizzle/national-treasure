"""Tests for base scraper functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.services.scraper.base import BaseScraper
from national_treasure.services.scraper.training import TrainingService


class MockScraper(BaseScraper):
    """Mock implementation of BaseScraper for testing."""

    SITE_PATTERNS = ["example.com", "test.org"]
    SELECTORS = {
        "title": [".title", "h1", "#main-title"],
        "content": [".content", "article", "#content"],
        "link": ["a.main-link", "a[href]"],
    }

    async def extract(self, page, url):
        """Mock extract implementation."""
        return {"url": url}


class EmptyPatternScraper(BaseScraper):
    """Scraper with no patterns."""

    SITE_PATTERNS = []
    SELECTORS = {}

    async def extract(self, page, url):
        return {}


class TestBaseScraperInit:
    """Test BaseScraper initialization."""

    def test_init_with_training(self):
        """Should initialize with training service."""
        training = MagicMock(spec=TrainingService)
        scraper = MockScraper(training_service=training)

        assert scraper.training is training
        assert scraper._site == "example.com"

    def test_init_without_training(self):
        """Should initialize without training service."""
        scraper = MockScraper()

        assert scraper.training is None
        assert scraper._site == "example.com"

    def test_get_site_name_from_patterns(self):
        """Should extract site name from patterns."""
        scraper = MockScraper()
        assert scraper._site == "example.com"

    def test_get_site_name_empty_patterns(self):
        """Should use class name when no patterns."""
        scraper = EmptyPatternScraper()
        # "EmptyPatternScraper" -> "emptypattern" (lowercase, remove "scraper")
        assert scraper._site == "emptypattern"


class TestBaseScraperMatches:
    """Test URL matching."""

    def test_matches_url_positive(self):
        """Should match URLs in patterns."""
        assert MockScraper.matches_url("https://example.com/page") is True
        assert MockScraper.matches_url("http://test.org/page") is True

    def test_matches_url_negative(self):
        """Should not match URLs not in patterns."""
        assert MockScraper.matches_url("https://other.com/page") is False

    def test_matches_url_case_insensitive(self):
        """Should match case-insensitively."""
        assert MockScraper.matches_url("https://EXAMPLE.COM/page") is True


class TestExtractText:
    """Test text extraction."""

    @pytest.mark.asyncio
    async def test_extract_text_success(self):
        """Should extract text using selector."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="  Test Title  ")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_text(mock_page, "title")

        assert result == "Test Title"
        mock_page.query_selector.assert_called_once_with(".title")
        training.record_selector_outcome.assert_called_once_with(
            "example.com", "title", ".title", True, "Test Title"
        )

    @pytest.mark.asyncio
    async def test_extract_text_fallback(self):
        """Should try fallback selectors."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="Found")

        # First selector returns None, second returns element
        mock_page.query_selector = AsyncMock(side_effect=[None, mock_element])

        scraper = MockScraper()
        result = await scraper.extract_text(mock_page, "title")

        assert result == "Found"
        assert mock_page.query_selector.call_count == 2

    @pytest.mark.asyncio
    async def test_extract_text_not_found(self):
        """Should return None when not found."""
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        scraper = MockScraper()
        result = await scraper.extract_text(mock_page, "title")

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_text_required_raises(self):
        """Should raise when required field not found."""
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        scraper = MockScraper()

        with pytest.raises(ValueError, match="Could not extract required field"):
            await scraper.extract_text(mock_page, "title", required=True)

    @pytest.mark.asyncio
    async def test_extract_text_empty_result(self):
        """Should handle empty text result."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_text(mock_page, "title")

        assert result is None
        # All selectors are tried, each records failure for empty text
        assert training.record_selector_outcome.call_count == 3
        # Check that first selector was recorded as failure
        training.record_selector_outcome.assert_any_call(
            "example.com", "title", ".title", False
        )

    @pytest.mark.asyncio
    async def test_extract_text_exception(self):
        """Should handle exceptions gracefully."""
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(side_effect=Exception("Error"))

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_text(mock_page, "title")

        assert result is None
        # All selectors are tried, each records failure
        assert training.record_selector_outcome.call_count == 3
        training.record_selector_outcome.assert_any_call(
            "example.com", "title", ".title", False
        )

    @pytest.mark.asyncio
    async def test_extract_text_custom_selectors(self):
        """Should use custom selectors when provided."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.inner_text = AsyncMock(return_value="Custom")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        scraper = MockScraper()
        result = await scraper.extract_text(mock_page, "custom", selectors=["#custom"])

        assert result == "Custom"
        mock_page.query_selector.assert_called_with("#custom")


class TestExtractAttribute:
    """Test attribute extraction."""

    @pytest.mark.asyncio
    async def test_extract_attribute_success(self):
        """Should extract attribute value."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.get_attribute = AsyncMock(return_value="https://link.com")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_attribute(mock_page, "link", "href")

        assert result == "https://link.com"
        training.record_selector_outcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_attribute_not_found(self):
        """Should return None when attribute not found."""
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        scraper = MockScraper()
        result = await scraper.extract_attribute(mock_page, "link", "href")

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_attribute_empty_value(self):
        """Should handle empty attribute value."""
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.get_attribute = AsyncMock(return_value=None)
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_attribute(mock_page, "link", "href")

        assert result is None
        # All selectors are tried, each records failure
        assert training.record_selector_outcome.call_count == 2
        training.record_selector_outcome.assert_any_call(
            "example.com", "link", "a.main-link", False
        )

    @pytest.mark.asyncio
    async def test_extract_attribute_required_raises(self):
        """Should raise when required attribute not found."""
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        scraper = MockScraper()

        with pytest.raises(ValueError, match="Could not extract required field"):
            await scraper.extract_attribute(mock_page, "link", "href", required=True)

    @pytest.mark.asyncio
    async def test_extract_attribute_exception(self):
        """Should handle exceptions gracefully."""
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(side_effect=Exception("Error"))

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_attribute(mock_page, "link", "href")

        assert result is None
        training.record_selector_outcome.assert_called()


class TestExtractAllText:
    """Test extracting all matching text."""

    @pytest.mark.asyncio
    async def test_extract_all_text_success(self):
        """Should extract text from all elements."""
        mock_page = MagicMock()
        mock_elements = [
            MagicMock(inner_text=AsyncMock(return_value="  Item 1  ")),
            MagicMock(inner_text=AsyncMock(return_value="Item 2")),
            MagicMock(inner_text=AsyncMock(return_value="")),  # Empty, should skip
        ]
        mock_page.query_selector_all = AsyncMock(return_value=mock_elements)

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_all_text(mock_page, "title")

        assert result == ["Item 1", "Item 2"]
        training.record_selector_outcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_all_text_empty(self):
        """Should return empty list when no matches."""
        mock_page = MagicMock()
        mock_page.query_selector_all = AsyncMock(return_value=[])

        scraper = MockScraper()
        result = await scraper.extract_all_text(mock_page, "title")

        assert result == []

    @pytest.mark.asyncio
    async def test_extract_all_text_exception(self):
        """Should continue on exception."""
        mock_page = MagicMock()
        mock_elements = [MagicMock(inner_text=AsyncMock(return_value="Found"))]
        mock_page.query_selector_all = AsyncMock(
            side_effect=[Exception("Error"), mock_elements]
        )

        scraper = MockScraper()
        result = await scraper.extract_all_text(mock_page, "title")

        assert result == ["Found"]


class TestExtractWithJS:
    """Test JavaScript extraction."""

    @pytest.mark.asyncio
    async def test_extract_with_js_success(self):
        """Should extract data using JavaScript."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value={"data": "value"})

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_with_js(mock_page, "custom", "return document.title")

        assert result == {"data": "value"}
        training.record_selector_outcome.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_with_js_null_result(self):
        """Should handle null JS result."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        scraper = MockScraper()
        result = await scraper.extract_with_js(mock_page, "custom", "return null")

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_with_js_exception(self):
        """Should handle JS exceptions."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("JS Error"))

        training = MagicMock(spec=TrainingService)
        training.record_selector_outcome = AsyncMock()

        scraper = MockScraper(training_service=training)
        result = await scraper.extract_with_js(mock_page, "custom", "throw new Error()")

        assert result is None
        training.record_selector_outcome.assert_called_with(
            "example.com", "custom", "js:throw new Error()", False
        )


class TestExtractJSONLD:
    """Test JSON-LD extraction."""

    @pytest.mark.asyncio
    async def test_extract_json_ld_success(self):
        """Should extract JSON-LD data."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(
            return_value={"@type": "Article", "headline": "Test"}
        )

        scraper = MockScraper()
        result = await scraper.extract_json_ld(mock_page)

        assert result == {"@type": "Article", "headline": "Test"}

    @pytest.mark.asyncio
    async def test_extract_json_ld_not_found(self):
        """Should return None when no JSON-LD."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        scraper = MockScraper()
        result = await scraper.extract_json_ld(mock_page)

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_json_ld_exception(self):
        """Should handle exceptions."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("Error"))

        scraper = MockScraper()
        result = await scraper.extract_json_ld(mock_page)

        assert result is None


class TestExtractMetaTags:
    """Test meta tag extraction."""

    @pytest.mark.asyncio
    async def test_extract_meta_tags_success(self):
        """Should extract meta tags."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(
            return_value={
                "og:title": "Test Title",
                "og:description": "Test Description",
                "description": "Meta Description",
            }
        )

        scraper = MockScraper()
        result = await scraper.extract_meta_tags(mock_page)

        assert result["og:title"] == "Test Title"
        assert result["description"] == "Meta Description"

    @pytest.mark.asyncio
    async def test_extract_meta_tags_empty(self):
        """Should return empty dict when no meta tags."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        scraper = MockScraper()
        result = await scraper.extract_meta_tags(mock_page)

        assert result == {}

    @pytest.mark.asyncio
    async def test_extract_meta_tags_exception(self):
        """Should handle exceptions."""
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("Error"))

        scraper = MockScraper()
        result = await scraper.extract_meta_tags(mock_page)

        assert result == {}
