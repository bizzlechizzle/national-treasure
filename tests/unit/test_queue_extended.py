"""Extended queue service tests for full coverage."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from national_treasure.core.database import init_database
from national_treasure.core.models import Job, JobStatus, JobType
from national_treasure.services.queue.service import JobQueue


@pytest.fixture
async def initialized_db(tmp_path):
    """Create an initialized database."""
    db_path = tmp_path / "queue.db"
    await init_database(str(db_path))
    return db_path


class TestJobQueueWorkers:
    """Test job queue worker functionality."""

    @pytest.mark.asyncio
    async def test_start_creates_workers(self, initialized_db):
        """Should create worker tasks on start."""
        queue = JobQueue(db_path=initialized_db, max_concurrent=3)
        await queue.start(num_workers=2)

        assert len(queue._workers) == 2
        assert queue._running is True

        await queue.stop()
        assert len(queue._workers) == 0

    @pytest.mark.asyncio
    async def test_start_already_running(self, initialized_db):
        """Should not start if already running."""
        queue = JobQueue(db_path=initialized_db)
        await queue.start(num_workers=1)

        # Try to start again
        await queue.start(num_workers=5)  # Should be ignored

        assert len(queue._workers) == 1  # Still only 1 worker

        await queue.stop()

    @pytest.mark.asyncio
    async def test_stop_waits_for_workers(self, initialized_db):
        """Should wait for workers to finish."""
        queue = JobQueue(db_path=initialized_db)
        await queue.start(num_workers=1)

        # Stop should cancel workers
        await queue.stop(wait=True)

        assert queue._running is False
        assert len(queue._workers) == 0

    @pytest.mark.asyncio
    async def test_register_handler(self, initialized_db):
        """Should register job handler."""
        queue = JobQueue(db_path=initialized_db)

        async def handler(job: Job):
            return {"success": True}

        queue.register_handler(JobType.CAPTURE, handler)

        assert JobType.CAPTURE in queue._handlers
        assert queue._handlers[JobType.CAPTURE] is handler

    @pytest.mark.asyncio
    async def test_get_queue_stats(self, initialized_db):
        """Should return queue statistics."""
        queue = JobQueue(db_path=initialized_db)

        # Add some jobs
        await queue.enqueue(JobType.CAPTURE, {"url": "https://a.com"})
        await queue.enqueue(JobType.CAPTURE, {"url": "https://b.com"})

        stats = await queue.get_queue_stats()

        assert "pending" in stats
        assert stats["pending"] >= 2


class TestJobQueueDeadLetter:
    """Test dead letter queue functionality."""

    @pytest.mark.asyncio
    async def test_get_dead_letter_jobs_empty(self, initialized_db):
        """Should return empty list when no dead letter jobs."""
        queue = JobQueue(db_path=initialized_db)
        jobs = await queue.get_dead_letter_jobs()

        assert jobs == []


class TestJobQueueClaim:
    """Test job claiming functionality."""

    @pytest.mark.asyncio
    async def test_claim_next_job(self, initialized_db):
        """Should claim next available job."""
        queue = JobQueue(db_path=initialized_db)

        # Add a job
        await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})

        # Claim it
        job = await queue._claim_next_job()

        assert job is not None
        assert job.status == JobStatus.RUNNING

    @pytest.mark.asyncio
    async def test_claim_respects_priority(self, initialized_db):
        """Should claim higher priority jobs first."""
        queue = JobQueue(db_path=initialized_db)

        # Add jobs with different priorities
        await queue.enqueue(JobType.CAPTURE, {"url": "https://low.com"}, priority=1)
        await queue.enqueue(JobType.CAPTURE, {"url": "https://high.com"}, priority=10)

        # First claim should get high priority job
        job = await queue._claim_next_job()

        assert job is not None
        assert job.payload["url"] == "https://high.com"


class TestJobQueueProcess:
    """Test job processing functionality."""

    @pytest.mark.asyncio
    async def test_process_job_success(self, initialized_db):
        """Should process job successfully."""
        queue = JobQueue(db_path=initialized_db)

        async def handler(job: Job):
            return {"processed": True}

        queue.register_handler(JobType.CAPTURE, handler)

        # Add and claim job
        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        # Process it
        await queue._process_job(job)

        # Check job is completed
        updated_job = await queue.get_job(job_id)
        assert updated_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_job_failure(self, initialized_db):
        """Should handle job failure with retry."""
        queue = JobQueue(db_path=initialized_db, max_retries=3)

        async def handler(job: Job):
            raise Exception("Processing failed")

        queue.register_handler(JobType.CAPTURE, handler)

        # Add and claim job
        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        # Process it (should fail and retry)
        await queue._process_job(job)

        # Check job retry count increased
        updated_job = await queue.get_job(job_id)
        assert updated_job.retry_count >= 1


class TestJobQueueBatch:
    """Test batch operations."""

    @pytest.mark.asyncio
    async def test_enqueue_batch(self, initialized_db):
        """Should enqueue multiple jobs."""
        queue = JobQueue(db_path=initialized_db)

        # enqueue_batch expects list of (JobType, payload) tuples
        jobs = [
            (JobType.CAPTURE, {"url": "https://a.com"}),
            (JobType.CAPTURE, {"url": "https://b.com"}),
            (JobType.CAPTURE, {"url": "https://c.com"}),
        ]

        job_ids = await queue.enqueue_batch(jobs)

        assert len(job_ids) == 3
        for job_id in job_ids:
            job = await queue.get_job(job_id)
            assert job is not None
            assert job.status == JobStatus.PENDING


class TestJobQueueProcessing:
    """Test job processing functionality."""

    @pytest.mark.asyncio
    async def test_process_job_no_handler(self, initialized_db):
        """Should fail job when no handler registered."""
        queue = JobQueue(db_path=initialized_db)

        # Add and claim job without registering handler
        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        await queue._process_job(job)

        # Job should be failed
        updated_job = await queue.get_job(job_id)
        assert updated_job.status == JobStatus.FAILED
        assert "No handler" in updated_job.error

    @pytest.mark.asyncio
    async def test_complete_job(self, initialized_db):
        """Should mark job as completed."""
        queue = JobQueue(db_path=initialized_db)

        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        await queue._complete_job(job, {"success": True})

        updated_job = await queue.get_job(job_id)
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.completed_at is not None

    @pytest.mark.asyncio
    async def test_fail_job(self, initialized_db):
        """Should mark job as failed."""
        queue = JobQueue(db_path=initialized_db)

        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        await queue._fail_job(job, "Test error")

        updated_job = await queue.get_job(job_id)
        assert updated_job.status == JobStatus.FAILED
        assert "Test error" in updated_job.error

    @pytest.mark.asyncio
    async def test_handle_job_failure_with_retry(self, initialized_db):
        """Should retry job on failure."""
        queue = JobQueue(db_path=initialized_db, max_retries=3)

        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        # First failure should trigger retry
        await queue._handle_job_failure(job, "First failure")

        updated_job = await queue.get_job(job_id)
        assert updated_job.status == JobStatus.PENDING  # Back to pending for retry
        assert updated_job.retry_count == 1

    @pytest.mark.asyncio
    async def test_handle_job_failure_max_retries(self, initialized_db):
        """Should move to dead letter after max retries."""
        queue = JobQueue(db_path=initialized_db, max_retries=1)

        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()
        job.retry_count = 1  # Already at max

        await queue._handle_job_failure(job, "Final failure")

        updated_job = await queue.get_job(job_id)
        assert updated_job.status == JobStatus.FAILED


class TestJobQueueDeadLetterExtended:
    """Extended dead letter queue tests."""

    @pytest.mark.asyncio
    async def test_move_to_dead_letter(self, initialized_db):
        """Should move job to dead letter queue."""
        queue = JobQueue(db_path=initialized_db, max_retries=0)

        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://example.com"})
        job = await queue._claim_next_job()

        await queue._move_to_dead_letter(job, "Permanent failure")

        dead_letters = await queue.get_dead_letter_jobs()
        assert len(dead_letters) >= 1
        assert any(dl.get("job_id") == job_id for dl in dead_letters)

    @pytest.mark.asyncio
    async def test_retry_dead_letter(self, initialized_db):
        """Should retry job from dead letter queue."""
        queue = JobQueue(db_path=initialized_db, max_retries=0)

        # Create and fail a job
        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://retry.com"})
        job = await queue._claim_next_job()
        await queue._fail_job(job, "Initial failure")
        await queue._move_to_dead_letter(job, "Initial failure")

        # Retry it
        new_job_id = await queue.retry_dead_letter(job_id)

        assert new_job_id is not None
        new_job = await queue.get_job(new_job_id)
        assert new_job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_retry_dead_letter_not_found(self, initialized_db):
        """Should return None for non-existent dead letter job."""
        queue = JobQueue(db_path=initialized_db)

        result = await queue.retry_dead_letter("nonexistent-job-id")
        assert result is None


class TestJobQueueWorkerLoop:
    """Test worker loop functionality."""

    @pytest.mark.asyncio
    async def test_worker_processes_jobs(self, initialized_db):
        """Worker should process available jobs."""
        queue = JobQueue(db_path=initialized_db)

        processed = []

        async def handler(job: Job):
            processed.append(job.job_id)
            return {"processed": True}

        queue.register_handler(JobType.CAPTURE, handler)

        # Add a job
        job_id = await queue.enqueue(JobType.CAPTURE, {"url": "https://worker.com"})

        # Start workers
        await queue.start(num_workers=1)

        # Wait for processing
        await asyncio.sleep(1)

        await queue.stop(wait=True)

        assert job_id in processed

    @pytest.mark.asyncio
    async def test_stop_without_wait(self, initialized_db):
        """Should stop workers without waiting."""
        queue = JobQueue(db_path=initialized_db)
        await queue.start(num_workers=1)

        await queue.stop(wait=False)

        assert queue._running is False
