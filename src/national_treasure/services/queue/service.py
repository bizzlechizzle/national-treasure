"""SQLite-backed job queue with priority, retry, and dead letter queue."""

import asyncio
import json
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any

import aiosqlite

from national_treasure.core.config import get_config
from national_treasure.core.models import Job, JobStatus, JobType


class JobQueue:
    """Persistent job queue with SQLite backend.

    Features:
    - Priority-based scheduling
    - Automatic retry with exponential backoff
    - Job dependencies
    - Dead letter queue for failed jobs
    - Concurrent worker support
    """

    def __init__(
        self,
        db_path: str | None = None,
        max_retries: int = 3,
        base_retry_delay_ms: int = 1000,
        max_concurrent: int = 5,
    ):
        """Initialize job queue.

        Args:
            db_path: Path to SQLite database
            max_retries: Maximum retry attempts
            base_retry_delay_ms: Base delay for exponential backoff
            max_concurrent: Maximum concurrent jobs
        """
        self.db_path = db_path or str(get_config().database_path)
        self.max_retries = max_retries
        self.base_retry_delay_ms = base_retry_delay_ms
        self.max_concurrent = max_concurrent

        self._handlers: dict[JobType, Callable[[Job], Coroutine[Any, Any, Any]]] = {}
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._semaphore: asyncio.Semaphore | None = None

    def register_handler(
        self,
        job_type: JobType,
        handler: Callable[[Job], Coroutine[Any, Any, Any]],
    ) -> None:
        """Register a handler for a job type.

        Args:
            job_type: Type of job to handle
            handler: Async function to process job
        """
        self._handlers[job_type] = handler

    async def enqueue(
        self,
        job_type: JobType,
        payload: dict[str, Any],
        priority: int = 0,
        depends_on: str | None = None,
        scheduled_for: datetime | None = None,
    ) -> str:
        """Add a job to the queue.

        Args:
            job_type: Type of job
            payload: Job payload data
            priority: Higher priority = processed first
            depends_on: Job ID this depends on
            scheduled_for: When to process (None = immediately)

        Returns:
            Job ID
        """
        job = Job(
            job_type=job_type,
            payload=payload,
            priority=priority,
            depends_on=depends_on,
            scheduled_for=scheduled_for or datetime.now(UTC),
        )

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO jobs (
                    job_id, job_type, payload, status, priority,
                    depends_on, scheduled_for, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.job_type.value,
                    json.dumps(job.payload),
                    job.status.value,
                    job.priority,
                    job.depends_on,
                    job.scheduled_for.isoformat() if job.scheduled_for else None,
                    job.created_at.isoformat(),
                ),
            )
            await db.commit()

        return job.job_id

    async def enqueue_batch(
        self,
        jobs: list[tuple[JobType, dict[str, Any]]],
        priority: int = 0,
    ) -> list[str]:
        """Add multiple jobs to the queue atomically.

        Args:
            jobs: List of (job_type, payload) tuples
            priority: Priority for all jobs

        Returns:
            List of job IDs
        """
        job_ids = []
        now = datetime.now(UTC)

        async with aiosqlite.connect(self.db_path) as db:
            for job_type, payload in jobs:
                job = Job(
                    job_type=job_type,
                    payload=payload,
                    priority=priority,
                    scheduled_for=now,
                )
                await db.execute(
                    """
                    INSERT INTO jobs (
                        job_id, job_type, payload, status, priority,
                        scheduled_for, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.job_id,
                        job.job_type.value,
                        json.dumps(job.payload),
                        job.status.value,
                        job.priority,
                        job.scheduled_for.isoformat(),
                        job.created_at.isoformat(),
                    ),
                )
                job_ids.append(job.job_id)
            await db.commit()

        return job_ids

    async def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_job(row)
        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled, False if not found or not cancellable
        """
        async with aiosqlite.connect(self.db_path) as db:
            result = await db.execute(
                """
                UPDATE jobs SET status = ?, updated_at = ?
                WHERE job_id = ? AND status = ?
                """,
                (
                    JobStatus.CANCELLED.value,
                    datetime.now(UTC).isoformat(),
                    job_id,
                    JobStatus.PENDING.value,
                ),
            )
            await db.commit()
            return result.rowcount > 0

    async def get_queue_stats(self) -> dict[str, int]:
        """Get queue statistics.

        Returns:
            Dict with counts by status
        """
        stats = {}
        async with aiosqlite.connect(self.db_path) as db, db.execute(
            """
                SELECT status, COUNT(*) as count
                FROM jobs
                GROUP BY status
                """
        ) as cursor:
            async for row in cursor:
                stats[row[0]] = row[1]
        return stats

    async def start(self, num_workers: int | None = None) -> None:
        """Start processing jobs.

        Args:
            num_workers: Number of worker tasks (default: max_concurrent)
        """
        if self._running:
            return

        self._running = True
        num_workers = num_workers or self.max_concurrent
        self._semaphore = asyncio.Semaphore(num_workers)

        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

    async def stop(self, wait: bool = True) -> None:
        """Stop processing jobs.

        Args:
            wait: Wait for current jobs to complete
        """
        self._running = False

        if wait:
            # Wait for workers to finish current jobs
            for worker in self._workers:
                worker.cancel()
                try:
                    await worker
                except asyncio.CancelledError:
                    pass

        self._workers.clear()

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop that processes jobs."""
        while self._running:
            try:
                job = await self._claim_next_job()
                if job:
                    await self._process_job(job)
                else:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but keep worker alive
                await asyncio.sleep(1)

    async def _claim_next_job(self) -> Job | None:
        """Claim the next available job atomically.

        Returns:
            Job if one was claimed, None otherwise
        """
        now = datetime.now(UTC)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Release stale running jobs (>30 min old) - job lease timeout
            await db.execute("""
                UPDATE jobs
                SET status = 'pending', started_at = NULL, updated_at = ?
                WHERE status = 'running'
                AND started_at < datetime('now', '-30 minutes')
            """, (now.isoformat(),))

            # Find next eligible job:
            # - Status is PENDING
            # - Scheduled time has passed
            # - No unfulfilled dependencies
            # - Order by priority (desc), then scheduled_for (asc)
            async with db.execute(
                """
                SELECT j.* FROM jobs j
                WHERE j.status = ?
                AND j.scheduled_for <= ?
                AND (
                    j.depends_on IS NULL
                    OR EXISTS (
                        SELECT 1 FROM jobs dep
                        WHERE dep.job_id = j.depends_on
                        AND dep.status = ?
                    )
                )
                ORDER BY j.priority DESC, j.scheduled_for ASC
                LIMIT 1
                """,
                (JobStatus.PENDING.value, now.isoformat(), JobStatus.COMPLETED.value),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                job = self._row_to_job(row)

            # Try to claim it
            result = await db.execute(
                """
                UPDATE jobs
                SET status = ?, started_at = ?, updated_at = ?
                WHERE job_id = ? AND status = ?
                """,
                (
                    JobStatus.RUNNING.value,
                    now.isoformat(),
                    now.isoformat(),
                    job.job_id,
                    JobStatus.PENDING.value,
                ),
            )
            await db.commit()

            if result.rowcount > 0:
                job.status = JobStatus.RUNNING
                job.started_at = now
                return job

        return None

    async def _process_job(self, job: Job) -> None:
        """Process a single job."""
        handler = self._handlers.get(job.job_type)
        if not handler:
            await self._fail_job(job, f"No handler for job type: {job.job_type}")
            return

        try:
            result = await handler(job)
            await self._complete_job(job, result)
        except Exception as e:
            await self._handle_job_failure(job, str(e))

    async def _complete_job(self, job: Job, result: Any = None) -> None:
        """Mark job as completed."""
        now = datetime.now(UTC)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = ?, completed_at = ?, updated_at = ?, result = ?
                WHERE job_id = ?
                """,
                (
                    JobStatus.COMPLETED.value,
                    now.isoformat(),
                    now.isoformat(),
                    json.dumps(result) if result else None,
                    job.job_id,
                ),
            )
            await db.commit()

    async def _handle_job_failure(self, job: Job, error: str) -> None:
        """Handle job failure with retry logic."""
        job.retry_count += 1

        if job.retry_count >= self.max_retries:
            await self._fail_job(job, error)
            await self._move_to_dead_letter(job, error)
        else:
            # Calculate backoff delay
            delay_ms = self.base_retry_delay_ms * (2 ** (job.retry_count - 1))
            next_attempt = datetime.now(UTC) + timedelta(milliseconds=delay_ms)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    UPDATE jobs
                    SET status = ?, retry_count = ?, scheduled_for = ?,
                        updated_at = ?, error = ?
                    WHERE job_id = ?
                    """,
                    (
                        JobStatus.PENDING.value,
                        job.retry_count,
                        next_attempt.isoformat(),
                        datetime.now(UTC).isoformat(),
                        error,
                        job.job_id,
                    ),
                )
                await db.commit()

    async def _fail_job(self, job: Job, error: str) -> None:
        """Mark job as failed."""
        now = datetime.now(UTC)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE jobs
                SET status = ?, completed_at = ?, updated_at = ?, error = ?
                WHERE job_id = ?
                """,
                (
                    JobStatus.FAILED.value,
                    now.isoformat(),
                    now.isoformat(),
                    error,
                    job.job_id,
                ),
            )
            await db.commit()

    async def _move_to_dead_letter(self, job: Job, error: str) -> None:
        """Move failed job to dead letter queue."""
        now = datetime.now(UTC)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO job_dead_letter (
                    job_id, job_type, payload, error, retry_count,
                    original_created_at, failed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.job_type.value,
                    json.dumps(job.payload),
                    error,
                    job.retry_count,
                    job.created_at.isoformat(),
                    now.isoformat(),
                ),
            )
            await db.commit()

    async def retry_dead_letter(self, job_id: str) -> str | None:
        """Retry a job from the dead letter queue.

        Args:
            job_id: Job ID in dead letter queue

        Returns:
            New job ID if successful, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM job_dead_letter WHERE job_id = ?", (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                # Re-enqueue the job
                new_job_id = await self.enqueue(
                    JobType(row["job_type"]),
                    json.loads(row["payload"]),
                )

                # Remove from dead letter queue
                await db.execute(
                    "DELETE FROM job_dead_letter WHERE job_id = ?", (job_id,)
                )
                await db.commit()

                return new_job_id

    async def get_dead_letter_jobs(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get jobs from dead letter queue.

        Args:
            limit: Maximum jobs to return
            offset: Offset for pagination

        Returns:
            List of dead letter job records
        """
        jobs = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM job_dead_letter
                ORDER BY failed_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ) as cursor:
                async for row in cursor:
                    jobs.append(dict(row))
        return jobs

    def _row_to_job(self, row: aiosqlite.Row) -> Job:
        """Convert database row to Job model."""
        return Job(
            job_id=row["job_id"],
            job_type=JobType(row["job_type"]),
            payload=json.loads(row["payload"]),
            status=JobStatus(row["status"]),
            priority=row["priority"],
            retry_count=row["retry_count"],
            depends_on=row["depends_on"],
            scheduled_for=datetime.fromisoformat(row["scheduled_for"])
            if row["scheduled_for"]
            else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None,
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
            error=row["error"],
        )
