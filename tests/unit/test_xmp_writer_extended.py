"""Extended tests for XMP writer - covers helper functions and module functions."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestHelperFunctions:
    """Test helper functions that don't require exiftool."""

    def test_generate_event_id(self):
        """Should generate unique event IDs."""
        from national_treasure.services.xmp_writer import _generate_event_id

        id1 = _generate_event_id()
        id2 = _generate_event_id()

        assert id1 != id2
        assert "-" in id1

    def test_get_hostname(self):
        """Should get hostname safely."""
        from national_treasure.services.xmp_writer import _get_hostname

        hostname = _get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0

    def test_get_hostname_exception(self):
        """Should handle hostname exception."""
        from national_treasure.services.xmp_writer import _get_hostname

        with patch("socket.gethostname", side_effect=Exception("Error")):
            hostname = _get_hostname()
            assert hostname == "unknown"

    def test_get_username(self):
        """Should get username safely."""
        from national_treasure.services.xmp_writer import _get_username

        username = _get_username()
        assert isinstance(username, str)
        assert len(username) > 0

    def test_get_username_exception_with_env(self):
        """Should fallback to USER env on exception."""
        from national_treasure.services.xmp_writer import _get_username

        with patch("os.getlogin", side_effect=OSError("Error")):
            with patch.dict(os.environ, {"USER": "testuser"}):
                username = _get_username()
                assert username == "testuser"

    def test_get_username_exception_no_env(self):
        """Should fallback to unknown when no USER env."""
        from national_treasure.services.xmp_writer import _get_username

        with patch("os.getlogin", side_effect=OSError("Error")):
            with patch.dict(os.environ, {}, clear=True):
                username = _get_username()
                assert username == "unknown"

    def test_build_custody_event_with_notes(self):
        """Should build custody event with notes."""
        from national_treasure.services.xmp_writer import _build_custody_event

        event = _build_custody_event("capture", "success", "Test notes")

        assert "EventAction=capture" in event
        assert "EventOutcome=success" in event
        assert "EventNotes=Test notes" in event
        assert event.startswith("{")
        assert event.endswith("}")

    def test_build_custody_event_no_notes(self):
        """Should build event without notes."""
        from national_treasure.services.xmp_writer import _build_custody_event

        event = _build_custody_event("capture", "success")

        assert "EventAction=capture" in event
        assert "EventNotes" not in event

    def test_build_custody_event_escapes_special_chars(self):
        """Should escape special characters in notes."""
        from national_treasure.services.xmp_writer import _build_custody_event

        event = _build_custody_event("capture", "success", "test{val=1,other}")

        # Verify notes are escaped (special chars replaced with _)
        assert "EventNotes=test_val_1_other_" in event


class TestWebProvenance:
    """Test WebProvenance dataclass."""

    def test_default_values(self):
        """Should have correct defaults."""
        from national_treasure.services.xmp_writer import WebProvenance

        prov = WebProvenance(source_url="https://example.com")

        assert prov.source_url == "https://example.com"
        assert prov.page_url is None
        assert prov.page_title is None
        assert prov.capture_method == "screenshot"
        assert prov.browser_engine == "chromium"
        assert prov.user_agent is None
        assert prov.viewport_size is None
        assert prov.http_status is None
        assert prov.was_blocked is False
        assert prov.warc_file is None
        assert prov.warc_record_id is None

    def test_all_values(self):
        """Should accept all values."""
        from national_treasure.services.xmp_writer import WebProvenance

        prov = WebProvenance(
            source_url="https://example.com",
            page_url="https://example.com/page",
            page_title="Test Page",
            capture_method="pdf",
            browser_engine="firefox",
            user_agent="TestAgent/1.0",
            viewport_size="1920x1080",
            http_status=200,
            was_blocked=True,
            warc_file="capture.warc.gz",
            warc_record_id="urn:uuid:test",
        )

        assert prov.page_title == "Test Page"
        assert prov.capture_method == "pdf"
        assert prov.http_status == 200
        assert prov.was_blocked is True
        assert prov.warc_file == "capture.warc.gz"


class TestModuleFunctions:
    """Test module-level functions."""

    def test_get_xmp_path(self, tmp_path):
        """Should return XMP path."""
        from national_treasure.services.xmp_writer import get_xmp_path

        result = get_xmp_path(tmp_path / "test.png")
        assert str(result).endswith(".xmp")
        assert "test.png.xmp" in str(result)

    def test_xmp_exists_true(self, tmp_path):
        """Should detect existing XMP."""
        from national_treasure.services.xmp_writer import xmp_exists

        xmp_file = tmp_path / "test.png.xmp"
        xmp_file.write_text("<xmp>test</xmp>")

        assert xmp_exists(tmp_path / "test.png") is True

    def test_xmp_exists_false(self, tmp_path):
        """Should detect missing XMP."""
        from national_treasure.services.xmp_writer import xmp_exists

        assert xmp_exists(tmp_path / "nonexistent.png") is False


class TestXmpWriterInit:
    """Test XmpWriter initialization."""

    def test_init_without_exiftool(self):
        """Should raise when exiftool not available."""
        import national_treasure.services.xmp_writer as xw_module

        original = xw_module.EXIFTOOL_AVAILABLE
        try:
            xw_module.EXIFTOOL_AVAILABLE = False
            with pytest.raises(RuntimeError, match="exiftool not available"):
                xw_module.XmpWriter()
        finally:
            xw_module.EXIFTOOL_AVAILABLE = original


class TestXmpWriterReadSidecar:
    """Test XmpWriter.read_sidecar method."""

    def test_read_sidecar_no_file(self, tmp_path):
        """Should return None when no sidecar exists."""
        import national_treasure.services.xmp_writer as xw_module

        if not xw_module.EXIFTOOL_AVAILABLE:
            pytest.skip("exiftool not available")

        writer = xw_module.XmpWriter()
        result = writer.read_sidecar(tmp_path / "nonexistent.png")
        assert result is None


class TestXmpWriterWithMockedExiftool:
    """Tests that mock ExifToolHelper."""

    def test_read_sidecar_success(self, tmp_path):
        """Should read sidecar content."""
        import national_treasure.services.xmp_writer as xw_module

        if not xw_module.EXIFTOOL_AVAILABLE:
            pytest.skip("exiftool not available")

        # Create XMP file
        xmp_file = tmp_path / "test.png.xmp"
        xmp_file.write_text("<xmp>test</xmp>")

        # Mock ExifToolHelper
        mock_et = MagicMock()
        mock_et.__enter__ = MagicMock(return_value=mock_et)
        mock_et.__exit__ = MagicMock(return_value=None)
        mock_et.get_metadata = MagicMock(return_value=[{"SourceURL": "https://example.com"}])

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_et):
            writer = xw_module.XmpWriter()
            result = writer.read_sidecar(tmp_path / "test.png")

        assert result == {"SourceURL": "https://example.com"}

    def test_read_sidecar_exception(self, tmp_path):
        """Should handle read exceptions."""
        import national_treasure.services.xmp_writer as xw_module

        if not xw_module.EXIFTOOL_AVAILABLE:
            pytest.skip("exiftool not available")

        # Create XMP file
        xmp_file = tmp_path / "test.png.xmp"
        xmp_file.write_text("<xmp>test</xmp>")

        # Mock ExifToolHelper to raise
        mock_et = MagicMock()
        mock_et.__enter__ = MagicMock(return_value=mock_et)
        mock_et.__exit__ = MagicMock(return_value=None)
        mock_et.get_metadata = MagicMock(side_effect=Exception("Read error"))

        with patch.object(xw_module, "ExifToolHelper", return_value=mock_et):
            writer = xw_module.XmpWriter()
            result = writer.read_sidecar(tmp_path / "test.png")

        assert result is None

    def test_has_capture_metadata_no_sidecar(self, tmp_path):
        """Should return False when no sidecar."""
        import national_treasure.services.xmp_writer as xw_module

        if not xw_module.EXIFTOOL_AVAILABLE:
            pytest.skip("exiftool not available")

        writer = xw_module.XmpWriter()
        assert writer.has_capture_metadata(tmp_path / "no.png") is False

    def test_read_capture_metadata_no_sidecar(self, tmp_path):
        """Should return None when no sidecar."""
        import national_treasure.services.xmp_writer as xw_module

        if not xw_module.EXIFTOOL_AVAILABLE:
            pytest.skip("exiftool not available")

        writer = xw_module.XmpWriter()
        assert writer.read_capture_metadata(tmp_path / "no.png") is None


class TestGetXmpWriter:
    """Test get_xmp_writer singleton function."""

    def test_get_xmp_writer_singleton(self):
        """Should return same instance."""
        import national_treasure.services.xmp_writer as xw_module

        if not xw_module.EXIFTOOL_AVAILABLE:
            pytest.skip("exiftool not available")

        # Reset global
        xw_module._writer = None

        writer1 = xw_module.get_xmp_writer()
        writer2 = xw_module.get_xmp_writer()

        assert writer1 is writer2


class TestNamespaceConstants:
    """Test namespace constants."""

    def test_namespace_constants(self):
        """Should have expected namespace constants."""
        from national_treasure.services.xmp_writer import (
            NAMESPACE,
            NAMESPACE_URI,
            TOOL_NAME,
            TOOL_VERSION,
            SCHEMA_VERSION,
        )

        assert NAMESPACE == "nt"
        assert "national-treasure" in NAMESPACE_URI
        assert TOOL_NAME == "national-treasure"
        assert TOOL_VERSION
        assert SCHEMA_VERSION >= 1
