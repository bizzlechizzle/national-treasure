"""Extended capture service tests for 100% coverage."""

import gzip
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.core.models import BrowserConfig, ValidationResult


class AsyncContextManagerMock:
    """Helper for mocking async context managers."""

    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestCaptureWARC:
    """Test WARC capture functionality."""

    @pytest.mark.asyncio
    async def test_capture_warc_format(self, tmp_path):
        """Should capture page in WARC format."""
        from national_treasure.services.capture.service import CaptureService

        mock_page = MagicMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.screenshot = AsyncMock()

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
                            formats=["warc"],
                        )

                        # WARC capture is called
                        assert result.success is True


class TestCreateWarcRecord:
    """Test WARC record creation."""

    def test_create_warc_record_string_content(self, tmp_path):
        """Should create WARC record from string content."""
        from national_treasure.services.capture.service import CaptureService

        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService(output_dir=tmp_path)

            record = service._create_warc_record(
                record_type="response",
                record_id="urn:uuid:test",
                timestamp="2024-01-01T00:00:00Z",
                target_uri="https://example.com",
                content="<html>Test</html>",
                content_type="text/html",
            )

            assert b"WARC/1.1" in record
            assert b"WARC-Type: response" in record
            assert b"<html>Test</html>" in record

    def test_create_warc_record_bytes_content(self, tmp_path):
        """Should create WARC record from bytes content."""
        from national_treasure.services.capture.service import CaptureService

        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService(output_dir=tmp_path)

            record = service._create_warc_record(
                record_type="response",
                record_id="urn:uuid:test",
                timestamp="2024-01-01T00:00:00Z",
                target_uri="https://example.com",
                content=b"binary content",
                content_type="application/octet-stream",
            )

            assert b"WARC/1.1" in record
            assert b"binary content" in record


class TestGetMetaDescription:
    """Test meta description extraction."""

    @pytest.mark.asyncio
    async def test_get_meta_description_success(self, tmp_path):
        """Should extract meta description."""
        from national_treasure.services.capture.service import CaptureService

        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value="This is a test description")

        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService(output_dir=tmp_path)

            result = await service._get_meta_description(mock_page)
            assert result == "This is a test description"

    @pytest.mark.asyncio
    async def test_get_meta_description_exception(self, tmp_path):
        """Should handle exception and return None."""
        from national_treasure.services.capture.service import CaptureService

        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("JS error"))

        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService(output_dir=tmp_path)

            result = await service._get_meta_description(mock_page)
            assert result is None


class TestCaptureAllFormats:
    """Test capturing with all formats."""

    @pytest.mark.asyncio
    async def test_capture_with_all_formats(self, tmp_path):
        """Should capture in all available formats."""
        from national_treasure.services.capture.service import CaptureService

        mock_page = MagicMock()
        mock_page.content = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_page.title = AsyncMock(return_value="Test Page")
        mock_page.screenshot = AsyncMock()
        mock_page.pdf = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)

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
                            formats=["screenshot", "pdf", "html", "warc"],
                        )

                        assert result.success is True


class TestCaptureOutputPath:
    """Test output path generation."""

    def test_get_output_path_with_subdir(self, tmp_path):
        """Should generate correct output path with subdirectory."""
        from national_treasure.services.capture.service import CaptureService

        with patch("national_treasure.services.capture.service.get_config") as mock_config:
            mock_config.return_value = MagicMock(archive_dir=tmp_path)
            service = CaptureService(output_dir=tmp_path)

            output_path = service._get_output_path("https://example.com/page/test")
            assert "example.com" in str(output_path)
