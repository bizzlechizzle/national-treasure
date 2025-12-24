"""Tests for core models."""

import pytest
from datetime import datetime

from national_treasure.core.models import (
    BrowserConfig,
    CaptureResult,
    DomainConfig,
    HeadlessMode,
    Job,
    JobStatus,
    JobType,
    OutcomeType,
    RequestOutcome,
    SelectorPattern,
    ValidationResult,
    WaitStrategy,
    generate_id,
)


class TestGenerateId:
    """Tests for ID generation."""

    def test_generates_unique_ids(self):
        """IDs should be unique."""
        ids = [generate_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_id_is_string(self):
        """ID should be a string."""
        id_ = generate_id()
        assert isinstance(id_, str)

    def test_id_has_valid_length(self):
        """ID should have reasonable length."""
        id_ = generate_id()
        assert len(id_) >= 20  # ULID is 26 chars


class TestBrowserConfig:
    """Tests for BrowserConfig model."""

    def test_default_values(self):
        """Default config should have sensible values."""
        config = BrowserConfig()
        assert config.headless_mode == HeadlessMode.SHELL
        assert config.stealth_enabled is True
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080

    def test_success_rate_zero_attempts(self):
        """Success rate should be 0.5 with zero attempts."""
        config = BrowserConfig()
        assert config.success_rate == 0.5

    def test_success_rate_calculation(self):
        """Success rate should be calculated correctly."""
        config = BrowserConfig(total_attempts=10, success_count=8)
        assert config.success_rate == 0.8

    def test_custom_values(self):
        """Custom values should be applied."""
        config = BrowserConfig(
            name="custom",
            headless_mode=HeadlessMode.VISIBLE,
            viewport_width=1280,
            viewport_height=720,
        )
        assert config.name == "custom"
        assert config.headless_mode == HeadlessMode.VISIBLE
        assert config.viewport_width == 1280


class TestSelectorPattern:
    """Tests for SelectorPattern model."""

    def test_confidence_zero_total(self):
        """Confidence should be 0 with no data."""
        pattern = SelectorPattern(site="example.com", field="title", selector="h1")
        assert pattern.confidence == 0.0

    def test_confidence_calculation(self):
        """Confidence should be calculated correctly."""
        pattern = SelectorPattern(
            site="example.com",
            field="title",
            selector="h1",
            success_count=8,
            failure_count=2,
        )
        assert pattern.confidence == 0.8

    def test_confidence_all_failures(self):
        """Confidence should be 0 with all failures."""
        pattern = SelectorPattern(
            site="example.com",
            field="title",
            selector="h1",
            success_count=0,
            failure_count=10,
        )
        assert pattern.confidence == 0.0


class TestJob:
    """Tests for Job model."""

    def test_default_status(self):
        """Default job status should be PENDING."""
        job = Job(job_type=JobType.CAPTURE)
        assert job.status == JobStatus.PENDING

    def test_payload_default(self):
        """Payload should default to empty dict."""
        job = Job(job_type=JobType.CAPTURE)
        assert job.payload == {}

    def test_job_with_payload(self):
        """Job should accept payload."""
        job = Job(
            job_type=JobType.CAPTURE,
            payload={"url": "https://example.com"},
        )
        assert job.payload["url"] == "https://example.com"


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_default_not_blocked(self):
        """Default result should not be blocked."""
        result = ValidationResult()
        assert result.blocked is False
        assert result.reason is None

    def test_blocked_with_reason(self):
        """Blocked result should have reason."""
        result = ValidationResult(blocked=True, reason="cloudflare")
        assert result.blocked is True
        assert result.reason == "cloudflare"


class TestCaptureResult:
    """Tests for CaptureResult model."""

    def test_required_fields(self):
        """CaptureResult requires success and url."""
        result = CaptureResult(success=True, url="https://example.com")
        assert result.success is True
        assert result.url == "https://example.com"

    def test_optional_paths(self):
        """Paths should be optional."""
        result = CaptureResult(success=True, url="https://example.com")
        assert result.screenshot_path is None
        assert result.pdf_path is None
        assert result.html_path is None


class TestEnums:
    """Tests for enum values."""

    def test_headless_modes(self):
        """HeadlessMode should have expected values."""
        assert HeadlessMode.SHELL.value == "shell"
        assert HeadlessMode.NEW.value == "new"
        assert HeadlessMode.VISIBLE.value == "visible"

    def test_wait_strategies(self):
        """WaitStrategy should have expected values."""
        assert WaitStrategy.LOAD.value == "load"
        assert WaitStrategy.NETWORKIDLE.value == "networkidle"

    def test_job_types(self):
        """JobType should have expected values."""
        assert JobType.CAPTURE.value == "capture"
        assert JobType.SCRAPE.value == "scrape"

    def test_job_status(self):
        """JobStatus should have expected values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
