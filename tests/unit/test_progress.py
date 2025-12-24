"""Tests for CLI progress tracking with EWMA."""

import pytest
from time import sleep

from national_treasure.core.progress import (
    EWMACalculator,
    ProgressState,
    CaptureStage,
    STAGE_WEIGHTS,
    format_duration,
    format_throughput,
    format_eta,
    truncate_middle,
)


class TestEWMACalculator:
    """Tests for EWMA throughput smoothing."""

    def test_first_sample_sets_value(self):
        """First sample should set value directly."""
        ewma = EWMACalculator(alpha=0.15)
        result = ewma.update(100.0)
        assert result == 100.0
        assert ewma.value == 100.0

    def test_smooths_subsequent_samples(self):
        """Subsequent samples should be smoothed."""
        ewma = EWMACalculator(alpha=0.5)  # 50% weight for easy math
        ewma.update(100.0)  # value = 100
        result = ewma.update(200.0)  # value = 0.5 * 200 + 0.5 * 100 = 150
        assert result == 150.0

    def test_low_alpha_smooths_more(self):
        """Lower alpha should smooth more aggressively."""
        ewma = EWMACalculator(alpha=0.1)
        ewma.update(100.0)
        # With alpha=0.1: 0.1 * 200 + 0.9 * 100 = 110
        result = ewma.update(200.0)
        assert result == 110.0

    def test_reset(self):
        """Reset should clear state."""
        ewma = EWMACalculator()
        ewma.update(100.0)
        ewma.reset()
        assert ewma.value == 0.0

    def test_handles_zero_samples(self):
        """Should handle zero values."""
        ewma = EWMACalculator()
        ewma.update(0.0)
        assert ewma.value == 0.0


class TestProgressState:
    """Tests for progress state tracking."""

    def test_initial_state(self):
        """Should initialize with correct defaults."""
        state = ProgressState(total_items=10)
        assert state.total_items == 10
        assert state.completed_items == 0
        assert state.failed_items == 0
        assert state.remaining_items == 10
        assert state.percent_complete == 0.0

    def test_start_item(self):
        """start_item should set current item and stage."""
        state = ProgressState(total_items=5)
        state.start_item("test.html")
        assert state.current_item == "test.html"
        assert state.current_stage == CaptureStage.INITIALIZING

    def test_set_stage(self):
        """set_stage should update current stage."""
        state = ProgressState(total_items=5)
        state.start_item("test.html")
        state.set_stage(CaptureStage.NAVIGATING)
        assert state.current_stage == CaptureStage.NAVIGATING

    def test_complete_item_success(self):
        """complete_item with success should increment completed."""
        state = ProgressState(total_items=5)
        state.start_item("test.html")
        state.complete_item(success=True)
        assert state.completed_items == 1
        assert state.failed_items == 0
        assert state.remaining_items == 4

    def test_complete_item_failure(self):
        """complete_item with failure should increment failed."""
        state = ProgressState(total_items=5)
        state.start_item("test.html")
        state.complete_item(success=False)
        assert state.completed_items == 0
        assert state.failed_items == 1
        assert state.remaining_items == 4

    def test_percent_complete_basic(self):
        """percent_complete should reflect completed items."""
        state = ProgressState(total_items=10)
        state.start_item("item1")
        state.complete_item(success=True)
        # 1/10 = 10%
        assert 9.5 <= state.percent_complete <= 10.5

    def test_percent_complete_with_failures(self):
        """percent_complete should count failures."""
        state = ProgressState(total_items=10)
        state.start_item("item1")
        state.complete_item(success=True)
        state.start_item("item2")
        state.complete_item(success=False)
        # 2 processed / 10 = 20%
        assert 19.5 <= state.percent_complete <= 20.5

    def test_eta_returns_none_initially(self):
        """ETA should be None before any items completed."""
        state = ProgressState(total_items=5)
        assert state.eta_seconds is None

    def test_elapsed_seconds(self):
        """elapsed_seconds should increase over time."""
        state = ProgressState(total_items=5)
        sleep(0.1)
        assert state.elapsed_seconds >= 0.1


class TestStageWeights:
    """Tests for stage weighting."""

    def test_weights_sum_to_100(self):
        """Stage weights should sum to 100."""
        total = sum(STAGE_WEIGHTS.values())
        assert total == 100

    def test_all_stages_have_weight(self):
        """All stages should have a weight defined."""
        for stage in CaptureStage:
            assert stage in STAGE_WEIGHTS


class TestFormatDuration:
    """Tests for duration formatting."""

    def test_less_than_second_short(self):
        """Sub-second should show '< 1s'."""
        assert format_duration(500, "short") == "< 1s"
        assert format_duration(0, "short") == "< 1s"

    def test_less_than_second_long(self):
        """Sub-second should show 'less than 1 second'."""
        assert format_duration(500, "long") == "less than 1 second"

    def test_negative_duration(self):
        """Negative duration should show 'now'."""
        assert format_duration(-1000, "short") == "now"
        assert format_duration(-1000, "long") == "now"

    def test_seconds_short(self):
        """Seconds should format correctly."""
        assert format_duration(5000, "short") == "5s"
        assert format_duration(45000, "short") == "45s"

    def test_minutes_short(self):
        """Minutes should format correctly."""
        assert format_duration(90000, "short") == "1m30s"
        assert format_duration(300000, "short") == "5m"

    def test_hours_short(self):
        """Hours should hide seconds."""
        assert format_duration(3700000, "short") == "1h1m"  # 1h 1m 40s -> 1h1m

    def test_days_short(self):
        """Days should format correctly."""
        ms = (2 * 86400 + 3 * 3600) * 1000  # 2 days 3 hours
        assert format_duration(ms, "short") == "2d3h"

    def test_seconds_long(self):
        """Long format seconds."""
        assert format_duration(1000, "long") == "1 second"
        assert format_duration(5000, "long") == "5 seconds"

    def test_minutes_long(self):
        """Long format minutes."""
        assert format_duration(60000, "long") == "1 minute"
        assert format_duration(150000, "long") == "2 minutes and 30 seconds"

    def test_hours_long(self):
        """Long format hours."""
        ms = 3600000 + 120000  # 1 hour 2 minutes
        assert format_duration(ms, "long") == "1 hour and 2 minutes"


class TestFormatThroughput:
    """Tests for throughput formatting."""

    def test_zero_throughput(self):
        """Zero should show placeholder."""
        assert format_throughput(0) == "-- B/s"
        assert format_throughput(-1) == "-- B/s"

    def test_bytes_per_second(self):
        """Small values should show B/s."""
        assert "B/s" in format_throughput(100)

    def test_kilobytes_per_second(self):
        """KB range should show KB/s."""
        assert "KB/s" in format_throughput(10 * 1024)

    def test_megabytes_per_second(self):
        """MB range should show MB/s."""
        assert "MB/s" in format_throughput(50 * 1024 * 1024)

    def test_gigabytes_per_second(self):
        """GB range should show GB/s."""
        assert "GB/s" in format_throughput(2 * 1024 * 1024 * 1024)


class TestFormatETA:
    """Tests for ETA formatting."""

    def test_none_eta(self):
        """None should show calculating."""
        assert format_eta(None) == "calculating..."

    def test_zero_eta(self):
        """Zero or negative should show finishing."""
        assert format_eta(0) == "finishing..."
        assert format_eta(-5) == "finishing..."

    def test_infinity_eta(self):
        """Infinity should show unknown."""
        assert format_eta(float("inf")) == "unknown"

    def test_normal_eta(self):
        """Normal values should format as duration."""
        eta = format_eta(90)  # 90 seconds
        assert "1m30s" in eta


class TestTruncateMiddle:
    """Tests for middle truncation."""

    def test_short_string_unchanged(self):
        """Short strings should not be truncated."""
        assert truncate_middle("short", 10) == "short"

    def test_exact_length_unchanged(self):
        """Strings at max length should not be truncated."""
        assert truncate_middle("12345", 5) == "12345"

    def test_truncates_long_string(self):
        """Long strings should be truncated with ellipsis."""
        result = truncate_middle("this_is_a_very_long_filename.html", 15)
        assert len(result) == 15
        assert "..." in result

    def test_preserves_start_and_end(self):
        """Truncation should preserve start and end."""
        result = truncate_middle("start_middle_end", 12)
        assert result.startswith("star")
        assert result.endswith("end")

    def test_very_short_max(self):
        """Very short max should still work."""
        result = truncate_middle("testing", 3)
        assert len(result) == 3
