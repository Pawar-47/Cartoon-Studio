from __future__ import annotations

import json
import struct
import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app import main
from app.rig_analysis import REQUIRED_HUMANOID_BONES

client = TestClient(main.app)


class _FakeEngineAdapter:

    def export_world_scene(self, world, output_path, allowed_root, **kwargs):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            '[gd_scene format=3]\n[node name="CartoonWorld" type="Node3D"]\n',
            encoding="utf-8",
        )
        return {
            "ok": True,
            "object_count": len(world.get("objects", [])),
            "scene_reopened": True,
            "lighting_preset": world.get("sky", "day"),
        }

    available = True

    def ping(self):
        return {
            "ok": True,
            "engine_version": "4.7.2.test",
            "protocol_version": 1,
            "capabilities": ["ping", "glb_inspect"],
            "elapsed_ms": 2,
        }

    def inspect_glb(self, source_path, allowed_root, timeout_seconds=None):
        return {
            "ok": True,
            "mesh_count": 1,
            "skeleton_count": 0,
            "animation_player_count": 0,
            "node_count": 2,
            "source_path": str(source_path),
        }


class _FakeAssemblyAdapter(_FakeEngineAdapter):
    def assemble_modular_character(
        self, base_path, parts, output_path, allowed_root, accessories=None
    ):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        json_chunk = json.dumps({"asset": {"version": "2.0"}}).encode("utf-8")
        json_chunk += b" " * ((-len(json_chunk)) % 4)
        total_length = 12 + 8 + len(json_chunk)
        output_path.write_bytes(
            b"glTF"
            + struct.pack("<II", 2, total_length)
            + struct.pack("<II", len(json_chunk), 0x4E4F534A)
            + json_chunk
        )
        return {
            "ok": True,
            "assembly_verified": True,
            "animation_preserved": True,
            "added_parts": [{"slot": part["slot"]} for part in parts],
            "added_accessories": [{"mesh_name": "Backpack"} for _ in accessories or []],
            "mesh_count": 4,
            "mesh_inventory": [],
            "skeleton_count": 1,
            "animation_count": 2,
            "animation_names": ["Idle", "Walk"],
            "node_count": 8,
            "morph_targets": [],
        }


def _new_project(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "engine-api.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    response = client.post("/api/projects", json={"name": "Engine API Test"})
    assert response.status_code == 201
    return response.json()["id"]


def test_engine_status_endpoint_reports_worker(monkeypatch):
    monkeypatch.setattr(main, "get_engine_adapter", _FakeEngineAdapter)
    response = client.get("/api/engine/status")
    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["engine_version"].startswith("4.7.2")


def test_engine_inspect_endpoint_uses_project_relative_asset_path(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    asset = tmp_path / "projects" / project_id / "assets" / "character.glb"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"fixture")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeEngineAdapter)
    response = client.post(
        f"/api/projects/{project_id}/engine/inspect-glb",
        json={"relative_path": "assets/character.glb"},
    )
    assert response.status_code == 200
    assert response.json()["mesh_count"] == 1


def test_engine_inspect_endpoint_rejects_project_path_traversal(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    response = client.post(
        f"/api/projects/{project_id}/engine/inspect-glb",
        json={"relative_path": "../../outside.glb"},
    )
    assert response.status_code == 422


def test_modular_assembly_api_validates_slots_and_persists_verified_asset(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    monkeypatch.setattr(main, "get_engine_adapter", _FakeAssemblyAdapter)
    source = tmp_path / "projects" / project_id / "assets" / "source.glb"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source")
    parts = [
        {
            "slot": slot,
            "relative_path": "assets/source.glb",
            "mesh_path": f"Character/{slot}",
        }
        for slot in ("head", "body", "legs", "feet")
    ]
    response = client.post(
        f"/api/projects/{project_id}/modular-assemblies",
        json={
            "base_relative_path": "assets/source.glb",
            "parts": parts,
            "accessories": [
                {
                    "relative_path": "assets/source.glb",
                    "mesh_path": "Character/Backpack",
                    "attachment_bone": "Spine",
                }
            ],
        },
    )
    assert response.status_code == 201
    result = response.json()
    assert result["assembly"]["verified"] is True
    assert result["assembly"]["animation_preserved"] is True
    assert {part["slot"] for part in result["assembly"]["added_parts"]} == {
        "head", "body", "legs", "feet"
    }
    assert result["engine_inspection"]["animation_names"] == ["Idle", "Walk"]
    download = client.get(
        f"/api/projects/{project_id}/character-assets/{result['asset_id']}"
    )
    assert download.status_code == 200
    assert download.content.startswith(b"glTF")
    manifest = client.get(
        f"/api/projects/{project_id}/character-assets/{result['asset_id']}/manifest"
    )
    assert manifest.status_code == 200
    assert manifest.json()["assembly"]["verified"] is True
    assert manifest.json()["assembly"]["parts"][0]["slot"] in {
        "head", "body", "legs", "feet"
    }
    assert manifest.json()["assembly"]["accessories"][0]["attachment_bone"] == "Spine"
    assert manifest.json()["assembly"]["added_accessories"][0]["mesh_name"] == "Backpack"


def test_modular_assembly_api_rejects_duplicate_or_missing_slots(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    response = client.post(
        f"/api/projects/{project_id}/modular-assemblies",
        json={
            "base_relative_path": "assets/source.glb",
            "parts": [
                {"slot": slot, "relative_path": "assets/source.glb", "mesh_path": "Root/Mesh"}
                for slot in ("head", "body", "legs", "legs")
            ],
        },
    )
    assert response.status_code == 422


def test_engine_status_endpoint_reports_missing_runtime(monkeypatch):
    class MissingEngine:
        available = False

    monkeypatch.setattr(main, "get_engine_adapter", MissingEngine)
    response = client.get("/api/engine/status")
    assert response.status_code == 200
    assert response.json()["status"] == "runtime_not_found"


class _FakeRetargetAdapter(_FakeEngineAdapter):
    def retarget_glb_pair(
        self,
        source_path,
        target_path,
        output_path,
        allowed_root,
        source_profile_mapping,
        target_profile_mapping,
        animation_name="",
    ):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("[gd_scene format=3]", encoding="utf-8")
        return {
            "ok": True,
            "animation_name": animation_name or "Walk",
            "mapped_bone_count": 15,
            "target_skinned_mesh_count": 1,
            "scene_reopened": True,
            "pose_transferred": True,
            "source_animation_playing": True,
            "source_pose_angle_degrees": 29.0,
            "target_pose_angle_degrees": 29.0,
        }


def _seed_retarget_character(tmp_path, project_id, name):
    character_id = str(uuid.uuid4())
    asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{asset_id}.glb"
    asset_path = tmp_path / "projects" / project_id / relative_path
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"fixture")
    mapping = {
        profile_name: {"bone_index": index, "source_name": profile_name}
        for index, profile_name in enumerate(REQUIRED_HUMANOID_BONES)
    }
    asset = {
        "relative_path": relative_path,
        "rig_analysis": {
            "status": "humanoid_names_complete",
            "hierarchy_validation": {
                "status": "valid",
                "note": "Valid test hierarchy",
            },
            "godot_profile_mapping": mapping,
        },
        "container": {"skin_count": 1},
        "engine_inspection": {
            "animation_count": 3,
            "animation_names": ["Walk", "Run"],
            "skeleton_count": 1,
        },
    }
    now = datetime.now(UTC).isoformat()
    document = main.make_envelope(
        "character",
        character_id,
        {
            "name": name,
            "asset": asset,
            "appearance_recipe": {"materials": {}, "morph_targets": {}},
        },
        now,
        now,
        1,
    )
    character_path = (
        tmp_path
        / "projects"
        / project_id
        / "characters"
        / f"{character_id}.json"
    )
    character_path.parent.mkdir(parents=True, exist_ok=True)
    character_path.write_text(json.dumps(document), encoding="utf-8")
    return character_id


def test_character_appearance_persists_facial_morph_weights(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    character_id = _seed_retarget_character(tmp_path, project_id, "Facial rig")

    response = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json={
            "materials": {},
            "morph_targets": {
                "0:Face/0:Head:Smile": 0.75,
                "0:Face/0:Head:Blink": -0.25,
            },
            "face_features": {
                "enabled": True,
                "eye_color": "#ffffff",
                "iris_color": "#4b83b8",
                "eye_scale": 1.1,
                "eye_spacing": 0.95,
                "smile": 0.6,
                "brow_angle": 0.1,
            },
        },
    )

    assert response.status_code == 200
    saved = response.json()
    assert saved["revision"] == 2
    assert saved["data"]["appearance_recipe"]["morph_targets"] == {
        "0:Face/0:Head:Smile": 0.75,
        "0:Face/0:Head:Blink": -0.25,
    }
    assert saved["data"]["appearance_recipe"]["face_features"]["enabled"] is True
    assert saved["data"]["appearance_recipe"]["face_features"]["eye_scale"] == 1.1
    reopened = client.get(
        f"/api/projects/{project_id}/characters/{character_id}"
    )
    assert reopened.status_code == 200
    assert reopened.json()["data"]["appearance_recipe"]["morph_targets"] == (
        saved["data"]["appearance_recipe"]["morph_targets"]
    )
    assert reopened.json()["data"]["appearance_recipe"]["face_features"] == (
        saved["data"]["appearance_recipe"]["face_features"]
    )

    invalid = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json={"morph_targets": {"Smile": 1.5}},
    )
    assert invalid.status_code == 422


def test_character_retarget_api_saves_scene_and_persistent_record(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeRetargetAdapter)

    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={
            "source_character_id": source_id,
            "target_character_id": target_id,
            "animation_name": "Run",
        },
    )
    assert response.status_code == 201
    record = response.json()
    assert record["document_type"] == "character_retarget"
    assert record["data"]["animation_name"] == "Run"
    assert record["data"]["mapped_bone_count"] == 15
    assert record["data"]["scene_reopened"] is True
    assert record["data"]["pose_transferred"] is True
    assert record["data"]["source_animation_playing"] is True
    assert record["data"]["source_pose_angle_degrees"] == 29.0
    assert record["data"]["target_pose_angle_degrees"] == 29.0
    assert record["data"]["source_glb_preserved"] is True
    assert record["data"]["target_glb_preserved"] is True

    listed = client.get(f"/api/projects/{project_id}/retargets")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [record["id"]]
    download = client.get(
        f"/api/projects/{project_id}/retargets/{record['id']}/scene"
    )
    assert download.status_code == 200
    assert download.text == "[gd_scene format=3]"

    preview = client.get(f"/api/projects/{project_id}/retargets/{record['id']}/preview")
    assert preview.status_code == 200
    preview_data = preview.json()
    assert preview_data["preview_kind"] == "threejs_browser_retarget"
    assert preview_data["animation_name"] == record["data"]["animation_name"]
    assert "/character-assets/" in preview_data["source_asset_url"]
    assert preview_data["source_mapping"]["Hips"] == "Hips"
    assert preview_data["target_mapping"]["LeftUpperArm"] == "LeftUpperArm"
    assert preview_data["authoritative_scene"].endswith("/scene")


def test_character_retarget_api_allows_verified_ik_foot_source_only(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "IK source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    source_path = (
        tmp_path / "projects" / project_id / "characters" / f"{source_id}.json"
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source["data"]["asset"]["rig_analysis"]["hierarchy_validation"]["status"] = (
        "valid_with_ik_foot_hierarchy"
    )
    source_path.write_text(json.dumps(source), encoding="utf-8")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeRetargetAdapter)

    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={
            "source_character_id": source_id,
            "target_character_id": target_id,
            "animation_name": "Run",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["animation_name"] == "Run"


def test_character_retarget_api_rejects_ik_foot_variant_as_target(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "IK target")
    target_path = (
        tmp_path / "projects" / project_id / "characters" / f"{target_id}.json"
    )
    target = json.loads(target_path.read_text(encoding="utf-8"))
    target["data"]["asset"]["rig_analysis"]["hierarchy_validation"]["status"] = (
        "valid_with_ik_foot_hierarchy"
    )
    target_path.write_text(json.dumps(target), encoding="utf-8")

    class MustNotRun:
        def retarget_glb_pair(self, *args, **kwargs):
            raise AssertionError("The IK-foot hierarchy exception is source-only.")

    monkeypatch.setattr(main, "get_engine_adapter", MustNotRun)
    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={"source_character_id": source_id, "target_character_id": target_id},
    )
    assert response.status_code == 422


def test_character_retarget_api_rejects_unknown_animation_before_engine_call(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")

    class MustNotRun:
        def retarget_glb_pair(self, *args, **kwargs):
            raise AssertionError("Godot must not run for an unknown animation.")

    monkeypatch.setattr(main, "get_engine_adapter", MustNotRun)
    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={
            "source_character_id": source_id,
            "target_character_id": target_id,
            "animation_name": "Dance",
        },
    )
    assert response.status_code == 422
    assert "not present" in response.json()["detail"]


def test_character_retarget_api_uses_first_clip_when_selection_is_blank(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeRetargetAdapter)

    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={"source_character_id": source_id, "target_character_id": target_id},
    )
    assert response.status_code == 201
    assert response.json()["data"]["animation_name"] == "Walk"


def test_character_retarget_api_rejects_empty_playable_clip_catalog(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    source_path = (
        tmp_path / "projects" / project_id / "characters" / f"{source_id}.json"
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    source["data"]["asset"]["engine_inspection"]["animation_names"] = []
    source_path.write_text(json.dumps(source), encoding="utf-8")

    class MustNotRun:
        def retarget_glb_pair(self, *args, **kwargs):
            raise AssertionError("Godot must not run without a playable source clip.")

    monkeypatch.setattr(main, "get_engine_adapter", MustNotRun)
    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={"source_character_id": source_id, "target_character_id": target_id},
    )
    assert response.status_code == 422
    assert "no playable imported animation clips" in response.json()["detail"]


def test_character_retarget_api_keeps_legacy_clip_metadata_compatible(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Legacy source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    source_path = (
        tmp_path / "projects" / project_id / "characters" / f"{source_id}.json"
    )
    source = json.loads(source_path.read_text(encoding="utf-8"))
    del source["data"]["asset"]["engine_inspection"]["animation_names"]
    source_path.write_text(json.dumps(source), encoding="utf-8")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeRetargetAdapter)

    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={
            "source_character_id": source_id,
            "target_character_id": target_id,
            "animation_name": "LegacyWalk",
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["animation_name"] == "LegacyWalk"


def test_character_retarget_api_rejects_invalid_hierarchy_before_engine_call(
    tmp_path, monkeypatch
):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    target_path = (
        tmp_path / "projects" / project_id / "characters" / f"{target_id}.json"
    )
    target = json.loads(target_path.read_text(encoding="utf-8"))
    target["data"]["asset"]["rig_analysis"]["hierarchy_validation"]["status"] = (
        "invalid"
    )
    target_path.write_text(json.dumps(target), encoding="utf-8")

    class MustNotRun:
        def retarget_glb_pair(self, *args, **kwargs):
            raise AssertionError("Godot must not run for an invalid hierarchy.")

    monkeypatch.setattr(main, "get_engine_adapter", MustNotRun)
    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={"source_character_id": source_id, "target_character_id": target_id},
    )
    assert response.status_code == 422
    assert "parent hierarchy" in response.json()["detail"]


def test_world_export_persists_and_serves_generated_godot_scene(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    monkeypatch.setattr(main, "get_engine_adapter", _FakeEngineAdapter)
    created = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Market Town",
            "theme": "market",
            "ground_color": "#789b58",
            "sky": "sunset",
            "objects": [
                {
                    "id": "road-1", "kind": "road", "label": "Main Road",
                    "x": 50, "y": 50, "width": 80, "height": 12,
                    "color": "#4b4d50",
                },
                {
                    "id": "shop-1", "kind": "shop", "label": "Bakery",
                    "x": 30, "y": 40, "width": 18, "height": 16,
                    "color": "#d9a46b",
                },
            ],
        },
    )
    assert created.status_code == 201
    world_id = created.json()["id"]
    exported = client.post(f"/api/projects/{project_id}/worlds/{world_id}/export")
    assert exported.status_code == 200, exported.text
    result = exported.json()
    assert result["object_count"] == 2
    assert result["scene_reopened"] is True
    downloaded = client.get(result["scene_url"])
    assert downloaded.status_code == 200
    assert "CartoonWorld" in downloaded.text
    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.json()["scene_relative_path"] == result["scene_relative_path"]

