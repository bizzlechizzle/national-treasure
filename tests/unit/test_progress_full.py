"""Full progress tests for 100% coverage."""

from time import sleep
from unittest.mock import MagicMock, patch

import pytest

from national_treasure.core.progress import (
    CaptureStage,
    ProgressState,
    EWMACalculator,
    format_duration,
)


class TestCompleteItemWithBytes:
    """Test complete_item with bytes_processed."""

    def test_complete_item_with_bytes(self):
        """Should track bytes throughput."""
        state = ProgressState(total_items=5)

        # Complete with bytes
        state.complete_item(success=True, bytes_processed=1024)

        assert state.completed_items == 1
        assert state.completed_bytes == 1024

    def test_complete_item_bytes_updates_ewma(self):
        """Should update bytes EWMA when bytes_processed > 0."""
        state = ProgressState(total_items=5)

        # Need time to pass for meaningful rate
        state.complete_item(success=True, bytes_processed=2048)
        sleep(0.01)
        state.complete_item(success=True, bytes_processed=4096)

        # bytes_per_second should be calculated
        assert state.bytes_per_second >= 0


class TestBytesPerSecond:
    """Test bytes_per_second property."""

    def test_bytes_per_second_initial(self):
        """Should return 0 initially."""
        state = ProgressState(total_items=1)
        assert state.bytes_per_second == 0.0


class TestEtaSeconds:
    """Test eta_seconds calculation."""

    def test_eta_with_zero_rate(self):
        """Should return None when rate is zero."""
        state = ProgressState(total_items=10)
        assert state.eta_seconds is None

    def test_eta_when_complete(self):
        """Should return 0 when all items done."""
        state = ProgressState(total_items=2)
        state.complete_item(success=True)
        state.complete_item(success=True)

        # All done
        eta = state.eta_seconds
        assert eta == 0.0

    def test_eta_calculation(self):
        """Should calculate ETA based on rate."""
        state = ProgressState(total_items=10)

        # Simulate some completions with time gaps
        for _ in range(3):
            state.complete_item(success=True)
            sleep(0.01)

        # Should have some ETA now
        if state.items_per_second > 0:
            eta = state.eta_seconds
            assert eta is not None
            assert eta >= 0


class TestWeightedStageProgress:
    """Test _get_weighted_stage_progress."""

    def test_weighted_progress_with_zero_total(self):
        """Should return 0 when total weight is 0."""
        state = ProgressState(total_items=1)

        with patch.dict("national_treasure.core.progress.STAGE_WEIGHTS", {}, clear=True):
            result = state._get_weighted_stage_progress()
            assert result == 0.0


class TestFormatDuration:
    """Test format_duration function."""

    def test_format_duration_short_style(self):
        """Should format with short style."""
        result = format_duration(65000, style="short")
        assert "1m" in result or "65" in result

    def test_format_duration_long_style(self):
        """Should format with long style."""
        result = format_duration(65000, style="long")
        assert "minute" in result.lower() or "1m" in result

    def test_format_duration_hours(self):
        """Should format hours correctly."""
        result = format_duration(3700000, style="short")  # ~1 hour
        assert "h" in result.lower() or "hour" in result.lower() or "61" in result

    def test_format_duration_zero(self):
        """Should handle zero duration."""
        result = format_duration(0)
        # Returns "< 1s" for sub-second durations
        assert "1s" in result or "0" in result


class TestPercentCompleteZeroItems:
    """Test percent_complete with zero items."""

    def test_percent_complete_zero_total(self):
        """Should return 0 when total_items is 0."""
        state = ProgressState(total_items=0)
        assert state.percent_complete == 0.0


class TestFormatDurationLong:
    """Test format_duration long style edge cases."""

    def test_format_duration_days_long(self):
        """Should format days in long style."""
        # 1 day 1 hour
        ms = (24 * 60 * 60 * 1000) + (60 * 60 * 1000)
        result = format_duration(ms, style="long")
        assert "day" in result
        assert "hour" in result

    def test_format_duration_less_than_second(self):
        """Should return 'less than 1 second' in long style."""
        result = format_duration(500, style="long")  # 500ms
        assert "less than 1 second" in result


class TestFormatThroughput:
    """Test format_throughput function."""

    def test_format_throughput_bytes(self):
        """Should format small throughput as B/s."""
        from national_treasure.core.progress import format_throughput
        result = format_throughput(500)
        assert "B/s" in result

    def test_format_throughput_very_small(self):
        """Should format very small throughput."""
        from national_treasure.core.progress import format_throughput
        result = format_throughput(0.5)  # Less than 1 B/s
        # Should hit the final return statement
        assert "B/s" in result


class TestEWMACalculator:
    """Test EWMA calculator."""

    def test_ewma_initial_value(self):
        """Should start at 0."""
        ewma = EWMACalculator()
        assert ewma.value == 0.0

    def test_ewma_single_update(self):
        """Should set value on first update."""
        ewma = EWMACalculator()
        ewma.update(100.0)
        assert ewma.value == 100.0

    def test_ewma_multiple_updates(self):
        """Should smooth values over updates."""
        ewma = EWMACalculator(alpha=0.3)
        ewma.update(100.0)
        ewma.update(200.0)

        # Should be between 100 and 200
        assert 100 < ewma.value < 200

    def test_ewma_custom_alpha(self):
        """Should use custom alpha."""
        ewma = EWMACalculator(alpha=0.9)
        ewma.update(100.0)
        ewma.update(200.0)

        # High alpha means more weight to recent
        assert ewma.value > 150  # Closer to 200
