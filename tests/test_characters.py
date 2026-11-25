from __future__ import annotations

import json
import struct

from fastapi.testclient import TestClient

from app import main


def make_glb() -> bytes:
    document = {
        "asset": {"version": "2.0", "generator": "Cartoon Studio test"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "Root", "mesh": 0, "skin": 0}],
        "meshes": [{"primitives": []}],
        "skins": [{"joints": [0]}],
        "animations": [{"name": "Idle", "samplers": [], "channels": []}],
    }
    encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((4 - len(encoded) % 4) % 4)
    chunk = struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk


class FakeEngine:
    def inspect_glb(self, source_path, allowed_root):
        assert source_path.is_relative_to(allowed_root)
        return {
            "engine_version": "4.7.2.stable",
            "mesh_count": 1,
            "skeleton_count": 1,
            "skeletons": [
                {
                    "node_path": "Root/Skeleton3D",
                    "bone_count": 15,
                    "bones": [
                        {"name": name}
                        for name in (
                            "mixamorig:Hips",
                            "mixamorig:Spine",
                            "mixamorig:Head",
                            "mixamorig:LeftUpLeg",
                            "mixamorig:LeftLeg",
                            "mixamorig:LeftFoot",
                            "mixamorig:RightUpLeg",
                            "mixamorig:RightLeg",
                            "mixamorig:RightFoot",
                            "mixamorig:LeftArm",
                            "mixamorig:LeftForeArm",
                            "mixamorig:LeftHand",
                            "mixamorig:RightArm",
                            "mixamorig:RightForeArm",
                            "mixamorig:RightHand",
                        )
                    ],
                }
            ],
            "animation_player_count": 1,
            "animation_count": 1,
            "node_count": 1,
        }


def setup_project(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "characters.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    monkeypatch.setattr(main, "get_engine_adapter", lambda: FakeEngine())
    client = TestClient(main.app)
    project = client.post("/api/projects", json={"name": "Character Project"})
    assert project.status_code == 201
    return client, project.json()["id"]


def import_asset(client, project_id):
    response = client.post(
        f"/api/projects/{project_id}/character-assets",
        content=make_glb(),
        headers={
            "Content-Type": "application/octet-stream",
            "X-Asset-Filename": "ali-source.glb",
        },
    )
    assert response.status_code == 201
    return response.json()


def profile_payload(asset_path):
    return {
        "name": "Ali",
        "description": "A cheerful recurring character.",
        "face_design": "Round face, expressive eyebrows.",
        "body_proportions": {"head_to_body": 5.5, "shoulder_width": 1.0},
        "height_cm": 145,
        "hair": "Short dark hair",
        "clothing": ["Blue shalwar kameez"],
        "accessories": ["Wristwatch"],
        "eye_design": "Large brown eyes",
        "mouth_design": "Wide expressive smile",
        "expressions": ["neutral", "happy", "surprised"],
        "personality": "Curious and kind.",
        "relationships": ["Bilu: best friend"],
        "voice_profile": "Warm youthful Pakistani Urdu voice.",
        "dialogue_style": "Friendly conversational Urdu.",
        "asset_path": asset_path,
    }


def test_browser_preview_modules_are_served_from_local_static_assets():
    client = TestClient(main.app)
    page = client.get("/characters")
    assert page.status_code == 200
    assert 'type="importmap"' in page.text
    assert "/static/vendor/three/build/three.module.js" in page.text

    preview = client.get("/static/character-preview.js")
    assert preview.status_code == 200
    assert "options.playAnimations !== false" in preview.text
    assert "if (playAnimations) mixer.clipAction(clips[0]).play();" in preview.text
    assert "morphTargetByKey.clear();" in preview.text
    clip_helper = client.get("/static/animation-clip.mjs")
    assert clip_helper.status_code == 200
    assert "resolveAnimationClip" in clip_helper.text

    for path in (
        "/static/character-preview.js",
        "/static/vendor/three/build/three.module.js",
        "/static/vendor/three/build/three.core.js",
        "/static/vendor/three/examples/jsm/loaders/GLTFLoader.js",
        "/static/vendor/three/examples/jsm/controls/OrbitControls.js",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert len(response.content) > 1000, path


def test_character_studio_page_is_served():
    response = TestClient(main.app).get("/characters")
    assert response.status_code == 200
    assert "Character Studio" in response.text
    assert "Import and inspect model" in response.text
    script = TestClient(main.app).get("/static/characters.js")
    assert script.status_code == 200
    assert "Edit profile" in script.text
    assert "cancel-edit-profile" in script.text
    assert 'join("\\n")' in script.text
    assert "Cancel editing" in response.text
    assert "Godot facial blend shapes" in script.text
    assert '<select id="retarget-animation"' in response.text
    assert "updateRetargetAnimationOptions" in script.text
    assert "animation_names" in script.text
    assert 'valid_with_ik_foot_hierarchy' in script.text
    assert "morph_target_count" in script.text
    assert "appearanceRecipe,{playAnimations:false}" in script.text
    preview = TestClient(main.app).get("/static/character-preview.js")
    assert preview.status_code == 200
    assert 'meshName: node.name || "Mesh"' in preview.text
    assert "resolveAnimationClip(sourceGltf.animations, requestedAnimation)" in preview.text
    assert "no substitute clip was previewed" in preview.text
    assert 'target.meshName?target.meshName+" · ":""' in script.text
    assert "morph weight" in script.text
    assert "appearanceRecipe.morph_targets[target.key]=target.value" in script.text


def test_character_glb_import_profile_round_trip_and_project_reference(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    assert imported["container"]["format"] == "glTF Binary 2.0"
    assert imported["container"]["skin_count"] == 1
    assert imported["engine_inspection"]["skeleton_count"] == 1
    assert imported["rig_ready"] is True
    assert imported["rig_analysis"]["status"] == "humanoid_names_complete"
    assert imported["rig_analysis"]["matched_bone_count"] == 15
    assert imported["rig_analysis"]["retargeting_ready"] is False
    assert imported["animation_ready"] is True

    payload = profile_payload(imported["relative_path"])
    created = client.post(f"/api/projects/{project_id}/characters", json=payload)
    assert created.status_code == 201
    document = created.json()
    character_id = document["id"]
    assert document["document_type"] == "character"
    assert document["revision"] == 1
    assert document["data"]["name"] == "Ali"
    assert document["data"]["rig_status"] == "ready"
    assert document["data"]["asset"]["container"]["sha256"] == imported["container"]["sha256"]

    listed = client.get(f"/api/projects/{project_id}/characters")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [character_id]
    reopened = client.get(f"/api/projects/{project_id}/characters/{character_id}")
    assert reopened.status_code == 200
    assert reopened.json()["data"]["relationships"] == ["Bilu: best friend"]

    updated_payload = profile_payload(imported["relative_path"])
    updated_payload["personality"] = "Brave, curious and kind."
    updated = client.put(
        f"/api/projects/{project_id}/characters/{character_id}",
        json=updated_payload,
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    assert updated.json()["data"]["personality"] == "Brave, curious and kind."

    opened = client.get(f"/api/projects/{project_id}")
    assert character_id in opened.json()["document"]["data"]["references"]["characters"]


def test_material_appearance_recipe_persists_and_survives_profile_updates(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(imported["relative_path"]),
    )
    character_id = created.json()["id"]

    saved = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json={
            "materials": {
                "0:Root#material:0": {
                    "color": "#e85d3f",
                    "roughness": 0.72,
                    "metalness": 0.08,
                }
            },
            "morph_targets": {"0:Face#0:Smile": 0.85},
        },
    )
    assert saved.status_code == 200
    assert saved.json()["revision"] == 2
    assert saved.json()["data"]["appearance_recipe"]["morph_targets"]["0:Face#0:Smile"] == 0.85
    assert saved.json()["data"]["appearance_recipe"]["materials"]["0:Root#material:0"] == {
        "color": "#e85d3f",
        "roughness": 0.72,
        "metalness": 0.08,
    }

    updated_payload = profile_payload(imported["relative_path"])
    updated_payload["personality"] = "More confident."
    updated = client.put(
        f"/api/projects/{project_id}/characters/{character_id}",
        json=updated_payload,
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 3
    assert updated.json()["data"]["appearance_recipe"]["materials"]["0:Root#material:0"][
        "color"
    ] == "#e85d3f"
    assert updated.json()["data"]["appearance_recipe"]["morph_targets"][
        "0:Face#0:Smile"
    ] == 0.85

    reopened = client.get(f"/api/projects/{project_id}/characters/{character_id}")
    assert reopened.json()["data"]["appearance_recipe"]["materials"]["0:Root#material:0"][
        "roughness"
    ] == 0.72


def test_appearance_recipe_accepts_negative_morph_weights_and_reopens_them(
    tmp_path, monkeypatch
):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(imported["relative_path"]),
    )
    character_id = created.json()["id"]

    saved = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json={"morph_targets": {"0:Face#0:Frown": -0.35}},
    )
    assert saved.status_code == 200
    assert saved.json()["data"]["appearance_recipe"]["morph_targets"][
        "0:Face#0:Frown"
    ] == -0.35

    reopened = client.get(f"/api/projects/{project_id}/characters/{character_id}")
    assert reopened.status_code == 200
    assert reopened.json()["data"]["appearance_recipe"]["morph_targets"][
        "0:Face#0:Frown"
    ] == -0.35


def test_material_appearance_rejects_invalid_values_and_missing_character(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    invalid = client.put(
        f"/api/projects/{project_id}/characters/{'a' * 36}/appearance",
        json={
            "materials": {"body": {"color": "red", "roughness": 1.5}},
            "morph_targets": {"smile": 1.5},
        },
    )
    assert invalid.status_code == 422
    missing = client.put(
        f"/api/projects/{project_id}/characters/00000000-0000-0000-0000-000000000000/appearance",
        json={"materials": {}},
    )
    assert missing.status_code == 404


def test_saved_character_asset_can_be_retrieved_for_preview(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    response = client.get(
        f"/api/projects/{project_id}/character-assets/{imported['asset_id']}"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("model/gltf-binary")
    assert response.content == make_glb()


def test_character_import_rejects_bad_glb_and_unsafe_filename(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    bad = client.post(
        f"/api/projects/{project_id}/character-assets",
        content=b"not a GLB",
        headers={"Content-Type": "application/octet-stream", "X-Asset-Filename": "bad.glb"},
    )
    assert bad.status_code == 422
    unsafe = client.post(
        f"/api/projects/{project_id}/character-assets",
        content=make_glb(),
        headers={"Content-Type": "application/octet-stream", "X-Asset-Filename": "../escape.glb"},
    )
    assert unsafe.status_code == 422


def test_character_profiles_recover_from_portable_files_after_database_loss(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(imported["relative_path"]),
    )
    assert created.status_code == 201
    character_id = created.json()["id"]

    for suffix in ("-wal", "-shm"):
        (tmp_path / f"characters.sqlite3{suffix}").unlink(missing_ok=True)
    (tmp_path / "characters.sqlite3").unlink()
    main._INITIALIZED_DB_KEY = None

    recovered = client.get(f"/api/projects/{project_id}/characters")
    assert recovered.status_code == 200
    assert [item["id"] for item in recovered.json()] == [character_id]
    with main.connect_db() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM project_documents WHERE document_type = 'character'"
        ).fetchone()[0] == 1
