"""Comprehensive CLI tests for National Treasure."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from national_treasure.cli.main import app


runner = CliRunner()


class TestVersionCommand:
    """Test version display."""

    def test_version_flag(self):
        """Should display version with --version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "national-treasure v" in result.output

    def test_version_short_flag(self):
        """Should display version with -v."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "national-treasure v" in result.output


class TestMainApp:
    """Test main app commands."""

    def test_no_args_shows_help(self):
        """Should show help when no args provided."""
        # no_args_is_help=True causes exit code 0
        result = runner.invoke(app, [])
        # Typer shows help and exits with 0 when no_args_is_help=True
        assert "National Treasure" in result.output or result.exit_code == 0

    def test_help_flag(self):
        """Should show help with --help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "capture" in result.output
        assert "queue" in result.output
        assert "training" in result.output


class TestConfigCommand:
    """Test config command."""

    def test_show_config(self, tmp_path, monkeypatch):
        """Should show current configuration."""
        # Mock config
        mock_config = MagicMock()
        mock_config.database_path = tmp_path / "test.db"
        mock_config.archive_dir = tmp_path / "archives"
        mock_config.log_level = "INFO"

        with patch("national_treasure.cli.main.get_config", return_value=mock_config):
            result = runner.invoke(app, ["config"])
            assert result.exit_code == 0
            assert "Configuration" in result.output
            assert "Database" in result.output


class TestCaptureCommands:
    """Test capture sub-commands."""

    def test_capture_url_success(self, tmp_path):
        """Should capture a URL successfully."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.screenshot_path = tmp_path / "screenshot.png"
        mock_result.pdf_path = None
        mock_result.html_path = tmp_path / "page.html"
        mock_result.warc_path = None
        mock_result.duration_ms = 1500

        mock_service = MagicMock()
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_service.capture = AsyncMock(return_value=mock_result)

        with patch("national_treasure.services.capture.service.CaptureService", return_value=mock_service):
            with patch("national_treasure.core.config.get_config") as mock_config:
                mock_config.return_value = MagicMock(archive_dir=tmp_path)
                result = runner.invoke(app, ["capture", "url", "https://example.com"])
                assert result.exit_code == 0
                assert "Success" in result.output

    def test_capture_url_failure(self, tmp_path):
        """Should handle capture failure."""
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Connection refused"
        mock_result.validation = MagicMock(blocked=True, reason="timeout")

        mock_service = MagicMock()
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_service.capture = AsyncMock(return_value=mock_result)

        with patch("national_treasure.services.capture.service.CaptureService", return_value=mock_service):
            with patch("national_treasure.core.config.get_config") as mock_config:
                mock_config.return_value = MagicMock(archive_dir=tmp_path)
                result = runner.invoke(app, ["capture", "url", "https://example.com"])
                assert result.exit_code == 1
                assert "Failed" in result.output

    def test_capture_batch_file_not_found(self):
        """Should error when batch file not found."""
        result = runner.invoke(app, ["capture", "batch", "/nonexistent/file.txt"])
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_capture_batch_empty_file(self, tmp_path):
        """Should handle empty URL file."""
        url_file = tmp_path / "urls.txt"
        url_file.write_text("")

        result = runner.invoke(app, ["capture", "batch", str(url_file)])
        assert result.exit_code == 0
        assert "No URLs found" in result.output

    def test_capture_batch_success(self, tmp_path):
        """Should process batch file successfully."""
        url_file = tmp_path / "urls.txt"
        url_file.write_text("https://example.com\nhttps://test.com\n")

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.validation = MagicMock(http_status=200)

        mock_service = MagicMock()
        mock_service.__aenter__ = AsyncMock(return_value=mock_service)
        mock_service.__aexit__ = AsyncMock(return_value=None)
        mock_service.capture = AsyncMock(return_value=mock_result)

        mock_learner = MagicMock()
        mock_learner.get_best_config = AsyncMock(return_value={})
        mock_learner.record_outcome = AsyncMock()

        with patch("national_treasure.services.capture.service.CaptureService", return_value=mock_service):
            with patch("national_treasure.services.learning.domain.DomainLearner", return_value=mock_learner):
                result = runner.invoke(app, ["capture", "batch", str(url_file)])
                assert result.exit_code == 0
                assert "Completed" in result.output


class TestQueueCommands:
    """Test queue sub-commands."""

    def test_queue_add(self):
        """Should add job to queue."""
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(return_value="job-123")

        with patch("national_treasure.services.queue.service.JobQueue", return_value=mock_queue):
            result = runner.invoke(app, ["queue", "add", "https://example.com"])
            assert result.exit_code == 0
            assert "Queued" in result.output
            assert "job-123" in result.output

    def test_queue_add_with_priority(self):
        """Should add job with priority."""
        mock_queue = MagicMock()
        mock_queue.enqueue = AsyncMock(return_value="job-456")

        with patch("national_treasure.services.queue.service.JobQueue", return_value=mock_queue):
            result = runner.invoke(app, ["queue", "add", "https://example.com", "-p", "5"])
            assert result.exit_code == 0

    def test_queue_status(self):
        """Should show queue status."""
        mock_queue = MagicMock()
        mock_queue.get_queue_stats = AsyncMock(return_value={
            "pending": 5,
            "running": 2,
            "completed": 10,
            "failed": 1,
        })

        with patch("national_treasure.services.queue.service.JobQueue", return_value=mock_queue):
            result = runner.invoke(app, ["queue", "status"])
            assert result.exit_code == 0
            assert "Queue Status" in result.output
            assert "pending" in result.output

    def test_queue_dead_letter_empty(self):
        """Should handle empty dead letter queue."""
        mock_queue = MagicMock()
        mock_queue.get_dead_letter_jobs = AsyncMock(return_value=[])

        with patch("national_treasure.services.queue.service.JobQueue", return_value=mock_queue):
            result = runner.invoke(app, ["queue", "dead-letter"])
            assert result.exit_code == 0
            assert "No failed jobs" in result.output

    def test_queue_dead_letter_with_jobs(self):
        """Should show dead letter jobs."""
        mock_queue = MagicMock()
        mock_queue.get_dead_letter_jobs = AsyncMock(return_value=[
            {
                "job_id": "job-abc123def456",
                "job_type": "CAPTURE",
                "error": "Connection timeout",
                "retry_count": 3,
                "failed_at": "2024-01-15T10:30:00Z",
            }
        ])

        with patch("national_treasure.services.queue.service.JobQueue", return_value=mock_queue):
            result = runner.invoke(app, ["queue", "dead-letter"])
            assert result.exit_code == 0
            assert "Dead Letter Queue" in result.output
            assert "CAPTURE" in result.output


class TestTrainingCommands:
    """Test training sub-commands."""

    def test_training_stats(self):
        """Should show training statistics."""
        mock_service = MagicMock()
        mock_service.get_training_stats = AsyncMock(return_value={
            "selectors": {
                "total_patterns": 100,
                "unique_sites": 25,
                "unique_fields": 15,
                "total_successes": 80,
                "total_failures": 20,
                "avg_confidence": 0.85,
            },
            "top_sites": [
                {"site": "example.com", "patterns": 20},
            ]
        })

        with patch("national_treasure.services.scraper.training.TrainingService", return_value=mock_service):
            result = runner.invoke(app, ["training", "stats"])
            assert result.exit_code == 0
            assert "Training Statistics" in result.output
            assert "Total patterns" in result.output

    def test_training_export(self, tmp_path):
        """Should export training data."""
        mock_service = MagicMock()
        mock_service.export_training_data = AsyncMock(return_value={
            "selectors": [{"id": 1}],
            "url_patterns": [{"id": 1}],
        })

        output_file = tmp_path / "export.json"
        with patch("national_treasure.services.scraper.training.TrainingService", return_value=mock_service):
            result = runner.invoke(app, ["training", "export", str(output_file)])
            assert result.exit_code == 0
            assert "Exported" in result.output
            assert output_file.exists()

    def test_training_import_file_not_found(self):
        """Should error when import file not found."""
        result = runner.invoke(app, ["training", "import", "/nonexistent/file.json"])
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_training_import_success(self, tmp_path):
        """Should import training data."""
        mock_service = MagicMock()
        mock_service.import_training_data = AsyncMock(return_value={
            "selectors": 5,
            "url_patterns": 3,
        })

        input_file = tmp_path / "import.json"
        input_file.write_text('{"selectors": [], "url_patterns": []}')

        with patch("national_treasure.services.scraper.training.TrainingService", return_value=mock_service):
            result = runner.invoke(app, ["training", "import", str(input_file)])
            assert result.exit_code == 0
            assert "Imported" in result.output


class TestLearningCommands:
    """Test learning sub-commands."""

    def test_learning_insights(self):
        """Should show domain insights."""
        mock_learner = MagicMock()
        mock_learner.get_domain_insights = AsyncMock(return_value={
            "total_attempts": 50,
            "success_rate": 0.92,
            "best_headless_mode": {"mode": "new", "success_rate": 0.95},
            "best_wait_strategy": {"strategy": "networkidle", "success_rate": 0.90},
            "best_user_agent": {"ua_key": "chrome", "success_rate": 0.88},
            "recommendations": ["Use stealth mode"],
        })

        with patch("national_treasure.services.learning.domain.DomainLearner", return_value=mock_learner):
            result = runner.invoke(app, ["learning", "insights", "example.com"])
            assert result.exit_code == 0
            assert "Insights" in result.output
            assert "example.com" in result.output
            assert "Total attempts" in result.output

    def test_learning_stats(self):
        """Should show global learning stats."""
        mock_learner = MagicMock()
        mock_learner.get_global_stats = AsyncMock(return_value={
            "total_domains": 100,
            "total_requests": 5000,
            "overall_success_rate": 0.87,
            "top_performing_configs": [
                {"config": "stealth", "success_rate": 0.95, "attempts": 100},
            ],
            "problematic_domains": [
                {"domain": "hard.com", "success_rate": 0.20, "attempts": 50},
            ],
        })

        with patch("national_treasure.services.learning.domain.DomainLearner", return_value=mock_learner):
            result = runner.invoke(app, ["learning", "stats"])
            assert result.exit_code == 0
            assert "Learning Statistics" in result.output
            assert "Total domains" in result.output


class TestDatabaseCommands:
    """Test database sub-commands."""

    @patch("national_treasure.cli.main.init_database")
    @patch("national_treasure.cli.main.get_config")
    def test_db_init_new(self, mock_config, mock_init, tmp_path):
        """Should initialize new database."""
        db_path = tmp_path / "new.db"
        mock_config.return_value = MagicMock(database_path=db_path)
        mock_init.return_value = None

        result = runner.invoke(app, ["db", "init"])
        assert result.exit_code == 0
        assert "initialized" in result.output

    @patch("national_treasure.cli.main.get_config")
    def test_db_init_exists_no_force(self, mock_config, tmp_path):
        """Should error when database exists without --force."""
        db_path = tmp_path / "existing.db"
        db_path.touch()
        mock_config.return_value = MagicMock(database_path=db_path)

        result = runner.invoke(app, ["db", "init"])
        assert result.exit_code == 1
        assert "already exists" in result.output

    @patch("national_treasure.cli.main.init_database")
    @patch("national_treasure.cli.main.get_config")
    def test_db_init_force(self, mock_config, mock_init, tmp_path):
        """Should recreate database with --force."""
        db_path = tmp_path / "existing.db"
        db_path.touch()
        mock_config.return_value = MagicMock(database_path=db_path)
        mock_init.return_value = None

        result = runner.invoke(app, ["db", "init", "--force"])
        assert result.exit_code == 0
        assert "initialized" in result.output

    @patch("national_treasure.cli.main.get_config")
    def test_db_info_not_found(self, mock_config, tmp_path):
        """Should error when database not found."""
        mock_config.return_value = MagicMock(database_path=tmp_path / "missing.db")

        result = runner.invoke(app, ["db", "info"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_db_info_success(self, tmp_path):
        """Should show database info."""
        import sqlite3

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO jobs VALUES (1)")
        conn.execute("CREATE TABLE selectors (id INTEGER PRIMARY KEY)")
        conn.close()

        mock_config = MagicMock(database_path=db_path)
        with patch("national_treasure.cli.main.get_config", return_value=mock_config):
            result = runner.invoke(app, ["db", "info"])
            assert result.exit_code == 0
            assert "jobs" in result.output


class TestETAColumn:
    """Test custom progress columns."""

    def test_eta_column_render(self):
        """Should render ETA correctly."""
        from national_treasure.cli.main import ETAColumn
        from national_treasure.core.progress import ProgressState

        state = ProgressState(total_items=10)
        column = ETAColumn(state)

        # Mock task
        mock_task = MagicMock()
        result = column.render(mock_task)
        assert "ETA:" in result


class TestCurrentFileColumn:
    """Test current file column."""

    def test_current_file_column_empty(self):
        """Should return empty string when no current item."""
        from national_treasure.cli.main import CurrentFileColumn
        from national_treasure.core.progress import ProgressState

        state = ProgressState(total_items=10)
        column = CurrentFileColumn(state)

        mock_task = MagicMock()
        result = column.render(mock_task)
        assert result == ""

    def test_current_file_column_with_item(self):
        """Should render current item."""
        from national_treasure.cli.main import CurrentFileColumn
        from national_treasure.core.progress import ProgressState

        state = ProgressState(total_items=10)
        state.start_item("https://example.com/very/long/path/to/page.html")
        column = CurrentFileColumn(state, max_width=30)

        mock_task = MagicMock()
        result = column.render(mock_task)
        assert len(result) <= 30
