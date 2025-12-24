"""Page behaviors for content expansion (Browsertrix-level)."""

import asyncio
from dataclasses import dataclass, field
from typing import Callable

from playwright.async_api import Page

from national_treasure.core.models import BehaviorStats


@dataclass
class BehaviorOptions:
    """Options for page behaviors."""

    max_total_time_ms: int = 120000  # 2 minutes total
    max_behavior_time_ms: int = 30000  # 30 seconds per behavior
    action_delay_ms: int = 300  # Delay between actions
    scroll_step_px: int = 500  # Scroll step size
    max_scroll_attempts: int = 50  # Max scroll iterations
    max_infinite_scroll_pages: int = 10  # Max infinite scroll pages

    # Enable/disable specific behaviors
    dismiss_overlays: bool = True
    scroll_to_load: bool = True
    expand_content: bool = True
    click_tabs: bool = True
    navigate_carousels: bool = True
    expand_comments: bool = True
    handle_infinite_scroll: bool = True


class PageBehaviors:
    """Execute page behaviors to expose hidden content."""

    def __init__(self, options: BehaviorOptions | None = None):
        """Initialize with options."""
        self.options = options or BehaviorOptions()

    async def run_all(self, page: Page) -> BehaviorStats:
        """Run all enabled behaviors.

        Args:
            page: Playwright page

        Returns:
            Statistics about behaviors run
        """
        stats = BehaviorStats()
        start_time = asyncio.get_event_loop().time()

        behaviors: list[tuple[str, Callable, bool]] = [
            ("overlays", self._dismiss_overlays, self.options.dismiss_overlays),
            ("scroll", self._scroll_to_load_all, self.options.scroll_to_load),
            ("expand", self._expand_all_content, self.options.expand_content),
            ("tabs", self._click_all_tabs, self.options.click_tabs),
            ("carousels", self._navigate_carousels, self.options.navigate_carousels),
            ("comments", self._expand_comments, self.options.expand_comments),
            ("infinite", self._handle_infinite_scroll, self.options.handle_infinite_scroll),
        ]

        for name, behavior, enabled in behaviors:
            if not enabled:
                continue

            # Check total time limit
            elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
            if elapsed >= self.options.max_total_time_ms:
                break

            try:
                result = await asyncio.wait_for(
                    behavior(page),
                    timeout=self.options.max_behavior_time_ms / 1000,
                )
                self._update_stats(stats, name, result)
            except asyncio.TimeoutError:
                pass  # Behavior timed out, continue with next
            except Exception:
                pass  # Behavior failed, continue with next

        stats.duration_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
        return stats

    def _update_stats(self, stats: BehaviorStats, name: str, result: int) -> None:
        """Update stats based on behavior result."""
        if name == "overlays":
            stats.overlays_dismissed = result
        elif name == "scroll":
            stats.scroll_depth = result
        elif name == "expand":
            stats.elements_expanded = result
        elif name == "tabs":
            stats.tabs_clicked = result
        elif name == "carousels":
            stats.carousel_slides = result
        elif name == "comments":
            stats.comments_loaded = result
        elif name == "infinite":
            stats.infinite_scroll_pages = result

    async def _dismiss_overlays(self, page: Page) -> int:
        """Dismiss cookie banners, modals, and popups."""
        dismissed = 0

        # Common overlay selectors
        overlay_selectors = [
            # Cookie banners
            "[class*='cookie'] button[class*='accept']",
            "[class*='cookie'] button[class*='agree']",
            "[class*='consent'] button[class*='accept']",
            "[id*='cookie'] button",
            ".cc-dismiss",
            "#onetrust-accept-btn-handler",
            ".cookie-banner button",

            # Modal close buttons
            "[class*='modal'] [class*='close']",
            "[class*='modal'] button[aria-label*='close']",
            "[class*='popup'] [class*='close']",
            ".modal-close",
            "button[class*='dismiss']",

            # Generic close buttons
            "[aria-label='Close']",
            "[aria-label='Dismiss']",
            "button.close",
        ]

        for selector in overlay_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        await element.click()
                        dismissed += 1
                        await asyncio.sleep(self.options.action_delay_ms / 1000)
            except Exception:
                continue

        # Press Escape to close any remaining modals
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass

        # Remove fixed/sticky overlays by modifying CSS
        try:
            await page.evaluate("""
                () => {
                    const overlays = document.querySelectorAll(
                        '[style*="position: fixed"], [style*="position: sticky"]'
                    );
                    overlays.forEach(el => {
                        if (el.offsetHeight > window.innerHeight * 0.5) {
                            el.remove();
                        }
                    });
                }
            """)
        except Exception:
            pass

        return dismissed

    async def _scroll_to_load_all(self, page: Page) -> int:
        """Scroll to load lazy content."""
        scroll_depth = 0

        for _ in range(self.options.max_scroll_attempts):
            # Get current scroll position
            prev_height = await page.evaluate("() => document.body.scrollHeight")

            # Scroll down
            await page.evaluate(f"() => window.scrollBy(0, {self.options.scroll_step_px})")
            scroll_depth += self.options.scroll_step_px

            # Wait for content to load
            await asyncio.sleep(self.options.action_delay_ms / 1000)

            # Check if we've reached the bottom
            current_height = await page.evaluate("() => document.body.scrollHeight")
            scroll_position = await page.evaluate(
                "() => window.scrollY + window.innerHeight"
            )

            if scroll_position >= current_height and current_height == prev_height:
                break

        # Scroll back to top
        await page.evaluate("() => window.scrollTo(0, 0)")

        return scroll_depth

    async def _expand_all_content(self, page: Page) -> int:
        """Expand accordions, details, and collapsible content."""
        expanded = 0

        # Expand <details> elements
        try:
            details = await page.query_selector_all("details:not([open])")
            for detail in details:
                try:
                    await detail.evaluate("el => el.open = true")
                    expanded += 1
                except Exception:
                    continue
        except Exception:
            pass

        # Click "read more" / "show more" buttons
        expand_selectors = [
            "[class*='read-more']",
            "[class*='show-more']",
            "[class*='expand']",
            "[class*='see-more']",
            "button[class*='more']",
            "a[class*='more']",
            "[aria-expanded='false']",
        ]

        for selector in expand_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        await element.click()
                        expanded += 1
                        await asyncio.sleep(self.options.action_delay_ms / 1000)
            except Exception:
                continue

        return expanded

    async def _click_all_tabs(self, page: Page) -> int:
        """Click through all tabs to load their content."""
        clicked = 0

        tab_selectors = [
            "[role='tab']",
            ".tab",
            "[class*='tab-']",
            ".nav-link",
            "[data-toggle='tab']",
        ]

        for selector in tab_selectors:
            try:
                tabs = await page.query_selector_all(selector)
                for tab in tabs:
                    if await tab.is_visible():
                        await tab.click()
                        clicked += 1
                        await asyncio.sleep(self.options.action_delay_ms / 1000)
            except Exception:
                continue

        return clicked

    async def _navigate_carousels(self, page: Page) -> int:
        """Navigate through carousels and sliders."""
        slides = 0

        carousel_selectors = [
            "[class*='carousel'] [class*='next']",
            "[class*='slider'] [class*='next']",
            "[class*='swiper'] [class*='next']",
            ".slick-next",
            "[aria-label*='next']",
        ]

        for selector in carousel_selectors:
            try:
                next_buttons = await page.query_selector_all(selector)
                for button in next_buttons:
                    # Click next multiple times to go through carousel
                    for _ in range(5):
                        if await button.is_visible():
                            await button.click()
                            slides += 1
                            await asyncio.sleep(self.options.action_delay_ms / 1000)
            except Exception:
                continue

        return slides

    async def _expand_comments(self, page: Page) -> int:
        """Load and expand comment sections."""
        loaded = 0

        comment_selectors = [
            "[class*='comment'] [class*='load-more']",
            "[class*='comment'] [class*='show-more']",
            "[class*='reply'] button",
            ".load-comments",
            "[class*='comments'] button",
        ]

        for selector in comment_selectors:
            try:
                buttons = await page.query_selector_all(selector)
                for button in buttons:
                    if await button.is_visible():
                        await button.click()
                        loaded += 1
                        await asyncio.sleep(self.options.action_delay_ms / 1000)
            except Exception:
                continue

        return loaded

    async def _handle_infinite_scroll(self, page: Page) -> int:
        """Handle infinite scroll pages."""
        pages_loaded = 0

        for _ in range(self.options.max_infinite_scroll_pages):
            # Get current content count
            prev_count = await page.evaluate(
                "() => document.body.querySelectorAll('*').length"
            )

            # Scroll to bottom
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)  # Wait for content to load

            # Check if new content loaded
            new_count = await page.evaluate(
                "() => document.body.querySelectorAll('*').length"
            )

            if new_count > prev_count:
                pages_loaded += 1
            else:
                break  # No new content, stop scrolling

        return pages_loaded


async def run_behaviors(page: Page, options: BehaviorOptions | None = None) -> BehaviorStats:
    """Convenience function to run all behaviors.

    Args:
        page: Playwright page
        options: Behavior options

    Returns:
        BehaviorStats
    """
    behaviors = PageBehaviors(options)
    return await behaviors.run_all(page)
