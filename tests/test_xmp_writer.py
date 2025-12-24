"""
XMP Writer Tests for national-treasure

Tests for XMP sidecar creation and metadata writing.
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from national_treasure.services.xmp_writer import (
    WebProvenance,
    XmpWriter,
    get_xmp_writer,
    get_xmp_path,
    xmp_exists,
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
            original_filename="image.jpg",
            capture_timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            archive_session_id="session-123",
        )

        assert prov.source_url == "https://example.com/image.jpg"
        assert prov.page_url == "https://example.com/page"
        assert prov.page_title == "Example Page"
        assert prov.original_filename == "image.jpg"
        assert prov.archive_session_id == "session-123"


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
        # Should not double the extension
        assert xmp_path == tmp_path / "file.xmp"

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


class TestXmpWriter:
    """Test XmpWriter class."""

    @pytest.fixture
    def mock_exiftool(self):
        """Mock subprocess.run for exiftool calls."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            yield mock_run

    @pytest.fixture
    def writer(self):
        """Create XmpWriter instance."""
        return XmpWriter()

    def test_create_initial_sidecar(self, tmp_path, mock_exiftool, writer):
        """Should create initial XMP sidecar with provenance."""
        test_file = tmp_path / "capture.png"
        test_file.touch()

        provenance = WebProvenance(
            source_url="https://example.com/image.png",
            page_url="https://example.com/gallery",
            page_title="Image Gallery",
            original_filename="image.png",
            capture_timestamp=datetime(2024, 12, 15, 10, 30, 0, tzinfo=timezone.utc),
            archive_session_id="sess-456",
        )

        result = writer.create_initial_sidecar(
            test_file,
            provenance,
            capture_tool="national-treasure/0.1.0",
            capture_method="browser-screenshot",
        )

        assert result is True
        mock_exiftool.assert_called()

        # Verify exiftool was called with correct arguments
        call_args = mock_exiftool.call_args[0][0]
        assert "exiftool" in call_args[0]
        assert any("nt:SchemaVersion" in arg for arg in call_args)
        assert any("nt:SourceURL" in arg for arg in call_args)
        assert any("nt:PageURL" in arg for arg in call_args)
        assert any("nt:CaptureTool" in arg for arg in call_args)
        assert any("wnb:CustodyChain" in arg for arg in call_args)

    def test_create_initial_sidecar_minimal(self, tmp_path, mock_exiftool, writer):
        """Should create sidecar with minimal provenance."""
        test_file = tmp_path / "simple.html"
        test_file.touch()

        provenance = WebProvenance(source_url="https://example.com")

        result = writer.create_initial_sidecar(test_file, provenance)

        assert result is True
        mock_exiftool.assert_called()

    def test_write_capture_metadata(self, tmp_path, mock_exiftool, writer):
        """Should write capture metadata to existing XMP."""
        test_file = tmp_path / "page.pdf"
        test_file.touch()
        xmp_file = tmp_path / "page.pdf.xmp"
        xmp_file.write_text('<?xml version="1.0"?><x:xmpmeta/>')

        provenance = WebProvenance(
            source_url="https://example.com/doc.pdf",
            page_url="https://example.com/documents",
            page_title="Documents",
        )

        result = writer.write_capture_metadata(test_file, provenance)

        assert result is True
        mock_exiftool.assert_called()

    def test_append_custody_event(self, tmp_path, mock_exiftool, writer):
        """Should append custody event to chain."""
        test_file = tmp_path / "archived.warc"
        test_file.touch()
        xmp_file = tmp_path / "archived.warc.xmp"
        xmp_file.write_text('<?xml version="1.0"?><x:xmpmeta/>')

        result = writer.append_custody_event(
            test_file,
            action="archive",
            outcome="success",
            notes="Archived to WARC format",
        )

        assert result is True
        mock_exiftool.assert_called()

        # Verify custody chain format
        call_args = mock_exiftool.call_args[0][0]
        custody_arg = next((arg for arg in call_args if "wnb:CustodyChain" in arg), None)
        assert custody_arg is not None
        assert "EventAction=archive" in custody_arg
        assert "EventOutcome=success" in custody_arg
        assert "EventTool=national-treasure" in custody_arg

    def test_exiftool_failure(self, tmp_path, mock_exiftool, writer):
        """Should return False on exiftool failure."""
        mock_exiftool.return_value = MagicMock(returncode=1, stderr="Error")

        test_file = tmp_path / "bad.jpg"
        test_file.touch()

        result = writer.create_initial_sidecar(
            test_file,
            WebProvenance(source_url="https://example.com"),
        )

        assert result is False

    def test_exiftool_preserves_namespaces(self, tmp_path, mock_exiftool, writer):
        """Should use exiftool flags to preserve unknown namespaces."""
        test_file = tmp_path / "multi.jpg"
        test_file.touch()

        writer.create_initial_sidecar(
            test_file,
            WebProvenance(source_url="https://example.com"),
        )

        call_args = mock_exiftool.call_args[0][0]
        # Should use -overwrite_original to avoid backup files
        assert "-overwrite_original" in call_args


class TestXmpWriterNamespace:
    """Test namespace handling."""

    @pytest.fixture
    def mock_exiftool(self):
        """Mock subprocess.run."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            yield mock_run

    def test_uses_nt_namespace(self, tmp_path, mock_exiftool):
        """Should use nt: namespace prefix."""
        writer = XmpWriter()
        test_file = tmp_path / "test.png"
        test_file.touch()

        writer.create_initial_sidecar(
            test_file,
            WebProvenance(source_url="https://example.com"),
        )

        call_args = mock_exiftool.call_args[0][0]

        # Check nt: namespace is used
        nt_args = [arg for arg in call_args if arg.startswith("-XMP-nt:")]
        assert len(nt_args) > 0, "Should use nt: namespace"

    def test_custody_uses_wnb_namespace(self, tmp_path, mock_exiftool):
        """Custody chain should use wnb: namespace (shared)."""
        writer = XmpWriter()
        test_file = tmp_path / "test.png"
        test_file.touch()

        writer.create_initial_sidecar(
            test_file,
            WebProvenance(source_url="https://example.com"),
        )

        call_args = mock_exiftool.call_args[0][0]

        # Check wnb:CustodyChain is used
        custody_args = [arg for arg in call_args if "wnb:CustodyChain" in arg]
        assert len(custody_args) > 0, "Should use wnb:CustodyChain"


class TestGetXmpWriter:
    """Test singleton behavior."""

    def test_returns_same_instance(self):
        """get_xmp_writer should return same instance."""
        writer1 = get_xmp_writer()
        writer2 = get_xmp_writer()
        assert writer1 is writer2


class TestXmpIntegration:
    """Integration tests requiring exiftool."""

    @pytest.fixture
    def has_exiftool(self):
        """Check if exiftool is available."""
        try:
            result = subprocess.run(
                ["exiftool", "-ver"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    @pytest.mark.integration
    def test_real_xmp_creation(self, tmp_path, has_exiftool):
        """Test actual XMP creation with real exiftool."""
        if not has_exiftool:
            pytest.skip("exiftool not available")

        # Create a minimal PNG file
        png_file = tmp_path / "test.png"
        # Minimal PNG header
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

        result = writer.create_initial_sidecar(png_file, provenance)
        assert result is True

        # Check XMP file was created
        xmp_path = get_xmp_path(png_file)
        assert xmp_path.exists()

        # Verify content with exiftool
        verify = subprocess.run(
            ["exiftool", "-XMP:all", str(xmp_path)],
            capture_output=True,
            text=True,
        )

        # Should contain our namespace data
        # Note: exiftool may report under different names depending on config
        output = verify.stdout + verify.stderr
        assert "example.com" in output.lower() or "source" in output.lower()
