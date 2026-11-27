from pathlib import Path

import pytest

from app.job_queue import JobQueue, JobQueueError
from app.storage import connect_db, initialize_database


@pytest.fixture
def queue(tmp_path: Path) -> JobQueue:
    data_dir = tmp_path / "data"
    db_path = tmp_path / "queue.sqlite3"
    initialize_database(data_dir, db_path)
    # Create a project so the foreign key constraint is satisfied
    with connect_db(data_dir, db_path) as connection:
        for pid, name in (("proj-1", "Test Project"), ("proj-2", "Second Project")):
            connection.execute(
                "INSERT INTO projects(id, name, description, created_at, updated_at, metadata_json)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (pid, name, "", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", "{}"),
            )
    return JobQueue(data_dir, db_path)


def test_enqueue_and_snapshot(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_production", total_units=1)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["job_id"] == job_id
    assert snapshot["job"]["project_id"] == "proj-1"
    assert snapshot["job"]["operation"] == "episode_production"
    assert snapshot["job"]["state"] == "queued"
    assert snapshot["job"]["progress"] == 0
    assert snapshot["job"]["total"] == 1
    assert snapshot["events"][0]["event_type"] == "job_queued"


def test_claim_and_complete(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_audio", total_units=1)
    claimed = queue.claim_specific(job_id, worker_id="worker-1")
    assert claimed is not None
    assert claimed["job_id"] == job_id
    assert claimed["worker"] == "worker-1"
    queue.complete(job_id, worker_id="worker-1", output={"status": "ok"})
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "completed"
    assert snapshot["job"]["progress"] == 1
    event_types = [e["event_type"] for e in snapshot["events"]]
    assert "job_completed" in event_types


def test_claim_unknown_job(queue: JobQueue) -> None:
    claimed = queue.claim_specific("nonexistent", worker_id="worker-1")
    assert claimed is None


def test_complete_non_running_job(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_render", total_units=1)
    with pytest.raises(JobQueueError):
        queue.complete(job_id, worker_id="worker-1")


def test_fail_with_retry(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_production", total_units=3)
    queue.claim_specific(job_id, worker_id="worker-1")

    # First failure: re-queued (progress 0 -> 1)
    queue.fail(job_id, worker_id="worker-1", error="transient", retry=True)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "queued"
    assert snapshot["job"]["progress"] == 1
    assert snapshot["job"]["error"] == "transient"

    # Claim again and fail again (progress 1 -> 2)
    queue.claim_specific(job_id, worker_id="worker-1")
    queue.fail(job_id, worker_id="worker-1", error="transient", retry=True)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "queued"
    assert snapshot["job"]["progress"] == 2

    # Claim again and fail again (progress 2 -> MAX_ATTEMPTS reached, failed)
    queue.claim_specific(job_id, worker_id="worker-1")
    queue.fail(job_id, worker_id="worker-1", error="permanent", retry=True)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "failed"
    assert snapshot["job"]["progress"] == 2
    assert snapshot["job"]["error"] == "permanent"


def test_fail_without_retry(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_audio", total_units=1)
    queue.claim_specific(job_id, worker_id="worker-1")
    queue.fail(job_id, worker_id="worker-1", error="bad input", retry=False)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "failed"
    assert snapshot["job"]["error"] == "bad input"


def test_request_cancel_queued_job(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_render", total_units=1)
    queue.request_cancel(job_id)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "cancelled"
    assert snapshot["job"]["cancel_requested"] == 1


def test_request_cancel_running_job(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_production", total_units=1)
    queue.claim_specific(job_id, worker_id="worker-1")
    queue.request_cancel(job_id)
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["cancel_requested"] == 1
    assert snapshot["job"]["state"] == "running"  # still running, cancelled after task


def test_list_jobs_for_project(queue: JobQueue) -> None:
    queue.enqueue("proj-1", "episode_production", total_units=1)
    queue.enqueue("proj-1", "episode_audio", total_units=1)
    queue.enqueue("proj-2", "episode_render", total_units=1)

    proj1_jobs = queue.list_for_project("proj-1")
    assert len(proj1_jobs) == 2
    assert all(j["project_id"] == "proj-1" for j in proj1_jobs)

    proj2_jobs = queue.list_for_project("proj-2")
    assert len(proj2_jobs) == 1
    assert proj2_jobs[0]["project_id"] == "proj-2"


def test_snapshot_unknown_job(queue: JobQueue) -> None:
    with pytest.raises(KeyError):
        queue.snapshot("nonexistent")


def test_multiple_jobs_claim_order(queue: JobQueue) -> None:
    j1 = queue.enqueue("proj-1", "op-a", total_units=1)
    j2 = queue.enqueue("proj-1", "op-b", total_units=1)
    j3 = queue.enqueue("proj-1", "op-c", total_units=1)

    claimed_ids = set()
    for _ in range(3):
        claimed = queue.claim_next(worker_id="worker-1")
        assert claimed is not None
        claimed_ids.add(claimed["job_id"])
    assert claimed_ids == {j1, j2, j3}

    # No more pending jobs
    fourth = queue.claim_next(worker_id="worker-1")
    assert fourth is None
