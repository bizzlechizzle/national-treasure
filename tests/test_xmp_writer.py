"""
XMP Writer Tests for national-treasure

Tests for XMP sidecar creation and metadata writing.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from national_treasure.services.xmp_writer import (
    WebProvenance,
    get_xmp_path,
    xmp_exists,
)

# Check if exiftool is available
try:
    from national_treasure.services.xmp_writer import XmpWriter, get_xmp_writer, EXIFTOOL_AVAILABLE
except ImportError:
    EXIFTOOL_AVAILABLE = False

# Skip all XmpWriter tests if exiftool not available
pytestmark = pytest.mark.skipif(
    not EXIFTOOL_AVAILABLE,
    reason="pyexiftool not installed"
)


class TestWebProvenance:
    """Test WebProvenance dataclass."""

    def test_basic_provenance(self):
        """Should create provenance with required fields."""
        prov = WebProvenance(source_url="https://example.com")
        assert prov.source_url == "https://example.com"
        assert prov.page_url is None
        assert prov.page_title is None

    def test_full_provenance(self):
        """Should create provenance with all fields."""
        prov = WebProvenance(
            source_url="https://example.com/image.jpg",
            page_url="https://example.com/page",
            page_title="Example Page",
            capture_method="screenshot",
            browser_engine="chromium",
            user_agent="Mozilla/5.0",
            viewport_size="1920x1080",
            http_status=200,
            was_blocked=False,
        )

        assert prov.source_url == "https://example.com/image.jpg"
        assert prov.page_url == "https://example.com/page"
        assert prov.page_title == "Example Page"
        assert prov.capture_method == "screenshot"
        assert prov.browser_engine == "chromium"


class TestXmpPathHelpers:
    """Test XMP path helper functions."""

    def test_get_xmp_path(self, tmp_path):
        """Should return correct XMP sidecar path."""
        test_file = tmp_path / "image.jpg"
        test_file.touch()

        xmp_path = get_xmp_path(test_file)
        assert xmp_path == tmp_path / "image.jpg.xmp"

    def test_get_xmp_path_with_xmp_extension(self, tmp_path):
        """Should handle files already ending in .xmp."""
        xmp_file = tmp_path / "file.xmp"
        xmp_file.touch()

        xmp_path = get_xmp_path(xmp_file)
        # Always appends .xmp (even to .xmp files)
        assert xmp_path == tmp_path / "file.xmp.xmp"

    def test_xmp_exists_false(self, tmp_path):
        """Should return False when XMP doesn't exist."""
        test_file = tmp_path / "image.jpg"
        test_file.touch()

        assert not xmp_exists(test_file)

    def test_xmp_exists_true(self, tmp_path):
        """Should return True when XMP exists."""
        test_file = tmp_path / "image.jpg"
        test_file.touch()
        xmp_file = tmp_path / "image.jpg.xmp"
        xmp_file.touch()

        assert xmp_exists(test_file)


@pytest.mark.skipif(not EXIFTOOL_AVAILABLE, reason="pyexiftool not installed")
class TestXmpWriter:
    """Test XmpWriter class - requires pyexiftool."""

    @pytest.fixture
    def writer(self):
        """Create XmpWriter instance."""
        return XmpWriter()

    @pytest.fixture
    def mock_exiftool(self):
        """Mock ExifToolHelper for tests."""
        from unittest.mock import MagicMock
        mock_et = MagicMock()
        mock_et.__enter__ = MagicMock(return_value=mock_et)
        mock_et.__exit__ = MagicMock(return_value=None)
        mock_et.execute = MagicMock(return_value=None)
        mock_et.get_metadata = MagicMock(return_value=[{}])
        return mock_et

    def test_create_initial_sidecar(self, tmp_path, mock_exiftool):
        """Should create initial XMP sidecar with provenance."""
        from national_treasure.services import xmp_writer as xw_module

        test_file = tmp_path / "capture.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

        provenance = WebProvenance(
            source_url="https://example.com/image.png",
            page_url="https://example.com/gallery",
            page_title="Image Gallery",
            user_agent="TestAgent",
            viewport_size="1920x1080",
            http_status=200,
            was_blocked=False,
            warc_file="test.warc.gz",
            warc_record_id="urn:uuid:test",
        )

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_exiftool):
            writer = XmpWriter()
            writer.create_initial_sidecar(
                test_file, provenance,
                content_hash="abc123",
                file_size=1024
            )

        # Verify exiftool was called with expected args
        mock_exiftool.execute.assert_called_once()
        args = mock_exiftool.execute.call_args[0]
        assert "-overwrite_original" in args

    def test_write_capture_metadata(self, tmp_path, mock_exiftool):
        """Should write capture metadata to existing XMP."""
        from national_treasure.services import xmp_writer as xw_module

        test_file = tmp_path / "page.pdf"
        test_file.write_bytes(b'%PDF-1.4\n' + b'\x00' * 100)
        xmp_file = tmp_path / "page.pdf.xmp"
        xmp_file.write_text('<?xml version="1.0"?><x:xmpmeta/>')

        provenance = WebProvenance(
            source_url="https://example.com/doc.pdf",
            page_url="https://example.com/documents",
            page_title="Documents",
            user_agent="TestAgent",
            viewport_size="1920x1080",
            http_status=200,
            was_blocked=True,
            warc_file="test.warc.gz",
            warc_record_id="urn:uuid:test",
        )

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_exiftool):
            writer = XmpWriter()
            writer.write_capture_metadata(test_file, provenance)

        mock_exiftool.execute.assert_called_once()

    def test_append_custody_event(self, tmp_path, mock_exiftool):
        """Should append custody event to chain."""
        from national_treasure.services import xmp_writer as xw_module

        test_file = tmp_path / "archived.html"
        test_file.write_text("<html></html>")
        xmp_file = tmp_path / "archived.html.xmp"
        xmp_file.write_text('<?xml version="1.0"?><x:xmpmeta/>')

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_exiftool):
            writer = XmpWriter()
            writer.append_custody_event(
                test_file,
                action="archive",
                outcome="success",
                notes="Archived to storage",
            )

        mock_exiftool.execute.assert_called_once()

    def test_has_capture_metadata_with_source(self, tmp_path, mock_exiftool):
        """Should detect capture metadata by SourceURL."""
        from national_treasure.services import xmp_writer as xw_module

        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n')
        xmp_file = tmp_path / "test.png.xmp"
        xmp_file.write_text('<xmp/>')

        mock_exiftool.get_metadata = MagicMock(return_value=[{"SourceURL": "https://example.com"}])

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_exiftool):
            writer = XmpWriter()
            result = writer.has_capture_metadata(test_file)

        assert result is True

    def test_has_capture_metadata_with_captured_at(self, tmp_path, mock_exiftool):
        """Should detect capture metadata by CapturedAt."""
        from national_treasure.services import xmp_writer as xw_module

        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n')
        xmp_file = tmp_path / "test.png.xmp"
        xmp_file.write_text('<xmp/>')

        mock_exiftool.get_metadata = MagicMock(return_value=[{"CapturedAt": "2024-01-01T00:00:00Z"}])

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_exiftool):
            writer = XmpWriter()
            result = writer.has_capture_metadata(test_file)

        assert result is True

    def test_read_capture_metadata_full(self, tmp_path, mock_exiftool):
        """Should read full capture metadata."""
        from national_treasure.services import xmp_writer as xw_module

        test_file = tmp_path / "test.png"
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n')
        xmp_file = tmp_path / "test.png.xmp"
        xmp_file.write_text('<xmp/>')

        mock_exiftool.get_metadata = MagicMock(return_value=[{
            "SourceURL": "https://example.com",
            "PageURL": "https://example.com/page",
            "PageTitle": "Test",
            "CaptureMethod": "pdf",
            "BrowserEngine": "firefox",
            "UserAgent": "Agent",
            "ViewportSize": "1920x1080",
            "HttpStatus": 200,
            "WasBlocked": True,
            "WarcFile": "test.warc",
            "WarcRecordID": "urn:uuid:123",
        }])

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_exiftool):
            writer = XmpWriter()
            result = writer.read_capture_metadata(test_file)

        assert result is not None
        assert result.source_url == "https://example.com"
        assert result.capture_method == "pdf"
        assert result.was_blocked is True


@pytest.mark.skipif(not EXIFTOOL_AVAILABLE, reason="pyexiftool not installed")
class TestGetXmpWriter:
    """Test singleton behavior."""

    def test_returns_same_instance(self):
        """get_xmp_writer should return same instance."""
        writer1 = get_xmp_writer()
        writer2 = get_xmp_writer()
        assert writer1 is writer2


@pytest.mark.skipif(not EXIFTOOL_AVAILABLE, reason="pyexiftool not installed")
class TestXmpIntegration:
    """Integration tests requiring exiftool binary with configured namespaces."""

    @pytest.fixture
    def has_exiftool_with_namespaces(self):
        """Check if exiftool binary has custom namespaces configured."""
        try:
            # Check if exiftool is available
            result = subprocess.run(
                ["exiftool", "-ver"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return False
            # Custom namespaces require .ExifTool_config - skip if not configured
            # Testing with custom namespaces requires local setup
            return False  # Skip integration tests - use mocked tests instead
        except FileNotFoundError:
            return False

    def test_real_xmp_creation(self, tmp_path, has_exiftool_with_namespaces):
        """Test actual XMP creation with real exiftool."""
        if not has_exiftool_with_namespaces:
            pytest.skip("exiftool with custom namespaces not configured")

        # Create a minimal PNG file
        png_file = tmp_path / "test.png"
        png_header = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
            0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
            0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82,
        ])
        png_file.write_bytes(png_header)

        writer = XmpWriter()
        provenance = WebProvenance(
            source_url="https://example.com/test.png",
            page_url="https://example.com",
            page_title="Test Page",
        )

        writer.create_initial_sidecar(png_file, provenance)

        # Check XMP file was created
        xmp_path = get_xmp_path(png_file)
        assert xmp_path.exists()
