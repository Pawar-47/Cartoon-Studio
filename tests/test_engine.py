from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.character_builder import ensure_model_asset
from app.engine import EngineTimeoutError, EngineUnavailableError, GodotEngineAdapter
from app.rig_analysis import analyze_rig
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
ROBOT_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "third_party"
    / "robot_expressive_cc0.glb"
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
    assert "skeleton_report" in ping["capabilities"]
    assert "probe_glb_animation" in ping["capabilities"]
    assert "export_character_appearance" in ping["capabilities"]
    assert "customize_character_proportions" in ping["capabilities"]
    assert "add_character_hair" in ping["capabilities"]

    project_root = tmp_path / "project"
    project_root.mkdir()
    fixture = project_root / "proof_triangle.glb"
    shutil.copy2(FIXTURE, fixture)
    inspection = adapter.inspect_glb(fixture, allowed_root=project_root)
    assert inspection["mesh_count"] >= 1
    assert len(inspection["mesh_inventory"]) == inspection["mesh_count"]
    mesh_record = inspection["mesh_inventory"][0]
    assert mesh_record["node_path"]
    assert mesh_record["mesh_type"]
    assert isinstance(mesh_record["surface_count"], int)
    assert isinstance(mesh_record["skin_bound"], bool)
    assert set(mesh_record["bounds"]) == {"position", "size"}
    assert mesh_record["slot_candidate"] in {"", "head", "body", "legs", "feet"}
    assert inspection["skeleton_count"] == len(inspection["skeletons"])
    assert inspection["engine_version"].startswith("4.7.2")



@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_assembles_four_parts_from_distinct_shared_rig_outfits(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path, timeout_seconds=180)
    project_root = tmp_path / "modular-project"
    project_root.mkdir()
    cache_root = project_root / "assets" / "character-library"

    base_path = ensure_model_asset(cache_root, "Male", "Adventurer")
    base_inspection = adapter.inspect_glb(base_path, allowed_root=project_root)
    assert base_inspection["skeleton_count"] == 1
    assert len(base_inspection["animation_names"]) == 24

    source_outfits = {
        "head": "Beach",
        "body": "Casual_2",
        "legs": "Farmer",
        "feet": "King",
    }
    parts = []
    for slot, outfit in source_outfits.items():
        source_path = ensure_model_asset(cache_root, "Male", outfit)
        inspection = adapter.inspect_glb(source_path, allowed_root=project_root)
        assert inspection["skeleton_count"] == 1
        candidates = [
            mesh
            for mesh in inspection["mesh_inventory"]
            if mesh["slot_candidate"] == slot and mesh["skin_bound"]
        ]
        assert candidates, f"{outfit} did not expose a skinned {slot} mesh"
        parts.append(
            {
                "slot": slot,
                "source_path": str(source_path),
                "mesh_path": candidates[0]["node_path"],
            }
        )

    accessory_candidates = [
        mesh
        for mesh in base_inspection["mesh_inventory"]
        if "backpack" in (
            mesh["node_name"] + " " + mesh["mesh_resource_name"] + " " + mesh["node_path"]
        ).lower()
        and (mesh["skin_bound"] or mesh["attachment_bone"])
    ]
    assert accessory_candidates, "Adventurer should expose its Backpack accessory"
    backpack = accessory_candidates[0]
    output_path = project_root / "assets" / "assembled" / "mixed-character.glb"
    result = adapter.assemble_modular_character(
        base_path,
        parts,
        output_path,
        allowed_root=project_root,
        accessories=[
            {
                "source_path": str(base_path),
                "mesh_path": backpack["node_path"],
                "attachment_bone": backpack["attachment_bone"],
            }
        ],
        timeout_seconds=180,
    )
    assert result["assembly_verified"] is True
    assert result["animation_preserved"] is True
    assert result["skeleton_count"] == 1
    assert result["animation_count"] == base_inspection["animation_count"]
    assert set(result["animation_names"]) == set(base_inspection["animation_names"])
    assert {part["slot"] for part in result["added_parts"]} == {
        "head", "body", "legs", "feet"
    }
    assert len(result["base_meshes_removed"]) >= 1
    assert len(result["added_accessories"]) == 1
    assert result["added_accessories"][0]["mesh_name"].lower().find("backpack") >= 0
    assert result["mesh_count"] >= 5
    probe = adapter.probe_glb_animation(
        output_path,
        "Walk",
        allowed_root=project_root,
        sample_ratio=0.37,
        timeout_seconds=60,
    )
    assert probe["ok"] is True
    assert probe["animation_name"] == "Walk"
    assert probe["pose_changed"] is True
    assert probe["changed_bone_count"] > 0
    assert probe["skinned_mesh_count"] >= 4
    assert probe["bone_count"] == result["skeletons"][0]["bone_count"]




@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_generates_attached_hair_and_preserves_animation(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path, timeout_seconds=120)
    project_root = tmp_path / "hair-project"
    project_root.mkdir()
    source = project_root / "source-humanoid.glb"
    output = project_root / "ponytail-humanoid.glb"
    shutil.copy2(
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
        / "proof_humanoid.glb",
        source,
    )
    original_bytes = source.read_bytes()
    before = adapter.inspect_glb(source, allowed_root=project_root)
    result = adapter.add_character_hair(
        source, "ponytail", "#2b1b13", output,
        allowed_root=project_root, timeout_seconds=120,
    )
    assert result["hair_verified"] is True
    assert result["hair_attachment_verified"] is True
    assert result["hair_mesh_count"] >= 3
    assert result["hair_attachment_bone"].lower().endswith("head")
    assert result["animation_names"] == before["animation_names"]
    assert source.read_bytes() == original_bytes
    playback = adapter.probe_glb_animation(
        output, before["animation_names"][0],
        allowed_root=project_root, timeout_seconds=60,
    )
    assert playback["pose_changed"] is True
    assert playback["skinned_mesh_count"] >= 1



@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_bakes_cartoon_face_geometry_and_preserves_animation(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path, timeout_seconds=180)
    project_root = tmp_path / "face-feature-project"
    project_root.mkdir()
    source = ensure_model_asset(
        project_root / "assets" / "character-library", "Male", "Adventurer"
    )
    output = project_root / "assets" / "adventurer-with-cartoon-face.glb"
    original_bytes = source.read_bytes()
    before = adapter.inspect_glb(source, allowed_root=project_root)
    assert before["skeleton_count"] == 1
    assert any(
        item["slot_candidate"] == "head" and item["skin_bound"]
        for item in before["mesh_inventory"]
    )

    result = adapter.export_character_appearance(
        source,
        [],
        [],
        output,
        allowed_root=project_root,
        face_features={
            "enabled": True,
            "skin_color_auto": False,
            "skin_color": "#bd8068",
            "moustache_enabled": True,
            "moustache_color": "#38251c",
            "moustache_size": 1.1,
            "face_width": 1.12,
            "cheek_fullness": 1.25,
            "jaw_width": 0.88,
            "chin_length": 1.18,
            "mouth_open": 0.78,
            "eye_color": "#ffffff",
            "iris_color": "#4b83b8",
            "brow_color": "#38251c",
            "mouth_color": "#612b2b",
            "nose_color": "#c98768",
            "eye_scale": 1.08,
            "eye_spacing": 0.96,
            "smile": 0.55,
            "brow_angle": 0.08,
            "ear_size": 1.2,
            "nose_width": 1.25,
            "nose_height": 0.9,
            "mouth_width": 1.15,
        },
        timeout_seconds=180,
    )

    assert result["appearance_verified"] is True
    assert result["face_features_verified"] is True
    assert result["face_attachment_bone"].lower().endswith("head")
    assert result["face_fit_basis"] == "generated_head_template"
    assert result["face_skin_replaced"] is True
    assert len(result["face_eye_anchor"]) == 3
    assert len(result["face_nose_anchor"]) == 3
    assert len(result["face_mouth_anchor"]) == 3
    assert result["applied_face_feature_count"] >= 23
    assert result["skeleton_count"] == before["skeleton_count"]
    assert result["animation_names"] == before["animation_names"]
    face_meshes = [
        item for item in result["mesh_inventory"]
        if item["node_name"].startswith("CartoonStudio_Face_")
    ]
    assert len(face_meshes) >= 22
    face_names = {item["node_name"] for item in face_meshes}
    assert any(name.startswith("CartoonStudio_Face_Ear_") for name in face_names)
    assert any(name.startswith("CartoonStudio_Face_EarInner_") for name in face_names)
    assert any(name.startswith("CartoonStudio_Face_Nostril_") for name in face_names)
    assert any(name.startswith("CartoonStudio_Face_Moustache_") for name in face_names)
    assert "CartoonStudio_Face_NoseBridge" in face_names
    assert "CartoonStudio_Face_MouthOpening" in face_names
    assert all(
        f"CartoonStudio_Face_Mouth_{index}" in face_names
        for index in range(3)
    ), "Closed-mouth line geometry must remain available for expression animation."
    assert "CartoonStudio_Face_MouthTongue" in face_names
    assert all(item["attachment_bone"].lower().endswith("head") for item in face_meshes)
    # glTF has no per-surface names, so the generated face surface is identified on
    # the re-imported GLB by the marker material name baked with it.
    generated_face_surfaces = [
        item for item in result["mesh_inventory"]
        if "CartoonStudio_GeneratedFace" in item.get("material_names", [])
    ]
    assert len(generated_face_surfaces) >= 1
    assert generated_face_surfaces[0]["skin_bound"] is True
    assert source.read_bytes() == original_bytes
    assert output.is_file()


@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_fits_hair_to_real_adventurer_head_and_keeps_source_unchanged(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path, timeout_seconds=120)
    project_root = tmp_path / "adventurer-hair-project"
    project_root.mkdir()
    source = ensure_model_asset(
        project_root / "assets" / "character-library", "Male", "Adventurer"
    )
    original_bytes = source.read_bytes()
    before = adapter.inspect_glb(source, allowed_root=project_root)
    assert before["animation_names"]
    assert any(
        mesh["slot_candidate"] == "head" and mesh["skin_bound"]
        for mesh in before["mesh_inventory"]
    )

    for style in ("short", "ponytail"):
        output = project_root / "assets" / f"adventurer-{style}.glb"
        result = adapter.add_character_hair(
            source,
            style,
            "#2b1b13",
            output,
            allowed_root=project_root,
            timeout_seconds=120,
        )
        assert result["hair_verified"] is True
        assert result["hair_placement_verified"] is True
        assert result["hair_fit_basis"] == "head_mesh_bounds"
        assert result["hair_front_direction"] == pytest.approx(1.0)
        assert result["hair_front_direction_basis"] == "face_feature_surfaces"
        assert result["hair_cap_clearance_verified"] is True
        assert result["hair_attachment_verified"] is True
        assert result["animation_names"] == before["animation_names"]
        assert result["hair_head_bounds_in_bone_space"]["size"][1] > 0
        if style == "short":
            assert result["hair_fringe_front_verified"] is True
        else:
            assert result["hair_ponytail_back_verified"] is True
        assert output.is_file()
        assert source.read_bytes() == original_bytes

    playback = adapter.probe_glb_animation(
        project_root / "assets" / "adventurer-ponytail.glb",
        "Walk",
        allowed_root=project_root,
        timeout_seconds=60,
    )
    assert playback["pose_changed"] is True
    assert playback["skinned_mesh_count"] >= 1


@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_bakes_humanoid_body_proportions_and_preserves_animation(tmp_path):
    adapter = GodotEngineAdapter(data_dir=tmp_path, timeout_seconds=120)
    project_root = tmp_path / "proportion-project"
    project_root.mkdir()
    source = project_root / "source-humanoid.glb"
    output = project_root / "proportioned-humanoid.glb"
    shutil.copy2(
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
        / "proof_humanoid.glb",
        source,
    )
    original_bytes = source.read_bytes()
    before = adapter.inspect_glb(source, allowed_root=project_root)
    rig = analyze_rig(before)
    assert rig["status"] == "humanoid_names_complete"
    result = adapter.customize_character_proportions(
        source,
        {"torso_length": 1.12, "shoulder_width": 1.08, "arm_length": 0.94,
         "leg_length": 1.06, "head_size": 1.1},
        output,
        allowed_root=project_root,
        timeout_seconds=120,
        bone_mapping=rig["bone_mapping"],
    )
    assert result["proportions_verified"] is True
    assert result["changed_bones"]
    assert result["skeleton_count"] == 1
    assert result["animation_count"] == before["animation_count"]
    assert set(result["animation_names"]) == set(before["animation_names"])
    assert source.read_bytes() == original_bytes
    assert output.is_file()
    playback = adapter.probe_glb_animation(
        output, before["animation_names"][0], allowed_root=project_root, timeout_seconds=60
    )
    assert playback["pose_changed"] is True
    assert playback["skinned_mesh_count"] >= 1


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


def test_modular_assembly_rejects_reusing_the_same_source_mesh(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    base = root / "base.glb"
    source = root / "parts.glb"
    base.write_bytes(b"fixture")
    source.write_bytes(b"fixture")
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    parts = [
        {"slot": slot, "source_path": str(source), "mesh_path": "Character/Mesh"}
        for slot in ("head", "body", "legs", "feet")
    ]
    with pytest.raises(ValueError, match="same source mesh"):
        adapter.assemble_modular_character(
            base,
            parts,
            root / "assembled.glb",
            allowed_root=root,
        )


def test_animation_probe_rejects_outside_paths_and_invalid_sample_ratio(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"fixture")
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    with pytest.raises(ValueError, match="escapes"):
        adapter.probe_glb_animation(outside, "Walk", allowed_root=root)
    source = root / "character.glb"
    source.write_bytes(b"fixture")
    with pytest.raises(ValueError, match="between 0 and 1"):
        adapter.probe_glb_animation(
            source, "Walk", allowed_root=root, sample_ratio=1.5
        )


def test_world_export_adapter_accepts_every_persistable_object_kind(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    kinds = (
        "road", "building", "shop", "school", "hospital", "office",
        "police_station", "tree", "vehicle", "lamp", "park", "garage",
        "indoor_room", "playground", "furniture", "water_body", "streetlight",
    )
    world = {
        "name": "Adapter Contract Test",
        "theme": "small_town",
        "ground_color": "#789b58",
        "sky": "day",
        "objects": [
            {
                "id": f"object-{index}",
                "kind": kind,
                "label": kind.replace("_", " ").title(),
                "x": 10 + index * 4,
                "y": 50,
                "width": 12,
                "height": 8,
                "rotation": 15,
                "color": "#c89b67",
            }
            for index, kind in enumerate(kinds)
        ],
    }
    captured = {}

    def fake_run(operation, payload, **kwargs):
        captured["operation"] = operation
        captured["payload"] = payload
        return {"ok": True}

    monkeypatch.setattr(adapter, "_run", fake_run)
    asset_path = project_root / "assets" / "world-library" / "road-straight.glb"
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"glTF-test-fixture")
    world["objects"][0]["asset_path"] = "assets/world-library/road-straight.glb"
    output = project_root / "assets" / "worlds" / "contract.tscn"
    result = adapter.export_world_scene(world, output, allowed_root=project_root)
    assert result["ok"] is True
    assert captured["operation"] == "export_world_scene"
    assert [item["kind"] for item in captured["payload"]["world"]["objects"]] == list(kinds)
    assert captured["payload"]["world"]["objects"][0]["asset_path"] == str(asset_path.resolve())
    assert output.parent.is_dir()


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

@pytest.mark.skipif(not HAS_GODOT, reason="Pinned Godot runtime is supplied by Windows CI.")
def test_godot_worker_bakes_and_reimports_material_and_facial_edits(tmp_path):
    assert ROBOT_FIXTURE.is_file(), "CI must fetch the pinned CC0 RobotExpressive fixture"
    adapter = GodotEngineAdapter(data_dir=tmp_path, timeout_seconds=120)
    project_root = tmp_path / "appearance-project"
    project_root.mkdir()
    source_path = project_root / "robot-expressive.glb"
    shutil.copy2(ROBOT_FIXTURE, source_path)
    before = adapter.inspect_glb(source_path, allowed_root=project_root)
    assert before["morph_targets"], "The facial fixture must expose blend shapes"
    mesh_name_counts = {}
    for item in before["mesh_inventory"]:
        mesh_name_counts[item["node_name"]] = mesh_name_counts.get(item["node_name"], 0) + 1
    morph = next(
        item for item in before["morph_targets"]
        if mesh_name_counts.get(item["mesh_name"]) == 1
    )
    material_mesh = next(
        item for item in before["mesh_inventory"]
        if item["surface_count"] > 0
        and item["material_properties"]
        and item["material_properties"][0]
        and mesh_name_counts.get(item["node_name"]) == 1
    )
    output_path = project_root / "assets" / "customized.glb"
    result = adapter.export_character_appearance(
        source_path,
        materials=[{
            "mesh_name": material_mesh["node_name"], "surface_index": 0,
            "material_name": material_mesh["material_names"][0],
            "color": "#e85d3f", "roughness": 0.72, "metalness": 0.08,
        }],
        morph_targets=[{
            "mesh_name": morph["mesh_name"], "target_index": morph["index"],
            "target_name": morph["name"], "value": 0.65,
        }],
        output_path=output_path, allowed_root=project_root, timeout_seconds=120,
    )
    assert result["appearance_verified"] is True
    assert result["applied_material_count"] == 1
    assert result["applied_morph_count"] == 1
    after = adapter.inspect_glb(output_path, allowed_root=project_root)
    assert set(after["animation_names"]) == set(before["animation_names"])
    baked_morph = next(
        item for item in after["morph_targets"]
        if item["mesh_name"] == morph["mesh_name"] and item["index"] == morph["index"]
    )
    assert baked_morph["default_value"] == pytest.approx(0.65, abs=0.02)
    baked_mesh = next(
        item for item in after["mesh_inventory"]
        if item["mesh_resource_name"].removeprefix("customized_")
        == material_mesh["mesh_resource_name"]
    )
    baked_material = baked_mesh["material_properties"][0]
    assert baked_material["color"][:3] == pytest.approx([232 / 255, 93 / 255, 63 / 255], abs=0.02)
    assert baked_material["roughness"] == pytest.approx(0.72, abs=0.02)
    assert baked_material["metalness"] == pytest.approx(0.08, abs=0.02)


def test_appearance_export_rejects_invalid_mesh_and_morph_bindings(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    source = root / "source.glb"
    source.write_bytes(b"fixture")
    adapter = GodotEngineAdapter(data_dir=tmp_path)
    with pytest.raises(ValueError, match="mesh name"):
        adapter.export_character_appearance(
            source, [{"surface_index": 0, "color": "#ffffff"}], [],
            root / "out.glb", allowed_root=root,
        )
    with pytest.raises(ValueError, match="target index"):
        adapter.export_character_appearance(
            source,
            [],
            [{"mesh_name": "Face", "target_name": "Smile", "target_index": -1, "value": 0.5}],
            root / "out.glb", allowed_root=root,
        )
