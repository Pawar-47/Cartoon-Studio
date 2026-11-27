"""Durable SQLite job queue for long-running Cartoon Studio operations.

Job state lives in the project index database: the ``jobs`` and ``job_events``
tables are created by schema migrations 3 and 4 in :mod:`app.storage`, so the
queue never defines a second, divergent copy of that schema.

What this module guarantees today:

- durable job records with a monotonic event history;
- one claim at a time (``BEGIN IMMEDIATE``), recorded with a lease owner and an
  expiry so a job whose worker died can be reclaimed by the next claim;
- bounded retries counted in whole attempts (``MAX_ATTEMPTS``);
- cancellation requests that the caller honours at its next task boundary;
- progress and output persisted for polling through the HTTP API.

What it does not do: it does not run work by itself. The FastAPI routes enqueue
a job, claim it, execute the Godot/FFmpeg call in-process and record the
outcome, so a cancellation cannot interrupt a call that is already running and a
crash mid-call is only recovered after the lease expires and the job is claimed
again.
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
MAX_LIST_LIMIT = 200


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


def _timestamp(value: float | None) -> float:
    return now_epoch() if value is None else value


def _iso(value: float | None) -> str:
    return now_iso() if value is None else datetime.fromtimestamp(value, UTC).isoformat()


class JobQueueError(RuntimeError):
    """Raised when a job queue operation cannot proceed."""


def _require_running(db: sqlite3.Connection, job_id: str, worker_id: str) -> sqlite3.Row:
    """Return the job row, or raise if it is missing, finished or leased elsewhere."""
    row = db.execute(
        """
        SELECT state, attempts, progress, total, lease_owner
        FROM jobs WHERE job_id = ?
        """,
        (job_id,),
    ).fetchone()
    if row is None or row["state"] != "running":
        raise JobQueueError(f"Job {job_id} is not in running state.")
    owner = row["lease_owner"]
    if owner is not None and owner != worker_id:
        raise JobQueueError(f"Job {job_id} is leased to another worker.")
    return row


class JobQueue:
    """SQLite-backed durable job queue with lease and checkpoint semantics."""

    def __init__(self, data_dir: Path, db_path: Path) -> None:
        self.data_dir = data_dir
        self.db_path = db_path
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        initialize_database(data_dir, db_path)

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

    def _reclaim_expired(self, db: sqlite3.Connection, timestamp: float) -> list[str]:
        """Return expired running jobs to the queue so another worker can take them."""
        rows = db.execute(
            """
            SELECT job_id FROM jobs
            WHERE state = 'running'
              AND lease_expires_at IS NOT NULL
              AND lease_expires_at < ?
            """,
            (timestamp,),
        ).fetchall()
        reclaimed = [str(row["job_id"]) for row in rows]
        for job_id in reclaimed:
            db.execute(
                """
                UPDATE jobs
                SET state = 'queued', lease_owner = NULL, lease_expires_at = NULL,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (_iso(timestamp), job_id),
            )
            self._event(db, job_id, "job_lease_expired", {"reclaimed_at": _iso(timestamp)})
        return reclaimed

    def enqueue(
        self,
        project_id: str,
        operation: str,
        total_units: int = 1,
        now: float | None = None,
    ) -> str:
        """Create a new queued job and return its job_id."""
        job_id = str(uuid.uuid4())
        created = _iso(now)
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """
                INSERT INTO jobs(job_id, project_id, operation, state, cancel_requested,
                                 attempts, progress, total, created_at, updated_at)
                VALUES (?, ?, ?, 'queued', 0, 0, 0, ?, ?, ?)
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
        self,
        worker_id: str,
        now: float | None = None,
        lease_seconds: float | None = None,
    ) -> dict[str, Any] | None:
        """Claim the oldest queued job across all projects, or return None."""
        return self._claim(
            job_id=None, worker_id=worker_id, now=now, lease_seconds=lease_seconds
        )

    def claim_specific(
        self,
        job_id: str,
        worker_id: str,
        now: float | None = None,
        lease_seconds: float | None = None,
    ) -> dict[str, Any] | None:
        """Claim a specific queued job by ID, or return None if it is not claimable.

        ``lease_seconds`` overrides the default lease for work known to run
        longer than LEASE_SECONDS, so a long operation is not reclaimed from its
        own worker while it is still running.
        """
        return self._claim(
            job_id=job_id, worker_id=worker_id, now=now, lease_seconds=lease_seconds
        )

    def _claim(
        self,
        job_id: str | None,
        worker_id: str,
        now: float | None = None,
        lease_seconds: float | None = None,
    ) -> dict[str, Any] | None:
        """Claim a job inside one write transaction, reclaiming expired leases first."""
        timestamp = _timestamp(now)
        claim_time = _iso(now)
        lease = LEASE_SECONDS if lease_seconds is None else max(1.0, lease_seconds)
        lease_expires_at = timestamp + lease
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            self._reclaim_expired(db, timestamp)
            if job_id is not None:
                task = db.execute(
                    """
                    SELECT job_id, project_id, operation, progress, total, state, attempts
                    FROM jobs
                    WHERE job_id = ? AND state = 'queued' AND cancel_requested = 0
                    """,
                    (job_id,),
                ).fetchone()
            else:
                task = db.execute(
                    """
                    SELECT job_id, project_id, operation, progress, total, state, attempts
                    FROM jobs
                    WHERE state = 'queued' AND cancel_requested = 0
                    ORDER BY created_at ASC, rowid ASC
                    LIMIT 1
                    """
                ).fetchone()
            if task is None:
                return None

            claimed_job_id = str(task["job_id"])
            attempts = int(task["attempts"]) + 1
            db.execute(
                """
                UPDATE jobs
                SET state = 'running', attempts = ?, updated_at = ?,
                    lease_owner = ?, lease_expires_at = ?
                WHERE job_id = ?
                """,
                (attempts, claim_time, worker_id, lease_expires_at, claimed_job_id),
            )
            self._event(
                db,
                claimed_job_id,
                "job_claimed",
                {
                    "worker": worker_id,
                    "operation": task["operation"],
                    "attempt": attempts,
                    "lease_expires_at": datetime.fromtimestamp(
                        lease_expires_at, UTC
                    ).isoformat(),
                },
            )
            return {
                "job_id": claimed_job_id,
                "project_id": task["project_id"],
                "operation": task["operation"],
                "attempts": attempts,
                "progress": task["progress"],
                "total": task["total"],
                "worker": worker_id,
            }

    def heartbeat(self, job_id: str, worker_id: str, now: float | None = None) -> bool:
        """Extend a running job's lease.

        Returns False when the job is missing, not running, or leased to a
        different worker; a caller that cannot heartbeat no longer owns the job.
        """
        timestamp = _timestamp(now)
        with _connect(self.db_path) as db:
            row = db.execute(
                "SELECT state, lease_owner FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None or row["state"] != "running":
                return False
            owner = row["lease_owner"]
            if owner is not None and owner != worker_id:
                return False
            db.execute(
                "UPDATE jobs SET updated_at = ?, lease_expires_at = ? WHERE job_id = ?",
                (_iso(now), timestamp + LEASE_SECONDS, job_id),
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
        """Mark a running job as completed with an optional output payload."""
        output_json = json.dumps(output) if output is not None else None
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            _require_running(db, job_id, worker_id)
            db.execute(
                """
                UPDATE jobs SET state = 'completed', progress = total,
                    lease_owner = NULL, lease_expires_at = NULL,
                    updated_at = ?, output_json = ? WHERE job_id = ?
                """,
                (_iso(now), output_json, job_id),
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
        """Mark a job as failed, re-queueing it while attempts remain."""
        updated = _iso(now)
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = _require_running(db, job_id, worker_id)
            attempts = int(row["attempts"])
            if retry and attempts < MAX_ATTEMPTS:
                db.execute(
                    """
                    UPDATE jobs SET state = 'queued', lease_owner = NULL,
                        lease_expires_at = NULL, updated_at = ?, error = ?
                    WHERE job_id = ?
                    """,
                    (updated, error, job_id),
                )
                self._event(
                    db,
                    job_id,
                    "job_failed_retry",
                    {"worker": worker_id, "attempt": attempts, "error": error},
                )
            else:
                db.execute(
                    """
                    UPDATE jobs SET state = 'failed', lease_owner = NULL,
                        lease_expires_at = NULL, updated_at = ?, error = ?
                    WHERE job_id = ?
                    """,
                    (updated, error, job_id),
                )
                self._event(
                    db,
                    job_id,
                    "job_failed",
                    {"worker": worker_id, "attempts": attempts, "error": error},
                )

    def request_cancel(self, job_id: str, now: float | None = None) -> None:
        """Request cancellation of a job.

        A queued job is cancelled immediately. A running job keeps its state and
        records the request, which the owning caller honours at its next task
        boundary because the call already in flight cannot be interrupted.
        """
        updated = _iso(now)
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT state FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobQueueError(f"Job {job_id} does not exist.")
            if row["state"] in ("completed", "failed", "cancelled"):
                return
            db.execute(
                "UPDATE jobs SET cancel_requested = 1, updated_at = ? WHERE job_id = ?",
                (updated, job_id),
            )
            if row["state"] == "running":
                self._event(db, job_id, "cancel_requested")
                return
            db.execute(
                """
                UPDATE jobs SET state = 'cancelled', lease_owner = NULL,
                    lease_expires_at = NULL, updated_at = ? WHERE job_id = ?
                """,
                (updated, job_id),
            )
            self._event(db, job_id, "job_cancelled")

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
        """List jobs for a project, most recent first, with a bounded page size."""
        page_size = max(1, min(int(limit), MAX_LIST_LIMIT))
        skip = max(0, int(offset))
        with _connect(self.db_path) as db:
            rows = db.execute(
                """
                SELECT job_id, project_id, operation, state, attempts, progress, total,
                    created_at, updated_at, error
                FROM jobs WHERE project_id = ?
                ORDER BY updated_at DESC, rowid DESC
                LIMIT ? OFFSET ?
                """,
                (project_id, page_size, skip),
            ).fetchall()
        return [dict(row) for row in rows]
