"""P0.6 architecture proof only: SQLite job lease/checkpoint semantics.

This prototype is deliberately isolated from app/ and is not production code.
It tests the smallest local queue contract before Phase 1 implementation.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


class SQLiteJobQueue:
    def __init__(self, database_path: str | Path, lease_seconds: int = 30) -> None:
        self.database_path = str(database_path)
        self.lease_seconds = lease_seconds
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    error TEXT
                );
                CREATE TABLE IF NOT EXISTS scene_tasks (
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    scene_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    lease_owner TEXT,
                    lease_until REAL,
                    output_path TEXT,
                    error TEXT,
                    PRIMARY KEY (job_id, scene_id)
                );
                CREATE TABLE IF NOT EXISTS job_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    scene_id TEXT,
                    event_type TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    detail_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS idx_scene_claim
                    ON scene_tasks(state, lease_until, job_id);
                """
            )

    @staticmethod
    def _event(
        db: sqlite3.Connection,
        job_id: str,
        event_type: str,
        now: float,
        scene_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        db.execute(
            """
            INSERT INTO job_events(job_id, scene_id, event_type, created_at, detail_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, scene_id, event_type, now, json.dumps(detail or {})),
        )

    def enqueue(self, job_id: str, scene_ids: list[str], now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        if not scene_ids or len(scene_ids) != len(set(scene_ids)):
            raise ValueError("A job requires unique scene IDs.")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO jobs(job_id, state, created_at, updated_at) VALUES (?, 'queued', ?, ?)",
                (job_id, timestamp, timestamp),
            )
            db.executemany(
                """
                INSERT INTO scene_tasks(job_id, scene_id, state)
                VALUES (?, ?, 'pending')
                """,
                [(job_id, scene_id) for scene_id in scene_ids],
            )
            self._event(db, job_id, "job_queued", timestamp, detail={"scene_count": len(scene_ids)})

    def claim_next(self, worker_id: str, now: float | None = None) -> dict[str, Any] | None:
        timestamp = time.time() if now is None else now
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            expired = db.execute(
                """
                SELECT job_id, scene_id FROM scene_tasks
                WHERE state = 'running' AND lease_until <= ?
                """,
                (timestamp,),
            ).fetchall()
            for row in expired:
                db.execute(
                    """
                    UPDATE scene_tasks
                    SET state = 'pending', lease_owner = NULL, lease_until = NULL
                    WHERE job_id = ? AND scene_id = ?
                    """,
                    (row["job_id"], row["scene_id"]),
                )
                db.execute(
                    "UPDATE jobs SET state = 'queued', updated_at = ? WHERE job_id = ? AND cancel_requested = 0",
                    (timestamp, row["job_id"]),
                )
                self._event(
                    db,
                    row["job_id"],
                    "scene_lease_expired",
                    timestamp,
                    row["scene_id"],
                )

            active = db.execute(
                """
                SELECT 1 FROM scene_tasks
                WHERE state = 'running' AND lease_until > ?
                LIMIT 1
                """,
                (timestamp,),
            ).fetchone()
            if active:
                return None

            task = db.execute(
                """
                SELECT s.job_id, s.scene_id, s.attempts, j.state
                FROM scene_tasks AS s
                JOIN jobs AS j ON j.job_id = s.job_id
                WHERE s.state = 'pending' AND j.cancel_requested = 0
                  AND j.state IN ('queued', 'preparing', 'rendering')
                ORDER BY j.created_at, s.rowid
                LIMIT 1
                """
            ).fetchone()
            if task is None:
                return None

            db.execute(
                "UPDATE jobs SET state = 'rendering', updated_at = ? WHERE job_id = ?",
                (timestamp, task["job_id"]),
            )
            db.execute(
                """
                UPDATE scene_tasks
                SET state = 'running', attempts = attempts + 1,
                    lease_owner = ?, lease_until = ?
                WHERE job_id = ? AND scene_id = ?
                """,
                (
                    worker_id,
                    timestamp + self.lease_seconds,
                    task["job_id"],
                    task["scene_id"],
                ),
            )
            self._event(
                db,
                task["job_id"],
                "scene_claimed",
                timestamp,
                task["scene_id"],
                {"worker": worker_id, "attempt": task["attempts"] + 1},
            )
            return {
                "job_id": task["job_id"],
                "scene_id": task["scene_id"],
                "attempt": task["attempts"] + 1,
                "lease_owner": worker_id,
                "lease_until": timestamp + self.lease_seconds,
            }

    def complete_scene(
        self,
        job_id: str,
        scene_id: str,
        worker_id: str,
        output_path: str,
        now: float | None = None,
    ) -> None:
        timestamp = time.time() if now is None else now
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            task = db.execute(
                """
                SELECT state, lease_owner FROM scene_tasks
                WHERE job_id = ? AND scene_id = ?
                """,
                (job_id, scene_id),
            ).fetchone()
            if task is None or task["state"] != "running" or task["lease_owner"] != worker_id:
                raise RuntimeError("Worker no longer owns this scene lease.")
            db.execute(
                """
                UPDATE scene_tasks
                SET state = 'completed', output_path = ?, lease_owner = NULL, lease_until = NULL
                WHERE job_id = ? AND scene_id = ?
                """,
                (output_path, job_id, scene_id),
            )
            self._event(
                db,
                job_id,
                "scene_completed",
                timestamp,
                scene_id,
                {"output_path": output_path},
            )
            remaining = db.execute(
                "SELECT COUNT(*) FROM scene_tasks WHERE job_id = ? AND state != 'completed'",
                (job_id,),
            ).fetchone()[0]
            if remaining == 0:
                db.execute(
                    "UPDATE jobs SET state = 'assembling', updated_at = ? WHERE job_id = ?",
                    (timestamp, job_id),
                )
                self._event(db, job_id, "assembly_ready", timestamp)

    def finish_assembly(self, job_id: str, now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            pending = db.execute(
                "SELECT COUNT(*) FROM scene_tasks WHERE job_id = ? AND state != 'completed'",
                (job_id,),
            ).fetchone()[0]
            if pending:
                raise RuntimeError("Cannot assemble before every scene is complete.")
            db.execute(
                "UPDATE jobs SET state = 'completed', updated_at = ? WHERE job_id = ? AND state = 'assembling'",
                (timestamp, job_id),
            )
            self._event(db, job_id, "job_completed", timestamp)

    def request_cancel(self, job_id: str, now: float | None = None) -> None:
        timestamp = time.time() if now is None else now
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "UPDATE jobs SET cancel_requested = 1, updated_at = ? WHERE job_id = ?",
                (timestamp, job_id),
            )
            running = db.execute(
                "SELECT COUNT(*) FROM scene_tasks WHERE job_id = ? AND state = 'running'",
                (job_id,),
            ).fetchone()[0]
            if running == 0:
                db.execute(
                    "UPDATE jobs SET state = 'cancelled' WHERE job_id = ?",
                    (job_id,),
                )
                self._event(db, job_id, "job_cancelled", timestamp)
            else:
                self._event(db, job_id, "cancel_requested", timestamp)

    def snapshot(self, job_id: str) -> dict[str, Any]:
        with self._connect() as db:
            job = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
            if job is None:
                raise KeyError(job_id)
            scenes = db.execute(
                """
                SELECT scene_id, state, attempts, output_path, error
                FROM scene_tasks WHERE job_id = ? ORDER BY rowid
                """,
                (job_id,),
            ).fetchall()
            events = db.execute(
                """
                SELECT event_type, scene_id FROM job_events
                WHERE job_id = ? ORDER BY event_id
                """,
                (job_id,),
            ).fetchall()
        return {
            "job": dict(job),
            "scenes": [dict(row) for row in scenes],
            "events": [dict(row) for row in events],
        }
