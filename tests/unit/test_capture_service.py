"""Tests for capture service."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.core.models import BrowserConfig, CaptureResult, ValidationResult
from national_treasure.services.capture.service import CaptureService


class TestCaptureServiceInit:
    """Test CaptureService initialization."""

    def test_default_config(self, tmp_path):
        """Should use default config."""
        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService()
            assert service.config is not None
            assert service.headless is True

    def test_custom_config(self, tmp_path):
        """Should use provided config."""
        config = BrowserConfig(viewport_width=1280)
        service = CaptureService(config=config, headless=False, output_dir=tmp_path)
        assert service.config.viewport_width == 1280
        assert service.headless is False
        assert service.output_dir == tmp_path


class TestCaptureServiceAsync:
    """Test async capture operations."""

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_path):
        """Should work as async context manager."""
        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            async with CaptureService(output_dir=tmp_path) as service:
                assert service._browser_service is mock_browser
                mock_browser.start.assert_called_once()

            mock_browser.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_success(self, tmp_path):
        """Should capture successfully."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        mock_page.pdf = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html></html>")
        mock_page.title = AsyncMock(return_value="Test Page")

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=200))

        # Create async context manager for page
        async def page_context():
            yield mock_page

        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=False)

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                with patch("national_treasure.services.capture.service.execute_behaviors", new=AsyncMock()):
                    async with CaptureService(output_dir=tmp_path) as service:
                        result = await service.capture(
                            "https://example.com",
                            formats=["screenshot", "html"],
                        )

                        assert result.success is True

    @pytest.mark.asyncio
    async def test_capture_blocked(self, tmp_path):
        """Should handle blocked response."""
        mock_page = MagicMock()

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=403))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=True, reason="cloudflare")

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                async with CaptureService(output_dir=tmp_path) as service:
                    result = await service.capture("https://example.com")

                    assert result.success is False
                    assert "Blocked" in result.error

    @pytest.mark.asyncio
    async def test_capture_exception(self, tmp_path):
        """Should handle exceptions gracefully."""
        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(side_effect=Exception("Connection failed"))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(MagicMock()))

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            async with CaptureService(output_dir=tmp_path) as service:
                result = await service.capture("https://example.com")

                assert result.success is False
                assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_capture_default_formats(self, tmp_path):
        """Should use all formats when none specified."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        mock_page.pdf = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html></html>")

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=False)

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                with patch("national_treasure.services.capture.service.execute_behaviors", new=AsyncMock()):
                    async with CaptureService(output_dir=tmp_path) as service:
                        # Call with formats=None to test default
                        result = await service.capture("https://example.com", formats=None)
                        assert result is not None


class TestCaptureServiceOutputPath:
    """Test output path generation."""

    def test_output_path_created(self, tmp_path):
        """Should create output directory structure."""
        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService()

            # Test internal path generation
            output_path = service._get_output_path("https://example.com/page")
            assert "example.com" in str(output_path)


class TestCaptureServiceFormats:
    """Test different capture formats."""

    @pytest.mark.asyncio
    async def test_capture_pdf_format(self, tmp_path):
        """Should capture PDF format."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        mock_page.pdf = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html></html>")
        mock_page.title = AsyncMock(return_value="Test Page")

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=False)

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                with patch("national_treasure.services.capture.service.execute_behaviors", new=AsyncMock()):
                    async with CaptureService(output_dir=tmp_path) as service:
                        result = await service.capture(
                            "https://example.com",
                            formats=["pdf"],
                        )
                        assert result.success is True
                        mock_page.pdf.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_html_format(self, tmp_path):
        """Should capture HTML format."""
        mock_page = MagicMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=False)

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                with patch("national_treasure.services.capture.service.execute_behaviors", new=AsyncMock()):
                    async with CaptureService(output_dir=tmp_path) as service:
                        result = await service.capture(
                            "https://example.com",
                            formats=["html"],
                        )
                        assert result.success is True
                        mock_page.content.assert_called()

    @pytest.mark.asyncio
    async def test_capture_format_error_continues(self, tmp_path):
        """Should continue capturing other formats on error."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))
        mock_page.content = AsyncMock(return_value="<html></html>")
        mock_page.title = AsyncMock(return_value="Test Page")

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=False)

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                with patch("national_treasure.services.capture.service.execute_behaviors", new=AsyncMock()):
                    async with CaptureService(output_dir=tmp_path) as service:
                        result = await service.capture(
                            "https://example.com",
                            formats=["screenshot", "html"],
                        )
                        # Should succeed despite screenshot error
                        assert result.success is True

    @pytest.mark.asyncio
    async def test_capture_without_behaviors(self, tmp_path):
        """Should skip behaviors when disabled."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html></html>")
        mock_page.title = AsyncMock(return_value="Test Page")

        mock_browser = MagicMock()
        mock_browser.start = AsyncMock()
        mock_browser.stop = AsyncMock()
        mock_browser.goto = AsyncMock(return_value=MagicMock(status=200))
        mock_browser.page = MagicMock(return_value=AsyncContextManagerMock(mock_page))

        mock_validation = ValidationResult(blocked=False)
        mock_behaviors = AsyncMock()

        with patch("national_treasure.services.capture.service.BrowserService", return_value=mock_browser):
            with patch("national_treasure.services.capture.service.validate_response", new=AsyncMock(return_value=mock_validation)):
                with patch("national_treasure.services.capture.service.execute_behaviors", mock_behaviors):
                    async with CaptureService(output_dir=tmp_path) as service:
                        await service.capture(
                            "https://example.com",
                            formats=["screenshot"],
                            run_behaviors=False,
                        )
                        mock_behaviors.assert_not_called()


class AsyncContextManagerMock:
    """Helper for mocking async context managers."""

    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
