"""Extended database tests for full coverage."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.core.database import (
    Database,
    SCHEMA_SQL,
    SCHEMA_VERSION,
    get_db,
    close_db,
    init_database,
)


class TestDatabase:
    """Test Database class."""

    @pytest.mark.asyncio
    async def test_connect_and_close(self, tmp_path):
        """Should connect and close correctly."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)

        await db.connect()
        assert db._connection is not None

        await db.close()
        assert db._connection is None

    @pytest.mark.asyncio
    async def test_init_schema(self, tmp_path):
        """Should initialize schema on connect."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)

        await db.connect()

        # Check tables exist
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        rows = await cursor.fetchall()
        table_names = [row[0] for row in rows]

        assert "jobs" in table_names
        assert "selector_patterns" in table_names
        assert "domain_configs" in table_names

        await db.close()

    @pytest.mark.asyncio
    async def test_schema_version_stored(self, tmp_path):
        """Should store schema version."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)

        await db.connect()

        result = await db.fetchone(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        )
        assert result is not None
        assert result["value"] == str(SCHEMA_VERSION)

        await db.close()

    @pytest.mark.asyncio
    async def test_execute_with_params(self, tmp_path):
        """Should execute with parameters."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        # Insert a job
        await db.execute(
            "INSERT INTO jobs (job_id, job_type, payload, status) VALUES (?, ?, ?, ?)",
            ("job-1", "CAPTURE", '{"url": "https://example.com"}', "pending"),
        )
        await db.commit()

        result = await db.fetchone("SELECT * FROM jobs WHERE job_id = ?", ("job-1",))
        assert result is not None
        assert result["job_type"] == "CAPTURE"

        await db.close()

    @pytest.mark.asyncio
    async def test_execute_without_params(self, tmp_path):
        """Should execute without parameters."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        cursor = await db.execute("SELECT COUNT(*) FROM jobs")
        row = await cursor.fetchone()
        assert row[0] == 0

        await db.close()

    @pytest.mark.asyncio
    async def test_executemany(self, tmp_path):
        """Should execute many statements."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        jobs = [
            ("job-1", "CAPTURE", '{}', "pending"),
            ("job-2", "CAPTURE", '{}', "pending"),
            ("job-3", "CAPTURE", '{}', "completed"),
        ]

        await db.executemany(
            "INSERT INTO jobs (job_id, job_type, payload, status) VALUES (?, ?, ?, ?)",
            jobs,
        )
        await db.commit()

        result = await db.fetchall("SELECT * FROM jobs")
        assert len(result) == 3

        await db.close()

    @pytest.mark.asyncio
    async def test_fetchone_returns_none(self, tmp_path):
        """Should return None when no row found."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        result = await db.fetchone("SELECT * FROM jobs WHERE job_id = ?", ("nonexistent",))
        assert result is None

        await db.close()

    @pytest.mark.asyncio
    async def test_fetchall_empty(self, tmp_path):
        """Should return empty list when no rows."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        result = await db.fetchall("SELECT * FROM jobs")
        assert result == []

        await db.close()

    @pytest.mark.asyncio
    async def test_transaction_commit(self, tmp_path):
        """Should commit transaction on success."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        async with db.transaction():
            await db.execute(
                "INSERT INTO jobs (job_id, job_type, payload, status) VALUES (?, ?, ?, ?)",
                ("job-tx", "CAPTURE", '{}', "pending"),
            )

        result = await db.fetchone("SELECT * FROM jobs WHERE job_id = ?", ("job-tx",))
        assert result is not None

        await db.close()

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, tmp_path):
        """Should rollback transaction on error."""
        db_path = tmp_path / "test.db"
        db = Database(db_path=db_path)
        await db.connect()

        try:
            async with db.transaction():
                await db.execute(
                    "INSERT INTO jobs (job_id, job_type, payload, status) VALUES (?, ?, ?, ?)",
                    ("job-fail", "CAPTURE", '{}', "pending"),
                )
                raise ValueError("Simulated error")
        except ValueError:
            pass

        result = await db.fetchone("SELECT * FROM jobs WHERE job_id = ?", ("job-fail",))
        assert result is None

        await db.close()


class TestGlobalDatabase:
    """Test global database functions."""

    @pytest.mark.asyncio
    async def test_get_db_creates_instance(self, tmp_path, monkeypatch):
        """Should create database instance on first call."""
        # Reset global state
        import national_treasure.core.database as db_module
        db_module._db = None

        # Mock config
        mock_config = MagicMock()
        mock_config.database_path = tmp_path / "global.db"

        with patch("national_treasure.core.database.get_config", return_value=mock_config):
            db = await get_db()
            assert db is not None
            assert db._connection is not None

            # Second call returns same instance
            db2 = await get_db()
            assert db is db2

            await close_db()

    @pytest.mark.asyncio
    async def test_close_db(self, tmp_path, monkeypatch):
        """Should close global database."""
        import national_treasure.core.database as db_module
        db_module._db = None

        mock_config = MagicMock()
        mock_config.database_path = tmp_path / "close.db"

        with patch("national_treasure.core.database.get_config", return_value=mock_config):
            db = await get_db()
            assert db_module._db is not None

            await close_db()
            assert db_module._db is None

    @pytest.mark.asyncio
    async def test_close_db_when_none(self):
        """Should handle close when no db exists."""
        import national_treasure.core.database as db_module
        db_module._db = None

        # Should not raise
        await close_db()


class TestInitDatabase:
    """Test init_database function."""

    @pytest.mark.asyncio
    async def test_init_database(self, tmp_path):
        """Should initialize database at path."""
        db_path = tmp_path / "init.db"

        await init_database(str(db_path))

        assert db_path.exists()

        # Verify schema was created
        import aiosqlite
        async with aiosqlite.connect(db_path) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
            )
            row = await cursor.fetchone()
            assert row is not None


class TestSchemaSQL:
    """Test schema definitions."""

    def test_schema_has_jobs_table(self):
        """Schema should define jobs table."""
        assert "CREATE TABLE IF NOT EXISTS jobs" in SCHEMA_SQL

    def test_schema_has_selector_patterns(self):
        """Schema should define selector_patterns table."""
        assert "CREATE TABLE IF NOT EXISTS selector_patterns" in SCHEMA_SQL

    def test_schema_has_domain_configs(self):
        """Schema should define domain_configs table."""
        assert "CREATE TABLE IF NOT EXISTS domain_configs" in SCHEMA_SQL

    def test_schema_version_defined(self):
        """Schema version should be defined."""
        assert SCHEMA_VERSION >= 1
