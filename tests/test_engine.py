from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.engine import EngineTimeoutError, EngineUnavailableError, GodotEngineAdapter
from app.storage import project_directory


class _TimedOutProcess:
    def __init__(self) -> None:
        self.returncode = None
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.returncode = -9

    def wait(self, timeout=None):
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "godot_engine_proof"
    / "fixtures"
    / "proof_triangle.glb"
)
GODOT_PATH = Path(os.environ.get("CARTOON_STUDIO_GODOT_PATH", ""))
HAS_GODOT = bool(os.environ.get("CARTOON_STUDIO_GODOT_PATH")) and GODOT_PATH.is_file()


def test_adapter_reports_missing_runtime(tmp_path):
    adapter = GodotEngineAdapter(
        data_dir=tmp_path,
        executable=tmp_path / "missing-godot.exe",
    )
    assert not adapter.available
    with pytest.raises(EngineUnavailableError):
        adapter.ping()


def test_adapter_rejects_glb_outside_project_root(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"not a real GLB")
    with pytest.raises(ValueError, match="escapes"):
        adapter.inspect_glb(outside, allowed_root=tmp_path / "project")


def test_adapter_rejects_non_glb_files(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    source = tmp_path / "model.obj"
    source.write_text("o test", encoding="utf-8")
    with pytest.raises(ValueError, match=".glb"):
        adapter.inspect_glb(source, allowed_root=tmp_path)


@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_ping_and_glb_inspection(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    ping = adapter.ping()
    assert ping["engine_version"].startswith("4.7.2")
    assert "glb_inspect" in ping["capabilities"]

    project_root = tmp_path / "project"
    project_root.mkdir()
    fixture = project_root / "proof_triangle.glb"
    shutil.copy2(FIXTURE, fixture)
    inspection = adapter.inspect_glb(fixture, allowed_root=project_root)
    assert inspection["mesh_count"] >= 1
    assert inspection["engine_version"].startswith("4.7.2")


@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_project_glb_inspection_api(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "engine-test.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    client = TestClient(main.app)

    created = client.post("/api/projects", json={"name": "Engine Import Test"})
    assert created.status_code == 201
    project_id = created.json()["id"]
    asset_dir = project_directory(tmp_path, project_id) / "assets"
    asset_dir.mkdir(parents=True)
    shutil.copy2(FIXTURE, asset_dir / "proof_triangle.glb")

    status = client.get("/api/engine/status")
    assert status.status_code == 200
    assert status.json()["available"] is True
    assert status.json()["engine_version"].startswith("4.7.2")

    inspected = client.post(
        f"/api/projects/{project_id}/engine/inspect-glb",
        json={"relative_path": "assets/proof_triangle.glb"},
    )
    assert inspected.status_code == 200
    assert inspected.json()["mesh_count"] >= 1

    rejected = client.post(
        f"/api/projects/{project_id}/engine/inspect-glb",
        json={"relative_path": "../../outside.glb"},
    )
    assert rejected.status_code == 422


def test_adapter_timeout_is_logged_and_raised(tmp_path, monkeypatch):
    executable = tmp_path / "godot.exe"
    executable.write_bytes(b"test-runtime")
    worker_project = tmp_path / "worker"
    worker_project.mkdir()
    (worker_project / "project.godot").write_text("config_version=5", encoding="utf-8")
    adapter = GodotEngineAdapter(
        data_dir=tmp_path,
        timeout_seconds=0.01,
        executable=executable,
        worker_project=worker_project,
    )
    process = _TimedOutProcess()
    monkeypatch.setattr("app.engine.subprocess.Popen", lambda *args, **kwargs: process)
    with pytest.raises(EngineTimeoutError, match="time budget"):
        adapter.ping()
    assert process.terminated

    log_path = tmp_path / "logs" / "godot-worker.jsonl"
    assert log_path.is_file()
    record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    assert record["operation"] == "ping"
    assert record["ok"] is False
    assert record["error"].startswith("Godot ping exceeded")
