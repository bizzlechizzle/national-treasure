"""
Progress Reporter Tests for national-treasure

Tests for Unix socket-based progress reporting.
"""

import json
import os
import socket
import sys
import tempfile
import threading
import time
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Direct file import to avoid conftest dependency chain issues
_module_path = Path(__file__).parent.parent / "src" / "national_treasure" / "core" / "progress_reporter.py"
_spec = importlib.util.spec_from_file_location("progress_reporter", _module_path)
_module = importlib.util.module_from_spec(_spec)
sys.modules["progress_reporter"] = _module
_spec.loader.exec_module(_module)

CAPTURE_STAGES = _module.CAPTURE_STAGES
ProgressData = _module.ProgressData
ProgressReporter = _module.ProgressReporter
get_progress_reporter = _module.get_progress_reporter


class TestCaptureStages:
    """Test stage definitions."""

    def test_stage_weights_sum_to_100(self):
        """Stage weights should sum to 100."""
        total_weight = sum(s["weight"] for s in CAPTURE_STAGES.values())
        assert total_weight == 100

    def test_all_stages_defined(self):
        """All expected stages should be defined."""
        expected = [
            "initializing", "navigating", "waiting", "behaviors",
            "validating", "screenshot", "pdf", "html", "warc", "learning"
        ]
        for stage in expected:
            assert stage in CAPTURE_STAGES, f"Missing stage: {stage}"

    def test_stages_have_sequential_numbers(self):
        """Stages should have sequential numbers 1-10."""
        numbers = [s["number"] for s in CAPTURE_STAGES.values()]
        assert sorted(numbers) == list(range(1, 11))

    def test_all_stages_have_total_10(self):
        """All stages should report total_stages = 10."""
        for stage in CAPTURE_STAGES.values():
            assert stage["total_stages"] == 10


class TestProgressReporter:
    """Test ProgressReporter class."""

    @pytest.fixture
    def socket_server(self):
        """Create a mock socket server."""
        import shutil
        tmp_dir = tempfile.mkdtemp(prefix="nt-", dir="/tmp")
        socket_path = os.path.join(tmp_dir, "p.sock")
        messages = []
        server_conn = {"socket": None}

        def accept_connection(server_socket):
            try:
                conn, _ = server_socket.accept()
                server_conn["socket"] = conn
                buffer = ""
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break
                    buffer += data.decode()
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line:
                            messages.append(json.loads(line))
            except Exception:
                pass

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(socket_path)
        server.listen(1)

        thread = threading.Thread(target=accept_connection, args=(server,))
        thread.daemon = True
        thread.start()

        yield {
            "path": socket_path,
            "messages": messages,
            "server_conn": server_conn,
            "server": server,
            "tmp_dir": tmp_dir,
        }

        server.close()
        shutil.rmtree(tmp_dir, ignore_errors=True)

    @pytest.fixture
    def reporter_with_socket(self, socket_server):
        """Create reporter connected to mock socket."""
        os.environ["PROGRESS_SOCKET"] = socket_server["path"]
        os.environ["PROGRESS_SESSION_ID"] = "nt-test-session"

        reporter = ProgressReporter()
        connected = reporter.connect()
        time.sleep(0.05)

        yield reporter, socket_server

        reporter.close()
        del os.environ["PROGRESS_SOCKET"]
        del os.environ["PROGRESS_SESSION_ID"]

    def test_connect_with_socket(self, reporter_with_socket):
        """Should connect when PROGRESS_SOCKET is set."""
        reporter, _ = reporter_with_socket
        assert reporter.is_connected

    def test_connect_without_socket(self):
        """Should return False when PROGRESS_SOCKET not set."""
        if "PROGRESS_SOCKET" in os.environ:
            del os.environ["PROGRESS_SOCKET"]

        reporter = ProgressReporter()
        assert not reporter.connect()
        assert not reporter.is_connected

    def test_send_message_format(self, reporter_with_socket):
        """Messages should include required fields."""
        reporter, socket_server = reporter_with_socket

        reporter.send({"type": "test", "custom": "data"})
        time.sleep(0.1)

        assert len(socket_server["messages"]) >= 1
        msg = socket_server["messages"][-1]

        assert msg["type"] == "test"
        assert msg["custom"] == "data"
        assert "timestamp" in msg
        assert msg["session_id"] == "nt-test-session"
        assert msg["app"] == "national-treasure"
        assert "app_version" in msg

    def test_stage_started_initializing(self, reporter_with_socket):
        """Should send stage_started message for initializing stage."""
        reporter, socket_server = reporter_with_socket

        reporter.stage_started("initializing")
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert msg["type"] == "stage_started"
        assert msg["stage"]["name"] == "initializing"
        assert msg["stage"]["display_name"] == "Browser startup"
        assert msg["stage"]["number"] == 1
        assert msg["stage"]["total_stages"] == 10

    def test_stage_started_behaviors(self, reporter_with_socket):
        """Should send stage_started for behaviors stage."""
        reporter, socket_server = reporter_with_socket

        reporter.stage_started("behaviors")
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert msg["stage"]["name"] == "behaviors"
        assert msg["stage"]["display_name"] == "Expanding content"
        assert msg["stage"]["number"] == 4

    def test_stage_completed(self, reporter_with_socket):
        """Should send stage_completed message."""
        reporter, socket_server = reporter_with_socket

        reporter.stage_completed("screenshot", 2500, 1)
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert msg["type"] == "stage_completed"
        assert msg["stage"]["name"] == "screenshot"
        assert msg["stage"]["number"] == 6
        assert msg["duration_ms"] == 2500
        assert msg["items_processed"] == 1

    def test_progress(self, reporter_with_socket):
        """Should send progress message with all fields."""
        reporter, socket_server = reporter_with_socket
        reporter.reset_start_time()

        data = ProgressData(
            completed=5,
            total=10,
            failed=1,
            skipped=0,
            current_item="https://example.com/page",
            percent_complete=50.0,
            eta_ms=15000,
        )

        reporter.progress("navigating", data)
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert msg["type"] == "progress"
        assert msg["stage"]["name"] == "navigating"
        assert msg["stage"]["display_name"] == "Loading page"
        assert msg["stage"]["weight"] == 25
        assert msg["items"]["completed"] == 5
        assert msg["items"]["total"] == 10
        assert msg["items"]["failed"] == 1
        assert msg["items"]["skipped"] == 0
        assert msg["current"]["item"] == "https://example.com/page"
        assert msg["timing"]["eta_ms"] == 15000
        assert msg["percent_complete"] == 50.0

    def test_progress_item_short_truncation(self, reporter_with_socket):
        """Should truncate long URLs in item_short."""
        reporter, socket_server = reporter_with_socket
        reporter.reset_start_time()

        long_url = "https://example.com/very/long/path/that/exceeds/fifty/characters/and/should/be/truncated"
        data = ProgressData(
            completed=1,
            total=1,
            current_item=long_url,
            percent_complete=100.0,
        )

        reporter.progress("navigating", data)
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert len(msg["current"]["item_short"]) == 53  # 50 + "..."
        assert msg["current"]["item_short"].endswith("...")

    def test_complete_with_failures(self, reporter_with_socket):
        """Complete message with failures should have exit_code 1."""
        reporter, socket_server = reporter_with_socket

        reporter.complete(
            total_items=10,
            successful=8,
            failed=2,
            skipped=0,
            duration_ms=120000,
        )
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert msg["type"] == "complete"
        assert msg["summary"]["total_items"] == 10
        assert msg["summary"]["successful"] == 8
        assert msg["summary"]["failed"] == 2
        assert msg["summary"]["skipped"] == 0
        assert msg["summary"]["duration_ms"] == 120000
        assert msg["exit_code"] == 1

    def test_complete_success(self, reporter_with_socket):
        """Complete message without failures should have exit_code 0."""
        reporter, socket_server = reporter_with_socket

        reporter.complete(
            total_items=10,
            successful=10,
            failed=0,
            skipped=0,
            duration_ms=60000,
        )
        time.sleep(0.1)

        msg = socket_server["messages"][-1]
        assert msg["exit_code"] == 0


class TestControlCommands:
    """Test control command handling."""

    @pytest.fixture
    def bidirectional_socket(self):
        """Create a bidirectional socket."""
        import shutil
        tmp_dir = tempfile.mkdtemp(prefix="nt-", dir="/tmp")
        socket_path = os.path.join(tmp_dir, "p.sock")
        messages = []
        client_conn = {"socket": None}

        def accept_connection(server_socket):
            try:
                conn, _ = server_socket.accept()
                client_conn["socket"] = conn
                buffer = ""
                while True:
                    try:
                        data = conn.recv(4096)
                        if not data:
                            break
                        buffer += data.decode()
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line:
                                messages.append(json.loads(line))
                    except Exception:
                        break
            except Exception:
                pass

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(socket_path)
        server.listen(1)

        thread = threading.Thread(target=accept_connection, args=(server,))
        thread.daemon = True
        thread.start()

        os.environ["PROGRESS_SOCKET"] = socket_path
        os.environ["PROGRESS_SESSION_ID"] = "nt-ctrl-test"

        reporter = ProgressReporter()
        reporter.connect()
        time.sleep(0.05)

        yield {
            "reporter": reporter,
            "messages": messages,
            "client_conn": client_conn,
            "server": server,
            "tmp_dir": tmp_dir,
        }

        reporter.close()
        server.close()
        del os.environ["PROGRESS_SOCKET"]
        del os.environ["PROGRESS_SESSION_ID"]
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_pause_command(self, bidirectional_socket):
        """Should handle pause command."""
        reporter = bidirectional_socket["reporter"]
        client_conn = bidirectional_socket["client_conn"]

        pause_called = threading.Event()
        reporter.on("pause", lambda: pause_called.set())

        client_conn["socket"].sendall(
            (json.dumps({"type": "control", "command": "pause"}) + "\n").encode()
        )
        time.sleep(0.1)

        assert reporter.paused
        assert pause_called.is_set()

    def test_resume_command(self, bidirectional_socket):
        """Should handle resume command."""
        reporter = bidirectional_socket["reporter"]
        client_conn = bidirectional_socket["client_conn"]

        # Pause first
        client_conn["socket"].sendall(
            (json.dumps({"type": "control", "command": "pause"}) + "\n").encode()
        )
        time.sleep(0.1)
        assert reporter.paused

        # Resume
        client_conn["socket"].sendall(
            (json.dumps({"type": "control", "command": "resume"}) + "\n").encode()
        )
        time.sleep(0.1)

        assert not reporter.paused

    def test_cancel_command(self, bidirectional_socket):
        """Should handle cancel command."""
        reporter = bidirectional_socket["reporter"]
        client_conn = bidirectional_socket["client_conn"]

        cancel_reason = None

        def on_cancel(reason):
            nonlocal cancel_reason
            cancel_reason = reason

        reporter.on("cancel", on_cancel)

        client_conn["socket"].sendall(
            (json.dumps({
                "type": "control",
                "command": "cancel",
                "reason": "Timeout exceeded"
            }) + "\n").encode()
        )
        time.sleep(0.1)

        assert reporter.cancelled
        assert cancel_reason == "Timeout exceeded"
        assert not reporter.should_continue()


class TestStandaloneMode:
    """Test operation without socket."""

    def test_standalone_operation(self):
        """Should operate silently without socket."""
        if "PROGRESS_SOCKET" in os.environ:
            del os.environ["PROGRESS_SOCKET"]

        reporter = ProgressReporter()

        # Should not throw
        reporter.send({"type": "test"})
        reporter.stage_started("navigating")
        reporter.progress("navigating", ProgressData(
            completed=1,
            total=1,
            percent_complete=100.0,
        ))
        reporter.complete(
            total_items=1,
            successful=1,
            failed=0,
            skipped=0,
            duration_ms=5000,
        )

        assert not reporter.is_connected


class TestGetProgressReporter:
    """Test singleton behavior."""

    def test_returns_same_instance(self):
        """get_progress_reporter should return same instance."""
        reporter1 = get_progress_reporter()
        reporter2 = get_progress_reporter()
        assert reporter1 is reporter2
