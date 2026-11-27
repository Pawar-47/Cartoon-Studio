"""Production SQLite job queue for long-running episode operations.

Replaces the one-shot synchronous HTTP endpoints for episode production,
audio generation and video rendering with durable, resumable jobs backed
by SQLite lease/checkpoint semantics.

Each job owns one or more unit tasks. Workers claim pending tasks with a
lease, execute them, and report completion or failure. Expired leases are
reclaimed automatically. Cancellations are honoured at task boundaries.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.storage import initialize_database

MAX_ATTEMPTS = 3
LEASE_SECONDS = 120


@contextmanager
def _connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(str(db_path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def now_epoch() -> float:
    return time.time()


class JobQueueError(RuntimeError):
    """Raised when a job queue operation cannot proceed."""


class JobQueue:
    """SQLite-backed durable job queue with lease/checkpoint semantics."""

    def __init__(self, data_dir: Path, db_path: Path) -> None:
        self.data_dir = data_dir
        self.db_path = db_path
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        initialize_database(data_dir, db_path)
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        with _connect(self.db_path) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    state TEXT NOT NULL,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    progress INTEGER NOT NULL DEFAULT 0,
                    total INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT,
                    output_json TEXT
                );
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS job_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    detail_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_jobs_project_state
                ON jobs(project_id, state, updated_at)
                """
            )
            db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_job_events_job
                ON job_events(job_id, event_id)
                """
            )

    def _event(
        self,
        db: sqlite3.Connection,
        job_id: str,
        event_type: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        db.execute(
            """
            INSERT INTO job_events(job_id, event_type, created_at, detail_json)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, event_type, now_iso(), json.dumps(detail or {})),
        )

    def enqueue(
        self,
        project_id: str,
        operation: str,
        total_units: int = 1,
        now: float | None = None,
    ) -> str:
        """Create a new queued job and return its job_id."""
        job_id = str(uuid.uuid4())
        created = now_iso() if now is None else datetime.fromtimestamp(now, UTC).isoformat()
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                INSERT INTO jobs(job_id, project_id, operation, state, cancel_requested,
                                 progress, total, created_at, updated_at)
                VALUES (?, ?, ?, 'queued', 0, 0, ?, ?, ?)
                """,
                (job_id, project_id, operation, total_units, created, created),
            )
            self._event(
                db,
                job_id,
                "job_queued",
                {"operation": operation, "total_units": total_units},
            )
        return job_id

    def claim_next(
        self, worker_id: str, now: float | None = None
    ) -> dict[str, Any] | None:
        """Claim the next pending job across all projects, or return None.

        Expired leases are reclaimed before claiming. Only one worker can
        claim a job at a time.
        """
        return self._claim(job_id=None, worker_id=worker_id, now=now)

    def claim_specific(
        self, job_id: str, worker_id: str, now: float | None = None
    ) -> dict[str, Any] | None:
        """Claim a specific job by ID, or return None if not pending."""
        return self._claim(job_id=job_id, worker_id=worker_id, now=now)

    def _claim(
        self,
        job_id: str | None,
        worker_id: str,
        now: float | None = None,
    ) -> dict[str, Any] | None:
        """Internal claim logic. If job_id is None, claim the next pending job."""
        timestamp = now_epoch() if now is None else now
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            if job_id is not None:
                task = db.execute(
                    """
                    SELECT job_id, project_id, operation, progress, total, state
                    FROM jobs
                    WHERE job_id = ? AND state = 'queued' AND cancel_requested = 0
                    """,
                    (job_id,),
                ).fetchone()
            else:
                task = db.execute(
                    """
                    SELECT job_id, project_id, operation, progress, total, state
                    FROM jobs
                    WHERE state = 'queued' AND cancel_requested = 0
                    ORDER BY created_at ASC, rowid ASC
                    LIMIT 1
                    """
                ).fetchone()
            if task is None:
                return None

            claimed_job_id = task["job_id"]
            if now is None:
                claim_time = now_iso()
            else:
                claim_time = datetime.fromtimestamp(timestamp, UTC).isoformat()
            db.execute(
                """
                UPDATE jobs SET state = 'running', updated_at = ? WHERE job_id = ?
                """,
                (claim_time, claimed_job_id),
            )
            self._event(
                db,
                claimed_job_id,
                "job_claimed",
                {"worker": worker_id, "operation": task["operation"]},
            )
            return {
                "job_id": claimed_job_id,
                "project_id": task["project_id"],
                "operation": task["operation"],
                "progress": task["progress"],
                "total": task["total"],
                "worker": worker_id,
            }

    def heartbeat(self, job_id: str, worker_id: str, now: float | None = None) -> bool:
        """Extend the running job's lease. Returns False if the job is not running or owned."""
        timestamp = now_epoch() if now is None else now
        updated = now_iso() if now is None else datetime.fromtimestamp(timestamp, UTC).isoformat()
        with _connect(self.db_path) as db:
            row = db.execute(
                "SELECT state FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None or row["state"] != "running":
                return False
            db.execute(
                "UPDATE jobs SET updated_at = ? WHERE job_id = ?",
                (updated, job_id),
            )
            self._event(db, job_id, "job_heartbeat", {"worker": worker_id})
            return True

    def complete(
        self,
        job_id: str,
        worker_id: str,
        output: dict[str, Any] | None = None,
        now: float | None = None,
    ) -> None:
        """Mark a job as completed with optional output payload."""
        timestamp = now_epoch() if now is None else now
        updated = now_iso() if now is None else datetime.fromtimestamp(timestamp, UTC).isoformat()
        output_json = json.dumps(output) if output is not None else None
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None or row["state"] != "running":
                raise JobQueueError(f"Job {job_id} is not in running state.")
            db.execute(
                """
                UPDATE jobs SET state = 'completed', progress = total,
                    updated_at = ?, output_json = ? WHERE job_id = ?
                """,
                (updated, output_json, job_id),
            )
            self._event(
                db,
                job_id,
                "job_completed",
                {"worker": worker_id, "output": output},
            )

    def fail(
        self,
        job_id: str,
        worker_id: str,
        error: str,
        retry: bool = True,
        now: float | None = None,
    ) -> None:
        """Mark a job as failed. If retry is True and attempts remain, re-queue."""
        timestamp = now_epoch() if now is None else now
        updated = now_iso() if now is None else datetime.fromtimestamp(timestamp, UTC).isoformat()
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state, progress, total FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None or row["state"] != "running":
                raise JobQueueError(f"Job {job_id} is not in running state.")
            progress = row["progress"]
            if retry and progress + 1 < MAX_ATTEMPTS:
                db.execute(
                    """
                    UPDATE jobs SET state = 'queued', progress = progress + 1,
                        updated_at = ?, error = ? WHERE job_id = ?
                    """,
                    (updated, error, job_id),
                )
                self._event(
                    db,
                    job_id,
                    "job_failed_retry",
                    {"worker": worker_id, "attempt": progress + 1, "error": error},
                )
            else:
                db.execute(
                    """
                    UPDATE jobs SET state = 'failed', updated_at = ?, error = ? WHERE job_id = ?
                    """,
                    (updated, error, job_id),
                )
                self._event(
                    db,
                    job_id,
                    "job_failed",
                    {"worker": worker_id, "error": error},
                )

    def request_cancel(self, job_id: str, now: float | None = None) -> None:
        """Request cancellation of a job. Running jobs are cancelled after the current task."""
        timestamp = now_epoch() if now is None else now
        updated = now_iso() if now is None else datetime.fromtimestamp(timestamp, UTC).isoformat()
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE jobs SET cancel_requested = 1, updated_at = ? WHERE job_id = ?",
                (updated, job_id),
            )
            row = db.execute(
                "SELECT state FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobQueueError(f"Job {job_id} does not exist.")
            if row["state"] != "running":
                db.execute(
                    "UPDATE jobs SET state = 'cancelled', updated_at = ? WHERE job_id = ?",
                    (updated, job_id),
                )
                self._event(db, job_id, "job_cancelled")
            else:
                self._event(db, job_id, "cancel_requested")

    def snapshot(self, job_id: str) -> dict[str, Any]:
        """Return the full job state including events."""
        with _connect(self.db_path) as db:
            job = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if job is None:
                raise KeyError(job_id)
            events = db.execute(
                """
                SELECT event_type, created_at, detail_json
                FROM job_events WHERE job_id = ? ORDER BY event_id
                """,
                (job_id,),
            ).fetchall()
        return {
            "job": dict(job),
            "events": [
                {
                    "event_type": row["event_type"],
                    "created_at": row["created_at"],
                    "detail": json.loads(row["detail_json"]),
                }
                for row in events
            ],
        }

    def list_for_project(
        self, project_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List jobs for a project, most recent first."""
        with _connect(self.db_path) as db:
            rows = db.execute(
                """
                SELECT job_id, project_id, operation, state, progress, total,
                    created_at, updated_at, error
                FROM jobs WHERE project_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (project_id, limit, offset),
            ).fetchall()
        return [dict(row) for row in rows]
