"""XMP Sidecar Writer for National Treasure.

Writes web capture provenance to XMP sidecar files using the nt: namespace.
Preserves other namespaces (wnb:, shoe:, vbuffet:) when writing.
Appends to shared custody chain for provenance tracking.
"""

import os
import secrets
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Try to import exiftool
try:
    from exiftool import ExifToolHelper
    EXIFTOOL_AVAILABLE = True
except ImportError:
    EXIFTOOL_AVAILABLE = False

# Namespace configuration
NAMESPACE = "nt"
NAMESPACE_URI = "http://national-treasure.dev/xmp/1.0/"
TOOL_NAME = "national-treasure"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = 1


@dataclass
class WebProvenance:
    """Web capture provenance data."""
    source_url: str
    page_url: str | None = None
    page_title: str | None = None
    capture_method: str = "screenshot"  # screenshot, pdf, html, warc
    browser_engine: str = "chromium"
    user_agent: str | None = None
    viewport_size: str | None = None
    http_status: int | None = None
    was_blocked: bool = False
    warc_file: str | None = None
    warc_record_id: str | None = None


def _generate_event_id() -> str:
    """Generate a unique event ID."""
    return f"{int(datetime.now().timestamp())}-{secrets.token_hex(4)}"


def _get_hostname() -> str:
    """Get current hostname safely."""
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def _get_username() -> str:
    """Get current username safely."""
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USER", "unknown")


def _build_custody_event(action: str, outcome: str, notes: str | None = None) -> str:
    """Build custody event struct for exiftool."""
    event_struct = (
        f"{{EventID={_generate_event_id()},"
        f"EventTimestamp={datetime.now(UTC).isoformat()},"
        f"EventAction={action},"
        f"EventOutcome={outcome},"
        f"EventTool={TOOL_NAME}/{TOOL_VERSION},"
        f"EventHost={_get_hostname()},"
        f"EventUser={_get_username()}"
    )
    if notes:
        # Escape special characters in notes
        safe_notes = notes.replace("{", "_").replace("}", "_").replace("=", "_").replace(",", "_")
        event_struct += f",EventNotes={safe_notes}"
    event_struct += "}"
    return event_struct


class XmpWriter:
    """Write XMP metadata preserving other namespaces."""

    def __init__(self):
        if not EXIFTOOL_AVAILABLE:
            raise RuntimeError(
                "exiftool not available. Install with: pip install pyexiftool"
            )

    def read_sidecar(self, file_path: Path) -> dict[str, Any] | None:
        """Read existing XMP sidecar."""
        xmp_path = Path(f"{file_path}.xmp")
        if not xmp_path.exists():
            return None
        try:
            with ExifToolHelper() as et:
                results = et.get_metadata(str(xmp_path))
                return results[0] if results else None
        except Exception:
            return None

    def write_capture_metadata(
        self,
        file_path: Path,
        provenance: WebProvenance,
    ) -> None:
        """Write web capture metadata to XMP sidecar.

        Args:
            file_path: Path to the captured file (screenshot, PDF, etc.)
            provenance: Web provenance data
        """
        xmp_path = Path(f"{file_path}.xmp")

        # Read existing XMP to get event count
        existing = self.read_sidecar(file_path) or {}
        event_count = existing.get("EventCount", 0)

        # Build exiftool arguments
        args = [
            f"-XMP-{NAMESPACE}:SchemaVersion={SCHEMA_VERSION}",
            f"-XMP-{NAMESPACE}:CapturedAt={datetime.now(UTC).isoformat()}",
            f"-XMP-{NAMESPACE}:SourceURL={provenance.source_url}",
            f"-XMP-{NAMESPACE}:CaptureMethod={provenance.capture_method}",
            f"-XMP-{NAMESPACE}:BrowserEngine={provenance.browser_engine}",
        ]

        # Optional fields
        if provenance.page_url:
            args.append(f"-XMP-{NAMESPACE}:PageURL={provenance.page_url}")
        if provenance.page_title:
            # Escape special chars in title
            safe_title = provenance.page_title.replace('"', "'")
            args.append(f'-XMP-{NAMESPACE}:PageTitle={safe_title}')
        if provenance.user_agent:
            args.append(f"-XMP-{NAMESPACE}:UserAgent={provenance.user_agent}")
        if provenance.viewport_size:
            args.append(f"-XMP-{NAMESPACE}:ViewportSize={provenance.viewport_size}")
        if provenance.http_status is not None:
            args.append(f"-XMP-{NAMESPACE}:HttpStatus={provenance.http_status}")
        if provenance.was_blocked:
            args.append(f"-XMP-{NAMESPACE}:WasBlocked=true")
        if provenance.warc_file:
            args.append(f"-XMP-{NAMESPACE}:WarcFile={provenance.warc_file}")
        if provenance.warc_record_id:
            args.append(f"-XMP-{NAMESPACE}:WarcRecordID={provenance.warc_record_id}")

        # Add custody chain event
        custody_notes = f"Captured {provenance.capture_method} from {provenance.source_url[:50]}"
        args.extend([
            f"-XMP-wnb:EventCount={event_count + 1}",
            f"-XMP-wnb:SidecarUpdated={datetime.now(UTC).isoformat()}",
            f"-XMP-wnb:CustodyChain+={_build_custody_event('web_capture', 'success', custody_notes)}",
        ])

        # Write using exiftool
        with ExifToolHelper() as et:
            et.execute("-overwrite_original", *args, str(xmp_path))

    def create_initial_sidecar(
        self,
        file_path: Path,
        provenance: WebProvenance,
        content_hash: str | None = None,
        file_size: int | None = None,
    ) -> None:
        """Create initial XMP sidecar for a web capture.

        Use this when creating a new file (not updating existing).
        Sets up initial custody chain.

        Args:
            file_path: Path to the captured file
            provenance: Web provenance data
            content_hash: Optional BLAKE3 hash of content
            file_size: Optional file size in bytes
        """
        xmp_path = Path(f"{file_path}.xmp")

        args = [
            # Initial custody chain setup
            f"-XMP-wnb:FirstSeen={datetime.now(UTC).isoformat()}",
            "-XMP-wnb:EventCount=1",
            f"-XMP-wnb:SidecarCreated={datetime.now(UTC).isoformat()}",
            f"-XMP-wnb:SidecarUpdated={datetime.now(UTC).isoformat()}",
            f"-XMP-wnb:CustodyChain+={_build_custody_event('web_capture', 'success', f'Initial capture from {provenance.source_url[:50]}')}",
            # NT namespace metadata
            f"-XMP-{NAMESPACE}:SchemaVersion={SCHEMA_VERSION}",
            f"-XMP-{NAMESPACE}:CapturedAt={datetime.now(UTC).isoformat()}",
            f"-XMP-{NAMESPACE}:SourceURL={provenance.source_url}",
            f"-XMP-{NAMESPACE}:CaptureMethod={provenance.capture_method}",
            f"-XMP-{NAMESPACE}:BrowserEngine={provenance.browser_engine}",
        ]

        # Add optional content identity
        if content_hash:
            args.append(f"-XMP-wnb:ContentHash={content_hash[:16]}")
            args.append(f"-XMP-wnb:ContentHashFull={content_hash}")
            args.append("-XMP-wnb:HashAlgorithm=blake3")
        if file_size is not None:
            args.append(f"-XMP-wnb:FileSize={file_size}")

        # Optional provenance fields
        if provenance.page_url:
            args.append(f"-XMP-{NAMESPACE}:PageURL={provenance.page_url}")
        if provenance.page_title:
            safe_title = provenance.page_title.replace('"', "'")
            args.append(f'-XMP-{NAMESPACE}:PageTitle={safe_title}')
        if provenance.user_agent:
            args.append(f"-XMP-{NAMESPACE}:UserAgent={provenance.user_agent}")
        if provenance.viewport_size:
            args.append(f"-XMP-{NAMESPACE}:ViewportSize={provenance.viewport_size}")
        if provenance.http_status is not None:
            args.append(f"-XMP-{NAMESPACE}:HttpStatus={provenance.http_status}")
        if provenance.was_blocked:
            args.append(f"-XMP-{NAMESPACE}:WasBlocked=true")
        if provenance.warc_file:
            args.append(f"-XMP-{NAMESPACE}:WarcFile={provenance.warc_file}")
        if provenance.warc_record_id:
            args.append(f"-XMP-{NAMESPACE}:WarcRecordID={provenance.warc_record_id}")

        with ExifToolHelper() as et:
            et.execute("-overwrite_original", *args, str(xmp_path))

    def append_custody_event(
        self,
        file_path: Path,
        action: str,
        outcome: str,
        notes: str | None = None,
    ) -> None:
        """Append a custody event to the chain.

        Args:
            file_path: Path to the file
            action: Event action (web_capture, metadata_extraction, etc.)
            outcome: Event outcome (success, failure, partial)
            notes: Optional notes about the event
        """
        xmp_path = Path(f"{file_path}.xmp")

        existing = self.read_sidecar(file_path) or {}
        event_count = existing.get("EventCount", 0)

        with ExifToolHelper() as et:
            et.execute(
                "-overwrite_original",
                f"-XMP-wnb:EventCount={event_count + 1}",
                f"-XMP-wnb:SidecarUpdated={datetime.now(UTC).isoformat()}",
                f"-XMP-wnb:CustodyChain+={_build_custody_event(action, outcome, notes)}",
                str(xmp_path),
            )

    def has_capture_metadata(self, file_path: Path) -> bool:
        """Check if XMP sidecar has national-treasure metadata."""
        existing = self.read_sidecar(file_path)
        if not existing:
            return False
        return existing.get("SourceURL") is not None or existing.get("CapturedAt") is not None

    def read_capture_metadata(self, file_path: Path) -> WebProvenance | None:
        """Read web provenance from XMP sidecar."""
        existing = self.read_sidecar(file_path)
        if not existing:
            return None

        source_url = existing.get("SourceURL")
        if not source_url:
            return None

        return WebProvenance(
            source_url=str(source_url),
            page_url=existing.get("PageURL"),
            page_title=existing.get("PageTitle"),
            capture_method=existing.get("CaptureMethod", "screenshot"),
            browser_engine=existing.get("BrowserEngine", "chromium"),
            user_agent=existing.get("UserAgent"),
            viewport_size=existing.get("ViewportSize"),
            http_status=existing.get("HttpStatus"),
            was_blocked=existing.get("WasBlocked", False),
            warc_file=existing.get("WarcFile"),
            warc_record_id=existing.get("WarcRecordID"),
        )


def get_xmp_path(file_path: Path) -> Path:
    """Get XMP sidecar path for a file."""
    return Path(f"{file_path}.xmp")


def xmp_exists(file_path: Path) -> bool:
    """Check if XMP sidecar exists."""
    return get_xmp_path(file_path).exists()


# Module-level instance
_writer: XmpWriter | None = None


def get_xmp_writer() -> XmpWriter:
    """Get or create XMP writer instance."""
    global _writer
    if _writer is None:
        _writer = XmpWriter()
    return _writer
