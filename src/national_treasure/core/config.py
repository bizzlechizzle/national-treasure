"""Configuration management for national-treasure."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BackupConfig(BaseModel):
    """Backup configuration."""

    enabled: bool = True
    max_backups: int = 5
    backup_on_startup: bool = True
    scheduled_backup: bool = True
    scheduled_interval_hours: int = 24


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    disk_warning_mb: int = 1024
    disk_critical_mb: int = 512
    disk_emergency_mb: int = 100
    integrity_check_on_startup: bool = True


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    max_file_size_mb: int = 10
    max_files: int = 7


class BrowserDefaults(BaseModel):
    """Default browser settings."""

    headless_mode: str = "shell"
    default_timeout_ms: int = 30000
    viewport_width: int = 1920
    viewport_height: int = 1080
    stealth_enabled: bool = True


class RateLimitConfig(BaseModel):
    """Rate limit configuration per domain."""

    min_delay_ms: int = 1000
    max_requests_per_minute: int = 10
    max_requests_per_hour: int = 100


class CookieSourceConfig(BaseModel):
    """Cookie source configuration."""

    type: str = "browser"  # browser, extension, manual
    name: str | None = None  # chrome, arc, brave, etc.
    profile: str = "Default"
    port: int | None = None  # For extension WebSocket


class Config(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="NT_",
        env_nested_delimiter="__",
    )

    # Paths
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".national-treasure")
    archive_dir: Path | None = None
    database_path: Path | None = None

    # Settings
    backup: BackupConfig = Field(default_factory=BackupConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    browser: BrowserDefaults = Field(default_factory=BrowserDefaults)

    # Rate limits (per domain)
    default_rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    domain_rate_limits: dict[str, RateLimitConfig] = Field(default_factory=dict)

    # Cookie sources
    cookie_sources: list[CookieSourceConfig] = Field(default_factory=list)
    fallback_cookie_source: str = "anonymous"

    def model_post_init(self, __context: Any) -> None:
        """Initialize derived paths after model creation."""
        if self.database_path is None:
            self.database_path = self.data_dir / "national-treasure.db"
        if self.archive_dir is None:
            self.archive_dir = self.data_dir / "archive"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Load configuration from YAML file."""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)

    def save_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        config_path = Path.home() / ".national-treasure" / "config.yaml"
        _config = Config.from_yaml(config_path)
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config
