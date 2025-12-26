"""Tests for browser service."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.core.models import BrowserConfig, HeadlessMode, WaitStrategy
from national_treasure.services.browser.service import (
    BrowserService,
    DEFAULT_USER_AGENT,
    STEALTH_ARGS,
)


class TestBrowserServiceInit:
    """Test BrowserService initialization."""

    def test_default_config(self):
        """Should use default config when none provided."""
        service = BrowserService()
        assert service.config is not None
        assert service.headless is True
        assert service.profile_path is None

    def test_custom_config(self):
        """Should use provided config."""
        config = BrowserConfig(viewport_width=1280, viewport_height=720)
        service = BrowserService(config=config, headless=False)
        assert service.config.viewport_width == 1280
        assert service.headless is False

    def test_with_profile_path(self, tmp_path):
        """Should accept profile path."""
        profile_dir = tmp_path / "profile"
        service = BrowserService(profile_path=profile_dir)
        assert service.profile_path == profile_dir


class TestBrowserServiceAsync:
    """Test async browser operations."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Should work as async context manager."""
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_context.close = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_playwright.stop = AsyncMock()

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            async with BrowserService() as service:
                assert service._browser is mock_browser
                assert service._context is mock_context

    @pytest.mark.asyncio
    async def test_start_with_visible_mode(self):
        """Should respect visible headless mode."""
        config = BrowserConfig(headless_mode=HeadlessMode.VISIBLE)

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_context.close = AsyncMock()
        mock_playwright.stop = AsyncMock()

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            service = BrowserService(config=config)
            await service.start()

            # Should launch with headless=False
            call_kwargs = mock_playwright.chromium.launch.call_args.kwargs
            assert call_kwargs["headless"] is False

            await service.stop()

    @pytest.mark.asyncio
    async def test_start_with_persistent_context(self, tmp_path):
        """Should use persistent context with profile path."""
        profile_path = tmp_path / "profile"

        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        # Regular launch is always called, but persistent context is used when profile_path is set
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.chromium.launch_persistent_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_context.close = AsyncMock()
        mock_playwright.stop = AsyncMock()

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            service = BrowserService(profile_path=profile_path)
            await service.start()

            # Should use persistent context
            mock_playwright.chromium.launch_persistent_context.assert_called_once()

            await service.stop()

    @pytest.mark.asyncio
    async def test_stop_cleans_up(self):
        """Should close browser and context on stop."""
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_context.close = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_playwright.stop = AsyncMock()

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            service = BrowserService()
            await service.start()
            await service.stop()

            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()
            mock_playwright.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_page_context_manager(self):
        """Should create and close pages correctly."""
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.add_init_script = AsyncMock()
        mock_page.close = AsyncMock()

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            service = BrowserService()
            await service.start()

            async with service.page() as page:
                assert page is mock_page

            mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_page_without_start_raises(self):
        """Should raise error if page() called before start()."""
        service = BrowserService()

        with pytest.raises(RuntimeError, match="Browser not started"):
            async with service.page():
                pass

    @pytest.mark.asyncio
    async def test_goto(self):
        """Should navigate to URL with config."""
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_response = MagicMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()
        mock_page.goto = AsyncMock(return_value=mock_response)

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            service = BrowserService()
            await service.start()

            response = await service.goto(mock_page, "https://example.com")

            assert response is mock_response
            mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_inject_cookies(self):
        """Should inject cookies into context."""
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.add_init_script = AsyncMock()
        mock_context.add_cookies = AsyncMock()

        with patch("national_treasure.services.browser.service.async_playwright") as mock_pw:
            mock_pw.return_value.start = AsyncMock(return_value=mock_playwright)

            service = BrowserService()
            await service.start()

            cookies = [
                {"name": "session", "value": "abc123", "domain": "example.com"},
                {"name": "prefs", "value": "dark", "domain": "example.com", "secure": True},
            ]

            await service.inject_cookies(mock_page, cookies)
            mock_context.add_cookies.assert_called_once()


class TestBrowserServiceProperties:
    """Test BrowserService properties."""

    def test_context_property_before_start(self):
        """Should return None before start."""
        service = BrowserService()
        assert service.context is None

    def test_browser_property_before_start(self):
        """Should return None before start."""
        service = BrowserService()
        assert service.browser is None


class TestStealthArgs:
    """Test stealth configuration."""

    def test_stealth_args_content(self):
        """Should have required stealth args."""
        assert "--no-sandbox" in STEALTH_ARGS
        assert "--disable-blink-features=AutomationControlled" in STEALTH_ARGS

    def test_default_user_agent(self):
        """Should have Chrome user agent."""
        assert "Chrome" in DEFAULT_USER_AGENT
        assert "Mozilla" in DEFAULT_USER_AGENT
