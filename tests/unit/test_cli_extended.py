"""Extended CLI tests for 100% coverage."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from national_treasure.cli.main import app


runner = CliRunner()


class TestShowConfig:
    """Test config command."""

    def test_show_config(self, tmp_path):
        """Should show current configuration."""
        mock_config = MagicMock()
        mock_config.database_path = tmp_path / "db.sqlite"
        mock_config.archive_dir = tmp_path / "archives"
        mock_config.log_level = "INFO"

        with patch("national_treasure.cli.main.get_config", return_value=mock_config):
            result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        assert "Database:" in result.stdout
        assert "Archive dir:" in result.stdout
        assert "Log level:" in result.stdout
