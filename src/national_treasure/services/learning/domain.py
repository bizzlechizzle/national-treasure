"""Domain learning with Thompson Sampling for adaptive strategy selection.

Uses Multi-Armed Bandit approach to learn optimal configurations per domain.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiosqlite

from national_treasure.core.config import get_config
from national_treasure.core.models import BrowserConfig, HeadlessMode, WaitStrategy


@dataclass
class ArmStats:
    """Statistics for a bandit arm (configuration option)."""

    arm_id: str
    successes: int = 0
    failures: int = 0

    @property
    def total(self) -> int:
        return self.successes + self.failures

    def sample_beta(self) -> float:
        """Sample from Beta distribution (Thompson Sampling).

        Returns:
            Sample from Beta(successes + 1, failures + 1)
        """
        # Add 1 to both for Beta prior (uniform)
        alpha = self.successes + 1
        beta = self.failures + 1
        return random.betavariate(alpha, beta)


class DomainLearner:
    """Learn optimal browser configurations per domain using Thompson Sampling.

    For each domain, tracks success/failure rates for different configurations
    and uses Thompson Sampling to balance exploration vs exploitation.
    """

    # Configuration arms (strategies to choose from)
    HEADLESS_MODES = [HeadlessMode.SHELL, HeadlessMode.NEW, HeadlessMode.VISIBLE]
    WAIT_STRATEGIES = [
        WaitStrategy.NETWORKIDLE,
        WaitStrategy.DOMCONTENTLOADED,
        WaitStrategy.LOAD,
    ]
    USER_AGENTS = [
        "chrome_mac",  # Default Chrome on macOS
        "chrome_win",  # Chrome on Windows
        "firefox_mac",  # Firefox on macOS
        "safari_mac",  # Safari on macOS
    ]

    USER_AGENT_MAP = {
        "chrome_mac": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "chrome_win": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "firefox_mac": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) "
            "Gecko/20100101 Firefox/121.0"
        ),
        "safari_mac": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.2 Safari/605.1.15"
        ),
    }

    def __init__(self, db_path: str | None = None):
        """Initialize domain learner.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or str(get_config().database_path)

    async def get_best_config(self, domain: str) -> BrowserConfig:
        """Get the best browser configuration for a domain.

        Uses Thompson Sampling to select configuration that balances
        exploitation (use what works) with exploration (try new options).

        Args:
            domain: Domain to get config for (e.g., "bandcamp.com")

        Returns:
            Recommended BrowserConfig
        """
        # Load stats for all arms
        stats = await self._load_domain_stats(domain)

        # Sample from each arm and pick the best
        best_headless = self._sample_best_arm(
            [ArmStats(f"headless:{m.value}", *stats.get(f"headless:{m.value}", (0, 0)))
             for m in self.HEADLESS_MODES]
        )
        best_wait = self._sample_best_arm(
            [ArmStats(f"wait:{w.value}", *stats.get(f"wait:{w.value}", (0, 0)))
             for w in self.WAIT_STRATEGIES]
        )
        best_ua = self._sample_best_arm(
            [ArmStats(f"ua:{ua}", *stats.get(f"ua:{ua}", (0, 0)))
             for ua in self.USER_AGENTS]
        )

        # Extract chosen values
        headless_mode = HeadlessMode(best_headless.arm_id.split(":")[1])
        wait_strategy = WaitStrategy(best_wait.arm_id.split(":")[1])
        ua_key = best_ua.arm_id.split(":")[1]

        return BrowserConfig(
            headless_mode=headless_mode,
            wait_strategy=wait_strategy,
            user_agent=self.USER_AGENT_MAP.get(ua_key),
            stealth_enabled=True,
        )

    def _sample_best_arm(self, arms: list[ArmStats]) -> ArmStats:
        """Sample from all arms and return the one with highest sample.

        Args:
            arms: List of arm statistics

        Returns:
            Arm with highest sampled value
        """
        samples = [(arm, arm.sample_beta()) for arm in arms]
        return max(samples, key=lambda x: x[1])[0]

    async def record_outcome(
        self,
        domain: str,
        config: BrowserConfig,
        success: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record the outcome of using a configuration.

        Args:
            domain: Domain that was accessed
            config: Configuration that was used
            success: Whether access succeeded
            details: Additional details (response code, block type, etc.)
        """
        now = datetime.now(UTC)

        # Determine which arms were used
        arms = [
            f"headless:{config.headless_mode.value}",
            f"wait:{config.wait_strategy.value}",
        ]

        # Find UA key
        for ua_key, ua_string in self.USER_AGENT_MAP.items():
            if config.user_agent == ua_string:
                arms.append(f"ua:{ua_key}")
                break
        else:
            arms.append("ua:chrome_mac")  # Default

        async with aiosqlite.connect(self.db_path) as db:
            # Update stats for each arm
            for arm_id in arms:
                await db.execute(
                    """
                    INSERT INTO domain_configs (
                        domain, config_key, success_count, failure_count,
                        last_used, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(domain, config_key) DO UPDATE SET
                        success_count = success_count + ?,
                        failure_count = failure_count + ?,
                        last_used = ?
                    """,
                    (
                        domain,
                        arm_id,
                        1 if success else 0,
                        0 if success else 1,
                        now.isoformat(),
                        now.isoformat(),
                        1 if success else 0,
                        0 if success else 1,
                        now.isoformat(),
                    ),
                )

            # Also record in request_outcomes for history
            await db.execute(
                """
                INSERT INTO request_outcomes (
                    domain, config_hash, success, response_code,
                    blocked_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    domain,
                    self._config_hash(config),
                    success,
                    details.get("response_code") if details else None,
                    details.get("blocked_by") if details else None,
                    now.isoformat(),
                ),
            )

            await db.commit()

    async def _load_domain_stats(self, domain: str) -> dict[str, tuple[int, int]]:
        """Load statistics for a domain.

        Args:
            domain: Domain to load stats for

        Returns:
            Dict mapping arm_id to (successes, failures)
        """
        stats: dict[str, tuple[int, int]] = {}

        async with aiosqlite.connect(self.db_path) as db:
            # First try exact domain
            async with db.execute(
                """
                SELECT config_key, success_count, failure_count
                FROM domain_configs
                WHERE domain = ?
                """,
                (domain,),
            ) as cursor:
                async for row in cursor:
                    stats[row[0]] = (row[1], row[2])

            # If no data, try similar domains
            if not stats:
                similar_domains = await self._find_similar_domains(domain)
                for similar in similar_domains:
                    async with db.execute(
                        """
                        SELECT config_key, success_count, failure_count
                        FROM domain_configs
                        WHERE domain = ?
                        """,
                        (similar,),
                    ) as cursor:
                        async for row in cursor:
                            key = row[0]
                            if key not in stats:
                                # Weight similar domain data lower (50%)
                                stats[key] = (row[1] // 2, row[2] // 2)

        return stats

    async def _find_similar_domains(self, domain: str) -> list[str]:
        """Find similar domains that might have transferable learnings.

        Args:
            domain: Domain to find similar domains for

        Returns:
            List of similar domains
        """
        similar = []

        # Check for explicit similarity mappings
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            """
                SELECT domain_b FROM domain_similarity
                WHERE domain_a = ?
                ORDER BY similarity_score DESC
                LIMIT 5
                """,
            (domain,),
        ) as cursor:
            async for row in cursor:
                similar.append(row[0])

        # If no explicit mappings, try TLD matching
        if not similar:
            parts = domain.split(".")
            if len(parts) >= 2:
                tld = parts[-1]
                async with aiosqlite.connect(self.db_path) as db, db.execute(
                    """
                        SELECT DISTINCT domain FROM domain_configs
                        WHERE domain LIKE ?
                        AND domain != ?
                        LIMIT 5
                        """,
                    (f"%.{tld}", domain),
                ) as cursor:
                    async for row in cursor:
                        similar.append(row[0])

        return similar

    def _config_hash(self, config: BrowserConfig) -> str:
        """Generate a hash for a configuration.

        Args:
            config: Browser configuration

        Returns:
            Hash string
        """
        key_parts = [
            config.headless_mode.value,
            config.wait_strategy.value,
            config.user_agent or "default",
        ]
        return ":".join(key_parts)

    async def get_domain_insights(self, domain: str) -> dict[str, Any]:
        """Get learning insights for a domain.

        Args:
            domain: Domain to analyze

        Returns:
            Dict with insights about what works for this domain
        """
        stats = await self._load_domain_stats(domain)

        insights: dict[str, Any] = {
            "domain": domain,
            "total_attempts": 0,
            "success_rate": 0.0,
            "best_headless_mode": None,
            "best_wait_strategy": None,
            "best_user_agent": None,
            "recommendations": [],
        }

        if not stats:
            insights["recommendations"].append(
                "No data for this domain. Will use default configuration."
            )
            return insights

        # Calculate overall stats
        total_success = sum(s[0] for s in stats.values())
        total_failure = sum(s[1] for s in stats.values())
        insights["total_attempts"] = total_success + total_failure

        if insights["total_attempts"] > 0:
            insights["success_rate"] = round(
                total_success / insights["total_attempts"], 3
            )

        # Find best options for each category
        headless_stats = {
            k: v for k, v in stats.items() if k.startswith("headless:")
        }
        wait_stats = {k: v for k, v in stats.items() if k.startswith("wait:")}
        ua_stats = {k: v for k, v in stats.items() if k.startswith("ua:")}

        if headless_stats:
            best_h = max(
                headless_stats.items(),
                key=lambda x: x[1][0] / (x[1][0] + x[1][1]) if x[1][0] + x[1][1] > 0 else 0,
            )
            insights["best_headless_mode"] = {
                "mode": best_h[0].split(":")[1],
                "success_rate": round(best_h[1][0] / max(sum(best_h[1]), 1), 3),
                "attempts": sum(best_h[1]),
            }

        if wait_stats:
            best_w = max(
                wait_stats.items(),
                key=lambda x: x[1][0] / (x[1][0] + x[1][1]) if x[1][0] + x[1][1] > 0 else 0,
            )
            insights["best_wait_strategy"] = {
                "strategy": best_w[0].split(":")[1],
                "success_rate": round(best_w[1][0] / max(sum(best_w[1]), 1), 3),
                "attempts": sum(best_w[1]),
            }

        if ua_stats:
            best_ua = max(
                ua_stats.items(),
                key=lambda x: x[1][0] / (x[1][0] + x[1][1]) if x[1][0] + x[1][1] > 0 else 0,
            )
            insights["best_user_agent"] = {
                "ua_key": best_ua[0].split(":")[1],
                "success_rate": round(best_ua[1][0] / max(sum(best_ua[1]), 1), 3),
                "attempts": sum(best_ua[1]),
            }

        # Generate recommendations
        if insights["success_rate"] < 0.5:
            insights["recommendations"].append(
                "Low success rate. Consider using visible browser or adding delays."
            )
        if insights["success_rate"] > 0.9:
            insights["recommendations"].append(
                "High success rate. Current configuration works well."
            )

        return insights

    async def get_global_stats(self) -> dict[str, Any]:
        """Get global learning statistics.

        Returns:
            Dict with global stats
        """
        stats: dict[str, Any] = {
            "total_domains": 0,
            "total_requests": 0,
            "overall_success_rate": 0.0,
            "top_performing_configs": [],
            "problematic_domains": [],
        }

        async with aiosqlite.connect(self.db_path) as db:
            # Count domains
            async with db.execute(
                "SELECT COUNT(DISTINCT domain) FROM domain_configs"
            ) as cursor:
                row = await cursor.fetchone()
                stats["total_domains"] = row[0]

            # Total requests
            async with db.execute(
                "SELECT SUM(success_count), SUM(failure_count) FROM domain_configs"
            ) as cursor:
                row = await cursor.fetchone()
                if row[0] or row[1]:
                    total = (row[0] or 0) + (row[1] or 0)
                    stats["total_requests"] = total
                    if total > 0:
                        stats["overall_success_rate"] = round(
                            (row[0] or 0) / total, 3
                        )

            # Top configs
            async with db.execute(
                """
                SELECT config_key,
                    SUM(success_count) as successes,
                    SUM(failure_count) as failures
                FROM domain_configs
                GROUP BY config_key
                ORDER BY CAST(successes AS REAL) / (successes + failures) DESC
                LIMIT 5
                """
            ) as cursor:
                async for row in cursor:
                    total = row[1] + row[2]
                    if total > 0:
                        stats["top_performing_configs"].append({
                            "config": row[0],
                            "success_rate": round(row[1] / total, 3),
                            "attempts": total,
                        })

            # Problematic domains (low success rate, enough data)
            async with db.execute(
                """
                SELECT domain,
                    SUM(success_count) as successes,
                    SUM(failure_count) as failures
                FROM domain_configs
                GROUP BY domain
                HAVING (successes + failures) >= 5
                ORDER BY CAST(successes AS REAL) / (successes + failures) ASC
                LIMIT 10
                """
            ) as cursor:
                async for row in cursor:
                    total = row[1] + row[2]
                    if total > 0:
                        rate = row[1] / total
                        if rate < 0.7:  # Less than 70% success
                            stats["problematic_domains"].append({
                                "domain": row[0],
                                "success_rate": round(rate, 3),
                                "attempts": total,
                            })

        return stats
