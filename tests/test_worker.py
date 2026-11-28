from pathlib import Path

import pytest

from app.job_queue import JobQueue
from app.storage import connect_db, initialize_database
from app.worker import OperationCancelled, OperationWorker


@pytest.fixture
def queue(tmp_path: Path) -> JobQueue:
    data_dir = tmp_path / "data"
    db_path = tmp_path / "worker.sqlite3"
    initialize_database(data_dir, db_path)
    with connect_db(data_dir, db_path) as connection:
        connection.execute(
            "INSERT INTO projects(id, name, description, created_at, updated_at, metadata_json)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                "proj-1",
                "Worker Project",
                "",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
                "{}",
            ),
        )
    return JobQueue(data_dir, db_path)


def test_worker_runs_a_registered_operation(queue: JobQueue) -> None:
    reported = []

    def handler(context):
        context.report(1, 2)
        reported.append(context.project_id)
        context.report(2, 2)
        return {"scenes": 2}

    worker = OperationWorker(queue, {"episode_render": handler}, worker_id="worker-1")
    job_id = queue.enqueue("proj-1", "episode_render", total_units=2)
    assert worker.run_once() is True

    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "completed"
    assert snapshot["job"]["progress"] == 2
    assert snapshot["job"]["total"] == 2
    assert snapshot["job"]["output_json"] == '{"scenes": 2}'
    assert reported == ["proj-1"]


def test_worker_fails_an_unknown_operation(queue: JobQueue) -> None:
    worker = OperationWorker(queue, {}, worker_id="worker-1")
    job_id = queue.enqueue("proj-1", "unknown_operation")
    assert worker.run_once() is True
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "failed"
    assert "No background handler" in snapshot["job"]["error"]


def test_worker_records_a_failure_for_a_raising_handler(queue: JobQueue) -> None:
    def handler(context):
        raise RuntimeError("Godot did not render")

    worker = OperationWorker(queue, {"episode_render": handler}, worker_id="worker-1")
    job_id = queue.enqueue("proj-1", "episode_render")
    assert worker.run_once() is True
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "queued"  # retryable failure re-queues
    assert "Godot did not render" in snapshot["job"]["error"]


def test_worker_honours_cancellation_between_units(queue: JobQueue) -> None:
    def handler(context):
        context.report(0, 2)
        queue.request_cancel(context.job_id)
        context.report(1, 2)  # must raise before the next scene
        raise AssertionError("the handler must stop once cancelled")

    worker = OperationWorker(queue, {"episode_render": handler}, worker_id="worker-1")
    job_id = queue.enqueue("proj-1", "episode_render", total_units=2)
    assert worker.run_once() is True
    snapshot = queue.snapshot(job_id)
    assert snapshot["job"]["state"] == "cancelled"
    assert snapshot["job"]["progress"] == 0
    assert "cancelled" in snapshot["job"]["error"]


def test_worker_cancelled_exception_marks_the_job_cancelled(queue: JobQueue) -> None:
    def handler(context):
        raise OperationCancelled("The owner cancelled this job.")

    worker = OperationWorker(queue, {"episode_render": handler}, worker_id="worker-1")
    job_id = queue.enqueue("proj-1", "episode_render")
    assert worker.run_once() is True
    assert queue.snapshot(job_id)["job"]["state"] == "cancelled"


def test_run_once_returns_false_when_the_queue_is_empty(queue: JobQueue) -> None:
    worker = OperationWorker(queue, {}, worker_id="worker-1")
    assert worker.run_once() is False


def test_progress_requires_ownership(queue: JobQueue) -> None:
    job_id = queue.enqueue("proj-1", "episode_render")
    queue.claim_specific(job_id, worker_id="worker-1")
    assert queue.report_progress(job_id, "worker-1", 1, total=5) is True
    assert queue.report_progress(job_id, "worker-2", 2, total=5) is False
    assert queue.snapshot(job_id)["job"]["progress"] == 1
