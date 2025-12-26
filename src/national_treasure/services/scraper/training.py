"""Selector training service for learning from scraping outcomes.

Ported from barbossa with enhancements for Thompson Sampling.
"""

from datetime import datetime
from typing import Any

import aiosqlite

from national_treasure.core.config import get_config
from national_treasure.core.models import SelectorPattern, UrlPattern


class TrainingService:
    """Service for tracking and improving selector patterns.

    Learns which selectors work for which sites by tracking
    success/failure rates and calculating confidence scores.
    """

    def __init__(self, db_path: str | None = None):
        """Initialize training service.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or str(get_config().database_path)

    async def record_selector_outcome(
        self,
        site: str,
        field: str,
        selector: str,
        success: bool,
        extracted_value: str | None = None,
    ) -> None:
        """Record outcome of using a selector.

        Args:
            site: Site identifier (e.g., "bandcamp.com")
            field: Field being extracted (e.g., "title", "artist")
            selector: CSS selector used
            success: Whether extraction succeeded
            extracted_value: Value extracted (for validation)
        """
        now = datetime.utcnow()

        async with aiosqlite.connect(self.db_path) as db:
            # Check if pattern exists
            async with db.execute(
                """
                SELECT success_count, failure_count FROM selector_patterns
                WHERE site = ? AND field = ? AND selector = ?
                """,
                (site, field, selector),
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                # Update existing pattern
                if success:
                    await db.execute(
                        """
                        UPDATE selector_patterns
                        SET success_count = success_count + 1,
                            last_used = ?,
                            last_value = ?
                        WHERE site = ? AND field = ? AND selector = ?
                        """,
                        (now.isoformat(), extracted_value, site, field, selector),
                    )
                else:
                    await db.execute(
                        """
                        UPDATE selector_patterns
                        SET failure_count = failure_count + 1,
                            last_used = ?
                        WHERE site = ? AND field = ? AND selector = ?
                        """,
                        (now.isoformat(), site, field, selector),
                    )
            else:
                # Insert new pattern
                await db.execute(
                    """
                    INSERT INTO selector_patterns (
                        site, field, selector, success_count, failure_count,
                        created_at, last_used, last_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        site,
                        field,
                        selector,
                        1 if success else 0,
                        0 if success else 1,
                        now.isoformat(),
                        now.isoformat(),
                        extracted_value if success else None,
                    ),
                )

            await db.commit()

    async def get_best_selector(
        self,
        site: str,
        field: str,
        min_confidence: float = 0.5,
    ) -> SelectorPattern | None:
        """Get the best selector for a site/field combination.

        Args:
            site: Site identifier
            field: Field to extract
            min_confidence: Minimum confidence threshold

        Returns:
            Best selector pattern or None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT *,
                    CAST(success_count AS REAL) / (success_count + failure_count) as confidence
                FROM selector_patterns
                WHERE site = ? AND field = ?
                AND (success_count + failure_count) > 0
                ORDER BY confidence DESC, success_count DESC
                LIMIT 1
                """,
                (site, field),
            ) as cursor:
                row = await cursor.fetchone()

                if row and row["confidence"] >= min_confidence:
                    return SelectorPattern(
                        site=row["site"],
                        field=row["field"],
                        selector=row["selector"],
                        success_count=row["success_count"],
                        failure_count=row["failure_count"],
                    )

        return None

    async def get_selectors_for_site(
        self,
        site: str,
        min_confidence: float = 0.0,
    ) -> list[SelectorPattern]:
        """Get all selectors for a site.

        Args:
            site: Site identifier
            min_confidence: Minimum confidence threshold

        Returns:
            List of selector patterns
        """
        patterns = []

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT *,
                    CAST(success_count AS REAL) / NULLIF(success_count + failure_count, 0) as confidence
                FROM selector_patterns
                WHERE site = ?
                AND (success_count + failure_count) > 0
                AND CAST(success_count AS REAL) / NULLIF(success_count + failure_count, 0) >= ?
                ORDER BY field, confidence DESC
                """,
                (site, min_confidence),
            ) as cursor:
                async for row in cursor:
                    patterns.append(
                        SelectorPattern(
                            site=row["site"],
                            field=row["field"],
                            selector=row["selector"],
                            success_count=row["success_count"],
                            failure_count=row["failure_count"],
                        )
                    )

        return patterns

    async def get_fallback_selectors(
        self,
        site: str,
        field: str,
        limit: int = 5,
    ) -> list[SelectorPattern]:
        """Get fallback selectors ordered by confidence.

        Args:
            site: Site identifier
            field: Field to extract
            limit: Maximum selectors to return

        Returns:
            List of selectors ordered by confidence
        """
        patterns = []

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT *,
                    CAST(success_count AS REAL) / NULLIF(success_count + failure_count, 0) as confidence
                FROM selector_patterns
                WHERE site = ? AND field = ?
                AND (success_count + failure_count) > 0
                ORDER BY confidence DESC, success_count DESC
                LIMIT ?
                """,
                (site, field, limit),
            ) as cursor:
                async for row in cursor:
                    patterns.append(
                        SelectorPattern(
                            site=row["site"],
                            field=row["field"],
                            selector=row["selector"],
                            success_count=row["success_count"],
                            failure_count=row["failure_count"],
                        )
                    )

        return patterns

    async def record_url_pattern_outcome(
        self,
        site: str,
        pattern_type: str,
        pattern: str,
        success: bool,
        source_url: str | None = None,
        result_url: str | None = None,
    ) -> None:
        """Record outcome of using a URL pattern.

        Args:
            site: Site identifier
            pattern_type: Type of pattern (e.g., "image_url", "album_url")
            pattern: Regex or template pattern
            success: Whether pattern worked
            source_url: Original URL
            result_url: Transformed URL
        """
        now = datetime.utcnow()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT success_count, failure_count FROM url_patterns
                WHERE site = ? AND pattern_type = ? AND pattern = ?
                """,
                (site, pattern_type, pattern),
            ) as cursor:
                row = await cursor.fetchone()

            if row:
                if success:
                    await db.execute(
                        """
                        UPDATE url_patterns
                        SET success_count = success_count + 1,
                            last_used = ?,
                            example_source = COALESCE(?, example_source),
                            example_result = COALESCE(?, example_result)
                        WHERE site = ? AND pattern_type = ? AND pattern = ?
                        """,
                        (
                            now.isoformat(),
                            source_url,
                            result_url,
                            site,
                            pattern_type,
                            pattern,
                        ),
                    )
                else:
                    await db.execute(
                        """
                        UPDATE url_patterns
                        SET failure_count = failure_count + 1,
                            last_used = ?
                        WHERE site = ? AND pattern_type = ? AND pattern = ?
                        """,
                        (now.isoformat(), site, pattern_type, pattern),
                    )
            else:
                await db.execute(
                    """
                    INSERT INTO url_patterns (
                        site, pattern_type, pattern, success_count, failure_count,
                        created_at, last_used, example_source, example_result
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        site,
                        pattern_type,
                        pattern,
                        1 if success else 0,
                        0 if success else 1,
                        now.isoformat(),
                        now.isoformat(),
                        source_url if success else None,
                        result_url if success else None,
                    ),
                )

            await db.commit()

    async def get_best_url_pattern(
        self,
        site: str,
        pattern_type: str,
        min_confidence: float = 0.5,
    ) -> UrlPattern | None:
        """Get the best URL pattern for a site/type combination.

        Args:
            site: Site identifier
            pattern_type: Type of pattern
            min_confidence: Minimum confidence threshold

        Returns:
            Best URL pattern or None
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT *,
                    CAST(success_count AS REAL) / (success_count + failure_count) as confidence
                FROM url_patterns
                WHERE site = ? AND pattern_type = ?
                AND (success_count + failure_count) > 0
                ORDER BY confidence DESC, success_count DESC
                LIMIT 1
                """,
                (site, pattern_type),
            ) as cursor:
                row = await cursor.fetchone()

                if row and row["confidence"] >= min_confidence:
                    return UrlPattern(
                        site=row["site"],
                        pattern_type=row["pattern_type"],
                        pattern=row["pattern"],
                        success_count=row["success_count"],
                        failure_count=row["failure_count"],
                    )

        return None

    async def export_training_data(self, site: str | None = None) -> dict[str, Any]:
        """Export training data for analysis or backup.

        Args:
            site: Optional site to filter by

        Returns:
            Dict with selectors and url_patterns
        """
        data: dict[str, Any] = {"selectors": [], "url_patterns": []}

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Export selectors
            query = "SELECT * FROM selector_patterns"
            params = ()
            if site:
                query += " WHERE site = ?"
                params = (site,)

            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    data["selectors"].append(dict(row))

            # Export URL patterns
            query = "SELECT * FROM url_patterns"
            if site:
                query += " WHERE site = ?"

            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    data["url_patterns"].append(dict(row))

        return data

    async def import_training_data(
        self,
        data: dict[str, Any],
        merge: bool = True,
    ) -> dict[str, int]:
        """Import training data.

        Args:
            data: Dict with selectors and url_patterns
            merge: If True, merge with existing. If False, replace.

        Returns:
            Dict with counts of imported records
        """
        counts = {"selectors": 0, "url_patterns": 0}

        async with aiosqlite.connect(self.db_path) as db:
            if not merge:
                await db.execute("DELETE FROM selector_patterns")
                await db.execute("DELETE FROM url_patterns")

            for selector in data.get("selectors", []):
                if merge:
                    # Upsert
                    await db.execute(
                        """
                        INSERT INTO selector_patterns (
                            site, field, selector, success_count, failure_count,
                            created_at, last_used
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(site, field, selector) DO UPDATE SET
                            success_count = success_count + excluded.success_count,
                            failure_count = failure_count + excluded.failure_count,
                            last_used = excluded.last_used
                        """,
                        (
                            selector["site"],
                            selector["field"],
                            selector["selector"],
                            selector["success_count"],
                            selector["failure_count"],
                            selector.get("created_at", datetime.utcnow().isoformat()),
                            selector.get("last_used", datetime.utcnow().isoformat()),
                        ),
                    )
                else:
                    await db.execute(
                        """
                        INSERT INTO selector_patterns (
                            site, field, selector, success_count, failure_count,
                            created_at, last_used
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            selector["site"],
                            selector["field"],
                            selector["selector"],
                            selector["success_count"],
                            selector["failure_count"],
                            selector.get("created_at", datetime.utcnow().isoformat()),
                            selector.get("last_used", datetime.utcnow().isoformat()),
                        ),
                    )
                counts["selectors"] += 1

            for pattern in data.get("url_patterns", []):
                if merge:
                    await db.execute(
                        """
                        INSERT INTO url_patterns (
                            site, pattern_type, pattern, success_count, failure_count,
                            created_at, last_used
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(site, pattern_type, pattern) DO UPDATE SET
                            success_count = success_count + excluded.success_count,
                            failure_count = failure_count + excluded.failure_count,
                            last_used = excluded.last_used
                        """,
                        (
                            pattern["site"],
                            pattern["pattern_type"],
                            pattern["pattern"],
                            pattern["success_count"],
                            pattern["failure_count"],
                            pattern.get("created_at", datetime.utcnow().isoformat()),
                            pattern.get("last_used", datetime.utcnow().isoformat()),
                        ),
                    )
                else:
                    await db.execute(
                        """
                        INSERT INTO url_patterns (
                            site, pattern_type, pattern, success_count, failure_count,
                            created_at, last_used
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            pattern["site"],
                            pattern["pattern_type"],
                            pattern["pattern"],
                            pattern["success_count"],
                            pattern["failure_count"],
                            pattern.get("created_at", datetime.utcnow().isoformat()),
                            pattern.get("last_used", datetime.utcnow().isoformat()),
                        ),
                    )
                counts["url_patterns"] += 1

            await db.commit()

        return counts

    async def get_training_stats(self) -> dict[str, Any]:
        """Get training statistics.

        Returns:
            Dict with statistics about training data
        """
        stats: dict[str, Any] = {}

        async with aiosqlite.connect(self.db_path) as db:
            # Selector stats
            async with db.execute(
                """
                SELECT
                    COUNT(*) as total_patterns,
                    COUNT(DISTINCT site) as unique_sites,
                    COUNT(DISTINCT field) as unique_fields,
                    SUM(success_count) as total_successes,
                    SUM(failure_count) as total_failures,
                    AVG(CAST(success_count AS REAL) / NULLIF(success_count + failure_count, 0)) as avg_confidence
                FROM selector_patterns
                WHERE success_count + failure_count > 0
                """
            ) as cursor:
                row = await cursor.fetchone()
                stats["selectors"] = {
                    "total_patterns": row[0],
                    "unique_sites": row[1],
                    "unique_fields": row[2],
                    "total_successes": row[3] or 0,
                    "total_failures": row[4] or 0,
                    "avg_confidence": round(row[5] or 0, 3),
                }

            # URL pattern stats
            async with db.execute(
                """
                SELECT
                    COUNT(*) as total_patterns,
                    COUNT(DISTINCT site) as unique_sites,
                    COUNT(DISTINCT pattern_type) as unique_types,
                    SUM(success_count) as total_successes,
                    SUM(failure_count) as total_failures
                FROM url_patterns
                WHERE success_count + failure_count > 0
                """
            ) as cursor:
                row = await cursor.fetchone()
                stats["url_patterns"] = {
                    "total_patterns": row[0],
                    "unique_sites": row[1],
                    "unique_types": row[2],
                    "total_successes": row[3] or 0,
                    "total_failures": row[4] or 0,
                }

            # Top sites by patterns
            async with db.execute(
                """
                SELECT site, COUNT(*) as pattern_count
                FROM selector_patterns
                GROUP BY site
                ORDER BY pattern_count DESC
                LIMIT 10
                """
            ) as cursor:
                stats["top_sites"] = [
                    {"site": row[0], "patterns": row[1]} async for row in cursor
                ]

        return stats
