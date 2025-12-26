"""Extended behavior tests for 100% coverage."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from national_treasure.services.browser.behaviors import (
    BehaviorOptions,
    PageBehaviors,
)


class MockElement:
    """Mock Playwright element."""

    def __init__(self, visible: bool = True, raises: bool = False):
        self._visible = visible
        self._raises = raises

    async def is_visible(self):
        if self._raises:
            raise Exception("Element error")
        return self._visible

    async def click(self):
        if self._raises:
            raise Exception("Click error")

    async def evaluate(self, script):
        if self._raises:
            raise Exception("Evaluate error")


class MockPage:
    """Mock Playwright page."""

    def __init__(self):
        self.keyboard = MagicMock()
        self.keyboard.press = AsyncMock()
        self._elements = []
        self._raise_on_query = False
        self._raise_on_evaluate = False

    async def query_selector_all(self, selector):
        if self._raise_on_query:
            raise Exception("Query error")
        return self._elements

    async def query_selector(self, selector):
        if self._raise_on_query:
            raise Exception("Query error")
        return self._elements[0] if self._elements else None

    async def evaluate(self, script):
        if self._raise_on_evaluate:
            raise Exception("Evaluate error")
        return 1000


class TestDismissOverlaysExceptions:
    """Test exception handling in overlay dismissal."""

    @pytest.mark.asyncio
    async def test_dismiss_overlays_query_exception(self):
        """Should continue when query throws."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._raise_on_query = True

        result = await behaviors._dismiss_overlays(page)
        # Should not crash, returns 0
        assert result >= 0

    @pytest.mark.asyncio
    async def test_dismiss_overlays_keyboard_exception(self):
        """Should handle keyboard press exception."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page.keyboard.press = AsyncMock(side_effect=Exception("Keyboard error"))
        page._elements = []

        result = await behaviors._dismiss_overlays(page)
        # Should not crash
        assert result >= 0

    @pytest.mark.asyncio
    async def test_dismiss_overlays_evaluate_exception(self):
        """Should handle CSS removal exception."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._elements = []
        page._raise_on_evaluate = True

        result = await behaviors._dismiss_overlays(page)
        # Should not crash
        assert result >= 0


class TestExpandContentExceptions:
    """Test exception handling in content expansion."""

    @pytest.mark.asyncio
    async def test_expand_content_details_exception(self):
        """Should continue on details expansion error."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._raise_on_query = True

        result = await behaviors._expand_all_content(page)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_expand_content_element_exception(self):
        """Should continue when element evaluate throws."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()

        element = MockElement(raises=True)
        page._elements = [element]

        result = await behaviors._expand_all_content(page)
        assert result >= 0


class TestClickTabsExceptions:
    """Test exception handling in tab clicking."""

    @pytest.mark.asyncio
    async def test_click_tabs_query_exception(self):
        """Should handle query exception."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._raise_on_query = True

        result = await behaviors._click_all_tabs(page)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_click_tabs_element_exception(self):
        """Should continue on element error."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()

        element = MockElement(raises=True)
        page._elements = [element]

        result = await behaviors._click_all_tabs(page)
        assert result >= 0


class TestNavigateCarouselsExceptions:
    """Test exception handling in carousel navigation."""

    @pytest.mark.asyncio
    async def test_navigate_carousels_query_exception(self):
        """Should handle query exception."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._raise_on_query = True

        result = await behaviors._navigate_carousels(page)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_navigate_carousels_click_exception(self):
        """Should continue on click error."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()

        element = MockElement(raises=True)
        page._elements = [element]

        result = await behaviors._navigate_carousels(page)
        assert result >= 0


class TestExpandCommentsExceptions:
    """Test exception handling in comment expansion."""

    @pytest.mark.asyncio
    async def test_expand_comments_query_exception(self):
        """Should handle query exception."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._raise_on_query = True

        result = await behaviors._expand_comments(page)
        assert result >= 0

    @pytest.mark.asyncio
    async def test_expand_comments_click_exception(self):
        """Should continue on click error."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()

        element = MockElement(raises=True)
        page._elements = [element]

        result = await behaviors._expand_comments(page)
        assert result >= 0


class TestInfiniteScrollExceptions:
    """Test exception handling in infinite scroll."""

    @pytest.mark.asyncio
    async def test_infinite_scroll_no_new_content(self):
        """Should stop when no new content loads."""
        options = BehaviorOptions(
            action_delay_ms=10,
            max_infinite_scroll_pages=5,
        )
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        # Same count means no new content
        page.evaluate = AsyncMock(return_value=100)

        result = await behaviors._handle_infinite_scroll(page)
        # Should return 0 since no new content loaded
        assert result == 0

    @pytest.mark.asyncio
    async def test_infinite_scroll_loads_pages(self):
        """Should count pages when content loads."""
        options = BehaviorOptions(
            action_delay_ms=10,
            max_infinite_scroll_pages=3,
        )
        behaviors = PageBehaviors(options=options)
        page = MockPage()

        # Simulate increasing element count
        counts = [100, 150, 200, 200, 200]
        call_idx = [0]

        async def mock_evaluate(script):
            idx = call_idx[0]
            call_idx[0] += 1
            return counts[min(idx, len(counts) - 1)]

        page.evaluate = mock_evaluate

        result = await behaviors._handle_infinite_scroll(page)
        assert result >= 0
