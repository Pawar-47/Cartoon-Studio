from __future__ import annotations

import os
import shutil
import threading
from pathlib import Path

import pytest

from app import engine
from app.engine import (
    EngineCancelledError,
    EngineExecutionError,
    EnginePathError,
    EngineTimeoutError,
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


def _fake_adapter(tmp_path, timeout=1):
    executable = tmp_path / "godot.exe"
    executable.write_bytes(b"fake executable")
    worker = tmp_path / "worker"
    worker.mkdir()
    (worker / "project.godot").write_text("config_version=5\n", encoding="utf-8")
    return GodotEngineAdapter(
        data_dir=tmp_path / "data",
        executable=executable,
        worker_project=worker,
        timeout_seconds=timeout,
    )


def test_engine_adapter_rejects_parent_traversal(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    adapter = _fake_adapter(tmp_path)
    with pytest.raises(EnginePathError, match="escapes"):
        adapter.inspect_glb(root / ".." / "outside.glb", allowed_root=root)


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
    adapter = _fake_adapter(tmp_path)
    with pytest.raises(EnginePathError):
        adapter.inspect_glb(link, allowed_root=root)


def test_engine_adapter_rejects_non_glb_files(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    source = root / "model.gltf"
    source.write_text("{}", encoding="utf-8")
    adapter = _fake_adapter(tmp_path)
    with pytest.raises(EnginePathError, match="Only .glb"):
        adapter.inspect_glb(source, allowed_root=root)


def test_worker_timeout_terminates_process(tmp_path, monkeypatch):
    adapter = _fake_adapter(tmp_path, timeout=0.01)
    process = _FakeProcess()
    monkeypatch.setattr(engine.subprocess, "Popen", lambda *args, **kwargs: process)
    with pytest.raises(EngineTimeoutError):
        adapter.ping()
    assert process.terminated
    assert process.waited
    assert not process.killed


def test_worker_cancellation_terminates_process(tmp_path, monkeypatch):
    adapter = _fake_adapter(tmp_path, timeout=5)
    process = _FakeProcess()
    monkeypatch.setattr(engine.subprocess, "Popen", lambda *args, **kwargs: process)
    cancellation = threading.Event()
    cancellation.set()
    with pytest.raises(EngineCancelledError):
        adapter.ping(cancel_event=cancellation)
    assert process.terminated
    assert process.waited


def _real_godot_adapter(tmp_path=None) -> GodotEngineAdapter:
    if not os.environ.get("CARTOON_STUDIO_GODOT_PATH"):
        pytest.skip("The pinned Godot runtime is installed only in the Windows CI job.")
    return GodotEngineAdapter(data_dir=tmp_path or Path.cwd() / ".godot-test-data")


def test_pinned_godot_worker_handshake(tmp_path):
    response = _real_godot_adapter(tmp_path).ping()
    assert response["ok"] is True
    assert response["engine_version"].startswith("4.7.2")
    assert "glb_inspect" in response["capabilities"]


def test_pinned_godot_worker_imports_glb_fixture(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
        / "proof_triangle.glb"
    )
    if not fixture.is_file():
        pytest.skip("The checked-in GLB proof fixture is unavailable.")
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    target = asset_dir / "proof_triangle.glb"
    shutil.copyfile(fixture, target)
    response = adapter.inspect_glb(target, allowed_root=tmp_path)
    assert response["ok"] is True
    assert response["mesh_count"] >= 1


def test_pinned_godot_worker_rejects_invalid_glb(tmp_path):
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    broken = asset_dir / "broken.glb"
    broken.write_bytes(b"not a glb")
    with pytest.raises(EngineExecutionError, match="could not import"):
        _real_godot_adapter(tmp_path).inspect_glb(broken, allowed_root=tmp_path)


def test_worker_rechecks_path_boundary_independently(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"not used")
    with pytest.raises(EngineExecutionError, match="outside"):
        adapter._run(
            "inspect_glb",
            {"project_root": str(project.resolve()), "source_path": str(outside.resolve())},
        )
