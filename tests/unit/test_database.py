"""Tests for database module."""

import pytest
import aiosqlite

from national_treasure.core.database import init_database, SCHEMA


class TestDatabaseInit:
    """Tests for database initialization."""

    @pytest.mark.asyncio
    async def test_creates_database(self, temp_dir):
        """init_database should create database file."""
        db_path = temp_dir / "test.db"
        await init_database(str(db_path))
        assert db_path.exists()

    @pytest.mark.asyncio
    async def test_creates_tables(self, test_db):
        """init_database should create all tables."""
        expected_tables = [
            "browser_configs",
            "domain_configs",
            "request_outcomes",
            "domain_similarity",
            "jobs",
            "job_dead_letter",
            "selector_patterns",
            "url_patterns",
            "web_sources",
            "web_source_images",
        ]

        async with aiosqlite.connect(test_db) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ) as cursor:
                tables = [row[0] for row in await cursor.fetchall()]

        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

    @pytest.mark.asyncio
    async def test_idempotent(self, temp_dir):
        """init_database should be idempotent."""
        db_path = temp_dir / "test.db"

        # Initialize twice
        await init_database(str(db_path))
        await init_database(str(db_path))

        # Should still work
        async with aiosqlite.connect(str(db_path)) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ) as cursor:
                tables = [row[0] for row in await cursor.fetchall()]
                assert len(tables) > 0


class TestSchema:
    """Tests for database schema."""

    def test_schema_not_empty(self):
        """Schema should contain SQL."""
        assert len(SCHEMA) > 100

    def test_schema_has_tables(self):
        """Schema should define expected tables."""
        assert "CREATE TABLE IF NOT EXISTS browser_configs" in SCHEMA
        assert "CREATE TABLE IF NOT EXISTS jobs" in SCHEMA
        assert "CREATE TABLE IF NOT EXISTS selector_patterns" in SCHEMA

    def test_schema_has_indexes(self):
        """Schema should define indexes."""
        assert "CREATE INDEX" in SCHEMA
