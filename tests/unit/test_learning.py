"""Tests for domain learning service."""

import pytest

from national_treasure.core.models import BrowserConfig, HeadlessMode, WaitStrategy
from national_treasure.services.learning.domain import DomainLearner, ArmStats


class TestArmStats:
    """Tests for ArmStats class."""

    def test_total_calculation(self):
        """Total should be sum of successes and failures."""
        arm = ArmStats(arm_id="test", successes=5, failures=3)
        assert arm.total == 8

    def test_sample_beta_returns_float(self):
        """Beta sample should return float between 0 and 1."""
        arm = ArmStats(arm_id="test", successes=5, failures=3)
        sample = arm.sample_beta()
        assert 0.0 <= sample <= 1.0

    def test_sample_beta_with_no_data(self):
        """Beta sample should work with no data (uniform prior)."""
        arm = ArmStats(arm_id="test", successes=0, failures=0)
        sample = arm.sample_beta()
        assert 0.0 <= sample <= 1.0


class TestDomainLearner:
    """Tests for DomainLearner service."""

    @pytest.mark.asyncio
    async def test_get_best_config_new_domain(self, test_db):
        """Should return valid config for new domain."""
        learner = DomainLearner(db_path=test_db)

        config = await learner.get_best_config("newdomain.com")
        assert isinstance(config, BrowserConfig)
        assert config.headless_mode in [HeadlessMode.SHELL, HeadlessMode.NEW, HeadlessMode.VISIBLE]
        assert config.wait_strategy in [WaitStrategy.NETWORKIDLE, WaitStrategy.DOMCONTENTLOADED, WaitStrategy.LOAD]
        assert config.stealth_enabled is True

    @pytest.mark.asyncio
    async def test_record_outcome(self, test_db):
        """Should record request outcome."""
        learner = DomainLearner(db_path=test_db)

        config = BrowserConfig(
            headless_mode=HeadlessMode.SHELL,
            wait_strategy=WaitStrategy.NETWORKIDLE,
            user_agent=DomainLearner.USER_AGENT_MAP["chrome_mac"],
        )

        await learner.record_outcome(
            domain="example.com",
            config=config,
            success=True,
            details={"response_code": 200},
        )

        # Get insights - each outcome records 3 arms (headless, wait, ua)
        insights = await learner.get_domain_insights("example.com")
        assert insights["total_attempts"] == 3  # 3 arms recorded
        assert insights["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_learning_from_outcomes(self, test_db):
        """Learner should improve based on outcomes."""
        learner = DomainLearner(db_path=test_db)

        # Record many successes with SHELL mode
        shell_config = BrowserConfig(
            headless_mode=HeadlessMode.SHELL,
            wait_strategy=WaitStrategy.NETWORKIDLE,
            user_agent=DomainLearner.USER_AGENT_MAP["chrome_mac"],
        )
        for _ in range(10):
            await learner.record_outcome("learned.com", shell_config, success=True)

        # Record failures with VISIBLE mode
        visible_config = BrowserConfig(
            headless_mode=HeadlessMode.VISIBLE,
            wait_strategy=WaitStrategy.NETWORKIDLE,
            user_agent=DomainLearner.USER_AGENT_MAP["chrome_mac"],
        )
        for _ in range(10):
            await learner.record_outcome("learned.com", visible_config, success=False)

        # The learner should now prefer SHELL mode
        insights = await learner.get_domain_insights("learned.com")
        assert insights["best_headless_mode"]["mode"] == "shell"
        assert insights["best_headless_mode"]["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_global_stats(self, test_db):
        """Should return global statistics."""
        learner = DomainLearner(db_path=test_db)

        config = BrowserConfig(
            headless_mode=HeadlessMode.SHELL,
            wait_strategy=WaitStrategy.NETWORKIDLE,
            user_agent=DomainLearner.USER_AGENT_MAP["chrome_mac"],
        )

        # Record outcomes for multiple domains
        for _ in range(5):
            await learner.record_outcome("domain1.com", config, success=True)
        for _ in range(3):
            await learner.record_outcome("domain2.com", config, success=True)
        for _ in range(2):
            await learner.record_outcome("domain2.com", config, success=False)

        stats = await learner.get_global_stats()
        assert stats["total_domains"] == 2
        assert stats["total_requests"] >= 10  # Counting each arm separately

    @pytest.mark.asyncio
    async def test_domain_insights_recommendations(self, test_db):
        """Should provide recommendations based on success rate."""
        learner = DomainLearner(db_path=test_db)

        config = BrowserConfig(
            headless_mode=HeadlessMode.SHELL,
            wait_strategy=WaitStrategy.NETWORKIDLE,
            user_agent=DomainLearner.USER_AGENT_MAP["chrome_mac"],
        )

        # Low success rate
        for _ in range(7):
            await learner.record_outcome("problematic.com", config, success=False)
        for _ in range(3):
            await learner.record_outcome("problematic.com", config, success=True)

        insights = await learner.get_domain_insights("problematic.com")
        assert insights["success_rate"] < 0.5
        assert len(insights["recommendations"]) > 0
