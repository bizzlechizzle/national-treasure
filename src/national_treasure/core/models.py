"""Pydantic models for national-treasure."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


class OutcomeType(str, Enum):
    """Request outcome types."""

    SUCCESS = "success"
    BLOCKED_403 = "blocked_403"
    CAPTCHA = "captcha"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    CONTENT_EMPTY = "content_empty"
    ERROR = "error"


class BlockedBy(str, Enum):
    """Bot detection services."""

    CLOUDFRONT = "cloudfront"
    CLOUDFLARE = "cloudflare"
    AKAMAI = "akamai"
    IMPERVA = "imperva"
    DATADOME = "datadome"
    PERIMETERX = "perimeterx"
    CUSTOM = "custom"


class HeadlessMode(str, Enum):
    """Browser headless modes."""

    SHELL = "shell"  # Chrome 129+ undetectable
    NEW = "new"  # Standard headless
    VISIBLE = "visible"  # Not headless


class WaitStrategy(str, Enum):
    """Page load wait strategies."""

    LOAD = "load"
    DOMCONTENTLOADED = "domcontentloaded"
    NETWORKIDLE = "networkidle"
    COMMIT = "commit"


class JobType(str, Enum):
    """Types of background jobs."""

    CAPTURE = "capture"
    SCRAPE = "scrape"
    VALIDATE = "validate"
    EXPORT = "export"
    SYNC = "sync"


class JobStatus(str, Enum):
    """Job status in queue."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationResult(BaseModel):
    """Result of response validation."""

    blocked: bool = False
    reason: str | None = None
    pattern: str | None = None
    details: str | None = None
    http_status: int | None = None


class BrowserConfig(BaseModel):
    """Browser configuration for requests."""

    config_id: str = Field(default_factory=generate_id)
    name: str = "default"

    # Browser settings
    headless_mode: HeadlessMode = HeadlessMode.SHELL
    user_agent: str | None = None
    viewport_width: int = 1920
    viewport_height: int = 1080

    # Stealth settings
    stealth_enabled: bool = True
    disable_automation_flag: bool = True

    # Behavior settings
    wait_strategy: WaitStrategy = WaitStrategy.NETWORKIDLE
    default_timeout_ms: int = 30000

    # Statistics
    total_attempts: int = 0
    success_count: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_attempts == 0:
            return 0.5
        return self.success_count / self.total_attempts


class DomainConfig(BaseModel):
    """Learned configuration for a domain."""

    domain: str
    best_config_id: str | None = None
    confidence: float = 0.5

    # Rate limiting
    min_delay_ms: int = 1000
    max_requests_per_minute: int = 10

    # Cookies/sessions
    requires_cookies: bool = False
    cookie_source: str | None = None
    session_lifetime_hours: int | None = None

    # Behavior flags
    needs_scroll_to_load: bool = False
    needs_click_to_expand: bool = False
    has_infinite_scroll: bool = False

    # Detection patterns
    block_indicators: list[str] = Field(default_factory=list)
    success_indicators: list[str] = Field(default_factory=list)

    # Metadata
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sample_count: int = 0


class RequestOutcome(BaseModel):
    """Outcome of a browser request."""

    outcome_id: str = Field(default_factory=generate_id)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Target info
    domain: str
    url: str
    tld: str

    # Configuration used
    config_id: str
    user_agent: str | None = None
    headless_mode: HeadlessMode = HeadlessMode.SHELL
    stealth_enabled: bool = True

    # Timing context
    request_hour: int = 0
    request_day_of_week: int = 0
    requests_last_minute: int = 0
    requests_last_hour: int = 0

    # Outcome
    http_status: int | None = None
    outcome: OutcomeType = OutcomeType.SUCCESS
    blocked_by: BlockedBy | None = None
    content_extracted: bool = False
    content_length: int = 0

    # Response analysis
    page_title: str | None = None
    has_captcha: bool = False
    has_login_wall: bool = False
    response_time_ms: int = 0


class CaptureResult(BaseModel):
    """Result of a page capture."""

    success: bool
    url: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Captured files
    screenshot_path: str | None = None
    pdf_path: str | None = None
    html_path: str | None = None
    warc_path: str | None = None

    # Metadata
    page_title: str | None = None
    page_description: str | None = None
    word_count: int = 0

    # Extraction
    image_count: int = 0
    video_count: int = 0

    # Validation
    validation: ValidationResult | None = None

    # Performance
    duration_ms: int = 0
    error: str | None = None


class BehaviorStats(BaseModel):
    """Statistics from running page behaviors."""

    overlays_dismissed: int = 0
    scroll_depth: int = 0
    elements_expanded: int = 0
    tabs_clicked: int = 0
    carousel_slides: int = 0
    comments_loaded: int = 0
    infinite_scroll_pages: int = 0
    duration_ms: int = 0


class SelectorPattern(BaseModel):
    """A learned CSS selector pattern."""

    pattern_id: str = Field(default_factory=generate_id)
    site: str
    field: str
    selector: str
    selector_type: str = "css"

    success_count: int = 0
    failure_count: int = 0
    examples: list[str] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def confidence(self) -> float:
        """Calculate confidence based on success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total


class SiteTrainingData(BaseModel):
    """Training data for a specific site."""

    site: str
    patterns: dict[str, list[SelectorPattern]] = Field(default_factory=dict)
    training_samples: list[dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime | None = None


class UrlPattern(BaseModel):
    """URL transformation pattern for image enhancement."""

    pattern_id: str = Field(default_factory=generate_id)
    name: str = ""
    site: str = ""
    pattern_type: str = ""  # image_url, album_url, etc.
    pattern: str = ""  # regex pattern
    site_type: str = ""  # wordpress, cdn, hosting, generic
    domain_regex: str = ""
    path_regex: str = ""
    transform_template: str = ""

    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    fail_count: int = 0  # Alias for backward compat
    is_enabled: bool = True
    is_builtin: bool = False


class Job(BaseModel):
    """A background job in the queue."""

    job_id: str = Field(default_factory=generate_id)
    job_type: JobType
    payload: dict[str, Any] = Field(default_factory=dict)

    status: JobStatus = JobStatus.PENDING
    priority: int = 0
    retry_count: int = 0

    depends_on: str | None = None
    scheduled_for: datetime | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime | None = None

    result: dict[str, Any] | None = None
    error: str | None = None
