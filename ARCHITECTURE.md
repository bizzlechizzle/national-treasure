# National Treasure - Architecture Plan

> **The Ultimate Browser Automation & Web Intelligence CLI**
> Combining the best of abandoned-archive + barbossa + ML-powered learning

---

## Executive Summary

National Treasure is a CLI tool that takes Playwright/Puppeteer browser automation to the next level by:

1. **Stealing all excellent patterns** from abandoned-archive (web archiving, image processing) and barbossa (scraping, training)
2. **Adding a machine learning feedback loop** that learns what works per domain
3. **Becoming a stand-in replacement** for both codebases' browser automation needs

---

## Part 1: Feature Inventory - What We're Stealing

### From abandoned-archive (38,000 LOC)

| Module | Priority | Files to Steal | Purpose |
|--------|----------|----------------|---------|
| **Web Capture** | P0 | websource-capture-service.ts | Screenshot, PDF, HTML, WARC capture |
| **Page Behaviors** | P0 | websource-behaviors.ts | Browsertrix-level content expansion |
| **Bot Detection Bypass** | P0 | (spread across capture service) | Stealth plugin, shell headless, anti-automation flags |
| **Response Validation** | P0 | (in capture service) | 403/CAPTCHA/CloudFront detection |
| **Image Source Discovery** | P1 | image-source-discovery.ts | srcset, meta, data-*, JSON-LD extraction |
| **Image Quality Analyzer** | P1 | image-quality-analyzer.ts | JPEG quantization, watermark detection, pHash |
| **Image Enhancement** | P1 | image-enhance-service.ts | Recursive suffix stripping, URL transformation |
| **URL Pattern Transformer** | P1 | url-pattern-transformer.ts | 30+ site patterns (Twitter, Flickr, Imgur, etc.) |
| **Perceptual Hashing** | P2 | perceptual-hash-service.ts | Duplicate detection, similarity search |
| **Job Queue** | P2 | job-queue.ts | SQLite-backed with dependencies |
| **Rate Limiting** | P2 | (in enhance service) | Per-domain rate limiting with caching |

### From barbossa (8,000 LOC)

| Module | Priority | Files to Steal | Purpose |
|--------|----------|----------------|---------|
| **Browser Service** | P0 | browser.py | Async context manager for Playwright |
| **Base Scraper** | P0 | base.py | Plugin architecture for site scrapers |
| **Training Service** | P0 | training.py | Selector confidence tracking |
| **Site Scrapers** | P1 | bandcamp.py | Site-specific extraction patterns |
| **Track Matcher** | P2 | matcher.py | Fuzzy matching with confidence |
| **Scraper Models** | P0 | scraper_models.py | Pydantic models for structured data |
| **RPC Server** | P2 | rpc.py | JSON-RPC 2.0 WebSocket interface |

---

## Part 1B: Cookie Sync & Browser Profile Management

### The Problem

Authenticated scraping requires cookies from a real browser session. Options:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COOKIE SYNC ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────┐                    ┌──────────────────────┐      │
│   │  Research       │   sync cookies     │  Headless Archive    │      │
│   │  Browser        │ ─────────────────▶ │  Browser (CDP)       │      │
│   │  (User Visible) │                    │                      │      │
│   │                 │                    │  userDataDir:        │      │
│   │  ~/.../Default/ │                    │  ~/.../archive-      │      │
│   │  Cookies        │                    │  browser-profile/    │      │
│   └─────────────────┘                    └──────────────────────┘      │
│          │                                                             │
│          │  Extension captures                                         │
│          │  authenticated session                                      │
│          ▼                                                             │
│   ┌─────────────────┐                                                  │
│   │  Session Store  │  JSON with cookies, userAgent, localStorage      │
│   │  {sourceId}_    │                                                  │
│   │  session.json   │                                                  │
│   └─────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Cookie Source Options

| Source | Pros | Cons | Implementation |
|--------|------|------|----------------|
| **Bundled Browser** (Ungoogled Chromium) | Zero detection, clean profile | 200MB binary, maintenance | `spawn()` with `--user-data-dir` |
| **User's Browser** (Chrome, Arc, Brave, etc.) | No extra install, real sessions | Profile lock conflicts | Copy `Cookies` file when browser closed |
| **Extension Capture** | Works with any browser, per-URL auth | Requires extension install | WebSocket server + `page.setCookie()` |
| **CDP Connect** | Real-time, same fingerprint | Requires `--remote-debugging-port` | `puppeteer.connect()` |

### Browser Profile Locations

```typescript
const CHROME_PROFILES = {
  // macOS
  'chrome-mac': '~/Library/Application Support/Google/Chrome',
  'brave-mac': '~/Library/Application Support/BraveSoftware/Brave-Browser',
  'arc-mac': '~/Library/Application Support/Arc/User Data',
  'edge-mac': '~/Library/Application Support/Microsoft Edge',
  'vivaldi-mac': '~/Library/Application Support/Vivaldi',

  // Linux
  'chrome-linux': '~/.config/google-chrome',
  'brave-linux': '~/.config/BraveSoftware/Brave-Browser',
  'chromium-linux': '~/.config/chromium',

  // Windows
  'chrome-win': '%LOCALAPPDATA%/Google/Chrome/User Data',
  'brave-win': '%LOCALAPPDATA%/BraveSoftware/Brave-Browser/User Data',
  'edge-win': '%LOCALAPPDATA%/Microsoft/Edge/User Data',
};

// Profile structure (all Chrome-based browsers):
// {profileDir}/Default/Cookies        (SQLite)
// {profileDir}/Default/Cookies-journal (WAL)
// {profileDir}/Profile 1/Cookies      (additional profiles)
```

### Cookie Sync Implementation

```python
from pathlib import Path
import shutil
import sqlite3

class CookieSync:
    """Sync cookies between browser profiles."""

    def __init__(self, archive_profile: Path):
        self.archive_profile = archive_profile
        self.archive_profile.mkdir(parents=True, exist_ok=True)

    def sync_from_browser(self, browser_name: str, profile: str = "Default") -> bool:
        """Copy cookies from a browser profile."""
        profile_path = self._get_browser_profile(browser_name)
        if not profile_path:
            return False

        source_cookies = profile_path / profile / "Cookies"
        if not source_cookies.exists():
            return False

        # Check for lock (browser running)
        lock_file = profile_path / "SingletonLock"
        if lock_file.exists():
            raise RuntimeError(f"{browser_name} is running. Close it or use extension capture.")

        # Copy cookies and journal
        dest_dir = self.archive_profile / "Default"
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file in ["Cookies", "Cookies-journal"]:
            src = profile_path / profile / file
            if src.exists():
                shutil.copy2(src, dest_dir / file)

        return True

    def inject_extension_session(self, page, session_data: dict) -> None:
        """Inject cookies captured by extension."""
        if session_data.get("userAgent"):
            page.set_user_agent(session_data["userAgent"])

        for cookie in session_data.get("cookies", []):
            page.context.add_cookies([{
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie.get("path", "/"),
                "secure": cookie.get("secure", False),
                "httpOnly": cookie.get("httpOnly", False),
                "expires": cookie.get("expirationDate", -1),
            }])
```

### Extension Session Capture Protocol

```typescript
// Extension captures authenticated session via WebSocket
interface SessionCapture {
  url: string;
  cookies: chrome.cookies.Cookie[];
  userAgent: string;
  localStorage?: Record<string, string>;
  sessionStorage?: Record<string, string>;
  html?: string;
  screenshot?: string;  // base64 PNG
  capturedAt: number;
}

// WebSocket server (national-treasure)
// Listen on localhost:47124
// Extension sends: { type: 'session:capture', data: SessionCapture }
// Server saves to: {archiveFolder}/_websources/{sourceId}_session.json
```

### Recommended Configuration

```yaml
# ~/.config/national-treasure/config.yaml
cookie_sources:
  # Priority order - first available wins
  - type: extension
    port: 47124
  - type: browser
    name: arc        # or chrome, brave, edge
    profile: Default
  - type: browser
    name: chrome
    profile: Default

  fallback: anonymous  # or 'fail'

# Per-domain overrides
domain_cookies:
  twitter.com:
    source: extension  # Always use fresh session
  reddit.com:
    source: browser
    name: chrome
```

---

## Part 1C: XMP Chain of Command (Provenance Tracking)

### Why Provenance Matters

Every scraped image/file should carry its full history:
- **Where** did it come from? (source URL, page context)
- **When** was it captured? (timestamps)
- **How** was it processed? (enhancement, quality analysis)
- **What** changes occurred? (custody chain)

### XMP Namespace Design (from wake-n-blake)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:xmp="http://ns.adobe.com/xap/1.0/"
           xmlns:nt="http://national-treasure.dev/xmp/1.0/">

    <rdf:Description rdf:about="">
      <!-- Core Identity -->
      <nt:ContentHash>blake3:abc123...</nt:ContentHash>
      <nt:HashAlgorithm>blake3</nt:HashAlgorithm>
      <nt:FileSize>1234567</nt:FileSize>

      <!-- Web Provenance -->
      <nt:SourceURL>https://example.com/image.jpg</nt:SourceURL>
      <nt:PageURL>https://example.com/gallery</nt:PageURL>
      <nt:PageTitle>Image Gallery</nt:PageTitle>
      <nt:CaptureTimestamp>2024-12-24T12:00:00Z</nt:CaptureTimestamp>
      <nt:CaptureMethod>playwright</nt:CaptureMethod>

      <!-- Image Context (from page) -->
      <nt:AltText>A beautiful sunset</nt:AltText>
      <nt:Caption>Sunset over the mountains</nt:Caption>
      <nt:Credit>Photo by John Doe</nt:Credit>
      <nt:LinkURL>https://example.com/photographer</nt:LinkURL>

      <!-- Enhancement Info -->
      <nt:OriginalURL>https://example.com/image-800x600.jpg</nt:OriginalURL>
      <nt:EnhancedURL>https://example.com/image.jpg</nt:EnhancedURL>
      <nt:EnhancementMethod>suffix_strip</nt:EnhancementMethod>
      <nt:SitePattern>generic_wordpress</nt:SitePattern>

      <!-- Quality Analysis -->
      <nt:JPEGQuality>85</nt:JPEGQuality>
      <nt:IsRecompressed>false</nt:IsRecompressed>
      <nt:HasWatermark>false</nt:HasWatermark>
      <nt:PerceptualHash>phash:abc123...</nt:PerceptualHash>

      <!-- Chain of Custody -->
      <nt:CustodyChain>
        <rdf:Seq>
          <rdf:li rdf:parseType="Resource">
            <nt:EventID>01HXY...</nt:EventID>
            <nt:EventTimestamp>2024-12-24T12:00:00Z</nt:EventTimestamp>
            <nt:EventAction>web_capture</nt:EventAction>
            <nt:EventOutcome>success</nt:EventOutcome>
            <nt:EventTool>national-treasure/1.0.0</nt:EventTool>
            <nt:EventHost>macbook.local</nt:EventHost>
          </rdf:li>
          <rdf:li rdf:parseType="Resource">
            <nt:EventID>01HXZ...</nt:EventID>
            <nt:EventTimestamp>2024-12-24T12:00:01Z</nt:EventTimestamp>
            <nt:EventAction>url_enhancement</nt:EventAction>
            <nt:EventOutcome>success</nt:EventOutcome>
            <nt:EventNotes>Found higher resolution via suffix stripping</nt:EventNotes>
          </rdf:li>
        </rdf:Seq>
      </nt:CustodyChain>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>
```

### Custody Event Actions (PREMIS-aligned)

```python
from enum import Enum

class CustodyEventAction(str, Enum):
    # Capture events
    WEB_CAPTURE = "web_capture"              # Initial download from URL
    PAGE_SCREENSHOT = "page_screenshot"      # Full-page screenshot
    WARC_ARCHIVE = "warc_archive"           # WARC file creation

    # Processing events
    URL_ENHANCEMENT = "url_enhancement"      # Found higher-res URL
    QUALITY_ANALYSIS = "quality_analysis"    # JPEG/watermark check
    PERCEPTUAL_HASH = "perceptual_hash"     # pHash calculation
    THUMBNAIL_GENERATION = "thumbnail_generation"
    FORMAT_CONVERSION = "format_conversion"

    # Verification events
    HASH_VERIFICATION = "hash_verification"  # Integrity check
    FIXITY_CHECK = "fixity_check"           # Periodic verification
    DUPLICATE_CHECK = "duplicate_check"     # pHash comparison

    # Storage events
    MIGRATION = "migration"                 # Moved to new location
    REPLICATION = "replication"            # Backup copy created
    DELETION = "deletion"                  # File removed
```

### XMP Sidecar Schema (Python)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from ulid import ULID

class WebProvenance(BaseModel):
    """Where the file came from on the web."""
    source_url: str                         # Direct URL to file
    page_url: Optional[str] = None          # Page where found
    page_title: Optional[str] = None
    capture_timestamp: datetime
    capture_method: str = "playwright"      # playwright, wget, curl

    # Context from page
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    credit: Optional[str] = None
    link_url: Optional[str] = None

    # Enhancement
    original_url: Optional[str] = None      # Before enhancement
    enhanced_url: Optional[str] = None      # After enhancement
    enhancement_method: Optional[str] = None
    site_pattern: Optional[str] = None

class QualityAnalysis(BaseModel):
    """Image quality metrics."""
    jpeg_quality: Optional[int] = None
    is_recompressed: bool = False
    has_watermark: bool = False
    watermark_confidence: Optional[float] = None
    perceptual_hash: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

class CustodyEvent(BaseModel):
    """Single event in the chain of custody."""
    event_id: str = Field(default_factory=lambda: str(ULID()))
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_action: CustodyEventAction
    event_outcome: str = "success"  # success, failure, partial
    event_tool: Optional[str] = None
    event_host: Optional[str] = None
    event_user: Optional[str] = None
    event_hash: Optional[str] = None
    event_notes: Optional[str] = None

class XMPSidecar(BaseModel):
    """Complete XMP sidecar for a scraped file."""
    schema_version: int = 1
    sidecar_created: datetime = Field(default_factory=datetime.utcnow)
    sidecar_updated: datetime = Field(default_factory=datetime.utcnow)

    # Core identity
    content_hash: str                       # blake3 hash
    hash_algorithm: str = "blake3"
    file_size: int

    # Web provenance
    provenance: WebProvenance

    # Quality (for images)
    quality: Optional[QualityAnalysis] = None

    # Chain of custody
    custody_chain: List[CustodyEvent] = Field(default_factory=list)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    event_count: int = 0

    def add_event(self, action: CustodyEventAction, **kwargs) -> CustodyEvent:
        """Add a custody event."""
        event = CustodyEvent(event_action=action, **kwargs)
        self.custody_chain.append(event)
        self.event_count = len(self.custody_chain)
        self.sidecar_updated = datetime.utcnow()
        return event
```

### XMP Writer Integration

```python
from exiftool import ExifToolHelper
import json

class XMPWriter:
    """Write XMP sidecars using exiftool."""

    def __init__(self):
        self.et = ExifToolHelper()

    def write_sidecar(self, file_path: Path, sidecar: XMPSidecar) -> Path:
        """Write XMP sidecar file."""
        xmp_path = file_path.with_suffix(file_path.suffix + ".xmp")

        # Prepare tags for exiftool
        tags = {
            "XMP-dc:Source": f"national-treasure:{json.dumps(sidecar.dict())}",
            "XMP-xmp:Label": "national-treasure-managed",
            "XMP-dc:Description": f"Captured from {sidecar.provenance.source_url}",
        }

        # Add web provenance to standard fields
        if sidecar.provenance.source_url:
            tags["XMP-dc:Identifier"] = sidecar.provenance.source_url
        if sidecar.provenance.credit:
            tags["XMP-dc:Creator"] = sidecar.provenance.credit
        if sidecar.provenance.caption:
            tags["XMP-dc:Title"] = sidecar.provenance.caption

        # Write XMP file
        self.et.set_tags(
            str(xmp_path),
            tags,
            params=["-overwrite_original"]
        )

        return xmp_path

    def read_sidecar(self, file_path: Path) -> Optional[XMPSidecar]:
        """Read XMP sidecar if it exists."""
        xmp_path = file_path.with_suffix(file_path.suffix + ".xmp")
        if not xmp_path.exists():
            return None

        tags = self.et.get_tags(str(xmp_path), ["XMP-dc:Source"])
        source = tags[0].get("XMP-dc:Source", "")

        if source.startswith("national-treasure:"):
            json_str = source[len("national-treasure:"):]
            return XMPSidecar.parse_raw(json_str)

        return None
```

### Integration with Capture Pipeline

```python
async def capture_image_with_provenance(
    page: Page,
    image_url: str,
    context: ImageContext
) -> Tuple[Path, XMPSidecar]:
    """Capture image with full provenance tracking."""

    # Create initial sidecar
    sidecar = XMPSidecar(
        content_hash="",  # Will be set after download
        file_size=0,
        provenance=WebProvenance(
            source_url=image_url,
            page_url=page.url,
            page_title=await page.title(),
            capture_timestamp=datetime.utcnow(),
            alt_text=context.alt,
            caption=context.caption,
            credit=context.credit,
            link_url=context.link_url,
        )
    )

    # Record capture event
    sidecar.add_event(
        CustodyEventAction.WEB_CAPTURE,
        event_tool=f"national-treasure/{VERSION}",
        event_host=socket.gethostname(),
    )

    # Try URL enhancement
    enhanced_url = await enhance_image_url(image_url)
    if enhanced_url != image_url:
        sidecar.provenance.original_url = image_url
        sidecar.provenance.enhanced_url = enhanced_url
        sidecar.add_event(
            CustodyEventAction.URL_ENHANCEMENT,
            event_notes=f"Enhanced: {image_url} → {enhanced_url}",
        )
        image_url = enhanced_url

    # Download image
    response = await page.request.get(image_url)
    image_data = await response.body()

    # Calculate hash
    sidecar.content_hash = blake3(image_data).hexdigest()
    sidecar.file_size = len(image_data)

    # Analyze quality (for JPEG)
    if image_url.lower().endswith(('.jpg', '.jpeg')):
        quality = await analyze_image_quality(image_data)
        sidecar.quality = quality
        sidecar.add_event(
            CustodyEventAction.QUALITY_ANALYSIS,
            event_notes=f"JPEG quality: {quality.jpeg_quality}, watermark: {quality.has_watermark}",
        )

    # Calculate perceptual hash
    phash = calculate_phash(image_data)
    if sidecar.quality:
        sidecar.quality.perceptual_hash = phash
    sidecar.add_event(
        CustodyEventAction.PERCEPTUAL_HASH,
        event_hash=phash,
    )

    # Save file
    output_path = get_output_path(image_url, sidecar.content_hash)
    output_path.write_bytes(image_data)

    # Write XMP sidecar
    xmp_writer = XMPWriter()
    xmp_writer.write_sidecar(output_path, sidecar)

    return output_path, sidecar
```

---

## Part 2: ML Feedback Loop Architecture

### Problem Statement

Web scraping fails unpredictably due to:
- Bot detection (403, CAPTCHA, CloudFront blocks)
- Rate limiting
- Session/cookie expiration
- Page structure changes

### ML Approach: Multi-Armed Bandit + Classification

Based on the ML skill guidance, we use a **hybrid approach**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ML FEEDBACK LOOP ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  REQUEST                                                            │
│     │                                                               │
│     ▼                                                               │
│  ┌──────────────────┐                                               │
│  │  Domain Lookup   │ ──▶ Known domain? Use learned config         │
│  └────────┬─────────┘                                               │
│           │ Unknown                                                 │
│           ▼                                                         │
│  ┌──────────────────┐                                               │
│  │ Similar Domain   │ ──▶ Find similar domains by TLD/pattern      │
│  │   Clustering     │     Use their best config as starting point  │
│  └────────┬─────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                               │
│  │  Config Selection│ ──▶ Multi-Armed Bandit (Thompson Sampling)   │
│  │  (Exploration)   │     Balance exploit (best known) vs explore  │
│  └────────┬─────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                               │
│  │  Execute Request │ ──▶ Browser automation with selected config  │
│  └────────┬─────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                               │
│  │ Outcome Analysis │ ──▶ Success? Blocked? CAPTCHA? Timeout?      │
│  └────────┬─────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────┐                                               │
│  │  Update Model    │ ──▶ Record result, update confidence         │
│  │  (Learning)      │     Decay old data, promote new patterns     │
│  └──────────────────┘                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Schema: Request Outcomes

```sql
CREATE TABLE request_outcomes (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Target Info
    domain TEXT NOT NULL,
    url TEXT NOT NULL,
    tld TEXT NOT NULL,  -- .com, .org, etc

    -- Configuration Used
    config_id INTEGER REFERENCES browser_configs(id),
    user_agent TEXT,
    headless_mode TEXT,  -- 'shell', 'new', 'old', 'visible'
    stealth_enabled BOOLEAN,
    proxy_used TEXT,

    -- Timing
    request_hour INTEGER,  -- 0-23
    request_day_of_week INTEGER,  -- 0-6
    requests_last_minute INTEGER,
    requests_last_hour INTEGER,

    -- Outcome
    http_status INTEGER,
    outcome TEXT,  -- 'success', 'blocked_403', 'captcha', 'timeout', 'rate_limited', 'content_empty'
    blocked_by TEXT,  -- 'cloudfront', 'cloudflare', 'akamai', 'custom', null
    content_extracted BOOLEAN,
    content_length INTEGER,

    -- Response Analysis
    page_title TEXT,
    has_captcha BOOLEAN,
    has_login_wall BOOLEAN,
    response_time_ms INTEGER,

    -- Indexes for fast queries
    INDEX idx_domain (domain),
    INDEX idx_outcome (outcome),
    INDEX idx_config (config_id)
);

CREATE TABLE browser_configs (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,

    -- Browser Settings
    headless_mode TEXT DEFAULT 'shell',
    user_agent_template TEXT,
    viewport_width INTEGER DEFAULT 1920,
    viewport_height INTEGER DEFAULT 1080,

    -- Stealth Settings
    stealth_enabled BOOLEAN DEFAULT true,
    disable_automation_flag BOOLEAN DEFAULT true,
    random_fingerprint BOOLEAN DEFAULT false,

    -- Behavior Settings
    wait_strategy TEXT DEFAULT 'networkidle',
    default_timeout_ms INTEGER DEFAULT 30000,

    -- Statistics (updated by ML loop)
    total_attempts INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    success_rate REAL GENERATED ALWAYS AS (
        CASE WHEN total_attempts > 0
        THEN CAST(success_count AS REAL) / total_attempts
        ELSE 0.5 END
    ) STORED,
    last_success DATETIME,
    last_failure DATETIME
);

CREATE TABLE domain_configs (
    domain TEXT PRIMARY KEY,

    -- Best Known Config
    best_config_id INTEGER REFERENCES browser_configs(id),
    confidence REAL DEFAULT 0.5,  -- 0-1

    -- Rate Limiting (learned)
    min_delay_ms INTEGER DEFAULT 1000,
    max_requests_per_minute INTEGER DEFAULT 10,

    -- Cookies/Sessions
    requires_cookies BOOLEAN DEFAULT false,
    cookie_source TEXT,  -- 'extension', 'manual', 'oauth'
    session_lifetime_hours INTEGER,

    -- Behavior Flags
    needs_scroll_to_load BOOLEAN DEFAULT false,
    needs_click_to_expand BOOLEAN DEFAULT false,
    has_infinite_scroll BOOLEAN DEFAULT false,

    -- Detection Patterns
    block_indicators TEXT,  -- JSON array of strings to detect
    success_indicators TEXT,  -- JSON array of strings indicating success

    -- Learning Metadata
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    sample_count INTEGER DEFAULT 0
);

CREATE TABLE domain_similarity (
    domain_a TEXT,
    domain_b TEXT,
    similarity_score REAL,  -- 0-1
    similarity_type TEXT,  -- 'tld', 'technology', 'behavior'
    PRIMARY KEY (domain_a, domain_b)
);
```

### ML Algorithm: Thompson Sampling for Config Selection

```python
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConfigStats:
    config_id: int
    successes: int = 0
    failures: int = 0

    def sample_success_rate(self) -> float:
        """Thompson Sampling: Draw from Beta distribution."""
        # Beta(successes + 1, failures + 1) gives posterior
        return np.random.beta(self.successes + 1, self.failures + 1)

class DomainLearner:
    """Multi-Armed Bandit for config selection per domain."""

    def __init__(self, db: Database):
        self.db = db
        self.config_stats: dict[str, dict[int, ConfigStats]] = {}

    def select_config(self, domain: str) -> int:
        """Select best config using Thompson Sampling."""
        stats = self._get_domain_stats(domain)

        if not stats:
            # New domain - find similar domains and use their best
            similar = self._find_similar_domains(domain)
            if similar:
                return self._get_best_config_from_similar(similar)
            return self._get_default_config()

        # Thompson Sampling: sample from each config's posterior
        samples = {
            config_id: stat.sample_success_rate()
            for config_id, stat in stats.items()
        }

        # Exploration bonus for under-sampled configs
        for config_id, stat in stats.items():
            if stat.successes + stat.failures < 10:
                samples[config_id] += 0.1  # Exploration bonus

        return max(samples, key=samples.get)

    def record_outcome(
        self,
        domain: str,
        config_id: int,
        success: bool,
        details: dict
    ):
        """Update model with new observation."""
        # Update config stats
        if domain not in self.config_stats:
            self.config_stats[domain] = {}
        if config_id not in self.config_stats[domain]:
            self.config_stats[domain][config_id] = ConfigStats(config_id)

        stat = self.config_stats[domain][config_id]
        if success:
            stat.successes += 1
        else:
            stat.failures += 1

        # Persist to database
        self._save_outcome(domain, config_id, success, details)

        # Update domain config if this is new best
        self._update_best_config(domain)

    def _find_similar_domains(self, domain: str) -> list[str]:
        """Find domains with similar characteristics."""
        # Strategy 1: Same TLD
        tld = domain.split('.')[-1]
        similar_by_tld = self.db.query(
            "SELECT domain FROM domain_configs WHERE domain LIKE ? "
            "AND confidence > 0.7 ORDER BY sample_count DESC LIMIT 5",
            (f'%.{tld}',)
        )

        # Strategy 2: Similar technology stack (detected from headers/content)
        # Strategy 3: Explicit similarity table

        return similar_by_tld
```

### Decay & Freshness

```python
def apply_time_decay(self, domain: str, half_life_days: int = 30):
    """Decay old observations so recent data matters more."""
    cutoff = datetime.now() - timedelta(days=half_life_days * 3)

    # Exponential decay on old outcomes
    self.db.execute("""
        UPDATE request_outcomes
        SET weight = EXP(-0.693 * (julianday('now') - julianday(timestamp)) / ?)
        WHERE domain = ? AND timestamp < ?
    """, (half_life_days, domain, cutoff))
```

### Anomaly Detection: When Things Change

```python
def detect_drift(self, domain: str) -> Optional[str]:
    """Detect when a previously-working config stops working."""
    recent = self._get_recent_outcomes(domain, limit=10)
    historical = self._get_historical_success_rate(domain)

    if len(recent) < 5:
        return None

    recent_rate = sum(1 for r in recent if r.success) / len(recent)

    # Statistical test: is recent rate significantly worse?
    if historical > 0.8 and recent_rate < 0.3:
        return "DRIFT_DETECTED: Success rate dropped from {:.0%} to {:.0%}".format(
            historical, recent_rate
        )

    # Check for new block patterns
    new_blocks = [r for r in recent if r.blocked_by and r.blocked_by not in self._known_blocks(domain)]
    if new_blocks:
        return f"NEW_BLOCK_DETECTED: {new_blocks[0].blocked_by}"

    return None
```

---

## Part 3: CLI Architecture

### Command Structure

```
national-treasure
├── capture <url>          # Capture a webpage (screenshot, PDF, HTML, WARC)
├── scrape <url>           # Extract structured data from a page
├── image <url>            # Download best version of an image
├── enhance <image-url>    # Find highest-res version of an image
├── archive <url>          # Full archival capture (all formats + assets)
│
├── learn                  # ML learning commands
│   ├── status             # Show learning statistics
│   ├── train              # Force training update
│   ├── export             # Export learned patterns
│   └── reset <domain>     # Reset learning for a domain
│
├── config                 # Configuration
│   ├── show               # Show current config
│   ├── set <key> <value>  # Set config value
│   └── profiles           # Manage browser profiles
│
└── server                 # RPC server mode
    └── start              # Start JSON-RPC server
```

### CLI Implementation

```python
# src/national_treasure/cli/main.py

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="national-treasure",
    help="Ultimate browser automation with ML-powered learning"
)

console = Console()

@app.command()
def capture(
    url: str,
    output: str = typer.Option(None, "--output", "-o", help="Output path"),
    format: str = typer.Option("all", "--format", "-f", help="screenshot|pdf|html|warc|all"),
    headless: bool = typer.Option(True, "--headless/--visible", help="Run headless"),
    behaviors: bool = typer.Option(True, "--behaviors/--no-behaviors", help="Run page behaviors"),
):
    """Capture a webpage in one or more formats."""
    import asyncio
    from ..services.capture import CaptureService

    async def run():
        async with CaptureService(headless=headless) as service:
            result = await service.capture(
                url,
                formats=format.split(",") if format != "all" else ["screenshot", "pdf", "html", "warc"],
                run_behaviors=behaviors,
            )

            # Show results
            table = Table(title="Capture Results")
            table.add_column("Format")
            table.add_column("Path")
            table.add_column("Size")

            for fmt, path in result.files.items():
                table.add_row(fmt, str(path), f"{path.stat().st_size:,} bytes")

            console.print(table)

    asyncio.run(run())


@app.command()
def scrape(
    url: str,
    output: str = typer.Option(None, "--output", "-o", help="Output JSON path"),
    site: str = typer.Option(None, "--site", "-s", help="Force specific scraper"),
    headless: bool = typer.Option(True, "--headless/--visible"),
):
    """Extract structured data from a webpage."""
    import asyncio
    from ..services.scraper import ScraperService

    async def run():
        async with ScraperService(headless=headless) as service:
            result = await service.scrape(url, site=site)

            if output:
                import json
                with open(output, 'w') as f:
                    json.dump(result.model_dump(), f, indent=2, default=str)
                console.print(f"[green]Saved to {output}[/green]")
            else:
                console.print_json(data=result.model_dump())

    asyncio.run(run())


@app.command()
def image(
    url: str,
    output: str = typer.Option(".", "--output", "-o", help="Output directory"),
    enhance: bool = typer.Option(True, "--enhance/--no-enhance", help="Find highest-res version"),
    analyze: bool = typer.Option(False, "--analyze", help="Show quality analysis"),
):
    """Download the best version of an image."""
    import asyncio
    from ..services.image import ImageService

    async def run():
        service = ImageService()

        if enhance:
            result = await service.enhance_and_download(url, output_dir=output)
            console.print(f"[green]Original:[/green] {url}")
            console.print(f"[green]Best version:[/green] {result.best_url}")
            console.print(f"[green]Improvement:[/green] {result.improvement:.1f}x larger")
        else:
            path = await service.download(url, output_dir=output)
            console.print(f"[green]Downloaded:[/green] {path}")

        if analyze:
            analysis = await service.analyze(result.best_url if enhance else url)
            console.print(f"[blue]Quality Score:[/blue] {analysis.quality_score}/100")
            console.print(f"[blue]Dimensions:[/blue] {analysis.dimensions.width}x{analysis.dimensions.height}")
            if analysis.watermark.has_watermark:
                console.print(f"[yellow]Watermark detected:[/yellow] {analysis.watermark.watermark_type}")

    asyncio.run(run())


# Learning subcommands
learn_app = typer.Typer(help="ML learning commands")
app.add_typer(learn_app, name="learn")

@learn_app.command("status")
def learn_status(
    domain: str = typer.Argument(None, help="Specific domain to check"),
):
    """Show learning statistics."""
    from ..services.learning import LearningService

    service = LearningService()

    if domain:
        stats = service.get_domain_stats(domain)
        console.print(f"[bold]Domain:[/bold] {domain}")
        console.print(f"[bold]Best Config:[/bold] {stats.best_config}")
        console.print(f"[bold]Confidence:[/bold] {stats.confidence:.1%}")
        console.print(f"[bold]Success Rate:[/bold] {stats.success_rate:.1%}")
        console.print(f"[bold]Sample Count:[/bold] {stats.sample_count}")
    else:
        # Global stats
        stats = service.get_global_stats()

        table = Table(title="Learning Statistics")
        table.add_column("Metric")
        table.add_column("Value")

        table.add_row("Total Domains", str(stats.total_domains))
        table.add_row("Total Requests", str(stats.total_requests))
        table.add_row("Overall Success Rate", f"{stats.overall_success_rate:.1%}")
        table.add_row("Domains with Drift", str(stats.domains_with_drift))

        console.print(table)


if __name__ == "__main__":
    app()
```

---

## Part 4: Service Architecture

```
src/national_treasure/
├── __init__.py
├── cli/
│   ├── __init__.py
│   └── main.py                 # Typer CLI
│
├── core/
│   ├── __init__.py
│   ├── models.py               # Pydantic models
│   ├── database.py             # SQLite with Kysely-like builder
│   └── config.py               # Configuration management
│
├── services/
│   ├── __init__.py
│   │
│   ├── browser/
│   │   ├── __init__.py
│   │   ├── service.py          # BrowserService (async context manager)
│   │   ├── stealth.py          # Bot detection bypass
│   │   ├── behaviors.py        # Page interaction behaviors
│   │   └── profiles.py         # Browser profile management
│   │
│   ├── capture/
│   │   ├── __init__.py
│   │   ├── service.py          # CaptureService orchestrator
│   │   ├── screenshot.py       # Screenshot capture
│   │   ├── pdf.py              # PDF capture
│   │   ├── html.py             # HTML with inlined resources
│   │   ├── warc.py             # WARC archiving
│   │   └── validation.py       # Response validation (403, CAPTCHA detection)
│   │
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── service.py          # ScraperService orchestrator
│   │   ├── base.py             # BaseScraper abstract class
│   │   ├── training.py         # Selector confidence tracking
│   │   └── sites/              # Site-specific scrapers
│   │       ├── __init__.py
│   │       ├── bandcamp.py
│   │       └── ...
│   │
│   ├── image/
│   │   ├── __init__.py
│   │   ├── service.py          # ImageService orchestrator
│   │   ├── discovery.py        # Image source discovery
│   │   ├── enhance.py          # URL enhancement (suffix stripping)
│   │   ├── quality.py          # Quality analysis (JPEG, watermark)
│   │   ├── patterns.py         # Site-specific URL patterns
│   │   └── phash.py            # Perceptual hashing
│   │
│   ├── learning/
│   │   ├── __init__.py
│   │   ├── service.py          # LearningService orchestrator
│   │   ├── bandit.py           # Multi-Armed Bandit (Thompson Sampling)
│   │   ├── drift.py            # Drift detection
│   │   ├── similarity.py       # Domain similarity clustering
│   │   └── decay.py            # Time decay for old data
│   │
│   └── queue/
│       ├── __init__.py
│       └── service.py          # Job queue with SQLite persistence
│
├── server/
│   ├── __init__.py
│   └── rpc.py                  # JSON-RPC 2.0 WebSocket server
│
└── data/
    ├── schema.sql              # Database schema
    └── migrations/             # Schema migrations
```

---

## Part 5: Feature Checklist for Stand-In Replacement

### To Replace abandoned-archive Browser Features

- [ ] **Screenshot Capture** - Full page, element, viewport
- [ ] **PDF Capture** - Paginated, background colors
- [ ] **HTML Capture** - With inlined CSS/images
- [ ] **WARC Capture** - ISO 28500:2017 format with CDP
- [ ] **Bot Detection Bypass** - Stealth plugin, shell headless, anti-automation
- [ ] **Response Validation** - 403, CAPTCHA, CloudFront, rate limit detection
- [ ] **Page Behaviors** - 7 Browsertrix-level behaviors
- [ ] **Cookie Management** - Extension sync, manual injection
- [ ] **Rate Limiting** - Per-domain with caching
- [ ] **Image Discovery** - srcset, meta, data-*, JSON-LD, backgrounds
- [ ] **Image Quality Analysis** - JPEG quantization, watermark, dimensions
- [ ] **Image Enhancement** - Recursive suffix stripping, 30+ site patterns
- [ ] **Perceptual Hashing** - pHash for similarity detection
- [ ] **Job Queue** - SQLite-backed with dependencies

### To Replace barbossa Browser Features

- [ ] **Browser Service** - Async context manager for Playwright
- [ ] **Base Scraper** - Plugin architecture for sites
- [ ] **Training Service** - Selector confidence tracking
- [ ] **Site Scrapers** - Bandcamp (and extensible)
- [ ] **Track Matcher** - Fuzzy matching with confidence
- [ ] **Pydantic Models** - Strict validation
- [ ] **RPC Server** - JSON-RPC 2.0 WebSocket

### New ML Features

- [ ] **Request Outcome Tracking** - Log all requests with full context
- [ ] **Config Selection** - Thompson Sampling multi-armed bandit
- [ ] **Domain Similarity** - Cluster similar domains
- [ ] **Drift Detection** - Alert when success rate drops
- [ ] **Time Decay** - Weight recent data more heavily
- [ ] **Export/Import** - Share learned patterns

### Cookie Sync & Session Management (Part 1B)

- [ ] **Browser Profile Detection** - Auto-detect Chrome, Arc, Brave, Edge, Vivaldi
- [ ] **Cookie File Sync** - Copy Cookies/Cookies-journal from source browser
- [ ] **Lock File Detection** - Warn if browser is running (SingletonLock)
- [ ] **Extension Session Capture** - WebSocket server for live session capture
- [ ] **Session Store** - Save/load {sourceId}_session.json
- [ ] **Cookie Injection** - Inject cookies before page navigation
- [ ] **Per-Domain Override** - Config for domain-specific cookie sources

### XMP Provenance Tracking (Part 1C)

- [ ] **XMP Sidecar Writer** - Generate .xmp files via exiftool
- [ ] **Web Provenance** - Source URL, page URL, capture timestamp
- [ ] **Image Context** - Alt text, caption, credit from DOM
- [ ] **Enhancement Tracking** - Original vs enhanced URL, method used
- [ ] **Quality Metrics** - JPEG quality, watermark detection, pHash
- [ ] **Custody Chain** - PREMIS-aligned event logging
- [ ] **Hash Verification** - Blake3 content hash in sidecar

---

## Part 6: Implementation Phases

### Phase 1: Core Foundation (Week 1-2)
- [ ] Project scaffolding (pyproject.toml, structure)
- [ ] Database schema and migrations
- [ ] BrowserService with async context manager
- [ ] Basic CLI with capture command
- [ ] Response validation (403/CAPTCHA detection)

### Phase 2: Capture Pipeline (Week 2-3)
- [ ] Screenshot, PDF, HTML capture
- [ ] WARC capture with CDP
- [ ] Page behaviors (scroll, expand, dismiss)
- [ ] Bot detection bypass (stealth)

### Phase 3: Image Processing (Week 3-4)
- [ ] Image source discovery
- [ ] URL pattern transformer
- [ ] Image enhancement service
- [ ] Quality analysis
- [ ] Perceptual hashing

### Phase 4: Scraper System (Week 4-5)
- [ ] Base scraper with plugin architecture
- [ ] Training service (selector confidence)
- [ ] Bandcamp scraper port
- [ ] Pydantic models

### Phase 5: ML Learning Loop (Week 5-6)
- [ ] Request outcome logging
- [ ] Thompson Sampling bandit
- [ ] Domain similarity clustering
- [ ] Drift detection
- [ ] CLI learn commands

### Phase 6: Polish & Server (Week 6-7)
- [ ] RPC server
- [ ] Configuration management
- [ ] Documentation
- [ ] Tests

---

## Part 7: Tech Stack

| Layer | Technology | Why |
|-------|------------|-----|
| **Language** | Python 3.11+ | Async/await, type hints, ecosystem |
| **CLI** | Typer + Rich | Best-in-class CLI experience |
| **Browser** | Playwright | Cross-browser, better than Puppeteer for Python |
| **Database** | SQLite + aiosqlite | Offline-first, no dependencies |
| **Models** | Pydantic v2 | Strict validation, serialization |
| **ML** | NumPy + scikit-learn (optional) | Thompson Sampling, clustering |
| **Async** | asyncio + httpx | Non-blocking I/O |
| **Image** | Pillow + sharp (via pysharp) | Image processing |
| **Testing** | pytest + pytest-asyncio | Async test support |

---

## Appendix: Key Insights from Audits

### From abandoned-archive
1. **7 Browsertrix-level behaviors** are essential for exposing hidden content
2. **Response validation** prevents silent 403 archival
3. **Recursive suffix stripping** finds true originals (image-1024x768-scaled.jpg → image.jpg)
4. **30+ site-specific URL patterns** for major platforms
5. **JPEG quantization table analysis** detects re-compression
6. **Per-domain rate limiting with caching** (15-minute cache)

### From barbossa
1. **Selector confidence tracking** learns what works over time
2. **Fallback chains** (primary selector → alternatives → hardcoded)
3. **Plugin architecture** makes adding new sites easy
4. **JSON-RPC 2.0** enables GUI/external integration
5. **Async context managers** prevent resource leaks

### ML Design Decisions
1. **Thompson Sampling** balances exploration vs exploitation
2. **Domain similarity** helps cold-start for new domains
3. **Time decay** ensures fresh data matters more
4. **Drift detection** catches when sites change their blocking
5. **SQLite persistence** works offline, no Redis needed

### From wake-n-blake (XMP Provenance)
1. **Custom XMP namespace** (`wnb:`) for provenance fields
2. **PREMIS-aligned custody events** (message_digest_calculation, fixity_check, migration, etc.)
3. **Source device tracking** (USB, card reader, camera fingerprint)
4. **Blake3 hashing** for content integrity
5. **Sidecar self-integrity** via hash of XMP content
6. **Batch/session tracking** for import operations

### From shoemaker (XMP Thumbnails)
1. **Batch queue processing** for efficient XMP updates
2. **JSON metadata in dc:Source** field
3. **exiftool-vendored** for cross-platform support
4. **RAW decoder chain** (embedded → sharp → rawtherapee → darktable → dcraw)

---

## Appendix B: Source Files Reference

### abandoned-archive
| File | LOC | Purpose |
|------|-----|---------|
| websource-capture-service.ts | 1716 | Browser automation, WARC, cookies |
| websource-behaviors.ts | 1079 | Browsertrix-level page interactions |
| websource-metadata-service.ts | 400+ | OG, Schema.org, Dublin Core extraction |
| image-source-discovery.ts | 716 | srcset, meta tags, JSON-LD image sources |
| image-quality-analyzer.ts | 924 | JPEG quantization, watermark, pHash |
| image-enhance-service.ts | 690 | URL enhancement, suffix stripping |
| detached-browser-service.ts | 315 | Zero-detection browser launcher |
| wacz-service.ts | 272 | WARC to WACZ conversion |

### barbossa
| File | LOC | Purpose |
|------|-----|---------|
| browser.py | 200+ | Playwright BrowserService |
| base.py | 300+ | BaseScraper with selectors |
| training.py | 250+ | Selector confidence tracking |
| bandcamp.py | 400+ | Site-specific scraper example |
| scraper_models.py | 150+ | Pydantic models |

### wake-n-blake
| File | LOC | Purpose |
|------|-----|---------|
| xmp/schema.ts | 507 | XmpSidecarData, CustodyEvent types |
| xmp/writer.ts | 395 | XMP sidecar generation |
| xmp/reader.ts | ~200 | XMP sidecar parsing |
| cli/commands/sidecar.ts | 463 | Sidecar CLI commands |

### shoemaker
| File | LOC | Purpose |
|------|-----|---------|
| services/xmp-updater.ts | 274 | XMP sidecar for thumbnails |
| core/decoder.ts | 419 | RAW file decoding chain |
| core/extractor.ts | ~300 | EXIF preview extraction |

---

## Appendix C: IRS ULTRATHINK - Complete Gap Analysis

> **Analysis Date**: 2024-12-24
> **Purpose**: Identify ALL features needed for national-treasure to be the CLI backbone for abandoned-archive web scraping

### Executive Summary

To become the CLI backbone for abandoned-archive, national-treasure must implement:

| Category | Current Status | Gap Level | Priority |
|----------|---------------|-----------|----------|
| Browser Automation Core | Partially Designed | MEDIUM | P0 |
| WARC/WACZ Archiving | Not Implemented | CRITICAL | P0 |
| Response Validation (OPT-122) | Not Implemented | CRITICAL | P0 |
| Job Queue System | Designed Only | HIGH | P0 |
| Database Schema | 4 tables vs 91 needed | CRITICAL | P0 |
| Image Processing Pipeline | Partially Designed | HIGH | P1 |
| Selector Training (barbossa) | Designed Only | MEDIUM | P1 |
| Extraction Pipeline (LLM) | Not Present | MEDIUM | P2 |
| Date Engine (NLP) | Not Present | LOW | P2 |
| Monitoring/Metrics | Not Present | MEDIUM | P2 |

---

### Section 1: CRITICAL GAPS - Must Have for Basic Function

#### 1.1 WARC Archiving (OPT-109)

**Current State**: Not implemented
**Required**: ISO 28500:2017 compliant WARC generation

```
IMPLEMENTATION REQUIRED:
├── warc.py              # WARC record generation
│   ├── wget primary     # Preferred: spawn wget --warc-file
│   ├── CDP fallback     # When wget unavailable:
│   │   ├── Network.enable (observe mode)
│   │   ├── Network.requestWillBeSent
│   │   ├── Network.responseReceived
│   │   └── Network.getResponseBody (after loadingFinished)
│   └── CDX index        # Create minimal CDX for replay
│
├── wacz.py              # WACZ conversion
│   ├── Zip archive creation
│   ├── datapackage.json (Frictionless Data spec)
│   └── SHA256 digest validation
```

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/websource-capture-service.ts:600-800` (WARC generation)
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/wacz-service.ts` (WACZ conversion)

#### 1.2 Response Validation (OPT-122)

**Current State**: Not implemented
**Required**: Detect bot blocks to prevent silent 403 archival

```python
class ResponseValidator:
    """Detect bot blocks, CAPTCHAs, and error pages."""

    BLOCK_PATTERNS = {
        'cloudfront': [
            'generated by cloudfront',
            'request could not be satisfied',
            'ERROR: The request could not be satisfied',
        ],
        'cloudflare': [
            'just a moment',
            'checking your browser',
            'ray id:',
            'cf-ray',
        ],
        'captcha': [
            'recaptcha',
            'hcaptcha',
            'captcha-container',
            'g-recaptcha',
        ],
        'rate_limit': [
            'too many requests',
            'rate limit exceeded',
            'please slow down',
        ],
        'security_services': [
            'perimeterx',
            'datadome',
            'akamai',
            'imperva',
            'incapsula',
        ],
    }

    def validate(self, response, page_content: str) -> ValidationResult:
        # Check HTTP status
        if response.status >= 400:
            return ValidationResult(blocked=True, reason=f'http_{response.status}')

        # Check content for block patterns
        content_lower = page_content.lower()
        for service, patterns in self.BLOCK_PATTERNS.items():
            for pattern in patterns:
                if pattern in content_lower:
                    return ValidationResult(blocked=True, reason=service, pattern=pattern)

        # Check for suspiciously short pages
        if len(page_content.strip()) < 500:
            return ValidationResult(
                blocked=True,
                reason='content_too_short',
                details=f'{len(page_content)} chars'
            )

        return ValidationResult(blocked=False)
```

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/websource-capture-service.ts:200-350` (validation logic)

#### 1.3 Database Schema (91 Tables)

**Current State**: 4 tables designed (request_outcomes, browser_configs, domain_configs, domain_similarity)
**Required**: Full schema for web source management

```sql
-- MISSING TABLES (Critical for abandoned-archive integration)

-- Web Sources (core entity)
CREATE TABLE web_sources (
    source_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    loc_id TEXT REFERENCES locs(locid),

    -- Status
    status TEXT DEFAULT 'pending',  -- pending, archiving, archived, failed
    archive_method TEXT,            -- 'extension', 'browser', 'wget'

    -- Capture Results
    screenshot_path TEXT,
    pdf_path TEXT,
    html_path TEXT,
    warc_path TEXT,
    wacz_path TEXT,

    -- Metadata
    page_title TEXT,
    page_description TEXT,
    og_data TEXT,           -- JSON
    schema_org_data TEXT,   -- JSON
    dublin_core_data TEXT,  -- JSON

    -- Extraction Results
    extracted_text TEXT,
    word_count INTEGER,
    image_count INTEGER,
    video_count INTEGER,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived_at DATETIME,
    last_checked DATETIME
);

-- Web Source Images (per-image metadata)
CREATE TABLE web_source_images (
    image_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES web_sources(source_id),

    -- URLs
    original_url TEXT NOT NULL,
    enhanced_url TEXT,
    final_url TEXT,

    -- Local Storage
    local_path TEXT,
    hash TEXT,

    -- Metadata from DOM
    alt_text TEXT,
    caption TEXT,
    credit TEXT,
    link_url TEXT,

    -- Quality Analysis
    width INTEGER,
    height INTEGER,
    jpeg_quality INTEGER,
    has_watermark BOOLEAN,
    perceptual_hash TEXT,

    -- Enhancement
    enhancement_method TEXT,
    original_size INTEGER,
    enhanced_size INTEGER,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Web Source Videos
CREATE TABLE web_source_videos (
    video_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES web_sources(source_id),

    url TEXT NOT NULL,
    platform TEXT,          -- youtube, vimeo, etc.
    video_id_external TEXT, -- Platform-specific ID

    -- Metadata (from yt-dlp)
    title TEXT,
    description TEXT,
    duration INTEGER,
    uploader TEXT,
    upload_date TEXT,
    view_count INTEGER,
    thumbnail_url TEXT,

    -- Local Storage
    local_path TEXT,
    metadata_json TEXT,     -- Full yt-dlp output

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Jobs (for queue system)
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    queue TEXT NOT NULL,
    priority INTEGER DEFAULT 10,
    status TEXT DEFAULT 'pending',
    payload TEXT,           -- JSON
    depends_on TEXT,        -- Parent job ID
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error TEXT,
    result TEXT,            -- JSON
    created_at DATETIME,
    started_at DATETIME,
    completed_at DATETIME,
    locked_by TEXT,
    locked_at DATETIME,
    retry_after DATETIME
);

-- Job Dead Letter Queue
CREATE TABLE job_dead_letter (
    id INTEGER PRIMARY KEY,
    job_id TEXT,
    queue TEXT,
    payload TEXT,
    error TEXT,
    attempts INTEGER,
    died_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- URL Patterns (learned image URL transformations)
CREATE TABLE url_patterns (
    pattern_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    site_type TEXT,         -- wordpress, cdn, hosting, generic
    domain_regex TEXT,
    path_regex TEXT,
    transform_js TEXT,      -- JavaScript transform function
    confidence REAL DEFAULT 0.5,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT 1,
    is_builtin BOOLEAN DEFAULT 0
);

-- Selector Training (from barbossa)
CREATE TABLE selector_patterns (
    id INTEGER PRIMARY KEY,
    site TEXT NOT NULL,     -- bandcamp, discogs, etc.
    field TEXT NOT NULL,    -- title, artist, date, etc.
    selector TEXT NOT NULL,
    selector_type TEXT DEFAULT 'css',
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    examples TEXT,          -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site, field, selector)
);
```

#### 1.4 Job Queue with Dependencies

**Current State**: Designed only in architecture
**Required**: Full implementation with:
- Priority ordering
- Job dependencies (wait for parent)
- Exponential backoff retry
- Dead letter queue
- Atomic claiming with locks

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/job-queue.ts` (350+ lines)

---

### Section 2: HIGH PRIORITY GAPS

#### 2.1 Image Processing Pipeline (10 Components)

**Current State**: Partially designed
**Required**: Full 10-file pipeline from abandoned-archive

```
image/
├── discovery.py          # Find images in page (srcset, meta, data-*, JSON-LD)
├── patterns.py           # 30+ URL transform patterns
├── enhance.py            # Recursive suffix stripping
├── quality.py            # JPEG quantization analysis
├── watermark.py          # Watermark detection
├── phash.py              # Perceptual hashing (imagehash)
├── staging.py            # Stage candidates before import
├── orchestrator.py       # Coordinate discovery → enhance → download → analyze
├── browser_capture.py    # Context menu, network monitoring
└── backfill.py           # Backfill pHash for existing images
```

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/image-downloader/` (10 files)

#### 2.2 Selector Training Service (barbossa)

**Current State**: Designed only
**Required**: Working implementation

```python
class TrainingService:
    """Port from barbossa/services/scraper/training.py"""

    def record_success(self, site: str, field: str, selector: str, value: str):
        """Record successful selector extraction."""

    def record_failure(self, site: str, field: str, selector: str):
        """Record failed selector extraction."""

    def get_best_selector(self, site: str, field: str, hardcoded: str = None) -> str:
        """Get best selector considering learned patterns."""

    def get_fallback_selectors(self, site: str, field: str, exclude: str = None) -> list[str]:
        """Get fallback chain when primary fails."""

    def add_training_sample(self, site: str, url: str, field: str, selector: str, value: str):
        """User-provided training sample."""

    def get_training_stats(self, site: str) -> dict:
        """Training statistics per site."""
```

**Source Files**:
- `/Volumes/projects/barbossa/src/barbossa/services/scraper/training.py` (260 lines)
- `/Volumes/projects/barbossa/src/barbossa/core/scraper_models.py` (167 lines)

---

### Section 3: MEDIUM PRIORITY GAPS

#### 3.1 Page Behaviors (Browsertrix-Level)

**Current State**: Designed only
**Required**: Working implementation of 7 behaviors

```python
class PageBehaviors:
    """Port from abandoned-archive websource-behaviors.ts"""

    async def run_all(self, page: Page, options: BehaviorOptions) -> BehaviorStats:
        stats = BehaviorStats()

        # 1. Dismiss overlays (cookie banners, modals, popups)
        stats.overlays_dismissed = await self.dismiss_overlays(page)

        # 2. Scroll to load all (lazy-load trigger)
        stats.scroll_depth = await self.scroll_to_load_all(page)

        # 3. Expand all content (accordions, details, FAQs)
        stats.elements_expanded = await self.expand_all_content(page)

        # 4. Click all tabs
        stats.tabs_clicked = await self.click_all_tabs(page)

        # 5. Navigate carousels
        stats.carousel_slides = await self.navigate_carousels(page)

        # 6. Expand comments
        stats.comments_loaded = await self.expand_comments(page)

        # 7. Handle infinite scroll
        stats.infinite_scroll_pages = await self.handle_infinite_scroll(page)

        return stats
```

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/websource-behaviors.ts` (1079 lines)

#### 3.2 Metadata Extraction Service

**Current State**: Not present
**Required**: Extract structured metadata

```python
class MetadataExtractor:
    """Extract Open Graph, Schema.org, Dublin Core, Twitter Cards."""

    async def extract_all(self, page: Page) -> PageMetadata:
        return PageMetadata(
            open_graph=await self._extract_open_graph(page),
            schema_org=await self._extract_schema_org(page),
            dublin_core=await self._extract_dublin_core(page),
            twitter_cards=await self._extract_twitter_cards(page),
            standard_meta=await self._extract_standard_meta(page),
            links=await self._extract_links(page),
            images_with_context=await self._extract_image_dom_context(page),
        )
```

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/websource-metadata-service.ts` (400+ lines)

#### 3.3 Configuration Service

**Current State**: Basic config.py designed
**Required**: Full config with backup, monitoring, domain overrides

```python
@dataclass
class AppConfig:
    backup: BackupConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig
    browser: BrowserDefaults
    rate_limits: dict[str, RateLimitConfig]
    domain_overrides: dict[str, DomainConfig]

@dataclass
class BackupConfig:
    enabled: bool = True
    max_backups: int = 5
    backup_on_startup: bool = True
    backup_after_import: bool = True
    scheduled_backup: bool = True
    scheduled_interval_hours: int = 24

@dataclass
class MonitoringConfig:
    disk_warning_mb: int = 1024
    disk_critical_mb: int = 512
    disk_emergency_mb: int = 100
    integrity_check_on_startup: bool = True
```

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/config-service.ts` (200+ lines)

---

### Section 4: LOWER PRIORITY GAPS (Can Defer)

#### 4.1 Date Engine Service (NLP)

**Purpose**: Extract dates from free text
**Implementation**: Multi-phase pipeline with Chrono-Node + patterns + false-positive filtering

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/date-engine-service.ts`

#### 4.2 LLM Extraction Pipeline

**Purpose**: Extract entities using spaCy (offline) → Ollama (local) → Cloud fallback
**Implementation**: Multi-provider with cost tracking

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/extraction/` (12 files)

#### 4.3 Monitoring & Metrics

**Purpose**: Track metrics, traces, alerts
**Implementation**: SQLite-backed metrics collector

**Source Files**:
- `/Volumes/projects/abandoned-archive/packages/desktop/electron/services/monitoring/` (3 files)

---

### Section 5: Integration Requirements

#### 5.1 CLI Commands for abandoned-archive

```
national-treasure
├── capture <url>           # Screenshot, PDF, HTML, WARC
├── archive <url>           # Full archival (all formats + assets)
├── scrape <url>            # Structured data extraction
├── image <url>             # Download best version
│
├── queue                   # Job management
│   ├── add <type> <data>   # Enqueue job
│   ├── list [--status]     # List jobs
│   ├── process             # Process pending jobs
│   └── cleanup             # Clear dead letter queue
│
├── learn                   # ML commands (existing)
│   └── ...
│
├── train                   # Selector training (NEW)
│   ├── record <site> <field> <selector> <value>
│   ├── stats [site]
│   └── export [site]
│
└── server                  # RPC server
    └── start [--port]
```

#### 5.2 IPC-Compatible API Surface

For abandoned-archive to call national-treasure as a subprocess:

```python
# JSON-RPC 2.0 interface
{
    "jsonrpc": "2.0",
    "method": "archive",
    "params": {
        "url": "https://example.com",
        "options": {
            "screenshot": true,
            "pdf": true,
            "html": true,
            "warc": true,
            "behaviors": true,
            "extract_images": true,
            "max_images": 50
        }
    },
    "id": 1
}

# Response
{
    "jsonrpc": "2.0",
    "result": {
        "success": true,
        "screenshot_path": "/path/to/screenshot.png",
        "pdf_path": "/path/to/page.pdf",
        "html_path": "/path/to/page.html",
        "warc_path": "/path/to/archive.warc.gz",
        "images": [
            {"url": "...", "path": "...", "enhanced": true}
        ],
        "metadata": { ... }
    },
    "id": 1
}
```

---

### Section 6: Implementation Checklist

#### Phase 1: Critical (Before Integration)

- [ ] WARC generation (wget primary, CDP fallback)
- [ ] WACZ conversion service
- [ ] Response validation (OPT-122)
- [ ] Extended database schema (web_sources, jobs, etc.)
- [ ] Job queue with dependencies
- [ ] Page behaviors (7 Browsertrix-level)

#### Phase 2: High Priority (For Full Function)

- [ ] Image discovery service
- [ ] URL pattern transformer (30+ patterns)
- [ ] Image enhancement service
- [ ] Perceptual hashing
- [ ] Selector training service (barbossa port)
- [ ] Metadata extraction (OG, Schema.org, DC)

#### Phase 3: Integration (Abandoned-Archive Compatibility)

- [ ] JSON-RPC server
- [ ] CLI commands matching IPC handlers
- [ ] Output format compatibility
- [ ] Error code standardization
- [ ] Progress event streaming

---

### Section 7: Key Source Files Reference

| Feature | Source Path | Lines |
|---------|-------------|-------|
| WARC + CDP | `abandoned-archive/.../websource-capture-service.ts` | 1716 |
| WACZ | `abandoned-archive/.../wacz-service.ts` | 272 |
| Page Behaviors | `abandoned-archive/.../websource-behaviors.ts` | 1079 |
| Metadata Extraction | `abandoned-archive/.../websource-metadata-service.ts` | 400+ |
| Image Discovery | `abandoned-archive/.../image-source-discovery.ts` | 716 |
| Image Quality | `abandoned-archive/.../image-quality-analyzer.ts` | 924 |
| Image Enhance | `abandoned-archive/.../image-enhance-service.ts` | 690 |
| URL Patterns | `abandoned-archive/.../url-pattern-transformer.ts` | 400+ |
| Job Queue | `abandoned-archive/.../job-queue.ts` | 350+ |
| Config | `abandoned-archive/.../config-service.ts` | 200+ |
| Selector Training | `barbossa/.../training.py` | 260 |
| Scraper Models | `barbossa/.../scraper_models.py` | 167 |
| File Matcher | `barbossa/.../matcher.py` | 322 |

---

**Total Estimated Implementation Effort**:
- **Critical gaps**: ~3,000 lines Python
- **High priority**: ~2,500 lines Python
- **Medium priority**: ~2,000 lines Python
- **Full parity with abandoned-archive browser features**: ~7,500+ lines Python
