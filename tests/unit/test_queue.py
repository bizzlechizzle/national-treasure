"""Tests for job queue service."""

import pytest

from national_treasure.core.models import Job, JobStatus, JobType
from national_treasure.services.queue.service import JobQueue


class TestJobQueue:
    """Tests for JobQueue service."""

    @pytest.mark.asyncio
    async def test_enqueue_job(self, test_db):
        """Should enqueue a job and return ID."""
        queue = JobQueue(db_path=test_db)
        job_id = await queue.enqueue(
            JobType.CAPTURE,
            {"url": "https://example.com"},
        )
        assert job_id is not None
        assert len(job_id) > 0

    @pytest.mark.asyncio
    async def test_get_job(self, test_db):
        """Should retrieve a job by ID."""
        queue = JobQueue(db_path=test_db)
        job_id = await queue.enqueue(
            JobType.CAPTURE,
            {"url": "https://example.com"},
            priority=5,
        )

        job = await queue.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.job_type == JobType.CAPTURE
        assert job.payload["url"] == "https://example.com"
        assert job.priority == 5

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, test_db):
        """Should return None for nonexistent job."""
        queue = JobQueue(db_path=test_db)
        job = await queue.get_job("nonexistent-id")
        assert job is None

    @pytest.mark.asyncio
    async def test_cancel_job(self, test_db):
        """Should cancel a pending job."""
        queue = JobQueue(db_path=test_db)
        job_id = await queue.enqueue(JobType.CAPTURE, {})

        result = await queue.cancel_job(job_id)
        assert result is True

        job = await queue.get_job(job_id)
        assert job.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, test_db):
        """Should return False for nonexistent job."""
        queue = JobQueue(db_path=test_db)
        result = await queue.cancel_job("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_enqueue_batch(self, test_db):
        """Should enqueue multiple jobs atomically."""
        queue = JobQueue(db_path=test_db)
        jobs = [
            (JobType.CAPTURE, {"url": "https://example.com/1"}),
            (JobType.CAPTURE, {"url": "https://example.com/2"}),
            (JobType.CAPTURE, {"url": "https://example.com/3"}),
        ]

        job_ids = await queue.enqueue_batch(jobs, priority=3)
        assert len(job_ids) == 3

        for job_id in job_ids:
            job = await queue.get_job(job_id)
            assert job is not None
            assert job.priority == 3

    @pytest.mark.asyncio
    async def test_queue_stats(self, test_db):
        """Should return queue statistics."""
        queue = JobQueue(db_path=test_db)

        # Enqueue some jobs
        await queue.enqueue(JobType.CAPTURE, {})
        await queue.enqueue(JobType.CAPTURE, {})
        job_id = await queue.enqueue(JobType.CAPTURE, {})
        await queue.cancel_job(job_id)

        stats = await queue.get_queue_stats()
        assert "pending" in stats
        assert stats["pending"] == 2
        assert "cancelled" in stats
        assert stats["cancelled"] == 1

    @pytest.mark.asyncio
    async def test_job_with_dependency(self, test_db):
        """Should enqueue job with dependency."""
        queue = JobQueue(db_path=test_db)

        parent_id = await queue.enqueue(JobType.CAPTURE, {"url": "parent"})
        child_id = await queue.enqueue(
            JobType.CAPTURE,
            {"url": "child"},
            depends_on=parent_id,
        )

        child = await queue.get_job(child_id)
        assert child.depends_on == parent_id

    @pytest.mark.asyncio
    async def test_dead_letter_queue_empty(self, test_db):
        """Should return empty list when no failed jobs."""
        queue = JobQueue(db_path=test_db)
        jobs = await queue.get_dead_letter_jobs()
        assert jobs == []
