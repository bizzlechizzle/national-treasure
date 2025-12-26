"""Capture services for archiving web pages."""

from national_treasure.services.capture.service import CaptureService
from national_treasure.services.capture.warc import (
    WarcResult,
    capture_warc,
    capture_warc_with_fallback,
)

__all__ = [
    "CaptureService",
    "WarcResult",
    "capture_warc",
    "capture_warc_with_fallback",
]
