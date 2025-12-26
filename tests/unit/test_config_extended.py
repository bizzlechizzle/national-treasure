"""Extended config tests for 100% coverage."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from national_treasure.core.config import Config, get_config, set_config


class TestGetConfigSingleton:
    """Test get_config singleton behavior."""

    def test_get_config_returns_same_instance(self):
        """Should return same config instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_set_config_updates_global(self):
        """Should update global config."""
        original = get_config()
        new_config = Config()
        set_config(new_config)

        current = get_config()
        assert current is new_config

        # Restore original
        set_config(original)
