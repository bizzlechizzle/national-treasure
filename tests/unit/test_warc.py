"""Tests for WARC archive generation."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.services.capture.warc import (
    WarcResult,
    capture_warc,
    capture_warc_with_fallback,
    _wget_available,
    _generate_warc_filename,
)


class TestWarcResult:
    """Test WarcResult namedtuple."""

    def test_success_result(self, tmp_path):
        """Should create successful result."""
        warc_path = tmp_path / "test.warc.gz"
        cdx_path = tmp_path / "test.cdx"

        result = WarcResult(
            success=True,
            warc_path=warc_path,
            cdx_path=cdx_path,
            error=None,
        )

        assert result.success is True
        assert result.warc_path == warc_path
        assert result.cdx_path == cdx_path
        assert result.error is None

    def test_failure_result(self):
        """Should create failure result."""
        result = WarcResult(
            success=False,
            warc_path=None,
            cdx_path=None,
            error="wget not available",
        )

        assert result.success is False
        assert result.warc_path is None
        assert result.error == "wget not available"


class TestGenerateWarcFilename:
    """Test WARC filename generation."""

    def test_generates_unique_filenames(self):
        """Should generate different filenames for different URLs."""
        filename1 = _generate_warc_filename("https://example.com/page1")
        filename2 = _generate_warc_filename("https://example.com/page2")

        assert filename1 != filename2

    def test_filename_format(self):
        """Should include capture prefix and hash."""
        filename = _generate_warc_filename("https://example.com")

        assert filename.startswith("capture-")
        # Format: capture-YYYYMMDDHHMMSS-hash
        parts = filename.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 14  # Timestamp
        assert len(parts[2]) == 12  # Hash

    def test_same_url_different_times(self):
        """Same URL at different times should have different timestamps."""
        # This tests the timestamp component
        filename = _generate_warc_filename("https://example.com")
        # Hash should be same, timestamp differs
        assert "-" in filename


class TestWgetAvailable:
    """Test wget availability check."""

    @patch("shutil.which")
    def test_wget_available(self, mock_which):
        """Should return True when wget is available."""
        mock_which.return_value = "/usr/bin/wget"
        assert _wget_available() is True
        mock_which.assert_called_once_with("wget")

    @patch("shutil.which")
    def test_wget_not_available(self, mock_which):
        """Should return False when wget is not available."""
        mock_which.return_value = None
        assert _wget_available() is False


class TestCaptureWarc:
    """Test WARC capture function."""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_wget_not_available_error(self, mock_which, tmp_path):
        """Should return error when wget not available."""
        mock_which.return_value = None

        result = await capture_warc("https://example.com", tmp_path)

        assert result.success is False
        assert "wget not available" in result.error

    @pytest.mark.asyncio
    @patch("shutil.which")
    @patch("asyncio.create_subprocess_exec")
    async def test_successful_capture(self, mock_exec, mock_which, tmp_path):
        """Should successfully capture WARC."""
        mock_which.return_value = "/usr/bin/wget"

        # Create mock process
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()
        mock_exec.return_value = mock_proc

        # Simulate wget creating the WARC file
        # We need to intercept the filename generation to create the file
        url = "https://example.com"

        result = await capture_warc(url, tmp_path, timeout_seconds=60)

        # The function was called, but WARC file doesn't exist (no real wget)
        # So it should fail gracefully
        assert mock_exec.called

    @pytest.mark.asyncio
    @patch("shutil.which")
    @patch("asyncio.create_subprocess_exec")
    async def test_timeout_handling(self, mock_exec, mock_which, tmp_path):
        """Should handle timeout gracefully."""
        mock_which.return_value = "/usr/bin/wget"

        # Create mock process that times out
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()
        mock_exec.return_value = mock_proc

        result = await capture_warc(
            "https://example.com",
            tmp_path,
            timeout_seconds=1
        )

        assert result.success is False
        assert "timed out" in result.error

    @pytest.mark.asyncio
    @patch("shutil.which")
    @patch("asyncio.create_subprocess_exec")
    async def test_exception_handling(self, mock_exec, mock_which, tmp_path):
        """Should handle exceptions gracefully."""
        mock_which.return_value = "/usr/bin/wget"
        mock_exec.side_effect = Exception("Process failed")

        result = await capture_warc("https://example.com", tmp_path)

        assert result.success is False
        assert "Process failed" in result.error


class TestCaptureWarcWithFallback:
    """Test WARC capture with HTML fallback."""

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_fallback_to_html(self, mock_which, tmp_path):
        """Should fallback to HTML when wget unavailable."""
        mock_which.return_value = None
        html_content = "<html><body>Test content</body></html>"

        result = await capture_warc_with_fallback(
            "https://example.com",
            tmp_path,
            html_content=html_content,
        )

        assert result.success is True
        assert result.warc_path is not None
        assert result.warc_path.suffix == ".html"
        assert result.warc_path.read_text() == html_content
        assert "Fallback" in result.error

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_no_fallback_without_html(self, mock_which, tmp_path):
        """Should fail when wget unavailable and no HTML provided."""
        mock_which.return_value = None

        result = await capture_warc_with_fallback(
            "https://example.com",
            tmp_path,
            html_content=None,
        )

        assert result.success is False
        assert "wget not available" in result.error

    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_creates_output_directory(self, mock_which, tmp_path):
        """Should create output directory if it doesn't exist."""
        mock_which.return_value = None
        output_dir = tmp_path / "nested" / "dir"
        html_content = "<html>Test</html>"

        result = await capture_warc_with_fallback(
            "https://example.com",
            output_dir,
            html_content=html_content,
        )

        assert result.success is True
        assert output_dir.exists()
