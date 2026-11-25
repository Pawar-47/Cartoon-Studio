from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path

import pytest

from app import engine
from app.engine import (
    EngineCancelledError,
    EnginePathError,
    EngineTimeoutError,
    EngineWorkerError,
    GodotEngineAdapter,
)


class _FakeProcess:
    def __init__(self) -> None:
        self.returncode = None
        self.terminated = False
        self.killed = False
        self.waited = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def kill(self):
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        self.waited = True
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def test_engine_adapter_rejects_parent_traversal(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    adapter = GodotEngineAdapter(executable=tmp_path / "missing.exe", worker_project=tmp_path)
    with pytest.raises(EnginePathError, match="inside the project"):
        adapter.inspect_glb(root, "../outside.glb")


def test_engine_adapter_rejects_absolute_paths(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    adapter = GodotEngineAdapter(executable=tmp_path / "missing.exe", worker_project=tmp_path)
    with pytest.raises(EnginePathError):
        adapter.inspect_glb(root, str((tmp_path / "outside.glb").resolve()))


def test_engine_adapter_rejects_symlink_escape(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"glTF")
    link = root / "escape.glb"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is not available in this runner.")
    adapter = GodotEngineAdapter(executable=tmp_path / "missing.exe", worker_project=tmp_path)
    with pytest.raises(EnginePathError):
        adapter.inspect_glb(root, "escape.glb")


def test_worker_timeout_terminates_process(tmp_path, monkeypatch):
    executable = tmp_path / "godot.exe"
    executable.write_bytes(b"test executable placeholder")
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    process = _FakeProcess()
    monkeypatch.setattr(engine.subprocess, "Popen", lambda *args, **kwargs: process)
    adapter = GodotEngineAdapter(executable, worker, timeout_seconds=0)
    with pytest.raises(EngineTimeoutError):
        adapter.handshake()
    assert process.terminated
    assert process.waited
    assert not process.killed


def test_worker_cancellation_terminates_process(tmp_path, monkeypatch):
    executable = tmp_path / "godot.exe"
    executable.write_bytes(b"test executable placeholder")
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    process = _FakeProcess()
    monkeypatch.setattr(engine.subprocess, "Popen", lambda *args, **kwargs: process)
    cancellation = threading.Event()
    cancellation.set()
    adapter = GodotEngineAdapter(executable, worker, timeout_seconds=5)
    with pytest.raises(EngineCancelledError):
        adapter.handshake(cancel_event=cancellation)
    assert process.terminated
    assert process.waited


def _real_godot_adapter() -> GodotEngineAdapter:
    if not os.environ.get("CARTOON_STUDIO_GODOT_PATH"):
        pytest.skip("The pinned Godot runtime is installed only in the Windows CI job.")
    return GodotEngineAdapter()


def test_pinned_godot_worker_handshake():
    response = _real_godot_adapter().handshake()
    assert response["status"] == "ok"
    assert response["protocol_version"] == 1
    assert response["engine"]["version"].startswith("4.7.2")
    assert "glb.inspect" in response["capabilities"]


def test_pinned_godot_worker_imports_glb_fixture(tmp_path):
    adapter = _real_godot_adapter()
    fixture = Path(__file__).resolve().parents[1] / "tools" / "godot_engine_proof" / "fixtures" / "proof_triangle.glb"
    if not fixture.is_file():
        pytest.skip("The checked-in GLB proof fixture is unavailable.")
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    target = asset_dir / "proof_triangle.glb"
    shutil.copyfile(fixture, target)
    response = adapter.inspect_glb(tmp_path, "assets/proof_triangle.glb")
    assert response["status"] == "ok"
    assert response["asset"]["file_name"] == "proof_triangle.glb"
    assert response["metrics"]["mesh_count"] >= 1


def test_pinned_godot_worker_rejects_invalid_glb(tmp_path):
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    (asset_dir / "broken.glb").write_bytes(b"not a glb")
    with pytest.raises(EngineWorkerError, match="could not import"):
        _real_godot_adapter().inspect_glb(tmp_path, "assets/broken.glb")


def test_worker_rechecks_path_boundary_independently(tmp_path):
    adapter = _real_godot_adapter()
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"not used")
    with pytest.raises(EngineWorkerError, match="outside"):
        adapter._invoke(
            "inspect_glb",
            payload={
                "project_root": str(project.resolve()),
                "source_path": str(outside.resolve()),
            },
        )
