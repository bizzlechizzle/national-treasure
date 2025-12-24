"""Browser service with Playwright."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from national_treasure.core.config import get_config
from national_treasure.core.models import BrowserConfig, HeadlessMode

# Default user agent (Chrome on macOS)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Stealth launch arguments (anti-bot detection)
STEALTH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--disable-gpu",
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--lang=en-US,en",
    "--disable-extensions",
    "--disable-default-apps",
    "--disable-component-update",
]


class BrowserService:
    """Async context manager for browser automation.

    Usage:
        async with BrowserService() as service:
            async with service.page() as page:
                await page.goto("https://example.com")
                content = await page.content()
    """

    def __init__(
        self,
        config: BrowserConfig | None = None,
        headless: bool = True,
        profile_path: Path | None = None,
    ):
        """Initialize browser service.

        Args:
            config: Browser configuration (uses defaults if None)
            headless: Run in headless mode
            profile_path: Path to browser profile for persistent sessions
        """
        self.config = config or BrowserConfig()
        self.headless = headless
        self.profile_path = profile_path

        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> "BrowserService":
        """Enter async context - launch browser."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context - close browser."""
        await self.stop()

    async def start(self) -> None:
        """Start browser."""
        self._playwright = await async_playwright().start()

        # Determine headless mode
        headless = self.headless
        if self.config.headless_mode == HeadlessMode.VISIBLE:
            headless = False

        # Build launch arguments
        args = list(STEALTH_ARGS)
        if self.config.disable_automation_flag:
            args.append("--disable-blink-features=AutomationControlled")

        # Launch browser
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=args,
        )

        # Create context with viewport and user agent
        context_options = {
            "viewport": {
                "width": self.config.viewport_width,
                "height": self.config.viewport_height,
            },
            "user_agent": self.config.user_agent or DEFAULT_USER_AGENT,
        }

        # Use persistent context if profile path provided
        if self.profile_path:
            self._context = await self._playwright.chromium.launch_persistent_context(
                self.profile_path,
                headless=headless,
                args=args,
                **context_options,
            )
        else:
            self._context = await self._browser.new_context(**context_options)

        # Apply stealth scripts
        if self.config.stealth_enabled:
            await self._apply_stealth_scripts()

    async def stop(self) -> None:
        """Stop browser."""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _apply_stealth_scripts(self) -> None:
        """Apply stealth scripts to avoid bot detection."""
        # Remove webdriver flag
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Mock plugins
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)

        # Mock languages
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        # Override permissions
        await self._context.add_init_script("""
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

    @asynccontextmanager
    async def page(self) -> AsyncGenerator[Page, None]:
        """Create a new page in the browser context.

        Usage:
            async with service.page() as page:
                await page.goto("https://example.com")
        """
        if not self._context:
            raise RuntimeError("Browser not started. Use 'async with BrowserService():'")

        page = await self._context.new_page()
        try:
            yield page
        finally:
            await page.close()

    async def goto(
        self,
        page: Page,
        url: str,
        wait_until: str | None = None,
        timeout: int | None = None,
    ):
        """Navigate to URL with configured wait strategy.

        Args:
            page: Playwright page
            url: URL to navigate to
            wait_until: Override wait strategy (load, domcontentloaded, networkidle)
            timeout: Override timeout in milliseconds

        Returns:
            Response object
        """
        wait_strategy = wait_until or self.config.wait_strategy.value
        timeout_ms = timeout or self.config.default_timeout_ms

        response = await page.goto(
            url,
            wait_until=wait_strategy,
            timeout=timeout_ms,
        )
        return response

    async def inject_cookies(self, page: Page, cookies: list[dict]) -> None:
        """Inject cookies into the page context.

        Args:
            page: Playwright page
            cookies: List of cookie dicts with name, value, domain, etc.
        """
        playwright_cookies = []
        for cookie in cookies:
            playwright_cookies.append({
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie.get("domain", ""),
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", False),
                "httpOnly": cookie.get("httpOnly", False),
                "expires": cookie.get("expirationDate", -1),
            })

        await self._context.add_cookies(playwright_cookies)

    @property
    def context(self) -> BrowserContext | None:
        """Get the browser context."""
        return self._context

    @property
    def browser(self) -> Browser | None:
        """Get the browser instance."""
        return self._browser
