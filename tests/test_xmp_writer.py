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

    def test_create_initial_sidecar(self, tmp_path, writer):
        """Should create initial XMP sidecar with provenance."""
        test_file = tmp_path / "capture.png"
        # Create minimal PNG
        test_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

        provenance = WebProvenance(
            source_url="https://example.com/image.png",
            page_url="https://example.com/gallery",
            page_title="Image Gallery",
        )

        writer.create_initial_sidecar(test_file, provenance)

        # Check sidecar was created
        xmp_path = get_xmp_path(test_file)
        assert xmp_path.exists()

    def test_write_capture_metadata(self, tmp_path, writer):
        """Should write capture metadata to existing XMP."""
        test_file = tmp_path / "page.pdf"
        test_file.write_bytes(b'%PDF-1.4\n' + b'\x00' * 100)
        xmp_file = tmp_path / "page.pdf.xmp"
        xmp_file.write_text('<?xml version="1.0"?><x:xmpmeta/>')

        provenance = WebProvenance(
            source_url="https://example.com/doc.pdf",
            page_url="https://example.com/documents",
            page_title="Documents",
        )

        writer.write_capture_metadata(test_file, provenance)
        # No assertion - just verify no exception

    def test_append_custody_event(self, tmp_path, writer):
        """Should append custody event to chain."""
        test_file = tmp_path / "archived.html"
        test_file.write_text("<html></html>")
        xmp_file = tmp_path / "archived.html.xmp"
        xmp_file.write_text('<?xml version="1.0"?><x:xmpmeta/>')

        writer.append_custody_event(
            test_file,
            action="archive",
            outcome="success",
            notes="Archived to storage",
        )
        # No assertion - just verify no exception


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
    """Integration tests requiring exiftool binary."""

    @pytest.fixture
    def has_exiftool_binary(self):
        """Check if exiftool binary is available."""
        try:
            result = subprocess.run(
                ["exiftool", "-ver"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def test_real_xmp_creation(self, tmp_path, has_exiftool_binary):
        """Test actual XMP creation with real exiftool."""
        if not has_exiftool_binary:
            pytest.skip("exiftool binary not available")

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
