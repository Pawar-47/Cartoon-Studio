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
from app.rig_analysis import REQUIRED_HUMANOID_BONES, analyze_rig


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
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"glTF")
    adapter = _fake_adapter(tmp_path)
    with pytest.raises(EnginePathError, match="escapes"):
        adapter.inspect_glb(outside, allowed_root=root)


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
    assert "skeleton_report" in response["capabilities"]


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
    assert response["skeleton_count"] == len(response["skeletons"])


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


def test_pinned_godot_worker_reports_imported_humanoid_rest_transforms(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
        / "proof_humanoid.glb"
    )
    assert fixture.is_file(), "The checked-in skinned humanoid fixture is unavailable."
    asset_dir = tmp_path / "humanoid-assets"
    asset_dir.mkdir()
    target = asset_dir / "proof_humanoid.glb"
    shutil.copyfile(fixture, target)

    response = adapter.inspect_glb(target, allowed_root=tmp_path)
    assert response["ok"] is True
    assert response["skeleton_count"] == 1
    assert response["animation_count"] >= 1
    skeleton = response["skeletons"][0]
    assert skeleton["bone_count"] == 15
    assert all(
        isinstance(bone.get("rest_transform", {}).get("origin"), list)
        and len(bone["rest_transform"]["origin"]) == 3
        for bone in skeleton["bones"]
    )


def test_pinned_godot_worker_creates_non_destructive_retarget_scene(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture_dir = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
    )
    source_fixture = fixture_dir / "proof_humanoid_retarget_source.glb"
    target_fixture = fixture_dir / "proof_humanoid_retarget_target.glb"
    assert source_fixture.is_file(), "The source humanoid fixture is unavailable."
    assert target_fixture.is_file(), "The retarget target fixture is unavailable."
    project_root = tmp_path / "retarget-project"
    project_root.mkdir()
    source = project_root / "source.glb"
    target = project_root / "target.glb"
    shutil.copyfile(source_fixture, source)
    shutil.copyfile(target_fixture, target)

    source_inspection = adapter.inspect_glb(source, allowed_root=project_root)
    target_inspection = adapter.inspect_glb(target, allowed_root=project_root)
    source_rig = analyze_rig(source_inspection)
    target_rig = analyze_rig(target_inspection)
    assert source_rig["status"] == "humanoid_names_complete"
    assert target_rig["status"] == "humanoid_names_complete"
    source_hierarchy = source_rig["hierarchy_validation"]
    target_hierarchy = target_rig["hierarchy_validation"]
    assert source_hierarchy["status"] == "valid", source_hierarchy
    assert target_hierarchy["status"] == "valid", target_hierarchy

    source_mapping = source_rig["godot_profile_mapping"]
    target_mapping = target_rig["godot_profile_mapping"]
    assert len(source_mapping) == len(target_mapping) == 15
    assert source_mapping["LeftUpperArm"]["source_name"] == "mixamorig_LeftArm"
    assert target_mapping["LeftUpperArm"]["source_name"] == "mixamorig_LeftArm"
    assert source_mapping["LeftUpperArm"]["bone_index"] != (
        target_mapping["LeftUpperArm"]["bone_index"]
    )
    assert (
        target_mapping["LeftLowerArm"]["source_name"]
        != source_mapping["LeftLowerArm"]["source_name"]
    )
    assert source_mapping["LeftLowerArm"]["rest_transform"]["origin"] != (
        target_mapping["LeftLowerArm"]["rest_transform"]["origin"]
    )

    output = project_root / "retargets" / "source-to-target.tscn"
    response = adapter.retarget_glb_pair(
        source,
        target,
        output,
        allowed_root=project_root,
        source_profile_mapping=source_mapping,
        target_profile_mapping=target_mapping,
    )
    assert response["ok"] is True
    assert response["mapped_bone_count"] == 15
    assert response["target_skinned_mesh_count"] >= 1
    assert response["scene_reopened"] is True
    assert response["pose_transferred"] is True
    assert output.is_file()
    assert source.read_bytes() == source_fixture.read_bytes()
    assert target.read_bytes() == target_fixture.read_bytes()


def test_retarget_adapter_accepts_complete_humanoid_mapping_and_builds_request(
    tmp_path, monkeypatch
):
    adapter = _fake_adapter(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    source = project_root / "source.glb"
    target = project_root / "target.glb"
    source.write_bytes(b"source")
    target.write_bytes(b"target")
    mapping = {
        profile_name: {"bone_index": index}
        for index, profile_name in enumerate(REQUIRED_HUMANOID_BONES)
    }
    captured = {}

    def fake_run(operation, payload, **kwargs):
        captured["operation"] = operation
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(adapter, "_run", fake_run)
    output = project_root / "retargets" / "pair.tscn"
    response = adapter.retarget_glb_pair(
        source,
        target,
        output,
        allowed_root=project_root,
        source_profile_mapping=mapping,
        target_profile_mapping=mapping,
    )
    assert response["ok"] is True
    assert captured["operation"] == "retarget_glb_pair"
    assert set(captured["payload"]["source_profile_mapping"]) == set(
        REQUIRED_HUMANOID_BONES
    )
    assert output.parent.is_dir()
