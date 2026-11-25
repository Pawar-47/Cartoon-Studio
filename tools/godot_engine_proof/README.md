from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app import main
from app.rig_analysis import REQUIRED_HUMANOID_BONES

client = TestClient(main.app)


class _FakeEngineAdapter:
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
        "engine_inspection": {"animation_count": 1, "skeleton_count": 1},
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


def test_character_retarget_api_saves_scene_and_persistent_record(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    source_id = _seed_retarget_character(tmp_path, project_id, "Source")
    target_id = _seed_retarget_character(tmp_path, project_id, "Target")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeRetargetAdapter)

    response = client.post(
        f"/api/projects/{project_id}/retargets",
        json={"source_character_id": source_id, "target_character_id": target_id},
    )
    assert response.status_code == 201
    record = response.json()
    assert record["document_type"] == "character_retarget"
    assert record["data"]["animation_name"] == "Walk"
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


## Distinct imported retarget target fixture

`fixtures/proof_humanoid_retarget_target.glb` is generated from the source humanoid fixture by `generate_retarget_target_fixture.py`. The generator changes arm and leg rest lengths, reorders the 15 skin joints, remaps the mesh JOINTS_0 indices, recalculates inverse-bind matrices and applies Mixamo-style bone names. The target has no animation clips. The source fixture is not modified.

The pinned Godot worker test imports the source and target as separate GLBs, checks their complete indexed humanoid mappings and changed rest offsets, creates and reopens the retarget scene, verifies source animation playback and target upper-arm pose transfer, and checks both original files remain byte-identical. The raw glTF skin-joint and child order differ; Godot may normalize the imported Skeleton3D bone indices, so the app always uses the indices reported by its actual Godot inspection rather than assuming the raw GLB order. This is still a controlled fixture proof, not broad acceptance of arbitrary third-party GLBs.


### Non-canonical animated source fixture

`fixtures/proof_humanoid_retarget_source.glb` preserves the source fixture's animation and skin data while renaming its 15 humanoid nodes to Mixamo-style names. `generate_retarget_source_fixture.py` recreates it. The worker must remap the animation's bone-track paths when it normalizes imported Skeleton3D bone names to the Godot humanoid profile, then prove that the source animation still plays and transfers to the differently ordered target rig.
