from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import threading
from pathlib import Path

import pytest

from app import engine
from app.character_builder import ensure_model_asset
from app.engine import (
    EngineCancelledError,
    EngineExecutionError,
    EnginePathError,
    EngineTimeoutError,
    GodotEngineAdapter,
)
from app.rig_analysis import REQUIRED_HUMANOID_BONES, analyze_rig
from tools.godot_engine_proof.generate_retarget_target_fixture import (
    generate_target_fixture,
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


def test_face_template_request_preserves_new_controls(tmp_path, monkeypatch):
    adapter = _fake_adapter(tmp_path)
    project_root = tmp_path / "face-template-project"
    project_root.mkdir()
    source = project_root / "source.glb"
    source.write_bytes(b"glTF")
    captured = {}

    def fake_run(operation, payload, **kwargs):
        captured["operation"] = operation
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(adapter, "_run", fake_run)
    result = adapter.export_character_appearance(
        source,
        [],
        [],
        project_root / "face-template.glb",
        allowed_root=project_root,
        face_features={
            "enabled": True,
            "skin_color_auto": False,
            "nose_color_auto": False,
            "moustache_enabled": True,
            "moustache_color": "#38251c",
            "moustache_size": 1.2,
            "ear_size": 1.3,
            "nose_width": 1.4,
            "nose_height": 0.8,
            "mouth_width": 1.25,
        },
    )

    assert result["ok"] is True
    assert captured["operation"] == "export_character_appearance"
    assert captured["payload"]["face_features"]["skin_color_auto"] is False
    assert captured["payload"]["face_features"]["nose_color_auto"] is False
    assert captured["payload"]["face_features"]["moustache_enabled"] is True
    assert captured["payload"]["face_features"]["moustache_size"] == 1.2
    assert captured["payload"]["face_features"]["ear_size"] == 1.3
    assert captured["payload"]["face_features"]["nose_width"] == 1.4
    assert captured["payload"]["face_features"]["nose_height"] == 0.8
    assert captured["payload"]["face_features"]["mouth_width"] == 1.25


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


def _make_morph_glb(
    default_weights: tuple[float, float] = (0.0, 0.0),
    node_weights: tuple[float, float] | None = None,
) -> bytes:
    positions = (
        -0.5, 0.0, 0.0,
        0.5, 0.0, 0.0,
        0.0, 1.0, 0.0,
    )
    smile_deltas = (
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, 0.15, 0.0,
    )
    blink_deltas = (
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        0.0, -0.1, 0.0,
    )
    binary = struct.pack("<27f", *(positions + smile_deltas + blink_deltas))
    face_node = {"name": "Face", "mesh": 0}
    if node_weights is not None:
        face_node["weights"] = list(node_weights)
    document = {
        "asset": {"version": "2.0", "generator": "Cartoon Studio morph fixture"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [face_node],
        "meshes": [{
            "name": "FaceMesh",
            "weights": list(default_weights),
            "extras": {"targetNames": ["Smile", "Blink"]},
            "primitives": [{
                "attributes": {"POSITION": 0},
                "targets": [{"POSITION": 1}, {"POSITION": 2}],
            }],
        }],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": offset, "byteLength": 36, "target": 34962}
            for offset in (0, 36, 72)
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": 3,
                "type": "VEC3",
                "min": [-0.5, 0.0, 0.0],
                "max": [0.5, 1.0, 0.0],
            },
            {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5126, "count": 3, "type": "VEC3"},
        ],
    }
    json_chunk = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((-len(json_chunk)) % 4)
    binary_chunk = binary + b"\x00" * ((-len(binary)) % 4)
    total_length = 12 + 8 + len(json_chunk) + 8 + len(binary_chunk)
    return (
        struct.pack("<4sII", b"glTF", 2, total_length)
        + struct.pack("<II", len(json_chunk), 0x4E4F534A)
        + json_chunk
        + struct.pack("<II", len(binary_chunk), 0x004E4942)
        + binary_chunk
    )


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


def test_pinned_godot_worker_inspects_real_third_party_rigged_figure(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "fixtures"
        / "third_party"
        / "rigged_figure_ccby.glb"
    )
    assert fixture.is_file(), "The licensed third-party Rigged Figure fixture is unavailable."
    asset_dir = tmp_path / "third-party-assets"
    asset_dir.mkdir()
    target = asset_dir / "rigged-figure.glb"
    shutil.copyfile(fixture, target)

    inspection = adapter.inspect_glb(target, allowed_root=tmp_path)
    rig = analyze_rig(inspection)

    assert inspection["ok"] is True
    assert inspection["mesh_count"] == 1
    assert inspection["skeleton_count"] == 1
    assert inspection["animation_count"] >= 1
    assert rig["status"] == "humanoid_names_complete"
    assert rig["matched_bone_count"] == 15
    assert rig["hierarchy_validation"]["status"] == "valid"
    mapping = rig["godot_profile_mapping"]
    assert mapping["Hips"]["source_name"] == "torso_joint_1"
    assert mapping["Spine"]["source_name"] == "torso_joint_2"
    assert mapping["Head"]["source_name"] == "neck_joint_2"
    assert mapping["LeftUpperLeg"]["source_name"] == "leg_joint_L_1"
    assert mapping["LeftUpperArm"]["source_name"] == "arm_joint_L_1"
    assert target.read_bytes() == fixture.read_bytes()


def test_pinned_godot_worker_inspects_real_cc0_robot_expressive_facial_morphs(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "fixtures"
        / "third_party"
        / "robot_expressive_cc0.glb"
    )
    assert fixture.is_file(), "The pinned CC0 RobotExpressive fixture was not fetched."
    payload = fixture.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == (
        "047f5e5fb3bb6d378bd1df16ca6137f2a596c99b3a1b5690b4020c05aaf6f319"
    )

    asset_dir = tmp_path / "robot-expressive-assets"
    asset_dir.mkdir()
    target = asset_dir / "robot-expressive.glb"
    shutil.copyfile(fixture, target)
    inspection = adapter.inspect_glb(target, allowed_root=tmp_path)

    assert inspection["ok"] is True
    assert inspection["animation_count"] >= 10
    animation_names = inspection["animation_names"]
    assert len(animation_names) >= 10
    assert len(set(animation_names)) == len(animation_names)
    assert all(animation_names)
    assert all(name.upper() != "RESET" for name in animation_names)
    morph_targets = inspection["morph_targets"]
    assert inspection["morph_target_count"] >= 3
    assert len(morph_targets) == inspection["morph_target_count"]
    assert {item["name"] for item in morph_targets} == {
        "Angry",
        "Surprised",
        "Sad",
    }
    assert all(item["default_value"] == 0.0 for item in morph_targets)
    assert target.read_bytes() == payload


@pytest.mark.parametrize("clip_name", ["Walking", "Running", "Dance"])
def test_pinned_godot_worker_retargets_robot_expressive_selected_clip(tmp_path, clip_name):
    adapter = _real_godot_adapter(tmp_path)
    fixture_dir = Path(__file__).resolve().parent / "fixtures" / "third_party"
    source_fixture = fixture_dir / "robot_expressive_cc0.glb"
    target_fixture = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
        / "proof_humanoid_retarget_target.glb"
    )
    assert source_fixture.is_file(), "The pinned RobotExpressive fixture is unavailable."
    assert target_fixture.is_file(), "The canonical retarget target fixture is unavailable."

    project_root = tmp_path / "robot-expressive-retarget-project"
    project_root.mkdir()
    source = project_root / "robot-expressive.glb"
    target = project_root / "canonical-target.glb"
    shutil.copyfile(source_fixture, source)
    shutil.copyfile(target_fixture, target)

    source_inspection = adapter.inspect_glb(source, allowed_root=project_root)
    target_inspection = adapter.inspect_glb(target, allowed_root=project_root)
    source_rig = analyze_rig(source_inspection)
    target_rig = analyze_rig(target_inspection)
    source_bone_names = [
        bone.get("name", "") for bone in source_inspection["skeletons"][0]["bones"]
    ]
    assert source_rig["status"] == "humanoid_names_complete", (
        f"RobotExpressive bones={source_bone_names}; "
        f"missing={source_rig['missing_bones']}; "
        f"ambiguous={source_rig['ambiguous_bones']}; "
        f"unmapped={source_rig['unmapped_bones']}"
    )
    # RobotExpressive's detached feet are accepted only as a bilateral IK-root variant.
    assert source_rig["hierarchy_validation"]["status"] == "valid_with_ik_foot_hierarchy"
    assert source_rig["godot_profile_mapping"]["Spine"]["source_name"] == "Abdomen"
    assert source_rig["godot_profile_mapping"]["LeftHand"]["source_name"] == "Palm2.L"
    assert target_rig["status"] == "humanoid_names_complete"

    animation_names = source_inspection["animation_names"]
    available_clips = {
        name.rsplit("/", 1)[-1]: name for name in animation_names
    }
    for clip_label in ("Walking", "Dance"):
        assert clip_label in available_clips
        selected_clip = available_clips[clip_label]
        output = (
            project_root
            / "retargets"
            / f"robot-expressive-{clip_label.lower()}.tscn"
        )
        response = adapter.retarget_glb_pair(
            source,
            target,
            output,
            allowed_root=project_root,
            source_profile_mapping=source_rig["godot_profile_mapping"],
            target_profile_mapping=target_rig["godot_profile_mapping"],
            animation_name=selected_clip,
        )

        assert response["ok"] is True
        assert response["animation_name"] == selected_clip
        assert response["scene_reopened"] is True
        assert response["source_animation_playing"] is True
        assert response["pose_transferred"] is True
        assert output.is_file()
        assert source.read_bytes() == source_fixture.read_bytes()
        assert target.read_bytes() == target_fixture.read_bytes()


def test_pinned_godot_worker_retargets_real_third_party_rigged_figure(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture_dir = Path(__file__).resolve().parent / "fixtures" / "third_party"
    source_fixture = fixture_dir / "rigged_figure_ccby.glb"
    target_fixture = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
        / "proof_humanoid_retarget_target.glb"
    )
    assert source_fixture.is_file(), "The licensed third-party source fixture is unavailable."
    assert target_fixture.is_file(), "The native retarget target fixture is unavailable."

    project_root = tmp_path / "third-party-retarget-project"
    project_root.mkdir()
    source = project_root / "source-rigged-figure.glb"
    target = project_root / "target-humanoid.glb"
    shutil.copyfile(source_fixture, source)
    shutil.copyfile(target_fixture, target)

    source_inspection = adapter.inspect_glb(source, allowed_root=project_root)
    target_inspection = adapter.inspect_glb(target, allowed_root=project_root)
    source_rig = analyze_rig(source_inspection)
    target_rig = analyze_rig(target_inspection)
    assert source_rig["status"] == target_rig["status"] == "humanoid_names_complete"
    assert source_rig["hierarchy_validation"]["status"] == "valid"
    assert target_rig["hierarchy_validation"]["status"] == "valid"
    assert source_inspection["animation_names"]
    selected_animation = source_inspection["animation_names"][0]

    output = project_root / "retargets" / "cesium-rigged-figure.tscn"
    response = adapter.retarget_glb_pair(
        source,
        target,
        output,
        allowed_root=project_root,
        source_profile_mapping=source_rig["godot_profile_mapping"],
        target_profile_mapping=target_rig["godot_profile_mapping"],
        animation_name=selected_animation,
    )
    assert response["ok"] is True
    assert response["animation_name"] == selected_animation
    assert response["mapped_bone_count"] == 15
    assert response["scene_reopened"] is True
    assert response["pose_transferred"] is True
    assert output.is_file()
    assert source.read_bytes() == source_fixture.read_bytes()
    assert target.read_bytes() == target_fixture.read_bytes()


def test_pinned_godot_worker_retargets_bone_roll_and_scaled_target(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture_dir = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
    )
    source_fixture = fixture_dir / "proof_humanoid_retarget_source.glb"
    base_target_fixture = fixture_dir / "proof_humanoid.glb"
    assert source_fixture.is_file(), "The animated source humanoid fixture is unavailable."
    assert base_target_fixture.is_file(), "The base target humanoid fixture is unavailable."

    project_root = tmp_path / "rest-axis-retarget-project"
    project_root.mkdir()
    source = project_root / "source.glb"
    target = project_root / "rolled-scaled-target.glb"
    shutil.copyfile(source_fixture, source)
    generate_target_fixture(
        base_target_fixture,
        target,
        rest_roll_degrees={
            "LeftUpperArm": 24.0,
            "LeftLowerArm": -32.0,
            "RightUpperArm": -24.0,
            "RightLowerArm": 32.0,
        },
        rest_scales={
            "LeftUpperArm": (1.0, 1.08, 0.94),
            "LeftLowerArm": (1.0, 0.92, 1.06),
            "RightUpperArm": (1.0, 0.94, 1.08),
            "RightLowerArm": (1.0, 1.06, 0.92),
        },
    )

    source_inspection = adapter.inspect_glb(source, allowed_root=project_root)
    target_inspection = adapter.inspect_glb(target, allowed_root=project_root)
    source_rig = analyze_rig(source_inspection)
    target_rig = analyze_rig(target_inspection)
    assert source_rig["status"] == target_rig["status"] == "humanoid_names_complete"
    assert source_rig["hierarchy_validation"]["status"] == "valid"
    assert target_rig["hierarchy_validation"]["status"] == "valid"
    source_arm = source_rig["godot_profile_mapping"]["LeftUpperArm"]
    target_arm = target_rig["godot_profile_mapping"]["LeftUpperArm"]
    assert source_arm["rest_transform"]["rotation"] != target_arm["rest_transform"]["rotation"]
    assert target_arm["rest_transform"]["scale"] != source_arm["rest_transform"]["scale"]

    output = project_root / "retargets" / "rolled-scaled-target.tscn"
    selected_animation = source_inspection["animation_names"][0]
    response = adapter.retarget_glb_pair(
        source,
        target,
        output,
        allowed_root=project_root,
        source_profile_mapping=source_rig["godot_profile_mapping"],
        target_profile_mapping=target_rig["godot_profile_mapping"],
        animation_name=selected_animation,
    )
    assert response["ok"] is True
    assert response["animation_name"] == selected_animation
    assert response["scene_reopened"] is True
    assert response["pose_transferred"] is True
    assert source.read_bytes() == source_fixture.read_bytes()


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

def test_node_morph_weights_override_mesh_defaults(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    asset_dir = tmp_path / "morph-node-override"
    asset_dir.mkdir()
    target = asset_dir / "face-node-override.glb"
    target.write_bytes(_make_morph_glb((0.1, 0.2), (0.35, 0.8)))

    response = adapter.inspect_glb(target, allowed_root=tmp_path)

    assert response["ok"] is True
    assert {
        entry["name"]: entry["default_value"]
        for entry in response["morph_targets"]
    } == {"Smile": 0.35, "Blink": 0.8}
    assert all(
        entry["default_value_source"] == "gltf_node"
        for entry in response["morph_targets"]
    )


def test_pinned_godot_worker_reports_real_animated_morph_cube(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    fixture = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "third_party"
        / "animated_morph_cube_cc0.glb"
    )
    assert fixture.is_file(), "The CC0 animated morph fixture is unavailable."
    asset_dir = tmp_path / "animated-morph-assets"
    asset_dir.mkdir()
    target = asset_dir / "animated-morph-cube.glb"
    shutil.copyfile(fixture, target)

    inspection = adapter.inspect_glb(target, allowed_root=tmp_path)

    assert inspection["ok"] is True
    assert inspection["mesh_count"] >= 1
    assert inspection["animation_count"] >= 1
    assert inspection["morph_target_count"] == 2
    # The upstream GLB does not encode targetNames; Godot correctly assigns
    # deterministic fallback names instead of guessing from the README order.
    assert {entry["name"] for entry in inspection["morph_targets"]} == {
        "morph_0",
        "morph_1",
    }
    assert all(entry["default_value"] == 0.0 for entry in inspection["morph_targets"])
    assert target.read_bytes() == fixture.read_bytes()


def test_pinned_godot_worker_preserves_nonzero_imported_morph_defaults(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    asset_dir = tmp_path / "morph-default-assets"
    asset_dir.mkdir()
    target = asset_dir / "face-with-default-expression.glb"
    target.write_bytes(_make_morph_glb((0.35, 0.8)))

    response = adapter.inspect_glb(target, allowed_root=tmp_path)

    assert response["ok"] is True
    assert {
        entry["name"]: entry["default_value"]
        for entry in response["morph_targets"]
    } == {"Smile": 0.35, "Blink": 0.8}
    assert {
        entry["name"]: entry["default_value_source"]
        for entry in response["morph_targets"]
    } == {"Smile": "gltf_mesh", "Blink": "gltf_mesh"}


def test_pinned_godot_worker_reports_imported_blend_shape_names_and_defaults(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    asset_dir = tmp_path / "morph-assets"
    asset_dir.mkdir()
    target = asset_dir / "face-with-morphs.glb"
    target.write_bytes(_make_morph_glb())

    response = adapter.inspect_glb(target, allowed_root=tmp_path)

    assert response["ok"] is True
    assert response["mesh_count"] == 1
    assert response["morph_target_count"] == 2
    assert [entry["name"] for entry in response["morph_targets"]] == [
        "Smile",
        "Blink",
    ]
    assert all(entry["mesh_name"] == "Face" for entry in response["morph_targets"])
    assert all(entry["default_value"] == 0.0 for entry in response["morph_targets"])




def test_pinned_quaternius_modular_models_share_rig_and_animation_library(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    cache_root = tmp_path / "character-library"
    expected_bone_names = None
    for pack, outfit in (
        ("Male", "Adventurer"),
        ("Male", "Worker"),
        ("Female", "Adventurer"),
    ):
        model_path = ensure_model_asset(cache_root, pack, outfit)
        inspection = adapter.inspect_glb(model_path, allowed_root=tmp_path)

        assert inspection["skeleton_count"] == 1
        assert inspection["animation_count"] == 24
        assert {"Idle", "Walk", "Run"}.issubset(
            set(inspection["animation_names"])
        )
        skeleton = inspection["skeletons"][0]
        bone_names = {
            bone["name"] for bone in skeleton["bones"] if bone.get("name")
        }
        assert skeleton["bone_count"] == 62
        assert len(bone_names) == 62
        if expected_bone_names is None:
            expected_bone_names = bone_names
        else:
            assert bone_names == expected_bone_names
        assert inspection["mesh_count"] >= 4


def test_world_scene_export_validates_layout_and_builds_worker_request(tmp_path, monkeypatch):
    adapter = _fake_adapter(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    captured = {}

    def fake_run(operation, payload, **kwargs):
        captured["operation"] = operation
        captured["payload"] = payload
        return {"ok": True, "object_count": 1, "scene_reopened": True}

    monkeypatch.setattr(adapter, "_run", fake_run)
    output = project_root / "assets" / "worlds" / "sample.tscn"
    world = {
        "name": "Town",
        "theme": "small_town",
        "sky": "day",
        "ground_color": "#789b58",
        "objects": [
            {
                "id": "tree-1", "kind": "tree", "label": "Tree",
                "x": 50, "y": 50, "width": 12, "height": 10,
                "rotation": 0, "color": "#4c9850",
            }
        ],
    }
    result = adapter.export_world_scene(world, output, allowed_root=project_root)
    assert result["ok"] is True
    assert captured["operation"] == "export_world_scene"
    assert captured["payload"]["world"] == world
    assert output.parent.is_dir()


def test_world_scene_export_rejects_output_path_escape(tmp_path):
    adapter = _fake_adapter(tmp_path)
    project_root = tmp_path / "project"
    project_root.mkdir()
    with pytest.raises(EnginePathError, match="escapes"):
        adapter.export_world_scene(
            {"objects": []}, tmp_path / "outside.tscn", allowed_root=project_root
        )



def test_pinned_godot_worker_exports_and_reopens_a_real_world_scene(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    project_root = tmp_path / "world-scene-project"
    project_root.mkdir()
    output = project_root / "assets" / "worlds" / "market-town.tscn"
    world = {
        "name": "Market Town",
        "theme": "market",
        "ground_color": "#789b58",
        "sky": "sunset",
        "objects": [
            {
                "id": "road-1", "kind": "road", "label": "Main Road",
                "x": 50, "y": 50, "width": 80, "height": 12,
                "rotation": 0, "color": "#4b4d50",
            },
            {
                "id": "shop-1", "kind": "shop", "label": "Bakery",
                "x": 30, "y": 40, "width": 18, "height": 16,
                "rotation": 0, "color": "#d9a46b",
            },
            {
                "id": "tree-1", "kind": "tree", "label": "Town Tree",
                "x": 70, "y": 25, "width": 10, "height": 12,
                "rotation": 0, "color": "#4c9850",
            },
            {
                "id": "car-1", "kind": "vehicle", "label": "Car",
                "x": 55, "y": 50, "width": 12, "height": 8,
                "rotation": 0, "color": "#477fa8",
            },
            {
                "id": "lamp-1", "kind": "lamp", "label": "Street Lamp",
                "x": 20, "y": 70, "width": 5, "height": 8,
                "rotation": 0, "color": "#e9d27a",
            },
            {
                "id": "park-1", "kind": "park", "label": "Green Park",
                "x": 80, "y": 80, "width": 20, "height": 18,
                "rotation": 0, "color": "#70a35b",
            },
            {
                "id": "house-1", "kind": "building", "label": "Town House",
                "x": 20, "y": 20, "width": 16, "height": 14,
                "rotation": 0, "color": "#c89b67",
            },
        ],
    }
    result = adapter.export_world_scene(world, output, allowed_root=project_root)
    assert result["ok"] is True
    assert result["object_count"] == 7
    assert result["theme_prop_count"] == 3
    assert result["world_theme"] == "market"
    assert result["scene_reopened"] is True
    assert result["lighting_preset"] == "sunset"
    assert result["glb_exported"] is True
    assert output.is_file()
    assert output.stat().st_size > 0
    preview = output.with_suffix(".glb")
    assert preview.is_file()
    inspection = adapter.inspect_glb(preview, allowed_root=project_root)
    assert inspection["ok"] is True
    assert inspection["mesh_count"] >= 10



def test_pinned_godot_worker_builds_episode_scenes_with_world_and_character_glb(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    project_root = tmp_path / "episode-production-project"
    project_root.mkdir()
    world_path = project_root / "assets" / "worlds" / "town.tscn"
    adapter.export_world_scene(
        {
            "name": "Town",
            "theme": "small_town",
            "ground_color": "#789b58",
            "sky": "day",
            "objects": [],
        },
        world_path,
        allowed_root=project_root,
    )
    source_character_path = ensure_model_asset(
        project_root / "assets" / "character-library", "Male", "Adventurer"
    )
    character_path = project_root / "assets" / "characters" / "ali.glb"
    character_path.parent.mkdir(parents=True, exist_ok=True)
    # Expression and speech tracks target baked CartoonStudio_Face_* nodes, so the
    # character must support generated-face replacement. The CC0 Adventurer has a
    # separable Skin surface; the robot fixture does not and is intentionally
    # rejected by the worker (covered by the regression test below).
    face_export = adapter.export_character_appearance(
        source_character_path,
        [],
        [],
        character_path,
        allowed_root=project_root,
        face_features={"enabled": True},
    )
    assert face_export["ok"] is True
    assert face_export["face_features_verified"] is True
    episode = {
        "title": "Five Scene Test",
        "characters": [{"id": "ali", "name": "Ali"}],
        "scenes": [
            {
                "id": f"scene-{index}",
                "title": f"Scene {index}",
                "duration_seconds": 60,
                "location_id": "street-cafe",
                "character_ids": ["ali"],
                "dialogue": (
                    [
                        {
                            "character_id": "ali",
                            "text": "یہ تو بہت مزے کی بات ہے!",
                            "emotion": "happy",
                            "delivery": "excited",
                            "start_seconds": 5,
                            "duration_seconds": 2,
                            "audio_duration_seconds": 2.0,
                            "audio_envelope": [
                                {"time": 0.0, "openness": 0.0},
                                {"time": 0.08, "openness": 0.8},
                                {"time": 0.16, "openness": 0.25},
                                {"time": 0.24, "openness": 0.0},
                            ],
                        }
                    ]
                    if index == 1
                    else []
                ),
                "actions": (
                    [
                        {
                            "character_id": "ali",
                            "action_id": "wave",
                            "start_seconds": 1,
                            "duration_seconds": 3,
                        },
                        {
                            "character_id": "ali",
                            "action_id": "walk",
                            "start_seconds": 8,
                            "duration_seconds": 4,
                        },
                        {
                            "character_id": "ali",
                            "action_id": "clap",
                            "start_seconds": 14,
                            "duration_seconds": 2,
                        }
                    ]
                    if index == 1
                    else []
                ),
                "camera": (
                    [
                        {
                            "shot": "medium",
                            "movement": "dolly",
                            "target": "ali",
                            "start_seconds": 1,
                            "duration_seconds": 3,
                        }
                    ]
                    if index == 1
                    else []
                ),
                "audio": [],
                "props": [],
            }
            for index in range(1, 6)
        ],
    }
    output = project_root / "assets" / "episodes" / "build-1" / "scenes"
    result = adapter.export_episode_scenes(
        episode,
        world_path,
        [{"id": "ali", "name": "Ali", "asset_path": str(character_path)}],
        output,
        allowed_root=project_root,
    )
    assert result["ok"] is True
    assert result["scene_count"] == 5
    assert all(scene["scene_reopened"] for scene in result["scenes"])
    assert all(scene["reopened_character_count"] == 1 for scene in result["scenes"])
    assert all(Path(scene["scene_path"]).is_file() for scene in result["scenes"])
    assert all(Path(scene["preview_path"]).is_file() for scene in result["scenes"])
    first_scene = result["scenes"][0]
    assert first_scene["action_cue_count"] == 3
    assert first_scene["skeletal_animation_track_count"] > 0
    assert (
        first_scene["skeletal_animation_keyframe_count"]
        > first_scene["skeletal_animation_track_count"]
    )
    assert result["scenes"][0]["expression_cue_count"] == 1
    assert result["scenes"][0]["speech_cue_count"] == 1
    assert result["scenes"][0]["speech_mouth_keyframe_count"] > 0
    assert result["scenes"][0]["audio_driven_speech_cue_count"] == 1
    assert result["scenes"][0]["audio_envelope_keyframe_count"] > 0
    assert result["scenes"][0]["camera_cue_count"] == 1
    assert result["scenes"][0]["animation_track_count"] > 5
    assert all(
        scene["action_cue_count"] == 0
        and scene["camera_cue_count"] == 0
        and scene["animation_track_count"] == 3
        for scene in result["scenes"][1:]
    )


def test_generated_face_replacement_rejects_rig_without_skin_surface(tmp_path):
    adapter = _real_godot_adapter(tmp_path)
    project_root = tmp_path / "face-surface-project"
    project_root.mkdir()
    fixture = (
        Path(__file__).resolve().parents[1]
        / "tests"
        / "fixtures"
        / "third_party"
        / "robot_expressive_cc0.glb"
    )
    if not fixture.is_file():
        pytest.skip("The pinned CC0 facial-morph fixture is unavailable.")
    source = project_root / "robot.glb"
    shutil.copyfile(fixture, source)
    output = project_root / "robot-with-generated-face.glb"

    with pytest.raises(EngineExecutionError, match="separable skin surface"):
        adapter.export_character_appearance(
            source,
            [],
            [],
            output,
            allowed_root=project_root,
            face_features={"enabled": True},
        )

    assert not output.exists()
