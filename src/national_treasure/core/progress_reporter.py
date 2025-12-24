"""Progress Reporter - Reports progress to orchestrator via Unix socket.

Enables bidirectional communication:
- Worker sends progress updates, stage changes, completion
- Orchestrator sends control commands: pause, resume, cancel

Falls back to standalone mode if no socket configured.
"""

import json
import os
import socket
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

# App identification
APP_NAME = "national-treasure"
APP_VERSION = "0.1.0"

# Stage definitions for national-treasure (10 stages)
CAPTURE_STAGES = {
    "initializing": {"name": "initializing", "display_name": "Browser startup", "number": 1, "total_stages": 10, "weight": 2},
    "navigating": {"name": "navigating", "display_name": "Loading page", "number": 2, "total_stages": 10, "weight": 25},
    "waiting": {"name": "waiting", "display_name": "Network idle", "number": 3, "total_stages": 10, "weight": 15},
    "behaviors": {"name": "behaviors", "display_name": "Expanding content", "number": 4, "total_stages": 10, "weight": 20},
    "validating": {"name": "validating", "display_name": "Checking response", "number": 5, "total_stages": 10, "weight": 3},
    "screenshot": {"name": "screenshot", "display_name": "Taking screenshot", "number": 6, "total_stages": 10, "weight": 10},
    "pdf": {"name": "pdf", "display_name": "Generating PDF", "number": 7, "total_stages": 10, "weight": 10},
    "html": {"name": "html", "display_name": "Saving HTML", "number": 8, "total_stages": 10, "weight": 5},
    "warc": {"name": "warc", "display_name": "Writing archive", "number": 9, "total_stages": 10, "weight": 8},
    "learning": {"name": "learning", "display_name": "Updating model", "number": 10, "total_stages": 10, "weight": 2},
}


@dataclass
class ProgressData:
    """Progress update data."""
    completed: int
    total: int
    failed: int = 0
    skipped: int = 0
    current_item: str | None = None
    percent_complete: float = 0.0
    eta_ms: int | None = None


class ProgressReporter:
    """Report progress to orchestrator via Unix socket."""

    def __init__(self):
        self.socket: socket.socket | None = None
        self._paused = False
        self._cancelled = False
        self._connected = False
        self._listeners: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()
        self.session_id = os.environ.get("PROGRESS_SESSION_ID", "")
        self.started_at = time.time()

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        """Connect to orchestrator socket. Returns False for standalone mode."""
        socket_path = os.environ.get("PROGRESS_SOCKET")
        if not socket_path:
            return False

        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(socket_path)
            self._connected = True
            threading.Thread(target=self._listen, daemon=True).start()
            return True
        except Exception:
            return False

    def _listen(self) -> None:
        """Listen for control commands from orchestrator."""
        if not self.socket:
            return
        buffer = ""
        while self._connected:
            try:
                data = self.socket.recv(4096).decode()
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    msg = json.loads(line)
                    if msg.get("type") == "control":
                        self._handle_control(msg)
            except Exception:
                break

    def _handle_control(self, msg: dict) -> None:
        """Handle control commands: pause, resume, cancel."""
        cmd = msg.get("command")
        with self._lock:
            if cmd == "pause":
                self._paused = True
                self._send_ack("pause", "accepted")
                self._emit("pause")
            elif cmd == "resume":
                self._paused = False
                self._send_ack("resume", "accepted")
                self._emit("resume")
            elif cmd == "cancel":
                self._cancelled = True
                self._send_ack("cancel", "accepted")
                self._emit("cancel", msg.get("reason"))

    def _send_ack(self, command: str, status: str) -> None:
        self.send({"type": "ack", "command": command, "status": status})

    def _emit(self, event: str, *args) -> None:
        for callback in self._listeners.get(event, []):
            try:
                callback(*args)
            except Exception:
                pass

    def on(self, event: str, callback: Callable) -> None:
        """Register event listener: 'pause', 'resume', 'cancel'."""
        self._listeners.setdefault(event, []).append(callback)

    def send(self, message: dict) -> None:
        """Send message to orchestrator."""
        if not self.socket or not self._connected:
            return

        full_msg = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "app": APP_NAME,
            "app_version": APP_VERSION,
            **message,
        }
        try:
            self.socket.sendall((json.dumps(full_msg) + "\n").encode())
        except Exception:
            pass

    def stage_started(self, stage_name: str) -> None:
        """Notify stage started."""
        stage = CAPTURE_STAGES.get(stage_name, {})
        self.send({
            "type": "stage_started",
            "stage": {
                "name": stage.get("name", stage_name),
                "display_name": stage.get("display_name", stage_name),
                "number": stage.get("number", 0),
                "total_stages": stage.get("total_stages", 10),
            },
        })

    def stage_completed(self, stage_name: str, duration_ms: int, items_processed: int = 1) -> None:
        """Notify stage completed."""
        stage = CAPTURE_STAGES.get(stage_name, {})
        self.send({
            "type": "stage_completed",
            "stage": {"name": stage.get("name", stage_name), "number": stage.get("number", 0)},
            "duration_ms": duration_ms,
            "items_processed": items_processed,
        })

    def progress(self, stage_name: str, data: ProgressData) -> None:
        """Send progress update."""
        stage = CAPTURE_STAGES.get(stage_name, {})
        elapsed_ms = int((time.time() - self.started_at) * 1000)

        self.send({
            "type": "progress",
            "stage": {
                "name": stage.get("name", stage_name),
                "display_name": stage.get("display_name", stage_name),
                "number": stage.get("number", 0),
                "total_stages": stage.get("total_stages", 10),
                "weight": stage.get("weight", 0),
            },
            "items": {
                "total": data.total,
                "completed": data.completed,
                "failed": data.failed,
                "skipped": data.skipped,
            },
            "current": {
                "item": data.current_item,
                "item_short": data.current_item[:50] + "..." if data.current_item and len(data.current_item) > 50 else data.current_item,
            },
            "timing": {
                "started_at": datetime.fromtimestamp(self.started_at, timezone.utc).isoformat(),
                "elapsed_ms": elapsed_ms,
                "eta_ms": data.eta_ms,
            },
            "percent_complete": data.percent_complete,
        })

    def complete(
        self,
        total_items: int,
        successful: int,
        failed: int,
        skipped: int,
        duration_ms: int,
    ) -> None:
        """Send completion message."""
        self.send({
            "type": "complete",
            "summary": {
                "total_items": total_items,
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "duration_ms": duration_ms,
            },
            "exit_code": 1 if failed > 0 else 0,
        })

    def wait_while_paused(self) -> None:
        """Block while paused."""
        while self._paused and not self._cancelled:
            time.sleep(0.1)

    def should_continue(self) -> bool:
        """Check if should continue processing."""
        return not self._cancelled

    def reset_start_time(self) -> None:
        """Reset start time."""
        self.started_at = time.time()

    def close(self) -> None:
        """Close socket connection."""
        self._connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass


# Module-level singleton
_reporter: ProgressReporter | None = None


def get_progress_reporter() -> ProgressReporter:
    """Get or create progress reporter instance."""
    global _reporter
    if _reporter is None:
        _reporter = ProgressReporter()
    return _reporter
