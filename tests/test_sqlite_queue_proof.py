from __future__ import annotations

import pytest

from tools.sqlite_queue_proof import SQLiteJobQueue


def test_job_runs_scenes_then_enters_assembly_and_completes(tmp_path):
    queue = SQLiteJobQueue(tmp_path / "jobs.sqlite3")
    queue.enqueue("job-1", ["scene-1", "scene-2"], now=100)

    first = queue.claim_next("worker-a", now=101)
    assert first["scene_id"] == "scene-1"
    assert queue.claim_next("worker-b", now=102) is None

    queue.complete_scene("job-1", "scene-1", "worker-a", "scene-1.mp4", now=103)
    second = queue.claim_next("worker-a", now=104)
    assert second["scene_id"] == "scene-2"
    queue.complete_scene("job-1", "scene-2", "worker-a", "scene-2.mp4", now=105)

    snapshot = queue.snapshot("job-1")
    assert snapshot["job"]["state"] == "assembling"
    assert [scene["state"] for scene in snapshot["scenes"]] == ["completed", "completed"]
    queue.finish_assembly("job-1", now=106)
    assert queue.snapshot("job-1")["job"]["state"] == "completed"


def test_expired_lease_retries_only_incomplete_scene_and_preserves_checkpoint(tmp_path):
    queue = SQLiteJobQueue(tmp_path / "jobs.sqlite3", lease_seconds=5)
    queue.enqueue("job-2", ["scene-1", "scene-2"], now=200)

    first = queue.claim_next("worker-a", now=201)
    assert first["scene_id"] == "scene-1"
    queue.complete_scene("job-2", "scene-1", "worker-a", "scene-1.mp4", now=202)
    second = queue.claim_next("worker-a", now=203)
    assert second["scene_id"] == "scene-2"

    retry = queue.claim_next("worker-b", now=209)
    assert retry["scene_id"] == "scene-2"
    assert retry["attempt"] == 2

    snapshot = queue.snapshot("job-2")
    assert snapshot["scenes"][0]["state"] == "completed"
    assert snapshot["scenes"][0]["output_path"] == "scene-1.mp4"
    assert snapshot["scenes"][1]["state"] == "running"
    assert any(event["event_type"] == "scene_lease_expired" for event in snapshot["events"])


def test_cancel_preserves_completed_scene_and_prevents_future_claims(tmp_path):
    queue = SQLiteJobQueue(tmp_path / "jobs.sqlite3")
    queue.enqueue("job-3", ["scene-1", "scene-2"], now=300)
    first = queue.claim_next("worker-a", now=301)
    queue.complete_scene("job-3", first["scene_id"], "worker-a", "scene-1.mp4", now=302)

    queue.request_cancel("job-3", now=303)
    snapshot = queue.snapshot("job-3")
    assert snapshot["job"]["state"] == "cancelled"
    assert snapshot["scenes"][0]["state"] == "completed"
    assert snapshot["scenes"][1]["state"] == "pending"
    assert queue.claim_next("worker-b", now=304) is None


def test_stale_worker_cannot_complete_after_lease_reassignment(tmp_path):
    queue = SQLiteJobQueue(tmp_path / "jobs.sqlite3", lease_seconds=3)
    queue.enqueue("job-4", ["scene-1"], now=400)
    queue.claim_next("worker-a", now=401)
    new_claim = queue.claim_next("worker-b", now=405)
    assert new_claim["lease_owner"] == "worker-b"

    with pytest.raises(RuntimeError, match="no longer owns"):
        queue.complete_scene("job-4", "scene-1", "worker-a", "stale.mp4", now=406)

    queue.complete_scene("job-4", "scene-1", "worker-b", "valid.mp4", now=407)
    assert queue.snapshot("job-4")["scenes"][0]["output_path"] == "valid.mp4"


def test_cancel_during_running_scene_finishes_safely_and_keeps_output(tmp_path):
    queue = SQLiteJobQueue(tmp_path / "jobs.sqlite3")
    queue.enqueue("job-5", ["scene-1", "scene-2"], now=500)
    claim = queue.claim_next("worker-a", now=501)
    queue.request_cancel("job-5", now=502)
    assert queue.snapshot("job-5")["job"]["state"] == "rendering"

    queue.complete_scene("job-5", claim["scene_id"], "worker-a", "scene-1.mp4", now=503)
    snapshot = queue.snapshot("job-5")
    assert snapshot["job"]["state"] == "cancelled"
    assert snapshot["scenes"][0]["state"] == "completed"
    assert snapshot["scenes"][0]["output_path"] == "scene-1.mp4"
    assert snapshot["scenes"][1]["state"] == "pending"
    assert queue.claim_next("worker-b", now=504) is None
