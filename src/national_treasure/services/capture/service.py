"""Capture service for archiving web pages."""

import gzip
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import Page

from national_treasure.core.config import get_config
from national_treasure.core.models import BrowserConfig, CaptureResult
from national_treasure.services.browser.behaviors import BehaviorOptions
from national_treasure.services.browser.behaviors import run_behaviors as execute_behaviors
from national_treasure.services.browser.service import BrowserService
from national_treasure.services.browser.validator import validate_response


class CaptureService:
    """Service for capturing web pages in multiple formats."""

    def __init__(
        self,
        config: BrowserConfig | None = None,
        headless: bool = True,
        output_dir: Path | None = None,
    ):
        """Initialize capture service.

        Args:
            config: Browser configuration
            headless: Run in headless mode
            output_dir: Output directory for captured files
        """
        self.config = config or BrowserConfig()
        self.headless = headless
        self.output_dir = output_dir or get_config().archive_dir
        self._browser_service: BrowserService | None = None

    async def __aenter__(self) -> "CaptureService":
        """Enter async context."""
        self._browser_service = BrowserService(
            config=self.config,
            headless=self.headless,
        )
        await self._browser_service.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._browser_service:
            await self._browser_service.stop()
            self._browser_service = None

    async def capture(
        self,
        url: str,
        formats: list[str] | None = None,
        run_behaviors: bool = True,
        behavior_options: BehaviorOptions | None = None,
        timeout_ms: int = 30000,
    ) -> CaptureResult:
        """Capture a web page in specified formats.

        Args:
            url: URL to capture
            formats: List of formats (screenshot, pdf, html, warc). Default: all
            run_behaviors: Run page behaviors before capture
            behavior_options: Options for page behaviors
            timeout_ms: Page load timeout

        Returns:
            CaptureResult with paths to captured files
        """
        if formats is None:
            formats = ["screenshot", "pdf", "html", "warc"]

        start_time = datetime.utcnow()
        result = CaptureResult(success=False, url=url, timestamp=start_time)

        # Create output directory
        output_path = self._get_output_path(url)
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            async with self._browser_service.page() as page:
                # Navigate to URL
                response = await self._browser_service.goto(
                    page, url, timeout=timeout_ms
                )

                # Validate response
                validation = await validate_response(response, page)
                result.validation = validation

                if validation.blocked:
                    result.error = f"Blocked: {validation.reason}"
                    return result

                # Run page behaviors to expand content
                if run_behaviors:
                    await execute_behaviors(page, behavior_options)

                # Extract metadata
                result.page_title = await page.title()
                result.page_description = await self._get_meta_description(page)

                # Capture in each format
                for fmt in formats:
                    try:
                        if fmt == "screenshot":
                            result.screenshot_path = await self._capture_screenshot(
                                page, output_path
                            )
                        elif fmt == "pdf":
                            result.pdf_path = await self._capture_pdf(page, output_path)
                        elif fmt == "html":
                            result.html_path = await self._capture_html(page, output_path)
                        elif fmt == "warc":
                            result.warc_path = await self._capture_warc(
                                page, url, output_path
                            )
                    except Exception:
                        # Log error but continue with other formats
                        pass

                result.success = True

        except Exception as e:
            result.error = str(e)

        result.duration_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        return result

    async def _capture_screenshot(self, page: Page, output_path: Path) -> str:
        """Capture full-page screenshot."""
        path = output_path / "screenshot.png"
        await page.screenshot(path=str(path), full_page=True)
        return str(path)

    async def _capture_pdf(self, page: Page, output_path: Path) -> str:
        """Capture page as PDF."""
        path = output_path / "page.pdf"
        await page.pdf(
            path=str(path),
            format="A4",
            print_background=True,
            margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"},
        )
        return str(path)

    async def _capture_html(self, page: Page, output_path: Path) -> str:
        """Capture page HTML."""
        path = output_path / "page.html"
        content = await page.content()

        # Inline resources (basic version)
        # TODO: Full resource inlining

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(path)

    async def _capture_warc(
        self, page: Page, url: str, output_path: Path
    ) -> str:
        """Capture page as WARC (Web ARChive) format.

        This is a simplified WARC implementation using CDP.
        For production, use wget --warc-file when available.
        """
        path = output_path / "archive.warc.gz"

        # Get page content and response info
        content = await page.content()

        # Create WARC record
        warc_records = []

        # WARC header
        warc_id = f"urn:uuid:{hashlib.sha256(url.encode()).hexdigest()[:36]}"
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Warcinfo record
        warcinfo = self._create_warc_record(
            "warcinfo",
            warc_id,
            timestamp,
            url,
            "software: national-treasure/0.1.0\r\nformat: WARC/1.1\r\n",
            "application/warc-fields",
        )
        warc_records.append(warcinfo)

        # Response record
        response_content = content.encode("utf-8")
        response_record = self._create_warc_record(
            "response",
            f"urn:uuid:{hashlib.sha256((url + 'response').encode()).hexdigest()[:36]}",
            timestamp,
            url,
            response_content,
            "text/html",
        )
        warc_records.append(response_record)

        # Write compressed WARC
        with gzip.open(path, "wb") as f:
            for record in warc_records:
                f.write(record)

        return str(path)

    def _create_warc_record(
        self,
        record_type: str,
        record_id: str,
        timestamp: str,
        target_uri: str,
        content: str | bytes,
        content_type: str,
    ) -> bytes:
        """Create a WARC record."""
        if isinstance(content, str):
            content = content.encode("utf-8")

        headers = [
            "WARC/1.1",
            f"WARC-Type: {record_type}",
            f"WARC-Record-ID: <{record_id}>",
            f"WARC-Date: {timestamp}",
            f"WARC-Target-URI: {target_uri}",
            f"Content-Type: {content_type}",
            f"Content-Length: {len(content)}",
        ]

        header_block = "\r\n".join(headers) + "\r\n\r\n"
        return header_block.encode("utf-8") + content + b"\r\n\r\n"

    async def _get_meta_description(self, page: Page) -> str | None:
        """Extract meta description from page."""
        try:
            return await page.evaluate("""
                () => {
                    const meta = document.querySelector('meta[name="description"]');
                    return meta ? meta.getAttribute('content') : null;
                }
            """)
        except Exception:
            return None

    def _get_output_path(self, url: str) -> Path:
        """Generate output path for a URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.replace(":", "_")
        path_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        return self.output_dir / domain / f"{timestamp}_{path_hash}"


async def capture_url(
    url: str,
    formats: list[str] | None = None,
    headless: bool = True,
    run_behaviors: bool = True,
) -> CaptureResult:
    """Convenience function to capture a URL.

    Args:
        url: URL to capture
        formats: Capture formats
        headless: Run headless
        run_behaviors: Run page behaviors

    Returns:
        CaptureResult
    """
    async with CaptureService(headless=headless) as service:
        return await service.capture(url, formats=formats, run_behaviors=run_behaviors)
