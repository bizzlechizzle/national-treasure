# National Treasure Enhancement Plan

> **Version**: 0.1.2 → 1.0.0
> **Created**: 2024-12-25
> **Status**: Implementation Ready
> **Goal**: A+ / 100 / 100 Production Release

---

## Executive Summary

This document details all enhancements required to bring National Treasure from Beta (0.1.2) to Production (1.0.0). Based on comprehensive audit findings against the SME reference and CLAUDE.md standards.

**Current Grade**: B (82%)
**Target Grade**: A+ (95%+)

---

## Table of Contents

1. [Critical Fixes](#phase-1-critical-fixes)
2. [Test Infrastructure](#phase-2-test-infrastructure)
3. [Missing Features](#phase-3-missing-features)
4. [Edge Cases](#phase-4-edge-cases)
5. [Documentation](#phase-5-documentation)
6. [Implementation Checklist](#implementation-checklist)
7. [Sources & References](#sources--references)

---

## Phase 1: Critical Fixes

### 1.1 Fix Test Environment

**Issue**: All 8 unit test files fail with import errors
**Root Cause**: Package not installed or Python version mismatch

**Fix**:
```bash
# Create virtual environment with correct Python
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/unit/ -v
```

**Files to Update**:
- `pyproject.toml` - Add pytest-asyncio properly
- `conftest.py` - Add proper async fixtures

**Source**: [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)

---

### 1.2 Fix datetime.utcnow() Deprecation

**Issue**: `datetime.utcnow()` deprecated in Python 3.12+
**Locations**:
- `learning/domain.py:161`
- `queue/service.py:129,283,356,408,429`
- `core/models.py:148,194`

**Fix**:
```python
# Before
from datetime import datetime
now = datetime.utcnow()

# After
from datetime import datetime, UTC
now = datetime.now(UTC)
```

**Source**: [Python 3.12 Deprecations](https://docs.python.org/3.12/library/datetime.html#datetime.datetime.utcnow)

---

### 1.3 Add Job Lease Timeout

**Issue**: Running jobs never timeout - orphaned jobs possible
**Location**: `queue/service.py`

**Fix**:
```python
# Add to _claim_next_job()
# Release stale running jobs (>30 min old)
await db.execute("""
    UPDATE jobs
    SET status = 'pending', started_at = NULL
    WHERE status = 'running'
    AND started_at < datetime('now', '-30 minutes')
""")
```

**Source**: [litequeue patterns](https://github.com/litements/litequeue)

---

## Phase 2: Test Infrastructure

### 2.1 Fix pytest-asyncio Configuration

**File**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

---

### 2.2 Add Integration Tests

**Create**: `tests/integration/test_capture.py`

```python
import pytest
from national_treasure.services.browser import BrowserService
from national_treasure.services.capture import CaptureService

@pytest.mark.integration
async def test_capture_simple_page():
    """End-to-end capture of a simple page."""
    async with BrowserService() as browser:
        async with browser.page() as page:
            capture = CaptureService(page)
            result = await capture.capture("https://example.com")

            assert result.success
            assert result.screenshot_path is not None
            assert result.html_path is not None

@pytest.mark.integration
async def test_capture_detects_cloudflare():
    """Verify Cloudflare detection works."""
    # Use a known Cloudflare-protected test site
    ...
```

---

### 2.3 Add CLI Tests

**Create**: `tests/integration/test_cli.py`

```python
from typer.testing import CliRunner
from national_treasure.cli.main import app

runner = CliRunner()

def test_capture_url_help():
    result = runner.invoke(app, ["capture", "url", "--help"])
    assert result.exit_code == 0
    assert "URL to capture" in result.output

def test_queue_status():
    result = runner.invoke(app, ["queue", "status", "--brief"])
    assert result.exit_code == 0
```

**Source**: [Typer Testing](https://typer.tiangolo.com/tutorial/testing/)

---

## Phase 3: Missing Features

### 3.1 WARC Generation

**Status**: Documented in SME but not implemented
**Priority**: HIGH

**Implementation Options**:

| Option | Pros | Cons |
|--------|------|------|
| **wget primary** | Standard format, reliable | External dependency |
| **CDP interception** | In-process, no external | Complex, may miss resources |
| **warcio library** | Python native | Requires manual resource collection |

**Recommended**: wget with CDP fallback

**Files to Create**:
- `services/capture/warc.py`

```python
import asyncio
import subprocess
from pathlib import Path

async def capture_warc(url: str, output_dir: Path) -> Path:
    """Capture URL as WARC using wget."""
    warc_path = output_dir / f"{hash(url)}.warc.gz"

    proc = await asyncio.create_subprocess_exec(
        "wget",
        "--warc-file", str(warc_path.with_suffix("")),
        "--warc-cdx",
        "--page-requisites",
        "--adjust-extension",
        "--span-hosts",
        "--convert-links",
        "--no-directories",
        "-P", str(output_dir),
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    return warc_path
```

**Source**: [WARC File Format](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1/)

---

### 3.2 Image Discovery Pipeline

**Status**: Not implemented
**Priority**: HIGH

**Implementation**:
```python
# services/image/discovery.py

from dataclasses import dataclass
from playwright.async_api import Page

@dataclass
class DiscoveredImage:
    url: str
    source: str  # img, srcset, og:image, schema.org, etc.
    alt: str | None
    width: int | None
    height: int | None

async def discover_images(page: Page) -> list[DiscoveredImage]:
    """Discover all images on page from multiple sources."""
    images = []

    # 1. Standard img tags
    img_tags = await page.evaluate("""
        () => Array.from(document.querySelectorAll('img'))
            .map(img => ({
                url: img.src,
                srcset: img.srcset,
                alt: img.alt,
                width: img.naturalWidth,
                height: img.naturalHeight
            }))
    """)

    # 2. srcset parsing
    for img in img_tags:
        if img.get('srcset'):
            for src in parse_srcset(img['srcset']):
                images.append(DiscoveredImage(
                    url=src['url'],
                    source='srcset',
                    alt=img.get('alt'),
                    width=src.get('width'),
                    height=None
                ))

    # 3. Open Graph images
    og_images = await page.evaluate("""
        () => Array.from(document.querySelectorAll('meta[property="og:image"]'))
            .map(meta => meta.content)
    """)

    # 4. Schema.org images
    schema_images = await page.evaluate("""
        () => {
            const scripts = document.querySelectorAll('script[type="application/ld+json"]');
            const images = [];
            scripts.forEach(s => {
                try {
                    const data = JSON.parse(s.textContent);
                    if (data.image) images.push(data.image);
                    if (data['@graph']) {
                        data['@graph'].forEach(item => {
                            if (item.image) images.push(item.image);
                        });
                    }
                } catch {}
            });
            return images.flat();
        }
    """)

    return images
```

**Source**: [srcset attribute MDN](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#srcset)

---

### 3.3 Image Enhancement

**Status**: Not implemented
**Priority**: MEDIUM

**Implementation**:
```python
# services/image/enhancement.py

import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

# Common CDN suffix patterns
QUALITY_SUFFIXES = [
    (r'-\d+x\d+(?=\.[a-z]+$)', ''),  # -800x600.jpg → .jpg
    (r'_\d+x\d+(?=\.[a-z]+$)', ''),  # _800x600.jpg → .jpg
    (r'\?.*$', ''),                   # Remove query params
    (r'@\d+x(?=\.[a-z]+$)', ''),     # @2x.jpg → .jpg
]

def enhance_image_url(url: str) -> str:
    """Remove quality-reducing suffixes from image URLs."""
    enhanced = url

    for pattern, replacement in QUALITY_SUFFIXES:
        enhanced = re.sub(pattern, replacement, enhanced)

    return enhanced
```

---

## Phase 4: Edge Cases

### 4.1 Graceful Shutdown

**Issue**: Workers cancelled abruptly on stop
**Fix**:

```python
# queue/service.py

import signal

class JobQueue:
    def __init__(self, ...):
        ...
        self._shutdown_event = asyncio.Event()

    async def start(self, ...):
        ...
        # Register signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

    def _handle_shutdown(self):
        self._shutdown_event.set()

    async def _worker_loop(self, worker_id: int):
        while self._running:
            if self._shutdown_event.is_set():
                # Finish current job, then exit
                break
            ...
```

---

### 4.2 Circuit Breaker for Domains

**Issue**: No way to stop hitting failing domains
**Fix**:

```python
# services/learning/circuit_breaker.py

from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CircuitState:
    failures: int = 0
    last_failure: datetime | None = None
    open_until: datetime | None = None

class DomainCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 300):
        self.threshold = failure_threshold
        self.reset_timeout = timedelta(seconds=reset_timeout)
        self._states: dict[str, CircuitState] = {}

    def is_open(self, domain: str) -> bool:
        state = self._states.get(domain)
        if not state:
            return False
        if state.open_until and datetime.now(UTC) < state.open_until:
            return True
        return False

    def record_failure(self, domain: str):
        state = self._states.setdefault(domain, CircuitState())
        state.failures += 1
        state.last_failure = datetime.now(UTC)

        if state.failures >= self.threshold:
            state.open_until = datetime.now(UTC) + self.reset_timeout

    def record_success(self, domain: str):
        if domain in self._states:
            del self._states[domain]
```

---

### 4.3 Remove Global Mutable State

**Issue**: `_db` global in `database.py`
**Fix**: Use dependency injection pattern

```python
# core/database.py

# Remove global _db
# Add to services that need database:

class DomainLearner:
    def __init__(self, db: Database):
        self.db = db
```

---

## Phase 5: Documentation

### 5.1 Update README.md

Add sections for:
- Installation troubleshooting
- Python version requirements
- Virtual environment setup
- Full CLI command reference

### 5.2 API Documentation

Create `docs/api.md` with:
- All public classes and methods
- Usage examples
- Configuration options

### 5.3 Example Scripts

Create `examples/`:
- `basic_capture.py`
- `batch_processing.py`
- `learning_insights.py`

---

## Implementation Checklist

### Critical (Must Complete)

- [ ] Fix test environment setup
- [ ] Add pytest-asyncio configuration
- [ ] Fix datetime.utcnow() deprecation
- [ ] Add job lease timeout
- [ ] Run all tests to 100% pass

### High Priority

- [ ] Add integration tests for capture
- [ ] Add CLI tests
- [ ] Implement WARC generation
- [ ] Implement image discovery
- [ ] Add graceful shutdown

### Medium Priority

- [ ] Implement image enhancement
- [ ] Add circuit breaker
- [ ] Remove global mutable state
- [ ] Add worker logging
- [ ] Add max queue depth limit

### Low Priority

- [ ] Add API documentation
- [ ] Create example scripts
- [ ] Add domain blacklist
- [ ] Add performance benchmarks

---

## Sources & References

### Official Documentation
- [Playwright Python Docs](https://playwright.dev/python/docs/intro)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Typer Testing](https://typer.tiangolo.com/tutorial/testing/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/latest/)

### Best Practices
- [Thompson Sampling Tutorial (Stanford)](https://web.stanford.edu/~bvr/pubs/TS_Tutorial.pdf)
- [ZenRows Cloudflare Bypass](https://www.zenrows.com/blog/bypass-cloudflare)
- [litequeue SQLite Queue](https://github.com/litements/litequeue)

### Standards
- [WARC 1.1 Specification](https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1/)
- [Schema.org ImageObject](https://schema.org/ImageObject)
- [Open Graph Protocol](https://ogp.me/)

### Python Best Practices
- [Python 3.12 Deprecations](https://docs.python.org/3.12/library/datetime.html)
- [PEP 668 - Externally Managed Environments](https://peps.python.org/pep-0668/)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-25 | Initial enhancement plan |
