"""CLI progress tracking with EWMA-smoothed ETA estimation.

Implements patterns from CLI Progress Tracking SME document:
- EWMA throughput smoothing (alpha=0.15)
- Weighted multi-stage progress
- Human-readable time formatting
- ETA calculation with stability
"""

from dataclasses import dataclass, field
from enum import Enum
from time import time


class CaptureStage(str, Enum):
    """Capture pipeline stages with weights."""

    INITIALIZING = "initializing"
    NAVIGATING = "navigating"
    WAITING = "waiting"
    BEHAVIORS = "behaviors"
    VALIDATING = "validating"
    SCREENSHOT = "screenshot"
    PDF = "pdf"
    HTML = "html"
    WARC = "warc"
    LEARNING = "learning"
    COMPLETE = "complete"


# Step weights based on typical execution time
# Values sum to 100 for easy percentage calculation
STAGE_WEIGHTS: dict[CaptureStage, int] = {
    CaptureStage.INITIALIZING: 2,
    CaptureStage.NAVIGATING: 25,
    CaptureStage.WAITING: 15,
    CaptureStage.BEHAVIORS: 20,
    CaptureStage.VALIDATING: 3,
    CaptureStage.SCREENSHOT: 10,
    CaptureStage.PDF: 10,
    CaptureStage.HTML: 5,
    CaptureStage.WARC: 8,
    CaptureStage.LEARNING: 2,
    CaptureStage.COMPLETE: 0,
}


@dataclass
class EWMACalculator:
    """Exponential Weighted Moving Average for throughput smoothing.

    Uses alpha=0.15 by default (equivalent to ~12 sample window).
    """

    alpha: float = 0.15
    _value: float = 0.0
    _initialized: bool = False

    def update(self, sample: float) -> float:
        """Update EWMA with new sample, return smoothed value."""
        if not self._initialized:
            self._value = sample
            self._initialized = True
        else:
            self._value = self.alpha * sample + (1 - self.alpha) * self._value
        return self._value

    @property
    def value(self) -> float:
        """Current smoothed value."""
        return self._value

    def reset(self) -> None:
        """Reset calculator state."""
        self._value = 0.0
        self._initialized = False


@dataclass
class ProgressState:
    """Track progress for batch operations with ETA."""

    # Counts
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0

    # Bytes (optional)
    total_bytes: int = 0
    completed_bytes: int = 0

    # Current item
    current_item: str = ""
    current_stage: CaptureStage = CaptureStage.INITIALIZING
    current_stage_progress: float = 0.0  # 0-100 within stage

    # Timing
    started_at: float = field(default_factory=time)
    _last_update: float = field(default_factory=time)

    # Throughput (EWMA smoothed)
    _items_ewma: EWMACalculator = field(default_factory=EWMACalculator)
    _bytes_ewma: EWMACalculator = field(default_factory=EWMACalculator)

    # Stage tracking for current item
    _completed_stages: list[CaptureStage] = field(default_factory=list)

    def start_item(self, item: str) -> None:
        """Begin processing a new item."""
        self.current_item = item
        self.current_stage = CaptureStage.INITIALIZING
        self.current_stage_progress = 0.0
        self._completed_stages = []
        self._last_update = time()

    def set_stage(self, stage: CaptureStage, progress: float = 0.0) -> None:
        """Update current stage and progress within stage."""
        if self.current_stage != stage:
            # Mark previous stage as complete
            if self.current_stage not in self._completed_stages:
                self._completed_stages.append(self.current_stage)
            self.current_stage = stage
        self.current_stage_progress = min(100.0, max(0.0, progress))

    def complete_item(self, success: bool = True, bytes_processed: int = 0) -> None:
        """Mark current item as complete."""
        now = time()
        elapsed = now - self._last_update

        if success:
            self.completed_items += 1
            if bytes_processed > 0:
                self.completed_bytes += bytes_processed
                # Update bytes throughput
                if elapsed > 0:
                    self._bytes_ewma.update(bytes_processed / elapsed)
        else:
            self.failed_items += 1

        # Update items throughput
        if elapsed > 0:
            self._items_ewma.update(1.0 / elapsed)

        self.current_stage = CaptureStage.COMPLETE
        self._completed_stages = []
        self._last_update = now

    @property
    def items_per_second(self) -> float:
        """EWMA-smoothed items per second."""
        return self._items_ewma.value

    @property
    def bytes_per_second(self) -> float:
        """EWMA-smoothed bytes per second."""
        return self._bytes_ewma.value

    @property
    def elapsed_seconds(self) -> float:
        """Total elapsed time in seconds."""
        return time() - self.started_at

    @property
    def remaining_items(self) -> int:
        """Items remaining to process."""
        return max(0, self.total_items - self.completed_items - self.failed_items)

    @property
    def eta_seconds(self) -> float | None:
        """Estimated seconds remaining, or None if unknown."""
        if self.items_per_second <= 0:
            return None
        if self.remaining_items <= 0:
            return 0.0
        return self.remaining_items / self.items_per_second

    @property
    def percent_complete(self) -> float:
        """Overall percentage complete (0-100)."""
        if self.total_items <= 0:
            return 0.0

        # Base progress from completed items
        items_done = self.completed_items + self.failed_items
        base_percent = (items_done / self.total_items) * 100

        # Add partial progress from current item using stage weights
        if self.remaining_items > 0 and self.current_item:
            item_weight = 100.0 / self.total_items
            stage_percent = self._get_weighted_stage_progress()
            base_percent += (stage_percent / 100.0) * item_weight

        return min(100.0, base_percent)

    def _get_weighted_stage_progress(self) -> float:
        """Get weighted progress through current item's stages."""
        total_weight = sum(STAGE_WEIGHTS.values())
        if total_weight == 0:
            return 0.0

        # Sum completed stage weights
        completed_weight = sum(
            STAGE_WEIGHTS.get(stage, 0) for stage in self._completed_stages
        )

        # Add partial current stage
        current_weight = STAGE_WEIGHTS.get(self.current_stage, 0)
        partial = current_weight * (self.current_stage_progress / 100.0)

        return ((completed_weight + partial) / total_weight) * 100


def format_duration(ms: float, style: str = "short") -> str:
    """Format milliseconds as human-readable duration.

    Args:
        ms: Duration in milliseconds
        style: 'short' (2m30s) or 'long' (2 minutes and 30 seconds)

    Returns:
        Formatted duration string
    """
    if ms < 0:
        return "now" if style == "short" else "now"
    if ms < 1000:
        return "< 1s" if style == "short" else "less than 1 second"

    seconds = int(ms / 1000) % 60
    minutes = int(ms / 60000) % 60
    hours = int(ms / 3600000) % 24
    days = int(ms / 86400000)

    if style == "short":
        parts: list[str] = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        # Hide seconds for durations >= 1 hour
        if seconds > 0 and hours == 0:
            parts.append(f"{seconds}s")
        return "".join(parts) or "< 1s"

    # Long format
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    # Hide seconds for durations >= 1 hour
    if seconds > 0 and hours == 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    if not parts:
        return "less than 1 second"
    if len(parts) == 1:
        return parts[0]

    last = parts.pop()
    return f"{', '.join(parts)} and {last}"


def format_throughput(bytes_per_sec: float) -> str:
    """Format bytes/second as human-readable throughput."""
    if bytes_per_sec <= 0:
        return "-- B/s"

    units = [("B/s", 1), ("KB/s", 1024), ("MB/s", 1024**2), ("GB/s", 1024**3)]

    for unit, divisor in reversed(units):
        if bytes_per_sec >= divisor:
            value = bytes_per_sec / divisor
            if value >= 100:
                return f"{value:.0f} {unit}"
            elif value >= 10:
                return f"{value:.1f} {unit}"
            else:
                return f"{value:.2f} {unit}"

    return f"{bytes_per_sec:.0f} B/s"


def format_eta(seconds: float | None) -> str:
    """Format ETA for display."""
    if seconds is None:
        return "calculating..."
    if seconds <= 0:
        return "finishing..."
    if seconds == float("inf"):
        return "unknown"
    return format_duration(seconds * 1000, style="short")


def truncate_middle(text: str, max_len: int) -> str:
    """Truncate text in the middle, preserving start and end."""
    if len(text) <= max_len:
        return text
    if max_len < 5:
        return text[:max_len]

    keep = (max_len - 3) // 2
    return f"{text[:keep]}...{text[-keep:]}"
