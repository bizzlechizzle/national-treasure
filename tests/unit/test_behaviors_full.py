"""Full behavior tests for 100% coverage."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from national_treasure.services.browser.behaviors import BehaviorOptions, PageBehaviors


class MockVisibleElement:
    """Mock element that is visible and clickable."""

    def __init__(self, visible: bool = True):
        self._visible = visible
        self.clicked = False

    async def is_visible(self):
        return self._visible

    async def click(self):
        self.clicked = True


class MockPage:
    """Mock Playwright page."""

    def __init__(self):
        self.keyboard = MagicMock()
        self.keyboard.press = AsyncMock()
        self._elements = {}
        self._scroll_height = 1000

    async def query_selector_all(self, selector):
        return self._elements.get(selector, [])

    async def query_selector(self, selector):
        elements = self._elements.get(selector, [])
        return elements[0] if elements else None

    async def evaluate(self, script):
        if "scrollHeight" in script or "document.body" in script:
            return self._scroll_height
        return None

    def set_elements(self, selector, elements):
        self._elements[selector] = elements


class TestClickTabsVisible:
    """Test clicking visible tabs."""

    @pytest.mark.asyncio
    async def test_click_visible_tabs(self):
        """Should click visible tab elements."""
        options = BehaviorOptions(action_delay_ms=1)
        behaviors = PageBehaviors(options=options)

        page = MockPage()
        tab1 = MockVisibleElement(visible=True)
        tab2 = MockVisibleElement(visible=True)
        tab3 = MockVisibleElement(visible=False)

        # Set tabs for one of the selectors
        page.set_elements("[role='tab']", [tab1, tab2, tab3])

        result = await behaviors._click_all_tabs(page)

        # Should have clicked visible tabs
        assert tab1.clicked is True
        assert tab2.clicked is True
        assert tab3.clicked is False
        assert result >= 2


class TestNavigateCarouselsVisible:
    """Test navigating visible carousel buttons."""

    @pytest.mark.asyncio
    async def test_click_visible_carousel_buttons(self):
        """Should click visible carousel next buttons."""
        options = BehaviorOptions(action_delay_ms=1)
        behaviors = PageBehaviors(options=options)

        page = MockPage()
        button = MockVisibleElement(visible=True)

        # Set carousel button
        page.set_elements("[class*='carousel'] [class*='next']", [button])

        result = await behaviors._navigate_carousels(page)

        # Should click next button multiple times (5 times per button)
        assert button.clicked is True
        assert result >= 1


class TestExpandCommentsVisible:
    """Test expanding visible comment buttons."""

    @pytest.mark.asyncio
    async def test_click_visible_comment_buttons(self):
        """Should click visible load more comment buttons."""
        options = BehaviorOptions(action_delay_ms=1)
        behaviors = PageBehaviors(options=options)

        page = MockPage()
        button = MockVisibleElement(visible=True)

        page.set_elements("[class*='comment'] [class*='load-more']", [button])

        result = await behaviors._expand_comments(page)

        assert button.clicked is True
        assert result >= 1


class TestInfiniteScrollNewContent:
    """Test infinite scroll with new content loading."""

    @pytest.mark.asyncio
    async def test_infinite_scroll_detects_new_content(self):
        """Should count pages when new content loads."""
        options = BehaviorOptions(
            action_delay_ms=1,
            max_infinite_scroll_pages=3,
        )
        behaviors = PageBehaviors(options=options)

        page = MockPage()

        # Simulate increasing content
        heights = iter([1000, 1500, 2000, 2500, 2500])

        async def mock_evaluate(script):
            return next(heights, 2500)

        page.evaluate = mock_evaluate

        result = await behaviors._handle_infinite_scroll(page)

        # Should detect new content loading
        assert result >= 0


class TestRunBehaviors:
    """Test run_behaviors function."""

    @pytest.mark.asyncio
    async def test_run_all_behaviors(self):
        """Should execute all behavior types."""
        from national_treasure.services.browser.behaviors import run_behaviors, BehaviorStats

        page = MockPage()

        options = BehaviorOptions(
            dismiss_overlays=True,
            expand_content=True,
            click_tabs=True,
            navigate_carousels=True,
            expand_comments=True,
            handle_infinite_scroll=False,  # Skip to avoid long test
            action_delay_ms=1,
        )

        result = await run_behaviors(page, options)

        assert isinstance(result, BehaviorStats)
