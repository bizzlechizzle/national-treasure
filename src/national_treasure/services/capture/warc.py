"""WARC archive generation for National Treasure.

Uses wget for WARC generation with fallback to simplified HTML capture.
"""

import asyncio
import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple


class WarcResult(NamedTuple):
    """Result of WARC capture."""
    success: bool
    warc_path: Path | None
    cdx_path: Path | None
    error: str | None = None


def _wget_available() -> bool:
    """Check if wget is available."""
    return shutil.which("wget") is not None


def _generate_warc_filename(url: str) -> str:
    """Generate a unique WARC filename from URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"capture-{timestamp}-{url_hash}"


async def capture_warc(
    url: str,
    output_dir: Path,
    timeout_seconds: int = 120,
    include_requisites: bool = True,
) -> WarcResult:
    """Capture URL as WARC archive using wget.

    Args:
        url: URL to capture
        output_dir: Directory to save WARC files
        timeout_seconds: Maximum time for capture
        include_requisites: Include page requisites (CSS, JS, images)

    Returns:
        WarcResult with paths to generated files
    """
    if not _wget_available():
        return WarcResult(
            success=False,
            warc_path=None,
            cdx_path=None,
            error="wget not available. Install with: brew install wget",
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    warc_basename = _generate_warc_filename(url)
    warc_path = output_dir / f"{warc_basename}.warc.gz"

    # Build wget command
    cmd = [
        "wget",
        "--warc-file", str(output_dir / warc_basename),
        "--warc-cdx",  # Generate CDX index
        "--no-check-certificate",
        "--timeout", "30",
        "--tries", "2",
        "--waitretry", "3",
        "-q",  # Quiet mode
        "-P", str(output_dir / "files"),  # Downloaded files directory
    ]

    if include_requisites:
        cmd.extend([
            "--page-requisites",
            "--span-hosts",
            "--convert-links",
        ])

    cmd.append(url)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            _, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return WarcResult(
                success=False,
                warc_path=None,
                cdx_path=None,
                error=f"WARC capture timed out after {timeout_seconds}s",
            )

        # Check if WARC was created
        if warc_path.exists():
            cdx_path = output_dir / f"{warc_basename}.cdx"
            return WarcResult(
                success=True,
                warc_path=warc_path,
                cdx_path=cdx_path if cdx_path.exists() else None,
                error=None,
            )
        else:
            return WarcResult(
                success=False,
                warc_path=None,
                cdx_path=None,
                error=f"WARC file not created. stderr: {stderr.decode()[:200]}",
            )

    except Exception as e:
        return WarcResult(
            success=False,
            warc_path=None,
            cdx_path=None,
            error=str(e),
        )


async def capture_warc_with_fallback(
    url: str,
    output_dir: Path,
    html_content: str | None = None,
) -> WarcResult:
    """Capture WARC with fallback to simplified archive.

    If wget fails, creates a minimal WARC-like archive from provided HTML.

    Args:
        url: URL to capture
        output_dir: Directory to save files
        html_content: Pre-captured HTML content for fallback

    Returns:
        WarcResult with paths
    """
    # Try wget first
    result = await capture_warc(url, output_dir)
    if result.success:
        return result

    # Fallback: save HTML directly if provided
    if html_content:
        output_dir.mkdir(parents=True, exist_ok=True)
        warc_basename = _generate_warc_filename(url)
        html_path = output_dir / f"{warc_basename}.html"
        html_path.write_text(html_content, encoding="utf-8")

        return WarcResult(
            success=True,
            warc_path=html_path,  # Not a real WARC but usable
            cdx_path=None,
            error=f"Fallback: saved HTML only ({result.error})",
        )

    return result
