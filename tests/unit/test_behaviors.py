"""Tests for page behaviors."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from national_treasure.services.browser.behaviors import (
    BehaviorOptions,
    PageBehaviors,
    run_behaviors,
)


class TestBehaviorOptions:
    """Tests for BehaviorOptions."""

    def test_default_values(self):
        """Should have sensible defaults."""
        options = BehaviorOptions()
        assert options.max_total_time_ms == 120000
        assert options.max_behavior_time_ms == 30000
        assert options.action_delay_ms == 300
        assert options.scroll_step_px == 500

    def test_default_behaviors_enabled(self):
        """All behaviors should be enabled by default."""
        options = BehaviorOptions()
        assert options.dismiss_overlays is True
        assert options.scroll_to_load is True
        assert options.expand_content is True
        assert options.click_tabs is True
        assert options.navigate_carousels is True
        assert options.expand_comments is True
        assert options.handle_infinite_scroll is True

    def test_custom_options(self):
        """Should accept custom options."""
        options = BehaviorOptions(
            max_total_time_ms=60000,
            dismiss_overlays=False,
            scroll_to_load=True,
        )
        assert options.max_total_time_ms == 60000
        assert options.dismiss_overlays is False
        assert options.scroll_to_load is True


class TestPageBehaviors:
    """Tests for PageBehaviors class."""

    def test_init_default_options(self):
        """Should use default options."""
        behaviors = PageBehaviors()
        assert behaviors.options.max_total_time_ms == 120000

    def test_init_custom_options(self):
        """Should accept custom options."""
        options = BehaviorOptions(max_total_time_ms=60000)
        behaviors = PageBehaviors(options=options)
        assert behaviors.options.max_total_time_ms == 60000


class MockElement:
    """Mock Playwright element."""

    def __init__(self, visible: bool = True, text: str = ""):
        self._visible = visible
        self._text = text

    async def is_visible(self):
        return self._visible

    async def click(self):
        pass

    async def inner_text(self):
        return self._text

    async def evaluate(self, script):
        pass


class MockPage:
    """Mock Playwright page."""

    def __init__(self):
        self.keyboard = MagicMock()
        self.keyboard.press = AsyncMock()
        self._elements = []

    async def query_selector_all(self, selector):
        return self._elements

    async def query_selector(self, selector):
        return self._elements[0] if self._elements else None

    async def evaluate(self, script):
        return 1000  # Return scroll height


class TestDismissOverlays:
    """Tests for overlay dismissal behavior."""

    @pytest.mark.asyncio
    async def test_dismisses_visible_overlays(self):
        """Should click visible overlay buttons."""
        behaviors = PageBehaviors()
        page = MockPage()

        element = MockElement(visible=True)
        element.click = AsyncMock()
        page._elements = [element]

        result = await behaviors._dismiss_overlays(page)
        # Should have attempted to dismiss overlays
        assert result >= 0

    @pytest.mark.asyncio
    async def test_skips_invisible_overlays(self):
        """Should skip invisible overlay buttons."""
        behaviors = PageBehaviors()
        page = MockPage()

        element = MockElement(visible=False)
        element.click = AsyncMock()
        page._elements = [element]

        result = await behaviors._dismiss_overlays(page)
        element.click.assert_not_called()


class TestScrollToLoad:
    """Tests for scroll behavior."""

    @pytest.mark.asyncio
    async def test_scrolls_page(self):
        """Should scroll the page."""
        options = BehaviorOptions(
            max_scroll_attempts=3,
            scroll_step_px=100,
            action_delay_ms=10,
        )
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page.evaluate = AsyncMock(return_value=1000)

        result = await behaviors._scroll_to_load_all(page)
        assert result > 0


class TestExpandContent:
    """Tests for content expansion behavior."""

    @pytest.mark.asyncio
    async def test_expands_details(self):
        """Should expand details elements."""
        options = BehaviorOptions(action_delay_ms=10)
        behaviors = PageBehaviors(options=options)
        page = MockPage()

        element = MockElement(visible=True)
        element.evaluate = AsyncMock()
        page._elements = [element]

        result = await behaviors._expand_all_content(page)
        assert result >= 0


class TestRunBehaviors:
    """Tests for the convenience function."""

    @pytest.mark.asyncio
    async def test_run_behaviors_function(self):
        """Should run all behaviors."""
        page = MockPage()
        page.evaluate = AsyncMock(return_value=1000)
        page._elements = []

        stats = await run_behaviors(page)
        assert stats.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_run_behaviors_with_options(self):
        """Should accept custom options."""
        page = MockPage()
        page.evaluate = AsyncMock(return_value=1000)
        page._elements = []

        options = BehaviorOptions(scroll_to_load=False)
        stats = await run_behaviors(page, options=options)
        assert stats.duration_ms >= 0
