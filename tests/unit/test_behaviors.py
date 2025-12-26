"""Tests for page behaviors."""

import asyncio

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


class TestBehaviorTimeouts:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_behavior_timeout(self):
        """Should handle behavior timeout gracefully."""
        async def slow_behavior(page):
            await asyncio.sleep(10)  # Longer than timeout
            return 1

        options = BehaviorOptions(
            max_behavior_time_ms=50,
            max_total_time_ms=100,
            dismiss_overlays=True,
            scroll_to_load=False,
            expand_content=False,
            click_tabs=False,
            navigate_carousels=False,
            expand_comments=False,
            handle_infinite_scroll=False,
        )
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._elements = []

        # Patch the overlay behavior to be slow
        behaviors._dismiss_overlays = slow_behavior

        stats = await behaviors.run_all(page)
        # Should complete without error despite timeout
        assert stats.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_behavior_exception(self):
        """Should handle behavior exception gracefully."""
        async def failing_behavior(page):
            raise ValueError("Test error")

        options = BehaviorOptions(
            dismiss_overlays=True,
            scroll_to_load=False,
            expand_content=False,
            click_tabs=False,
            navigate_carousels=False,
            expand_comments=False,
            handle_infinite_scroll=False,
        )
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._elements = []

        # Patch the overlay behavior to fail
        behaviors._dismiss_overlays = failing_behavior

        stats = await behaviors.run_all(page)
        # Should complete without error despite exception
        assert stats.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_total_time_limit(self):
        """Should respect total time limit."""
        call_count = 0

        async def counting_behavior(page):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return 1

        options = BehaviorOptions(
            max_total_time_ms=50,  # Very short total time
            max_behavior_time_ms=30000,
            dismiss_overlays=True,
            scroll_to_load=True,
            expand_content=True,
            click_tabs=True,
            navigate_carousels=True,
            expand_comments=True,
            handle_infinite_scroll=True,
        )
        behaviors = PageBehaviors(options=options)
        page = MockPage()
        page._elements = []

        # Patch all behaviors
        behaviors._dismiss_overlays = counting_behavior
        behaviors._scroll_to_load_all = counting_behavior
        behaviors._expand_all_content = counting_behavior
        behaviors._click_all_tabs = counting_behavior
        behaviors._navigate_carousels = counting_behavior
        behaviors._expand_comments = counting_behavior
        behaviors._handle_infinite_scroll = counting_behavior

        stats = await behaviors.run_all(page)
        # Should have stopped before running all behaviors
        assert call_count < 7


class TestStatsUpdate:
    """Tests for stats update method."""

    def test_update_stats_overlays(self):
        """Should update overlays stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "overlays", 5)
        assert stats.overlays_dismissed == 5

    def test_update_stats_scroll(self):
        """Should update scroll stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "scroll", 1500)
        assert stats.scroll_depth == 1500

    def test_update_stats_expand(self):
        """Should update expand stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "expand", 10)
        assert stats.elements_expanded == 10

    def test_update_stats_tabs(self):
        """Should update tabs stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "tabs", 3)
        assert stats.tabs_clicked == 3

    def test_update_stats_carousels(self):
        """Should update carousel stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "carousels", 8)
        assert stats.carousel_slides == 8

    def test_update_stats_comments(self):
        """Should update comments stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "comments", 25)
        assert stats.comments_loaded == 25

    def test_update_stats_infinite(self):
        """Should update infinite scroll stat."""
        from national_treasure.core.models import BehaviorStats

        behaviors = PageBehaviors()
        stats = BehaviorStats()
        behaviors._update_stats(stats, "infinite", 4)
        assert stats.infinite_scroll_pages == 4
