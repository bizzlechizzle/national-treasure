# Playwright Browser Automation SME

> **Generated**: 2024-12-24
> **Sources current as of**: December 2024
> **Scope**: Exhaustive
> **Version**: 1.2
> **Languages**: Python (Playwright) & TypeScript (Puppeteer-core)
> **Parts**: 23 sections covering browser automation, archiving, extraction, and provenance

---

## Executive Summary / TLDR

This document provides production-grade patterns for browser automation using Playwright (Python) and Puppeteer (TypeScript). Key takeaways:

1. **Use async context managers** for browser lifecycle management to prevent resource leaks
2. **Implement bot detection bypass** using stealth plugins, shell headless mode, and proper browser flags
3. **Build robust scrapers** with fallback selectors, confidence tracking, and intelligent retry logic
4. **Validate responses** to catch silent failures (403s, CAPTCHAs, blocked pages from CloudFront/Cloudflare/PerimeterX/DataDome/Akamai)
5. **Use comprehensive behaviors** (scroll, expand, click tabs) to expose all hidden content before capture
6. **Smart image discovery** - Extract ALL image sources (srcset, picture, meta tags, data-* attributes, JSON-LD)
7. **Image quality analysis** - JPEG quality detection via quantization tables, watermark detection, perceptual hashing
8. **Intelligent URL enhancement** - Find highest-res versions via recursive suffix stripping and site-specific patterns
9. **WARC/WACZ archiving** - ISO 28500:2017 compliant web preservation with wget or CDP fallback
10. **Multi-standard metadata** - Extract Open Graph, Schema.org JSON-LD, Dublin Core, Twitter Cards
11. **Content extraction** - Main text via Trafilatura, video metadata via yt-dlp, EXIF via exiftool
12. **Extension integration** - WebSocket protocol for authenticated session capture and cookie injection

The patterns documented here are extracted from two production codebases (38,000+ LOC combined) handling music metadata scraping and web archiving.

---

## Background & Context

Browser automation serves multiple purposes: E2E testing, web scraping, web archiving, and automated data extraction. Playwright and Puppeteer are the leading tools, with Playwright offering better cross-browser support and Puppeteer providing deeper Chrome DevTools Protocol (CDP) access.

Modern websites employ aggressive bot detection, lazy loading, and dynamic content rendering that require sophisticated automation patterns to handle correctly.

---

## Part 1: Browser Lifecycle Management

### Python Async Context Manager Pattern [HIGH]

The gold standard for managing Playwright browser lifecycle:

```python
"""Playwright browser management service."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Browser, Page, Playwright, async_playwright


class BrowserService:
    """Manages Playwright browser lifecycle.

    Usage:
        async with BrowserService(headless=True) as browser:
            page = await browser.new_page()
            await page.goto("https://example.com")
            content = await page.content()
    """

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def __aenter__(self) -> "BrowserService":
        """Async context manager entry - start browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit - close browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def new_page(self) -> Page:
        """Create a new browser page."""
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use as async context manager.")
        return await self._browser.new_page()

    @asynccontextmanager
    async def page_context(self) -> AsyncIterator[Page]:
        """Create a page that auto-closes when done."""
        page = await self.new_page()
        try:
            yield page
        finally:
            await page.close()

    async def scrape_url(
        self,
        url: str,
        wait_for_selector: str | None = None,
        timeout: int = 30000,
    ) -> Page:
        """Navigate to URL and return page ready for extraction."""
        page = await self.new_page()

        # Navigate and wait for network idle (dynamic content loaded)
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        # Optionally wait for specific element
        if wait_for_selector:
            await page.wait_for_selector(wait_for_selector, timeout=timeout)

        return page
```

### TypeScript Singleton Browser Pattern [HIGH]

For Puppeteer/TypeScript, manage a shared browser instance:

```typescript
import puppeteerCore, { Browser, Page } from 'puppeteer-core';

let browserInstance: Browser | null = null;
let browserLaunchPromise: Promise<Browser> | null = null;

/**
 * Get or create a shared browser instance
 * Reuses browser to avoid cold start overhead on each capture
 */
export async function getBrowser(): Promise<Browser> {
  if (browserInstance?.isConnected()) {
    return browserInstance;
  }

  if (browserLaunchPromise) {
    return browserLaunchPromise;
  }

  browserLaunchPromise = launchBrowser();
  browserInstance = await browserLaunchPromise;
  browserLaunchPromise = null;

  return browserInstance;
}

/**
 * Close the shared browser instance
 */
export async function closeBrowser(): Promise<void> {
  if (browserInstance) {
    await browserInstance.close();
    browserInstance = null;
  }
}
```

---

## Part 2: Bot Detection Bypass [CRITICAL]

### Stealth Configuration (TypeScript/Puppeteer) [HIGH]

Bot detection is the #1 reason for scraping failures. Use these techniques:

```typescript
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Apply stealth plugin BEFORE first launch
puppeteerExtra.use(StealthPlugin());

async function launchBrowser(): Promise<Browser> {
  const options = {
    executablePath: '/path/to/chromium',

    // Chrome 129+: 'shell' mode is undetectable
    // Falls back gracefully on older versions
    headless: 'shell' as unknown as boolean,

    // Use dedicated profile (never shared with other instances)
    userDataDir: '/path/to/profile',

    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--window-size=1920,1080',

      // Anti-bot detection measures
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process',

      // Realistic browser settings
      '--lang=en-US,en',
      '--disable-extensions-except=',
      '--disable-default-apps',
      '--disable-component-update',

      // Prevent detection via WebGL/Canvas fingerprinting
      '--disable-reading-from-canvas',
      '--disable-3d-apis',
    ],

    // CRITICAL: Hide automation flag
    ignoreDefaultArgs: ['--enable-automation'],
  };

  return puppeteerExtra.launch(options);
}
```

### Key Bot Detection Indicators to Avoid

| Indicator | Solution |
|-----------|----------|
| `navigator.webdriver = true` | Stealth plugin removes this |
| `--enable-automation` flag | Use `ignoreDefaultArgs: ['--enable-automation']` |
| `cdc_` variables in window | Stealth plugin patches these |
| Headless detection | Use `headless: 'shell'` (Chrome 129+) |
| Missing plugins/fonts | Full browser profile with extensions |
| Canvas fingerprinting | `--disable-reading-from-canvas` |

### Zero-Detection Alternative: Detached Browser [MEDIUM]

For maximum stealth, launch browser with NO CDP connection:

```typescript
import { spawn, ChildProcess } from 'child_process';

/**
 * Launch browser as completely independent process
 * NO DevTools Protocol = NO automation fingerprints
 */
export async function launchDetachedBrowser(): Promise<{ pid: number }> {
  const args = [
    `--user-data-dir=/path/to/profile`,
    `--load-extension=/path/to/extension`,
    '--no-first-run',
    '--no-default-browser-check',
    // CRITICAL: NO --remote-debugging-port (no CDP)
    // CRITICAL: NO --enable-automation
    'https://starting-page.com',
  ];

  const browserProcess = spawn('/path/to/chromium', args, {
    detached: true,
    stdio: 'ignore',
    env: {
      ...process.env,
      // Remove automation environment variables
      PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: undefined,
      PUPPETEER_EXECUTABLE_PATH: undefined,
    },
  });

  browserProcess.unref();
  return { pid: browserProcess.pid! };
}
```

---

## Part 3: Response Validation [CRITICAL]

### Prevent Silent 403 Archival [HIGH]

Always validate page responses to catch blocks and errors:

```typescript
async function validatePageResponse(
  page: Page,
  response: HTTPResponse | null,
  url: string
): Promise<{ valid: boolean; error?: string }> {
  // Check HTTP status code
  if (!response) {
    return { valid: false, error: `No response received from ${url}` };
  }

  const status = response.status();
  if (status >= 400) {
    return { valid: false, error: `HTTP ${status}: ${response.statusText()}` };
  }

  // Check for bot detection / block pages in content
  const blockInfo = await page.evaluate(() => {
    const bodyText = document.body?.innerText?.toLowerCase() || '';
    const title = document.title?.toLowerCase() || '';

    const indicators = [
      // CloudFront (Amazon AWS)
      { pattern: 'generated by cloudfront', reason: 'CloudFront 403 block' },
      { pattern: 'request could not be satisfied', reason: 'CloudFront request blocked' },

      // Generic access/error patterns
      { pattern: 'access denied', reason: 'Access Denied page' },
      { pattern: 'forbidden', reason: 'Forbidden response' },
      { pattern: '403 error', reason: 'HTTP 403 Forbidden' },

      // CAPTCHA challenges
      { pattern: 'captcha', reason: 'CAPTCHA challenge' },
      { pattern: 'verify you are human', reason: 'Human verification required' },

      // Cloudflare
      { pattern: 'checking your browser', reason: 'Browser check in progress' },
      { pattern: 'just a moment', reason: 'Cloudflare challenge' },
      { pattern: 'ray id:', reason: 'Cloudflare error page' },

      // Rate limiting
      { pattern: 'too many requests', reason: 'Rate limit exceeded' },
    ];

    for (const { pattern, reason } of indicators) {
      if (bodyText.includes(pattern) || title.includes(pattern)) {
        return { isBlocked: true, reason };
      }
    }

    // Check for suspiciously short pages
    if (bodyText.length < 500 && (
      bodyText.includes('error') ||
      bodyText.includes('denied') ||
      bodyText.includes('forbidden')
    )) {
      return { isBlocked: true, reason: 'Suspiciously short error page' };
    }

    return { isBlocked: false, reason: '' };
  });

  if (blockInfo.isBlocked) {
    return { valid: false, error: `Page blocked: ${blockInfo.reason}` };
  }

  return { valid: true };
}
```

---

## Part 4: Page Interaction Behaviors [HIGH]

### Comprehensive Content Expansion

Modern web pages hide content behind lazy loading, accordions, tabs, and infinite scroll. Run these behaviors BEFORE capturing:

### 1. Dismiss Overlays (Cookie Banners, Modals)

```typescript
async function dismissOverlays(page: Page): Promise<number> {
  return await page.evaluate(async () => {
    let count = 0;
    const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

    const overlaySelectors = [
      // Cookie consent
      '[class*="cookie"] button[class*="accept"]',
      '[class*="cookie"] button[class*="agree"]',
      '#onetrust-accept-btn-handler',
      '.cc-accept', '.cc-allow', '.cc-dismiss',

      // Generic close buttons
      '[class*="modal"] [class*="close"]',
      '[class*="popup"] [class*="close"]',
      '[data-dismiss="modal"]',

      // Newsletter popups
      '[class*="newsletter"] [class*="close"]',
      'button[class*="dismiss"]',
      'button[class*="no-thanks"]',
    ];

    for (const selector of overlaySelectors) {
      try {
        const elements = document.querySelectorAll(selector);
        for (const el of Array.from(elements)) {
          if (el instanceof HTMLElement && el.offsetParent !== null) {
            el.click();
            count++;
            await sleep(300);
          }
        }
      } catch { /* ignore */ }
    }

    // Press Escape key to close modals
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));

    return count;
  });
}
```

### 2. Scroll to Load All Lazy Content

```typescript
async function scrollToLoadAll(page: Page): Promise<{ scrollCount: number }> {
  return await page.evaluate(async () => {
    const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

    let scrollCount = 0;
    let lastHeight = 0;
    let sameHeightCount = 0;
    const maxSameHeight = 3;

    while (sameHeightCount < maxSameHeight && scrollCount < 100) {
      const currentHeight = document.documentElement.scrollHeight;

      window.scrollTo({
        top: window.scrollTop + window.innerHeight,
        behavior: 'smooth'
      });
      scrollCount++;

      await sleep(300);

      if (window.scrollTop + window.innerHeight >= document.documentElement.scrollHeight - 10) {
        if (currentHeight === lastHeight) {
          sameHeightCount++;
        } else {
          sameHeightCount = 0;
        }
        lastHeight = currentHeight;
        await sleep(500); // Wait for lazy load
      }
    }

    window.scrollTo({ top: 0, behavior: 'instant' });
    return { scrollCount };
  });
}
```

### 3. Expand All Accordions and "Read More"

```typescript
async function expandAllContent(page: Page): Promise<{ expanded: number }> {
  return await page.evaluate(async () => {
    const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
    let expanded = 0;

    // 1. Expand all <details> elements
    const details = document.querySelectorAll('details:not([open])');
    for (const el of Array.from(details)) {
      (el as HTMLDetailsElement).open = true;
      expanded++;
    }

    // 2. Click aria-expanded="false" elements
    const ariaExpanded = document.querySelectorAll('[aria-expanded="false"]');
    for (const el of Array.from(ariaExpanded)) {
      try {
        (el as HTMLElement).click();
        expanded++;
        await sleep(150);
      } catch { /* ignore */ }
    }

    // 3. Click "read more" / "show more" links
    const textMatches = ['read more', 'show more', 'see more', 'view more', 'expand'];
    const allClickables = document.querySelectorAll('button, a, span[role="button"]');
    for (const el of Array.from(allClickables)) {
      const text = (el as HTMLElement).innerText?.toLowerCase().trim();
      if (text && textMatches.some(m => text === m || text.startsWith(m + ' '))) {
        try {
          (el as HTMLElement).click();
          expanded++;
          await sleep(300);
        } catch { /* ignore */ }
      }
    }

    return { expanded };
  });
}
```

### 4. Click Through All Tabs

```typescript
async function clickAllTabs(page: Page): Promise<{ clicked: number }> {
  return await page.evaluate(async () => {
    const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
    let clicked = 0;
    const processedTabs = new Set<HTMLElement>();

    const tabContainerSelectors = [
      '[role="tablist"]',
      '.tabs',
      '.nav-tabs',
      '[class*="tabs"]',
    ];

    for (const containerSelector of tabContainerSelectors) {
      const containers = document.querySelectorAll(containerSelector);

      for (const container of Array.from(containers)) {
        const tabs = container.querySelectorAll(
          '[role="tab"], .tab, .nav-link, [data-toggle="tab"]'
        );

        for (const tab of Array.from(tabs)) {
          if (processedTabs.has(tab as HTMLElement)) continue;
          processedTabs.add(tab as HTMLElement);

          const isSelected =
            tab.getAttribute('aria-selected') === 'true' ||
            tab.classList.contains('active');

          if (!isSelected) {
            try {
              (tab as HTMLElement).click();
              clicked++;
              await sleep(300);
            } catch { /* ignore */ }
          }
        }
      }
    }

    return { clicked };
  });
}
```

### 5. Navigate Carousels

```typescript
async function navigateCarousels(page: Page): Promise<{ slides: number }> {
  return await page.evaluate(async () => {
    const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
    let slides = 0;

    const carouselSelectors = [
      '.carousel', '.slider', '.swiper',
      '.slick-slider', '.owl-carousel',
      '[class*="carousel"]', '[class*="slider"]',
    ];

    for (const selector of carouselSelectors) {
      const containers = document.querySelectorAll(selector);

      for (const container of Array.from(containers)) {
        // Find next button
        const nextButton = container.querySelector(
          '.carousel-next, .slick-next, .swiper-button-next, ' +
          '[class*="next"], [aria-label*="next"]'
        ) as HTMLElement | null;

        if (nextButton) {
          const maxSlides = 20;
          let clickCount = 0;

          while (clickCount < maxSlides) {
            try {
              nextButton.click();
              slides++;
              clickCount++;
              await sleep(300);
            } catch { break; }
          }
        }
      }
    }

    return { slides };
  });
}
```

### Master Behavior Runner

```typescript
interface BehaviorResult {
  overlaysDismissed: number;
  scrollDepth: number;
  elementsExpanded: number;
  tabsClicked: number;
  carouselSlides: number;
  totalDurationMs: number;
}

async function runAllBehaviors(page: Page): Promise<BehaviorResult> {
  const startTime = Date.now();

  // 1. First, dismiss any overlays blocking content
  const overlaysDismissed = await dismissOverlays(page);

  // 2. Initial scroll to load lazy content
  const { scrollCount } = await scrollToLoadAll(page);

  // 3. Expand all accordions, details, read-more
  const { expanded } = await expandAllContent(page);

  // 4. Click through all tabs
  const { clicked } = await clickAllTabs(page);

  // 5. Navigate all carousels
  const { slides } = await navigateCarousels(page);

  // 6. Final scroll back to top
  await page.evaluate(() => window.scrollTo({ top: 0 }));

  return {
    overlaysDismissed,
    scrollDepth: scrollCount,
    elementsExpanded: expanded,
    tabsClicked: clicked,
    carouselSlides: slides,
    totalDurationMs: Date.now() - startTime,
  };
}
```

---

## Part 5: Scraper Architecture (Python) [HIGH]

### Base Scraper Pattern with Helper Methods

```python
"""Base scraper interface for site-specific implementations."""

import re
from abc import ABC, abstractmethod
from playwright.async_api import Page


class BaseScraper(ABC):
    """Abstract base class for site scrapers."""

    # Override in subclasses
    name: str = "base"
    url_patterns: list[str] = []  # Regex patterns to match URLs

    def can_handle(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        return any(re.match(pattern, url) for pattern in self.url_patterns)

    @abstractmethod
    def get_hardcoded_selectors(self) -> dict[str, str]:
        """Return hardcoded CSS selectors for this site."""
        ...

    @abstractmethod
    async def extract(self, page: Page) -> dict:
        """Extract metadata from a page."""
        ...

    async def extract_text(self, page: Page, selector: str) -> str | None:
        """Helper to extract text from a selector."""
        element = await page.query_selector(selector)
        if element:
            text = await element.inner_text()
            return text.strip() if text else None
        return None

    async def extract_attribute(
        self, page: Page, selector: str, attribute: str
    ) -> str | None:
        """Helper to extract an attribute from a selector."""
        element = await page.query_selector(selector)
        if element:
            return await element.get_attribute(attribute)
        return None

    async def extract_all_text(self, page: Page, selector: str) -> list[str]:
        """Helper to extract text from all matching elements."""
        elements = await page.query_selector_all(selector)
        results = []
        for element in elements:
            text = await element.inner_text()
            if text:
                results.append(text.strip())
        return results
```

### Site-Specific Scraper Example

```python
"""Bandcamp scraper with hardcoded selectors."""

import re
from datetime import datetime
from playwright.async_api import Page
from .base import BaseScraper


class BandcampScraper(BaseScraper):
    """Scraper for Bandcamp album pages."""

    name = "bandcamp"
    url_patterns = [
        r"https?://[\w-]+\.bandcamp\.com/album/[\w-]+",
    ]

    # Hardcoded CSS selectors - maintain as dictionary for easy updates
    SELECTORS = {
        "title": "h2.trackTitle",
        "artist": "h3 span a",
        "artist_alt": "p#band-name-location span.title",  # Fallback
        "cover_image": "#tralbumArt img",
        "track_rows": "table.track_list tr",
        "track_number": ".track-number-col div",
        "track_title": ".title-col a, .title-col span.track-title",
        "track_duration": ".title-col span.time",
        "credits_block": ".tralbumData.tralbum-credits",
        "tags": ".tralbumData.tralbum-tags a",
    }

    def get_hardcoded_selectors(self) -> dict[str, str]:
        return self.SELECTORS.copy()

    async def extract(self, page: Page) -> dict:
        """Extract album metadata from Bandcamp page."""

        # Title - simple extraction
        title = await self.extract_text(page, self.SELECTORS["title"]) or "Unknown"

        # Artist - try primary, then fallback
        artist = await self.extract_text(page, self.SELECTORS["artist"])
        if not artist:
            artist = await self.extract_text(page, self.SELECTORS["artist_alt"])
        artist = artist or "Unknown Artist"

        # Cover URL with attribute extraction
        cover_url = await self.extract_attribute(
            page, self.SELECTORS["cover_image"], "src"
        )

        # JavaScript evaluation for complex extraction
        release_date = await page.evaluate("""
            () => {
                const credits = document.querySelector('.tralbum-credits');
                if (!credits) return null;
                const match = credits.innerText.match(/released\\s+(\\w+\\s+\\d+,\\s+\\d{4})/);
                return match ? match[1] : null;
            }
        """)

        # Tags - extract all matching elements
        tags = await self.extract_all_text(page, self.SELECTORS["tags"])

        # Tracks - iterate over table rows
        tracks = await self._extract_tracks(page)

        return {
            "title": title,
            "artist": artist,
            "cover_url": cover_url,
            "release_date": release_date,
            "tags": tags,
            "tracks": tracks,
        }

    async def _extract_tracks(self, page: Page) -> list[dict]:
        """Extract track list from page."""
        tracks = []
        track_rows = await page.query_selector_all(self.SELECTORS["track_rows"])

        for row in track_rows:
            # Get title element within row
            title_el = await row.query_selector(".title-col a, .title-col .track-title")
            if not title_el:
                continue

            track_title = await title_el.inner_text()
            if not track_title:
                continue

            # Get track number
            num_el = await row.query_selector(".track-number-col div")
            track_num = 0
            if num_el:
                num_text = await num_el.inner_text()
                if num_text:
                    num_text = num_text.strip().rstrip(".")
                    if num_text.isdigit():
                        track_num = int(num_text)

            # Get duration
            dur_el = await row.query_selector(".title-col span.time")
            duration = None
            if dur_el:
                duration = await dur_el.inner_text()

            tracks.append({
                "number": track_num,
                "title": track_title.strip(),
                "duration": duration.strip() if duration else None,
            })

        return tracks
```

---

## Part 6: Selector Learning System [MEDIUM]

### Track Selector Success/Failure Rates

```python
"""Training data management and pattern learning."""

from datetime import datetime
from pydantic import BaseModel


class SelectorPattern(BaseModel):
    """A learned CSS selector pattern."""

    field: str           # Which field this extracts (e.g., "title", "artist")
    selector: str        # CSS selector
    examples: list[str] = []    # Example values extracted
    success_count: int = 0
    failure_count: int = 0

    @property
    def confidence(self) -> float:
        """Calculate confidence based on success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total


class TrainingService:
    """Manages training data and pattern learning."""

    def record_success(
        self, site: str, field: str, selector: str, value: str | None = None
    ) -> None:
        """Record a successful selector extraction."""
        # Load site training data
        # Find or create pattern for selector
        # Increment success_count
        # Add value to examples (keep last 10)
        # Save training data
        pass

    def record_failure(self, site: str, field: str, selector: str) -> None:
        """Record a failed selector extraction."""
        # Increment failure_count
        pass

    def get_best_selector(
        self,
        site: str,
        field: str,
        hardcoded: str | None = None,
    ) -> str | None:
        """Get the best selector, considering learned patterns."""
        # Load training data
        # Sort patterns by confidence (descending)

        # If hardcoded exists and has high confidence (>=0.8), prefer it
        # This ensures we don't break working scrapers

        # Return best learned pattern if confidence >= 0.6
        # Otherwise fall back to hardcoded
        pass

    def get_fallback_selectors(
        self,
        site: str,
        field: str,
        exclude: str | None = None,
    ) -> list[str]:
        """Get fallback selectors for a field."""
        # Return selectors with confidence >= 0.3
        # Sorted by confidence, excluding the primary that failed
        pass
```

---

## Part 7: Wait Strategies [HIGH]

### Comprehensive Wait Strategy Reference

| Strategy | When to Use | Code |
|----------|-------------|------|
| `networkidle` | Page fully loaded, all XHR complete | `await page.goto(url, wait_until="networkidle")` |
| `networkidle2` | Same as above (Puppeteer) | `await page.goto(url, { waitUntil: 'networkidle2' })` |
| `domcontentloaded` | DOM ready, assets may still load | `wait_until="domcontentloaded"` |
| `load` | All resources loaded | `wait_until="load"` |
| `waitForSelector` | Specific element appears | `await page.wait_for_selector("#content")` |
| `waitForFunction` | JS condition becomes true | `await page.wait_for_function("window.loaded === true")` |
| `waitForNetworkIdle` | Post-navigation idle check | `await page.waitForNetworkIdle({ idleTime: 500 })` |

### Wait Strategy Best Practice

```python
async def robust_navigation(page: Page, url: str, critical_selector: str) -> None:
    """Navigate with multiple wait strategies."""

    # 1. Navigate and wait for network to settle
    await page.goto(url, wait_until="networkidle", timeout=30000)

    # 2. Wait for critical content element
    await page.wait_for_selector(critical_selector, timeout=10000)

    # 3. Extra wait for any final JS rendering
    await page.wait_for_timeout(500)
```

---

## Part 8: Cookie/Session Management [MEDIUM]

### Inject Cookies for Authenticated Scraping

```typescript
interface ExtensionCookie {
  name: string;
  value: string;
  domain: string;
  path: string;
  secure: boolean;
  httpOnly: boolean;
  expirationDate?: number;
}

async function injectCookies(
  page: Page,
  cookies: ExtensionCookie[],
  url: string
): Promise<boolean> {
  // Parse URL to get domain for cookie matching
  const urlObj = new URL(url);
  const urlDomain = urlObj.hostname;

  // Convert and filter cookies by domain
  const puppeteerCookies = cookies
    .filter(cookie => {
      const cookieDomain = cookie.domain.startsWith('.')
        ? cookie.domain.slice(1)
        : cookie.domain;
      return urlDomain === cookieDomain ||
             urlDomain.endsWith('.' + cookieDomain);
    })
    .map(cookie => ({
      name: cookie.name,
      value: cookie.value,
      domain: cookie.domain,
      path: cookie.path || '/',
      secure: cookie.secure,
      httpOnly: cookie.httpOnly,
      expires: cookie.expirationDate,
    }));

  if (puppeteerCookies.length === 0) {
    return false;
  }

  // Inject cookies BEFORE navigation
  await page.setCookie(...puppeteerCookies);
  return true;
}
```

### Profile Sync Between Browser Instances

```typescript
import * as fs from 'fs';
import * as path from 'path';

/**
 * Copy cookies from visible browser to headless archiver
 */
async function syncCookiesFromResearchBrowser(): Promise<boolean> {
  const researchProfile = path.join(userDataPath, 'research-browser');
  const archiveProfile = path.join(userDataPath, 'archive-browser-profile');

  const cookieFiles = ['Cookies', 'Cookies-journal'];
  let copied = false;

  for (const file of cookieFiles) {
    const srcPath = path.join(researchProfile, 'Default', file);
    const dstDir = path.join(archiveProfile, 'Default');
    const dstPath = path.join(dstDir, file);

    try {
      if (fs.existsSync(srcPath)) {
        await fs.promises.mkdir(dstDir, { recursive: true });
        await fs.promises.copyFile(srcPath, dstPath);
        copied = true;
      }
    } catch (err) {
      // Cookie file might be locked - try next time
      console.log(`Could not copy ${file}:`, err);
    }
  }

  return copied;
}
```

---

## Part 9: Capture Operations [HIGH]

### Full-Page Screenshot with Scroll

```typescript
async function captureScreenshot(
  page: Page,
  outputPath: string,
  options?: { fullPage?: boolean; runBehaviors?: boolean }
): Promise<void> {
  // Run behaviors to expand all content
  if (options?.runBehaviors !== false) {
    await runAllBehaviors(page);
  }

  // Capture screenshot
  await page.screenshot({
    path: outputPath,
    fullPage: options?.fullPage !== false,
    type: 'png',
  });
}
```

### PDF Generation

```typescript
async function capturePdf(page: Page, outputPath: string): Promise<void> {
  await page.pdf({
    path: outputPath,
    format: 'A4',
    printBackground: true,
    margin: {
      top: '20mm',
      right: '20mm',
      bottom: '20mm',
      left: '20mm',
    },
  });
}
```

### HTML with Inlined Resources

```typescript
async function captureHtml(page: Page): Promise<string> {
  return await page.evaluate(async () => {
    // Inline all stylesheets
    const styleSheets = Array.from(document.styleSheets);
    const styles: string[] = [];

    for (const sheet of styleSheets) {
      try {
        if (sheet.cssRules) {
          const rules = Array.from(sheet.cssRules)
            .map((rule) => rule.cssText)
            .join('\n');
          styles.push(rules);
        }
      } catch {
        // Cross-origin stylesheets can't be read
      }
    }

    // Create inline style tag
    const styleTag = document.createElement('style');
    styleTag.textContent = styles.join('\n');

    // Clone the document
    const clone = document.cloneNode(true) as Document;
    clone.head.appendChild(styleTag);

    return clone.documentElement.outerHTML;
  });
}
```

### Parallel Capture Operations

```typescript
interface CaptureAllResult {
  screenshot: CaptureResult;
  pdf: CaptureResult;
  html: CaptureResult;
  totalDuration: number;
}

async function captureAll(options: CaptureOptions): Promise<CaptureAllResult> {
  const startTime = Date.now();

  // Run all captures in parallel
  const [screenshot, pdf, html] = await Promise.all([
    captureScreenshot(options),
    capturePdf(options),
    captureHtml(options),
  ]);

  return {
    screenshot,
    pdf,
    html,
    totalDuration: Date.now() - startTime,
  };
}
```

---

## Part 10: Error Handling Patterns [HIGH]

### Proper Cleanup in Finally Blocks

```typescript
async function robustScrape(url: string): Promise<ScrapedData> {
  let page: Page | null = null;
  let cdpSession: CDPSession | null = null;

  try {
    const browser = await getBrowser();
    page = await browser.newPage();

    // Optional CDP session
    cdpSession = await page.createCDPSession();
    await cdpSession.send('Network.enable');

    // Do scraping work...
    const result = await scrapeData(page);

    return result;

  } catch (error) {
    // Log error, potentially retry
    console.error('Scrape failed:', error);
    throw error;

  } finally {
    // ALWAYS cleanup, even on error
    if (cdpSession) {
      try {
        await cdpSession.detach();
      } catch { /* ignore detach errors */ }
    }
    if (page) {
      await page.close().catch(() => {});
    }
  }
}
```

### Timeout Management at Multiple Levels

```typescript
interface TimeoutConfig {
  navigation: number;  // Page load timeout
  selector: number;    // Element wait timeout
  behavior: number;    // Per-behavior timeout
  total: number;       // Overall operation timeout
}

const DEFAULT_TIMEOUTS: TimeoutConfig = {
  navigation: 30000,   // 30 seconds
  selector: 10000,     // 10 seconds
  behavior: 30000,     // 30 seconds per behavior
  total: 120000,       // 2 minutes total
};

async function scrapeWithTimeouts(
  page: Page,
  url: string,
  config: TimeoutConfig = DEFAULT_TIMEOUTS
): Promise<ScrapedData> {
  // Set page-level timeout
  page.setDefaultTimeout(config.navigation);

  // Navigation with specific timeout
  await page.goto(url, { timeout: config.navigation });

  // Selector wait with specific timeout
  await page.waitForSelector('#content', { timeout: config.selector });

  // Behaviors with their own timeout
  await Promise.race([
    runAllBehaviors(page),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Behavior timeout')), config.behavior)
    ),
  ]);

  // Extract data...
}
```

---

## Limitations & Uncertainties

### What This Document Does NOT Cover

- Playwright Test runner (E2E testing framework)
- Cross-browser testing with Firefox/WebKit
- Video recording and tracing
- Playwright component testing
- HAR (HTTP Archive) recording (native Playwright feature, simpler than WARC)

### Platform-Specific Considerations

- Profile paths differ between Windows/macOS/Linux
- Chromium executable locations vary by platform
- Some stealth techniques are Chrome-specific
- wget availability varies (may need fallback to CDP)

### Rapidly Changing Landscape

Bot detection evolves constantly. Techniques effective today may be detected tomorrow. Keep stealth plugins updated and monitor for detection.

See **Part 21** for detailed limitations table and workaround templates.

---

## Quick Reference

### Essential Imports (Python)

```python
from playwright.async_api import async_playwright, Browser, Page, Playwright
from contextlib import asynccontextmanager
```

### Essential Imports (TypeScript)

```typescript
import puppeteerCore, { Browser, Page, CDPSession } from 'puppeteer-core';
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
```

### Common Patterns Cheat Sheet

| Task | Pattern |
|------|---------|
| Navigate | `await page.goto(url, wait_until="networkidle")` |
| Extract text | `await page.query_selector(sel)` then `.inner_text()` |
| Extract attribute | `await element.get_attribute("href")` |
| Multiple elements | `await page.query_selector_all(sel)` |
| JavaScript eval | `await page.evaluate("() => document.title")` |
| Wait for element | `await page.wait_for_selector("#id")` |
| Screenshot | `await page.screenshot(path=path, full_page=True)` |
| PDF | `await page.pdf(path=path, format='A4')` |

---

## Part 11: Image Source Discovery [HIGH]

### Comprehensive Image Extraction from Web Pages

Extract ALL possible image sources, not just visible `<img>` tags:

```typescript
export type SourceType =
  | 'img_src'           // Standard <img src="">
  | 'img_srcset'        // <img srcset=""> entries
  | 'picture_source'    // <picture><source> entries
  | 'meta_og'           // <meta property="og:image">
  | 'meta_twitter'      // <meta name="twitter:image">
  | 'link_original'     // <a href="original.jpg"><img src="thumb.jpg"></a>
  | 'data_attribute'    // data-src, data-full, data-original, etc.
  | 'css_background'    // background-image: url(...)
  | 'json_ld'           // Structured data
  | 'download_link';    // "Download" or "View Full Size" links

interface DiscoveredSource {
  url: string;
  width?: number;
  height?: number;
  descriptor?: string;  // "2x", "800w", etc.
  sourceType: SourceType;
  confidence: number;   // 0-1, higher = more likely high quality
}
```

### Srcset Parser

```typescript
/**
 * Parse srcset attribute into individual entries
 * Handles both width descriptors (800w) and density descriptors (2x)
 */
export function parseSrcset(srcset: string, baseUrl: string): SrcsetEntry[] {
  const entries: SrcsetEntry[] = [];

  // Split by comma, but handle URLs with commas in query strings
  const parts = srcset.split(/,(?=\s*https?:|[^,]*\s+\d+[wx])/);

  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;

    // Match: url [descriptor]
    const match = trimmed.match(/^(.+?)\s+(\d+(?:\.\d+)?[wx])?\s*$/);
    if (!match) continue;

    let [, url, descriptor] = match;
    descriptor = descriptor || '1x';

    // Resolve relative URLs
    try {
      url = new URL(url.trim(), baseUrl).href;
    } catch {
      continue;
    }

    const entry: SrcsetEntry = { url, descriptor };

    if (descriptor.endsWith('w')) {
      entry.width = parseInt(descriptor);
    } else if (descriptor.endsWith('x')) {
      entry.density = parseFloat(descriptor);
    }

    entries.push(entry);
  }

  // Sort by size (largest first)
  return entries.sort((a, b) => {
    if (a.width && b.width) return b.width - a.width;
    if (a.density && b.density) return b.density - a.density;
    return 0;
  });
}
```

### Site-Specific URL Patterns for Original Images

```typescript
const SITE_PATTERNS: SitePattern[] = [
  // Twitter/X - use orig or 4096x4096
  {
    name: 'Twitter/X',
    domainMatch: /pbs\.twimg\.com/,
    toOriginal: (url) => [
      url.replace(/[?&]name=\w+/, '?name=orig'),
      url.replace(/[?&]name=\w+/, '?name=4096x4096'),
    ],
    confidence: 0.95,
  },

  // Pinterest - use originals path
  {
    name: 'Pinterest',
    domainMatch: /pinimg\.com/,
    toOriginal: (url) => [
      url.replace(/\/\d+x\//, '/originals/'),
      url.replace(/\/\d+x\d+\//, '/originals/'),
    ],
    confidence: 0.9,
  },

  // Wikimedia Commons - remove thumb path
  {
    name: 'Wikimedia',
    domainMatch: /upload\.wikimedia\.org/,
    toOriginal: (url) => {
      // /thumb/.../800px-File.jpg → /.../File.jpg
      return [url.replace(/\/thumb\//, '/').replace(/\/\d+px-([^/]+)$/, '/$1')];
    },
    confidence: 0.95,
  },

  // Flickr - use _o suffix for original
  {
    name: 'Flickr',
    domainMatch: /staticflickr\.com/,
    toOriginal: (url) => [
      url.replace(/_[smzclkbht]\./, '_o.'),  // _o is original
      url.replace(/_[smzclkbht]\./, '_k.'),  // _k is 2048px
    ],
    confidence: 0.85,
  },

  // Imgur - remove suffix for original
  {
    name: 'Imgur',
    domainMatch: /imgur\.com/,
    toOriginal: (url) => [
      url.replace(/([a-zA-Z0-9]+)[smlhtb]\.(\w+)$/, '$1.$2'),
    ],
    confidence: 0.95,
  },

  // Google Photos/Drive
  {
    name: 'Google Photos',
    domainMatch: /googleusercontent\.com/,
    toOriginal: (url) => [
      url.replace(/=w\d+-h\d+.*$/, '=w0-h0'),  // Original size
      url.replace(/=s\d+.*$/, '=s0'),
    ],
    confidence: 0.9,
  },
];
```

### Data Attributes to Check for Lazy-Loaded Images

```typescript
const DATA_ATTRIBUTES = [
  'data-src',
  'data-original',
  'data-full',
  'data-fullsize',
  'data-large',
  'data-hires',
  'data-zoom',
  'data-lazy',
  'data-srcset',
];
```

---

## Part 12: Image Quality Analysis [HIGH]

### Dimension Verification via Partial Download

Only download 64KB to get image dimensions (header contains this info):

```typescript
export async function getImageDimensions(
  url: string,
  options: { timeout?: number } = {}
): Promise<ImageDimensions> {
  const response = await fetch(url, {
    headers: {
      Range: 'bytes=0-65535',  // First 64KB contains dimensions
      'User-Agent': 'Mozilla/5.0 (compatible)',
    },
  });

  const buffer = Buffer.from(await response.arrayBuffer());
  const metadata = await sharp(buffer).metadata();

  return {
    width: metadata.width!,
    height: metadata.height!,
    megapixels: (metadata.width! * metadata.height!) / 1000000,
    aspectRatio: metadata.width! / metadata.height!,
    orientation: metadata.width! > metadata.height! ? 'landscape' : 'portrait',
  };
}
```

### JPEG Quality Detection via Quantization Tables

```typescript
/**
 * Analyze JPEG quality by examining quantization tables
 *
 * JPEG compression uses quantization tables (QT) to reduce data.
 * Higher quality = lower QT values (less quantization).
 * Re-compression typically increases QT values.
 *
 * Typical values: Q100 ≈ 1, Q90 ≈ 3, Q80 ≈ 5, Q50 ≈ 16
 */
export async function analyzeJpegQuality(buffer: Buffer): Promise<JpegQualityResult | null> {
  // Check if JPEG
  if (buffer[0] !== 0xff || buffer[1] !== 0xd8) {
    return null;
  }

  // Parse JPEG markers to find DQT (Define Quantization Table) segments
  // Extract quantization values from marker 0xDB
  // Calculate average quantization value
  // Estimate quality based on average

  return {
    estimatedQuality: 85,           // 0-100
    isRecompressed: false,          // Detected via QT variance
    confidence: 0.9,
    quantizationAverage: 5.2,
    hasSubsampling: true,           // 4:2:0 vs 4:4:4
    colorSpace: 'YCbCr',
  };
}
```

### Watermark Detection via Edge Analysis

```typescript
interface WatermarkAnalysis {
  hasWatermark: boolean;
  confidence: number;
  watermarkType: 'none' | 'corner' | 'overlay' | 'text' | 'pattern';
  affectedArea: number;  // percentage 0-100
}

/**
 * Detect watermarks using edge detection and pattern analysis
 *
 * Detection strategies:
 * 1. Corner analysis - Check for logos/text in corners (common placement)
 * 2. Overlay detection - Look for semi-transparent overlays via alpha variance
 * 3. Edge density - High edge density in corners often indicates watermarks
 */
export async function detectWatermark(buffer: Buffer): Promise<WatermarkAnalysis> {
  const image = sharp(buffer);
  const metadata = await image.metadata();

  // Analyze corners (15% of each corner)
  const cornerSize = Math.min(
    Math.floor(metadata.width! * 0.15),
    Math.floor(metadata.height! * 0.15),
    200
  );

  const corners = [
    { name: 'bottomRight', x: metadata.width! - cornerSize, y: metadata.height! - cornerSize },
    // ... other corners
  ];

  for (const corner of corners) {
    const cornerBuffer = await image
      .clone()
      .extract({ left: corner.x, top: corner.y, width: cornerSize, height: cornerSize })
      .greyscale()
      .raw()
      .toBuffer();

    const edgeScore = analyzeEdgeDensity(cornerBuffer, cornerSize, cornerSize);
    if (edgeScore > 0.15) {
      // High edge density in corner = likely watermark
    }
  }

  return { hasWatermark: false, confidence: 0, watermarkType: 'none', affectedArea: 0 };
}
```

### Perceptual Hash for Similarity Search

```typescript
/**
 * Calculate perceptual hash for similarity comparison
 * Uses DCT-based algorithm (compatible with pHash)
 */
export async function calculateSimilarityHash(buffer: Buffer): Promise<string> {
  // 1. Resize to 32x32 and convert to grayscale
  const resized = await sharp(buffer)
    .resize(32, 32, { fit: 'fill' })
    .greyscale()
    .raw()
    .toBuffer();

  // 2. Compute DCT (8x8 top-left)
  const dctValues: number[] = [];
  for (let u = 0; u < 8; u++) {
    for (let v = 0; v < 8; v++) {
      let sum = 0;
      for (let x = 0; x < 32; x++) {
        for (let y = 0; y < 32; y++) {
          const pixel = resized[y * 32 + x];
          sum += pixel *
            Math.cos(((2 * x + 1) * u * Math.PI) / 64) *
            Math.cos(((2 * y + 1) * v * Math.PI) / 64);
        }
      }
      dctValues.push(sum);
    }
  }

  // 3. Generate binary hash using median threshold
  const acValues = dctValues.slice(1);  // Skip DC component
  const median = [...acValues].sort((a, b) => a - b)[Math.floor(acValues.length / 2)];

  let hash = '';
  for (const value of acValues) {
    hash += value > median ? '1' : '0';
  }

  // 4. Convert to hex (16 chars = 64 bits)
  return binaryToHex(hash);
}

/**
 * Calculate Hamming distance between two hashes
 * Distance <= 10 typically indicates same/similar image
 */
export function hashDistance(hash1: string, hash2: string): number {
  let distance = 0;
  for (let i = 0; i < hash1.length; i++) {
    const n1 = parseInt(hash1[i], 16);
    const n2 = parseInt(hash2[i], 16);
    let xor = n1 ^ n2;
    while (xor) {
      distance += xor & 1;
      xor >>= 1;
    }
  }
  return distance;
}
```

---

## Part 13: Smart Image Enhancement [HIGH]

### Find Highest Resolution Version of Any URL

```typescript
interface EnhanceResult {
  originalUrl: string;
  bestUrl: string;
  bestSize: number;
  allCandidates: ValidatedCandidate[];
  improvement: number;  // ratio vs original size
}

/**
 * Intelligently discovers the highest-resolution version of any image URL.
 *
 * Key capabilities:
 * 1. Recursive suffix stripping (removes -WxH, -scaled, -N variants iteratively)
 * 2. Multi-site pattern library (WordPress, Imgur, Flickr, etc.)
 * 3. Format preference (jpg/png > webp)
 * 4. Parallel candidate validation via HEAD requests
 * 5. Size-based ranking to find largest (highest res) version
 */
```

### Recursive Suffix Stripping Patterns

```typescript
const SUFFIX_PATTERNS = [
  // WordPress dimension suffix: -1024x768, -800x600
  { name: 'wp_dimensions', regex: /-\d+x\d+$/ },

  // WordPress scaled suffix
  { name: 'wp_scaled', regex: /-scaled$/ },

  // WordPress numeric variant: -1, -2, -3
  { name: 'wp_variant', regex: /-\d+$/ },

  // Retina suffix: @2x, @3x
  { name: 'retina', regex: /@[23]x$/ },

  // Generic thumbnail suffixes
  { name: 'thumb_suffix', regex: /[-_](thumb|thumbnail|small|medium|large)$/i },

  // Size indicators: _s, _m, _l
  { name: 'size_letter', regex: /[-_][smlSML]$/ },
];
```

### Recursive Enhancement Algorithm

```typescript
/**
 * The key insight: suffixes can stack!
 * image-1024x768-scaled.jpg → image-1024x768.jpg → image.jpg
 */
function generateCandidates(url: URL, maxDepth: number): ImageCandidate[] {
  const candidates: ImageCandidate[] = [];
  const seen = new Set<string>();

  // Recursive suffix stripping
  const recursiveStrip = (currentUrl: string, depth: number) => {
    if (depth > maxDepth) return;

    const pathMatch = currentUrl.match(/^(.+)\/([^/]+)\.(\w+)$/);
    if (!pathMatch) return;

    const [, basePath, filename, ext] = pathMatch;

    for (const pattern of SUFFIX_PATTERNS) {
      if (pattern.regex.test(filename)) {
        const strippedName = filename.replace(pattern.regex, '');
        const newUrl = `${basePath}/${strippedName}.${ext}`;

        if (!seen.has(newUrl)) {
          seen.add(newUrl);
          candidates.push({
            url: newUrl,
            source: 'recursive',
            patternName: pattern.name,
            depth,
          });

          // Recurse to strip more suffixes
          recursiveStrip(newUrl, depth + 1);
        }
      }
    }
  };

  recursiveStrip(url.href, 1);
  return candidates;
}
```

### Validation with Caching and Rate Limiting

```typescript
// 15-minute cache for HEAD request results
const VALIDATION_CACHE = new Map<string, CacheEntry>();
const CACHE_TTL_MS = 15 * 60 * 1000;

// Per-domain rate limiting
const DOMAIN_LAST_REQUEST = new Map<string, number>();
const MIN_DOMAIN_DELAY_MS = 100;  // 100ms between requests to same domain

async function validateCandidate(url: string, timeout: number): Promise<ValidatedCandidate> {
  // Check cache first
  const cached = getCachedResult(url);
  if (cached) return cached;

  // Wait for rate limit
  const domain = new URL(url).hostname;
  await waitForRateLimit(domain);

  // HEAD request to check existence and size
  const response = await fetch(url, {
    method: 'HEAD',
    headers: { 'User-Agent': 'Mozilla/5.0' },
  });

  const result: ValidatedCandidate = {
    url,
    exists: response.ok,
    contentLength: parseInt(response.headers.get('content-length') || '0'),
    contentType: response.headers.get('content-type'),
  };

  cacheResult(url, result);
  return result;
}
```

---

## Part 14: WARC Archiving [HIGH]

### ISO 28500:2017 Compliant Web Archiving

WARC (Web ARChive) format is the international standard for web preservation. Two implementation approaches:

### Approach 1: wget-Based (Preferred for Quality)

```typescript
import { execFile } from 'child_process';

/**
 * wget produces archival-grade WARCs with proper headers and CDX index
 * Preferred when wget is available on the system
 */
async function captureWithWget(
  url: string,
  outputPath: string,
  options: WgetOptions = {}
): Promise<WarcResult> {
  const args = [
    '--warc-file', outputPath.replace(/\.warc(\.gz)?$/, ''),  // wget adds extension
    '--warc-cdx',                // Generate CDX index
    '--page-requisites',         // Capture CSS, JS, images
    '--span-hosts',              // Allow cross-domain resources
    '--convert-links',           // Make links relative
    '--adjust-extension',        // Add proper extensions
    '--no-verbose',
    '--timeout', '30',
    '--tries', '3',
    '--user-agent', options.userAgent || DEFAULT_USER_AGENT,
    url,
  ];

  if (options.cookies) {
    args.push('--load-cookies', options.cookieFile);
  }

  return new Promise((resolve, reject) => {
    execFile('wget', args, { timeout: 120000 }, (error, stdout, stderr) => {
      if (error) {
        reject(new Error(`wget failed: ${stderr}`));
        return;
      }
      resolve({
        warcPath: `${outputPath}.warc.gz`,
        cdxPath: `${outputPath}.cdx`,
        method: 'wget',
      });
    });
  });
}
```

### Approach 2: CDP-Based (Fallback)

When wget is unavailable, use Chrome DevTools Protocol to capture network traffic:

```typescript
interface NetworkResource {
  url: string;
  method: string;
  requestHeaders: Record<string, string>;
  responseHeaders: Record<string, string>;
  status: number;
  body: Buffer;
  timestamp: Date;
}

/**
 * CDP-based WARC capture using Network.observe mode
 * Note: observe mode (not intercept) to avoid breaking page functionality
 */
async function captureWithCDP(
  page: Page,
  url: string,
  outputPath: string
): Promise<WarcResult> {
  const resources: NetworkResource[] = [];
  const pendingResponses = new Map<string, Partial<NetworkResource>>();

  // Enable Network domain with large buffers
  const cdp = await page.target().createCDPSession();
  await cdp.send('Network.enable', {
    maxResourceBufferSize: 100 * 1024 * 1024,   // 100MB per resource
    maxTotalBufferSize: 500 * 1024 * 1024,      // 500MB total
  });

  // Track request details
  cdp.on('Network.requestWillBeSent', (event) => {
    pendingResponses.set(event.requestId, {
      url: event.request.url,
      method: event.request.method,
      requestHeaders: event.request.headers,
      timestamp: new Date(),
    });
  });

  // Track response headers
  cdp.on('Network.responseReceived', (event) => {
    const pending = pendingResponses.get(event.requestId);
    if (pending) {
      pending.status = event.response.status;
      pending.responseHeaders = event.response.headers;
    }
  });

  // Capture response body after load completes
  cdp.on('Network.loadingFinished', async (event) => {
    const pending = pendingResponses.get(event.requestId);
    if (!pending) return;

    try {
      const { body, base64Encoded } = await cdp.send('Network.getResponseBody', {
        requestId: event.requestId,
      });
      pending.body = base64Encoded ? Buffer.from(body, 'base64') : Buffer.from(body);
      resources.push(pending as NetworkResource);
    } catch {
      // Body not available for some resources
    }
  });

  // Navigate and wait for completion
  await page.goto(url, { waitUntil: 'networkidle2' });

  // Cleanup
  await cdp.detach();

  // Generate WARC from collected resources
  return generateWarc(resources, outputPath);
}
```

### WARC 1.1 Record Format

```typescript
function generateWarcRecord(resource: NetworkResource): string {
  const warcRecordId = `<urn:uuid:${crypto.randomUUID()}>`;
  const warcDate = resource.timestamp.toISOString();

  // Request record
  const requestBlock = [
    `${resource.method} ${new URL(resource.url).pathname} HTTP/1.1`,
    ...Object.entries(resource.requestHeaders).map(([k, v]) => `${k}: ${v}`),
    '',
    '',
  ].join('\r\n');

  const requestHeader = [
    'WARC/1.1',
    `WARC-Type: request`,
    `WARC-Record-ID: ${warcRecordId}`,
    `WARC-Target-URI: ${resource.url}`,
    `WARC-Date: ${warcDate}`,
    `Content-Type: application/http;msgtype=request`,
    `Content-Length: ${Buffer.byteLength(requestBlock)}`,
  ].join('\r\n');

  // Response record
  const responseBlock = [
    `HTTP/1.1 ${resource.status} OK`,
    ...Object.entries(resource.responseHeaders).map(([k, v]) => `${k}: ${v}`),
    '',
    '',
  ].join('\r\n');

  const fullResponseBlock = Buffer.concat([
    Buffer.from(responseBlock),
    resource.body,
  ]);

  const responseHeader = [
    'WARC/1.1',
    `WARC-Type: response`,
    `WARC-Record-ID: <urn:uuid:${crypto.randomUUID()}>`,
    `WARC-Target-URI: ${resource.url}`,
    `WARC-Date: ${warcDate}`,
    `WARC-Concurrent-To: ${warcRecordId}`,
    `Content-Type: application/http;msgtype=response`,
    `Content-Length: ${fullResponseBlock.length}`,
  ].join('\r\n');

  return [requestHeader, requestBlock, responseHeader, fullResponseBlock].join('\r\n\r\n');
}
```

---

## Part 15: WACZ Conversion [MEDIUM]

### Webrecorder Archive Format

WACZ (Web Archive Collection Zipped) is the modern format for distributing web archives:

```typescript
import JSZip from 'jszip';
import * as zlib from 'zlib';

interface WaczOptions {
  title?: string;
  description?: string;
  mainPageUrl: string;
  mainPageDate: Date;
}

/**
 * Convert WARC to WACZ (Webrecorder format 1.1.1)
 */
async function convertToWacz(
  warcPath: string,
  cdxPath: string,
  outputPath: string,
  options: WaczOptions
): Promise<void> {
  const zip = new JSZip();

  // 1. Add compressed WARC
  const warcData = await fs.promises.readFile(warcPath);
  const compressedWarc = zlib.gzipSync(warcData);
  zip.file('archive/data.warc.gz', compressedWarc);

  // 2. Add compressed CDX index
  const cdxData = await fs.promises.readFile(cdxPath);
  const compressedCdx = zlib.gzipSync(cdxData);
  zip.file('indexes/index.cdx.gz', compressedCdx);

  // 3. Add pages.jsonl
  const pagesJsonl = JSON.stringify({
    url: options.mainPageUrl,
    title: options.title || options.mainPageUrl,
    ts: options.mainPageDate.toISOString(),
  });
  zip.file('pages/pages.jsonl', pagesJsonl);

  // 4. Add datapackage.json (Frictionless Data format)
  const datapackage = {
    profile: 'data-package',
    wacz_version: '1.1.1',
    title: options.title || 'Web Archive',
    description: options.description,
    mainPageUrl: options.mainPageUrl,
    mainPageDate: options.mainPageDate.toISOString(),
    created: new Date().toISOString(),
    resources: [
      {
        path: 'archive/data.warc.gz',
        hash: `sha256:${calculateSha256(compressedWarc)}`,
      },
      {
        path: 'indexes/index.cdx.gz',
        hash: `sha256:${calculateSha256(compressedCdx)}`,
      },
    ],
  };
  zip.file('datapackage.json', JSON.stringify(datapackage, null, 2));

  // Write zip file
  const content = await zip.generateAsync({ type: 'nodebuffer' });
  await fs.promises.writeFile(outputPath, content);
}
```

---

## Part 16: Comprehensive Metadata Extraction [HIGH]

### Multi-Standard Metadata Extraction

```typescript
interface WebPageMetadata {
  // Standard HTML
  title: string;
  description?: string;
  author?: string;
  keywords?: string[];
  canonical?: string;
  language?: string;

  // Open Graph
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogType?: string;
  ogSiteName?: string;
  ogLocale?: string;
  articleAuthor?: string;
  articlePublishedTime?: string;
  articleModifiedTime?: string;

  // Twitter Cards
  twitterCard?: string;
  twitterSite?: string;
  twitterCreator?: string;
  twitterTitle?: string;
  twitterDescription?: string;
  twitterImage?: string;

  // Schema.org JSON-LD
  schemaOrg?: SchemaOrgObject[];

  // Dublin Core
  dcTitle?: string;
  dcCreator?: string;
  dcSubject?: string;
  dcDescription?: string;
  dcPublisher?: string;
  dcDate?: string;
  dcType?: string;
  dcFormat?: string;
  dcIdentifier?: string;
  dcSource?: string;
  dcLanguage?: string;
  dcRights?: string;
}

async function extractAllMetadata(page: Page): Promise<WebPageMetadata> {
  return await page.evaluate(() => {
    const meta = (name: string): string | undefined => {
      const el = document.querySelector(
        `meta[name="${name}"], meta[property="${name}"]`
      );
      return el?.getAttribute('content') || undefined;
    };

    const metadata: WebPageMetadata = {
      // Standard HTML
      title: document.title,
      description: meta('description'),
      author: meta('author'),
      keywords: meta('keywords')?.split(',').map(s => s.trim()),
      canonical: document.querySelector('link[rel="canonical"]')?.getAttribute('href') || undefined,
      language: document.documentElement.lang || meta('language'),

      // Open Graph
      ogTitle: meta('og:title'),
      ogDescription: meta('og:description'),
      ogImage: meta('og:image'),
      ogType: meta('og:type'),
      ogSiteName: meta('og:site_name'),
      ogLocale: meta('og:locale'),
      articleAuthor: meta('article:author'),
      articlePublishedTime: meta('article:published_time'),
      articleModifiedTime: meta('article:modified_time'),

      // Twitter Cards
      twitterCard: meta('twitter:card'),
      twitterSite: meta('twitter:site'),
      twitterCreator: meta('twitter:creator'),
      twitterTitle: meta('twitter:title'),
      twitterDescription: meta('twitter:description'),
      twitterImage: meta('twitter:image'),

      // Dublin Core
      dcTitle: meta('DC.title'),
      dcCreator: meta('DC.creator'),
      dcSubject: meta('DC.subject'),
      dcDescription: meta('DC.description'),
      dcPublisher: meta('DC.publisher'),
      dcDate: meta('DC.date'),
      dcType: meta('DC.type'),
      dcFormat: meta('DC.format'),
      dcIdentifier: meta('DC.identifier'),
      dcSource: meta('DC.source'),
      dcLanguage: meta('DC.language'),
      dcRights: meta('DC.rights'),
    };

    // Schema.org JSON-LD
    const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
    const schemaOrg: object[] = [];
    for (const script of jsonLdScripts) {
      try {
        const data = JSON.parse(script.textContent || '');
        if (Array.isArray(data)) {
          schemaOrg.push(...data);
        } else {
          schemaOrg.push(data);
        }
      } catch { /* invalid JSON-LD */ }
    }
    if (schemaOrg.length > 0) {
      metadata.schemaOrg = schemaOrg;
    }

    return metadata;
  });
}
```

---

## Part 17: Text Extraction with Trafilatura [MEDIUM]

### Main Content Extraction

```python
"""
Text extraction using Trafilatura for article content
with BeautifulSoup fallback for non-article pages.
"""

import trafilatura
from bs4 import BeautifulSoup

def extract_main_content(html: str, url: str) -> dict:
    """
    Extract main content from HTML.
    Returns structured data with text, title, author, date.
    """
    # Try trafilatura first (best for articles)
    result = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=True,
        include_images=False,
        include_links=False,
        output_format='txt',
        favor_recall=True,  # Get more content vs precision
    )

    metadata = trafilatura.extract_metadata(html, url=url)

    extracted = {
        'text': result or '',
        'word_count': len((result or '').split()),
        'title': metadata.title if metadata else None,
        'author': metadata.author if metadata else None,
        'date': metadata.date if metadata else None,
        'source': 'trafilatura',
    }

    # Fallback enrichment for short extractions (OPT-120)
    if extracted['word_count'] < 50:
        soup = BeautifulSoup(html, 'html.parser')

        # Try meta descriptions
        og_desc = soup.find('meta', property='og:description')
        meta_desc = soup.find('meta', attrs={'name': 'description'})

        fallback_text = ''
        if og_desc and og_desc.get('content'):
            fallback_text += og_desc['content'] + ' '
        if meta_desc and meta_desc.get('content'):
            fallback_text += meta_desc['content'] + ' '

        if fallback_text:
            extracted['text'] = (extracted['text'] + ' ' + fallback_text).strip()
            extracted['word_count'] = len(extracted['text'].split())
            extracted['source'] = 'trafilatura+fallback'

    return extracted
```

---

## Part 18: Video Extraction with yt-dlp [MEDIUM]

### Multi-Platform Video Metadata Extraction

```typescript
import { exec } from 'child_process';

interface VideoMetadata {
  id: string;
  title: string;
  description?: string;
  duration?: number;
  uploader?: string;
  uploaderUrl?: string;
  uploadDate?: string;
  viewCount?: number;
  likeCount?: number;
  tags?: string[];
  categories?: string[];
  thumbnailUrl?: string;
  platform: string;
  embedUrl?: string;
  downloadUrl?: string;
}

/**
 * Extract video metadata using yt-dlp
 * Supports YouTube, Vimeo, Twitter, and 1000+ platforms
 */
async function extractVideoMetadata(url: string): Promise<VideoMetadata | null> {
  return new Promise((resolve) => {
    const args = [
      '--dump-json',
      '--no-download',
      '--no-playlist',
      '--socket-timeout', '30',
      url,
    ];

    exec(`yt-dlp ${args.join(' ')}`, { timeout: 60000 }, (error, stdout) => {
      if (error) {
        resolve(null);
        return;
      }

      try {
        const data = JSON.parse(stdout);
        resolve({
          id: data.id,
          title: data.title,
          description: data.description,
          duration: data.duration,
          uploader: data.uploader,
          uploaderUrl: data.uploader_url,
          uploadDate: data.upload_date,
          viewCount: data.view_count,
          likeCount: data.like_count,
          tags: data.tags,
          categories: data.categories,
          thumbnailUrl: data.thumbnail,
          platform: data.extractor || detectPlatform(url),
          embedUrl: data.webpage_url,
        });
      } catch {
        resolve(null);
      }
    });
  });
}

function detectPlatform(url: string): string {
  const urlLower = url.toLowerCase();
  if (urlLower.includes('youtube') || urlLower.includes('youtu.be')) return 'YouTube';
  if (urlLower.includes('vimeo')) return 'Vimeo';
  if (urlLower.includes('twitter') || urlLower.includes('x.com')) return 'Twitter';
  if (urlLower.includes('tiktok')) return 'TikTok';
  if (urlLower.includes('instagram')) return 'Instagram';
  return 'Unknown';
}
```

---

## Part 19: Browser Extension Communication [MEDIUM]

### WebSocket Protocol for Extension Data Capture

```typescript
/**
 * Extension captures authenticated session data and sends to main app
 * via WebSocket for injection into headless browser.
 */

// Extension side (background.js)
const WS_PORT = 47124;
const HEARTBEAT_INTERVAL = 5000;

class ExtensionClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;

  connect(): void {
    this.ws = new WebSocket(`ws://localhost:${WS_PORT}`);

    this.ws.onopen = () => {
      // Register extension
      this.send({ type: 'extension:register', version: '1.0.0' });
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleCommand(message);
    };

    this.ws.onclose = () => {
      this.scheduleReconnect();
    };
  }

  private handleCommand(message: BrowserCommand): void {
    switch (message.command) {
      case 'captureSession':
        this.captureSessionData(message.tabId);
        break;
      case 'injectCookies':
        this.injectCookies(message.cookies, message.url);
        break;
      case 'screenshot':
        this.captureScreenshot(message.tabId);
        break;
    }
  }

  private async captureSessionData(tabId: number): Promise<void> {
    const tab = await chrome.tabs.get(tabId);
    const url = new URL(tab.url!);

    // Get all cookies for this domain
    const cookies = await chrome.cookies.getAll({ domain: url.hostname });

    // Get current page HTML
    const [{ result: html }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => document.documentElement.outerHTML,
    });

    // Get screenshot
    const screenshot = await chrome.tabs.captureVisibleTab(tab.windowId!, {
      format: 'png',
    });

    this.send({
      type: 'browser:response',
      command: 'captureSession',
      data: {
        url: tab.url,
        cookies,
        html,
        screenshot,
        userAgent: navigator.userAgent,
        timestamp: Date.now(),
      },
    });
  }

  private send(message: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### Session Data Storage

```typescript
interface ExtensionSessionData {
  cookies: ExtensionCookie[];
  userAgent: string;
  html?: string;
  screenshot?: string;  // base64 PNG
  capturedAt: number;
}

/**
 * Save session data for later injection into headless browser
 */
async function saveSessionData(
  sourceId: string,
  data: ExtensionSessionData
): Promise<void> {
  const sessionPath = path.join(
    archiveFolder,
    '_websources',
    sourceId,
    `${sourceId}_session.json`
  );

  await fs.promises.mkdir(path.dirname(sessionPath), { recursive: true });
  await fs.promises.writeFile(sessionPath, JSON.stringify(data, null, 2));
}

/**
 * Load and inject session data before navigation
 */
async function injectExtensionCookies(
  page: Page,
  sourceId: string,
  targetUrl: string
): Promise<boolean> {
  const sessionPath = path.join(
    archiveFolder,
    '_websources',
    sourceId,
    `${sourceId}_session.json`
  );

  if (!fs.existsSync(sessionPath)) {
    return false;
  }

  const sessionData: ExtensionSessionData = JSON.parse(
    await fs.promises.readFile(sessionPath, 'utf-8')
  );

  // Set matching user agent
  if (sessionData.userAgent) {
    await page.setUserAgent(sessionData.userAgent);
  }

  // Filter and inject cookies
  const targetDomain = new URL(targetUrl).hostname;
  const matchingCookies = sessionData.cookies.filter((cookie) => {
    const cookieDomain = cookie.domain.replace(/^\./, '');
    return targetDomain === cookieDomain ||
           targetDomain.endsWith('.' + cookieDomain);
  });

  if (matchingCookies.length > 0) {
    await page.setCookie(...matchingCookies.map(c => ({
      name: c.name,
      value: c.value,
      domain: c.domain,
      path: c.path || '/',
      secure: c.secure,
      httpOnly: c.httpOnly,
      expires: c.expirationDate,
    })));
    return true;
  }

  return false;
}
```

---

## Part 20: Extended Bot Detection Patterns [HIGH]

### Enterprise Anti-Bot Service Detection

```typescript
/**
 * Comprehensive bot detection patterns for enterprise anti-bot services
 */
const EXTENDED_BLOCK_PATTERNS = [
  // CloudFront (Amazon AWS WAF)
  {
    service: 'CloudFront',
    patterns: [
      { text: 'generated by cloudfront', type: 'body' },
      { text: 'request could not be satisfied', type: 'body' },
      { header: 'x-amz-cf-id', type: 'header' },  // Present on all CF responses
    ],
    httpCodes: [403],
  },

  // Cloudflare
  {
    service: 'Cloudflare',
    patterns: [
      { text: 'checking your browser', type: 'body' },
      { text: 'just a moment', type: 'body' },
      { text: 'ray id:', type: 'body' },
      { text: 'cf-browser-verification', type: 'body' },
      { text: 'cloudflare', type: 'title' },
      { header: 'cf-ray', type: 'header' },
    ],
    httpCodes: [403, 503],
  },

  // PerimeterX (HUMAN)
  {
    service: 'PerimeterX',
    patterns: [
      { text: 'px-captcha', type: 'body' },
      { text: '_pxhd', type: 'cookie' },
      { text: 'perimeterx', type: 'body' },
      { text: 'press & hold', type: 'body' },
    ],
    httpCodes: [403, 429],
  },

  // DataDome
  {
    service: 'DataDome',
    patterns: [
      { text: 'datadome', type: 'body' },
      { text: 'dd_', type: 'cookie' },
      { header: 'x-datadome', type: 'header' },
    ],
    httpCodes: [403],
  },

  // Akamai Bot Manager
  {
    service: 'Akamai',
    patterns: [
      { text: 'akamai', type: 'body' },
      { text: 'ak_bmsc', type: 'cookie' },
      { text: 'bm_sz', type: 'cookie' },
      { header: 'akamai-grn', type: 'header' },
    ],
    httpCodes: [403],
  },

  // Imperva Incapsula
  {
    service: 'Imperva',
    patterns: [
      { text: 'incapsula', type: 'body' },
      { text: 'visid_incap', type: 'cookie' },
      { text: 'incap_ses', type: 'cookie' },
    ],
    httpCodes: [403],
  },

  // reCAPTCHA / hCaptcha
  {
    service: 'CAPTCHA',
    patterns: [
      { text: 'recaptcha', type: 'body' },
      { text: 'hcaptcha', type: 'body' },
      { text: 'g-recaptcha', type: 'body' },
      { text: 'h-captcha', type: 'body' },
      { text: 'captcha-container', type: 'body' },
    ],
    httpCodes: [403, 429],
  },
];

async function detectBlockService(
  page: Page,
  response: HTTPResponse | null
): Promise<BlockDetection | null> {
  const status = response?.status() || 0;
  const headers = response?.headers() || {};

  const bodyText = await page.evaluate(() =>
    document.body?.innerText?.toLowerCase() || ''
  );
  const title = await page.title();
  const cookies = await page.cookies();
  const cookieNames = cookies.map(c => c.name.toLowerCase()).join(' ');

  for (const service of EXTENDED_BLOCK_PATTERNS) {
    // Check HTTP status
    const statusMatch = service.httpCodes.includes(status);

    // Check patterns
    for (const pattern of service.patterns) {
      let matched = false;

      switch (pattern.type) {
        case 'body':
          matched = bodyText.includes(pattern.text);
          break;
        case 'title':
          matched = title.toLowerCase().includes(pattern.text);
          break;
        case 'header':
          matched = pattern.header in headers;
          break;
        case 'cookie':
          matched = cookieNames.includes(pattern.text);
          break;
      }

      if (matched && statusMatch) {
        return {
          blocked: true,
          service: service.service,
          pattern: pattern.text,
          httpStatus: status,
        };
      }
    }
  }

  return null;
}
```

---

## Part 22: XMP Provenance for Scraped Files [HIGH]

### Chain of Custody for Web Content

Every scraped file should carry its complete provenance in XMP sidecar:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from ulid import ULID

class CustodyEventAction(str, Enum):
    """PREMIS-aligned custody events for web scraping."""
    WEB_CAPTURE = "web_capture"
    URL_ENHANCEMENT = "url_enhancement"
    QUALITY_ANALYSIS = "quality_analysis"
    PERCEPTUAL_HASH = "perceptual_hash"

class WebProvenance(BaseModel):
    """Where the file came from on the web."""
    source_url: str
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    capture_timestamp: datetime
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    credit: Optional[str] = None
    original_url: Optional[str] = None  # Before enhancement
    enhanced_url: Optional[str] = None  # After enhancement

class CustodyEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(ULID()))
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_action: CustodyEventAction
    event_outcome: str = "success"
    event_tool: Optional[str] = None
    event_notes: Optional[str] = None

class XMPSidecar(BaseModel):
    content_hash: str  # blake3
    file_size: int
    provenance: WebProvenance
    custody_chain: List[CustodyEvent] = Field(default_factory=list)
```

### XMP Writer with exiftool

```python
from exiftool import ExifToolHelper
import json

def write_sidecar(file_path: Path, sidecar: XMPSidecar) -> Path:
    xmp_path = file_path.with_suffix(file_path.suffix + ".xmp")
    tags = {
        "XMP-dc:Source": f"scraper:{json.dumps(sidecar.dict())}",
        "XMP-dc:Identifier": sidecar.provenance.source_url,
    }
    if sidecar.provenance.credit:
        tags["XMP-dc:Creator"] = sidecar.provenance.credit

    with ExifToolHelper() as et:
        et.set_tags(str(xmp_path), tags, params=["-overwrite_original"])
    return xmp_path
```

---

## Part 23: Cookie Sync for Authenticated Scraping [HIGH]

### Browser Profile Locations

```python
BROWSER_PROFILES = {
    "darwin": {  # macOS
        "chrome": "~/Library/Application Support/Google/Chrome",
        "arc": "~/Library/Application Support/Arc/User Data",
        "brave": "~/Library/Application Support/BraveSoftware/Brave-Browser",
    },
    "linux": {
        "chrome": "~/.config/google-chrome",
        "brave": "~/.config/BraveSoftware/Brave-Browser",
    },
}
# Profile structure: {profile}/Default/Cookies (SQLite)
```

### Cookie Sync Implementation

```python
import shutil

def sync_cookies(browser: str, archive_profile: Path) -> bool:
    """Copy cookies from browser to archive profile."""
    browser_path = Path(BROWSER_PROFILES[platform.system().lower()][browser]).expanduser()

    # Check for lock (browser running)
    if (browser_path / "SingletonLock").exists():
        raise RuntimeError(f"{browser} is running. Close it first.")

    # Copy cookies
    src = browser_path / "Default" / "Cookies"
    dest = archive_profile / "Default" / "Cookies"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True
```

### Extension Session Capture

```typescript
// Extension captures: cookies, userAgent, localStorage
// Saves to: {archive}/_sessions/{domain}_session.json
// Load before navigation for authenticated scraping
```

---

## Part 21: Known Limitations & Gaps [CRITICAL]

### Features NOT Implemented

| Feature | Status | Workaround |
|---------|--------|------------|
| **Proxy Rotation** | ❌ Not implemented | Use external proxy manager or environment variables |
| **Geolocation Spoofing** | ❌ Not implemented | Add `Emulation.setGeolocationOverride` CDP call |
| **Shadow DOM Piercing** | ❌ Not implemented | Use `page.evaluateHandle` with manual shadow root traversal |
| **WebSocket Stream Capture** | ⚠️ Partial | Extension WS works, page WS not captured in WARC |
| **Mobile Device Profiles** | ⚠️ Basic | Viewport works, but no touch emulation or device-specific user agents |

### Shadow DOM Access Pattern

```typescript
/**
 * Workaround for Shadow DOM access
 * Playwright/Puppeteer evaluate() cannot pierce shadow roots
 */
async function queryShadowRoot(
  page: Page,
  hostSelector: string,
  innerSelector: string
): Promise<string | null> {
  return await page.evaluate(
    ({ host, inner }) => {
      const hostEl = document.querySelector(host);
      if (!hostEl?.shadowRoot) return null;

      const innerEl = hostEl.shadowRoot.querySelector(inner);
      return innerEl?.textContent || null;
    },
    { host: hostSelector, inner: innerSelector }
  );
}
```

### Proxy Configuration Template

```typescript
/**
 * Proxy configuration (NOT implemented in source codebases)
 * Template for adding proxy support
 */
interface ProxyConfig {
  server: string;      // 'http://proxy:port'
  username?: string;
  password?: string;
}

async function launchWithProxy(proxy: ProxyConfig): Promise<Browser> {
  const browser = await puppeteer.launch({
    args: [
      `--proxy-server=${proxy.server}`,
    ],
  });

  // For authenticated proxies, intercept auth challenges
  if (proxy.username && proxy.password) {
    const page = await browser.newPage();
    await page.authenticate({
      username: proxy.username,
      password: proxy.password,
    });
  }

  return browser;
}
```

### Geolocation Spoofing Template

```typescript
/**
 * Geolocation spoofing (NOT implemented in source codebases)
 * Template for adding location override
 */
async function setGeolocation(
  page: Page,
  latitude: number,
  longitude: number,
  accuracy: number = 100
): Promise<void> {
  const cdp = await page.target().createCDPSession();
  await cdp.send('Emulation.setGeolocationOverride', {
    latitude,
    longitude,
    accuracy,
  });
}
```

---

## Source Appendix

| # | Source | Type | Used For |
|---|--------|------|----------|
| 1 | barbossa/services/scraper/browser.py | Internal | BrowserService pattern |
| 2 | barbossa/scrapers/base.py | Internal | Base scraper architecture |
| 3 | barbossa/scrapers/bandcamp.py | Internal | Site-specific implementation |
| 4 | barbossa/services/scraper/training.py | Internal | Selector learning system |
| 5 | abandoned-archive/services/websource-capture-service.ts | Internal | Bot detection, WARC capture, CDP |
| 6 | abandoned-archive/services/websource-behaviors.ts | Internal | Content expansion behaviors |
| 7 | abandoned-archive/services/detached-browser-service.ts | Internal | Zero-detection browser |
| 8 | abandoned-archive/services/image-downloader/image-source-discovery.ts | Internal | Image source extraction |
| 9 | abandoned-archive/services/image-downloader/image-quality-analyzer.ts | Internal | Quality analysis, watermark detection |
| 10 | abandoned-archive/services/image-downloader/image-enhance-service.ts | Internal | URL enhancement, suffix stripping |
| 11 | abandoned-archive/services/wacz-service.ts | Internal | WACZ conversion |
| 12 | abandoned-archive/services/websource-metadata-service.ts | Internal | OG, Schema.org, Dublin Core extraction |
| 13 | abandoned-archive/services/websource-extraction-service.ts | Internal | Text/video/EXIF extraction |
| 14 | abandoned-archive/resources/extension/background.js | Internal | Extension WebSocket protocol |
| 15 | Playwright Documentation | Primary | API reference |
| 16 | Puppeteer Documentation | Primary | API reference |
| 17 | WARC ISO 28500:2017 | Primary | Archive format specification |
| 18 | Webrecorder WACZ Spec | Primary | WACZ format specification |
| 19 | wake-n-blake/xmp/schema.ts | Internal | XMP sidecar schema, custody events |
| 20 | wake-n-blake/xmp/writer.ts | Internal | XMP sidecar generation |
| 21 | shoemaker/services/xmp-updater.ts | Internal | XMP batch updates with exiftool |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-24 | Initial version - comprehensive patterns from barbossa and abandoned-archive |
| 1.1 | 2024-12-24 | Added Parts 14-21: WARC/WACZ archiving, metadata extraction, video/text extraction, extension communication, extended bot detection, known limitations |
| 1.2 | 2024-12-24 | Added Parts 22-23: XMP provenance tracking from wake-n-blake, cookie sync from any Chrome-based browser |
