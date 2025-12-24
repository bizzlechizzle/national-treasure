"""SQLite database management for national-treasure."""

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator

import aiosqlite

from national_treasure.core.config import get_config

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- Browser configurations
CREATE TABLE IF NOT EXISTS browser_configs (
    config_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    headless_mode TEXT DEFAULT 'shell',
    user_agent TEXT,
    viewport_width INTEGER DEFAULT 1920,
    viewport_height INTEGER DEFAULT 1080,
    stealth_enabled INTEGER DEFAULT 1,
    disable_automation_flag INTEGER DEFAULT 1,
    wait_strategy TEXT DEFAULT 'networkidle',
    default_timeout_ms INTEGER DEFAULT 30000,
    total_attempts INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_success TEXT,
    last_failure TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Domain configurations (learned)
CREATE TABLE IF NOT EXISTS domain_configs (
    domain TEXT PRIMARY KEY,
    best_config_id TEXT REFERENCES browser_configs(config_id),
    confidence REAL DEFAULT 0.5,
    min_delay_ms INTEGER DEFAULT 1000,
    max_requests_per_minute INTEGER DEFAULT 10,
    requires_cookies INTEGER DEFAULT 0,
    cookie_source TEXT,
    session_lifetime_hours INTEGER,
    needs_scroll_to_load INTEGER DEFAULT 0,
    needs_click_to_expand INTEGER DEFAULT 0,
    has_infinite_scroll INTEGER DEFAULT 0,
    block_indicators TEXT,
    success_indicators TEXT,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    sample_count INTEGER DEFAULT 0
);

-- Request outcomes (ML training data)
CREATE TABLE IF NOT EXISTS request_outcomes (
    outcome_id TEXT PRIMARY KEY,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    domain TEXT NOT NULL,
    url TEXT NOT NULL,
    tld TEXT NOT NULL,
    config_id TEXT REFERENCES browser_configs(config_id),
    user_agent TEXT,
    headless_mode TEXT,
    stealth_enabled INTEGER,
    request_hour INTEGER,
    request_day_of_week INTEGER,
    requests_last_minute INTEGER,
    requests_last_hour INTEGER,
    http_status INTEGER,
    outcome TEXT,
    blocked_by TEXT,
    content_extracted INTEGER,
    content_length INTEGER,
    page_title TEXT,
    has_captcha INTEGER,
    has_login_wall INTEGER,
    response_time_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_outcomes_domain ON request_outcomes(domain);
CREATE INDEX IF NOT EXISTS idx_outcomes_outcome ON request_outcomes(outcome);
CREATE INDEX IF NOT EXISTS idx_outcomes_timestamp ON request_outcomes(timestamp);

-- Domain similarity (clustering)
CREATE TABLE IF NOT EXISTS domain_similarity (
    domain_a TEXT NOT NULL,
    domain_b TEXT NOT NULL,
    similarity_score REAL,
    similarity_type TEXT,
    PRIMARY KEY (domain_a, domain_b)
);

-- Jobs queue
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    queue TEXT NOT NULL,
    priority INTEGER DEFAULT 10,
    status TEXT DEFAULT 'pending',
    payload TEXT,
    depends_on TEXT,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error TEXT,
    result TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    started_at TEXT,
    completed_at TEXT,
    locked_by TEXT,
    locked_at TEXT,
    retry_after TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(queue, status, priority DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- Job dead letter queue
CREATE TABLE IF NOT EXISTS job_dead_letter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    queue TEXT,
    payload TEXT,
    error TEXT,
    attempts INTEGER,
    died_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Selector patterns (learned from barbossa)
CREATE TABLE IF NOT EXISTS selector_patterns (
    pattern_id TEXT PRIMARY KEY,
    site TEXT NOT NULL,
    field TEXT NOT NULL,
    selector TEXT NOT NULL,
    selector_type TEXT DEFAULT 'css',
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    examples TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site, field, selector)
);
CREATE INDEX IF NOT EXISTS idx_selectors_site ON selector_patterns(site);

-- URL patterns (image enhancement)
CREATE TABLE IF NOT EXISTS url_patterns (
    pattern_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    site_type TEXT,
    domain_regex TEXT,
    path_regex TEXT,
    transform_template TEXT,
    confidence REAL DEFAULT 0.5,
    success_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    is_enabled INTEGER DEFAULT 1,
    is_builtin INTEGER DEFAULT 0
);

-- Web sources (captured pages)
CREATE TABLE IF NOT EXISTS web_sources (
    source_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    archive_method TEXT,
    screenshot_path TEXT,
    pdf_path TEXT,
    html_path TEXT,
    warc_path TEXT,
    wacz_path TEXT,
    page_title TEXT,
    page_description TEXT,
    og_data TEXT,
    schema_org_data TEXT,
    dublin_core_data TEXT,
    extracted_text TEXT,
    word_count INTEGER,
    image_count INTEGER,
    video_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    archived_at TEXT,
    last_checked TEXT
);
CREATE INDEX IF NOT EXISTS idx_sources_url ON web_sources(url);
CREATE INDEX IF NOT EXISTS idx_sources_status ON web_sources(status);

-- Web source images
CREATE TABLE IF NOT EXISTS web_source_images (
    image_id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES web_sources(source_id),
    original_url TEXT NOT NULL,
    enhanced_url TEXT,
    final_url TEXT,
    local_path TEXT,
    hash TEXT,
    alt_text TEXT,
    caption TEXT,
    credit TEXT,
    link_url TEXT,
    width INTEGER,
    height INTEGER,
    jpeg_quality INTEGER,
    has_watermark INTEGER,
    perceptual_hash TEXT,
    enhancement_method TEXT,
    original_size INTEGER,
    enhanced_size INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_source_images_source ON web_source_images(source_id);

-- Schema metadata
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    """Async SQLite database wrapper."""

    def __init__(self, db_path: Path | None = None):
        """Initialize database."""
        self.db_path = db_path or get_config().database_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Connect to database and initialize schema."""
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row

        # Enable WAL mode for better concurrency
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")

        # Initialize schema
        await self._init_schema()

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _init_schema(self) -> None:
        """Initialize database schema."""
        await self._connection.executescript(SCHEMA_SQL)

        # Check/update schema version
        async with self._connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                await self._connection.execute(
                    "INSERT INTO schema_meta (key, value) VALUES ('version', ?)",
                    (str(SCHEMA_VERSION),),
                )
                await self._connection.commit()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Context manager for database transactions."""
        try:
            yield self._connection
            await self._connection.commit()
        except Exception:
            await self._connection.rollback()
            raise

    async def execute(
        self, sql: str, params: tuple[Any, ...] | None = None
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement."""
        if params:
            return await self._connection.execute(sql, params)
        return await self._connection.execute(sql)

    async def executemany(
        self, sql: str, params_list: list[tuple[Any, ...]]
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        return await self._connection.executemany(sql, params_list)

    async def fetchone(
        self, sql: str, params: tuple[Any, ...] | None = None
    ) -> dict[str, Any] | None:
        """Fetch a single row."""
        cursor = await self.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetchall(
        self, sql: str, params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch all rows."""
        cursor = await self.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._connection.commit()


# Global database instance
_db: Database | None = None


async def get_db() -> Database:
    """Get the global database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.connect()
    return _db


async def close_db() -> None:
    """Close the global database instance."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
