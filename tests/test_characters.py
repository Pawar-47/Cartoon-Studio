from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest
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
    def __init__(self):
        self.proportion_source_paths = []
        self.proportion_values = []

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

    def export_character_appearance(
        self, source_path, materials, morph_targets, output_path, allowed_root,
        face_features=None,
    ):
        assert source_path.is_relative_to(allowed_root)
        assert materials and morph_targets
        output_path.write_bytes(make_glb())
        result = self.inspect_glb(source_path, allowed_root)
        result.update({
            "appearance_verified": True,
            "applied_material_count": len(materials),
            "applied_morph_count": len(morph_targets),
        })
        return result


    def add_character_hair(self, source_path, style, color, destination, allowed_root):
        assert source_path.is_relative_to(allowed_root)
        assert style in {"short", "bob", "long", "ponytail", "spiky", "curly", "mohawk"}
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(make_glb())
        result = self.inspect_glb(destination, allowed_root)
        result.update({
            "hair_verified": True,
            "hair_style": style,
            "hair_color": color,
            "hair_attachment_bone": "mixamorig:Head",
            "hair_mesh_count": 3,
        })
        return result

    def customize_character_proportions(
        self, source_path, proportions, destination, allowed_root, bone_mapping=None
    ):
        assert source_path.is_relative_to(allowed_root)
        assert bone_mapping and bone_mapping.get("Spine") == "mixamorig:Spine"
        self.proportion_source_paths.append(source_path)
        self.proportion_values.append(dict(proportions))
        assert any(abs(value - 1.0) > 0.0001 for value in proportions.values())
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(make_glb())
        result = self.inspect_glb(destination, allowed_root)
        result.update({
            "proportions_verified": True,
            "applied_proportions": proportions,
            "changed_bones": ["mixamorig:Spine", "mixamorig:Head"],
        })
        return result

    def assemble_modular_character(
        self, base_path, parts, destination, allowed_root, accessories=None
    ):
        assert base_path.is_relative_to(allowed_root)
        assert all(Path(part["source_path"]).is_relative_to(allowed_root) for part in parts)
        assert all(
            Path(item["source_path"]).is_relative_to(allowed_root)
            for item in (accessories or [])
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(make_glb())
        inspection = self.inspect_glb(destination, allowed_root)
        return {
            **inspection,
            "assembly_verified": True,
            "animation_preserved": True,
            "animation_names": ["Idle"],
            "added_parts": [{"slot": part["slot"]} for part in parts],
            "base_meshes_removed": ["BaseBody"],
            "added_accessories": [
                {"mesh_name": Path(item["mesh_path"]).name}
                for item in (accessories or [])
            ],
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
    assert "resolveDefaultAnimationClip(clips)" in preview.text
    assert "activeAction = mixer.clipAction(initialClip);" in preview.text
    assert "activeAction.paused = playbackPaused;" in preview.text
    assert "function frameCharacter" in preview.text
    assert 'data-camera-frame="head"' in page.text
    assert 'id="preview-speed"' in page.text
    assert 'id="export-preview-png"' in page.text
    assert 'id="export-turnaround-png"' in page.text
    assert "exportCharacterTurnaround" in client.get("/static/character-preview.js").text
    assert 'id="preview-transparent"' in page.text
    assert "exportCharacterPreview" in client.get("/static/character-preview.js").text
    assert 'id="body-morph-controls"' in page.text
    assert 'id="body-morph-status"' in page.text
    assert 'id="torso-length"' in page.text
    assert 'id="apply-proportions"' in page.text
    assert 'id="hair-style"' in page.text
    assert 'id="apply-hair"' in page.text
    assert "applyHairStyle" in client.get("/static/characters.js").text
    assert "applyBodyProportions" in client.get("/static/characters.js").text
    assert 'id="body-morph-controls"' in page.text
    assert 'id="body-morph-status"' in page.text
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


def test_turnaround_setup_is_inside_preview_state_restoration_scope():
    source = (
        Path(__file__).parents[1] / "app" / "static" / "character-preview.js"
    ).read_text(encoding="utf-8")
    start = source.index("export async function exportCharacterTurnaround")
    end = source.index("export async function exportCharacterPreview", start)
    function_body = source[start:end]
    try_start = function_body.index("  try {")
    finally_start = function_body.index("  } finally {", try_start)
    protected_setup = function_body[try_start:finally_start]

    assert 'frameCharacter("full");' in protected_setup
    assert 'const context = sheet.getContext("2d");' in protected_setup


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
    assert "prepareRetargetedClip" in preview.text
    assert "new THREE.AnimationMixer(targetMesh)" in preview.text
    assert "no substitute clip was previewed" in preview.text
    retarget_helper = TestClient(main.app).get("/static/retarget-preview.mjs")
    assert retarget_helper.status_code == 200
    assert "prepareRetargetedClip" in retarget_helper.text
    assert "sourceRoot.skeleton = sourceMesh.skeleton" in retarget_helper.text
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
    data = reopened.json()["data"]
    assert data["relationships"] == ["Bilu: best friend"]
    assert data["hair"] == "Short dark hair"
    assert data["face_design"] == "Round face, expressive eyebrows."
    assert data["voice_profile"] == "Warm youthful Pakistani Urdu voice."

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


def test_modular_assembly_recipe_survives_profile_reopen_and_reassembly(
    tmp_path, monkeypatch
):
    client, project_id = setup_project(tmp_path, monkeypatch)
    base = import_asset(client, project_id)
    head = import_asset(client, project_id)
    body = import_asset(client, project_id)
    legs = import_asset(client, project_id)
    feet = import_asset(client, project_id)

    original_payload = {
        "base_relative_path": base["relative_path"],
        "parts": [
            {"slot": "head", "relative_path": head["relative_path"], "mesh_path": "Head/Mesh"},
            {"slot": "body", "relative_path": body["relative_path"], "mesh_path": "Body/Mesh"},
            {"slot": "legs", "relative_path": legs["relative_path"], "mesh_path": "Legs/Mesh"},
            {"slot": "feet", "relative_path": feet["relative_path"], "mesh_path": "Feet/Mesh"},
        ],
        "accessories": [
            {
                "relative_path": base["relative_path"],
                "mesh_path": "Root/Backpack",
                "attachment_bone": "mixamorig:Spine",
            }
        ],
    }
    assembled = client.post(
        f"/api/projects/{project_id}/modular-assemblies", json=original_payload
    )
    assert assembled.status_code == 201, assembled.text
    first = assembled.json()
    assert first["assembly"]["verified"] is True
    assert first["assembly"]["animation_preserved"] is True

    saved_manifest = client.get(
        f"/api/projects/{project_id}/character-assets/{first['asset_id']}/manifest"
    )
    assert saved_manifest.status_code == 200
    recipe = saved_manifest.json()["assembly"]
    assert recipe["base_relative_path"] == original_payload["base_relative_path"]
    assert recipe["parts"] == original_payload["parts"]
    assert recipe["accessories"] == original_payload["accessories"]
    assert len(recipe["added_parts"]) == 4
    assert len(recipe["added_accessories"]) == 1

    # Every source needed by the browser's Reopen assembly action must still
    # have a readable, project-scoped manifest after the character is saved.
    source_paths = [
        recipe["base_relative_path"],
        *(part["relative_path"] for part in recipe["parts"]),
        *(item["relative_path"] for item in recipe["accessories"]),
    ]
    for relative_path in set(source_paths):
        source_id = relative_path.rsplit("/", 1)[-1].removesuffix(".glb")
        source_manifest = client.get(
            f"/api/projects/{project_id}/character-assets/{source_id}/manifest"
        )
        assert source_manifest.status_code == 200
        assert source_manifest.json()["relative_path"] == relative_path

    profile = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(first["relative_path"]),
    )
    assert profile.status_code == 201
    character_id = profile.json()["id"]
    reopened_profile = client.get(
        f"/api/projects/{project_id}/characters/{character_id}"
    )
    assert reopened_profile.status_code == 200
    assert reopened_profile.json()["data"]["asset"]["assembly"]["parts"] == recipe["parts"]
    reopened_recipe = reopened_profile.json()["data"]["asset"]["assembly"]
    assert reopened_recipe["accessories"] == recipe["accessories"]

    # Reassemble exclusively from the persisted recipe, as the UI does after
    # restoring source manifests; no original selector state is reused.
    replay_payload = {
        "base_relative_path": recipe["base_relative_path"],
        "parts": recipe["parts"],
        "accessories": recipe["accessories"],
    }
    replayed = client.post(
        f"/api/projects/{project_id}/modular-assemblies", json=replay_payload
    )
    assert replayed.status_code == 201, replayed.text
    assert replayed.json()["assembly"]["parts"] == recipe["parts"]
    assert replayed.json()["assembly"]["accessories"] == recipe["accessories"]
    assert replayed.json()["assembly"]["animation_preserved"] is True



def test_body_proportion_edit_creates_verified_asset_without_mutating_source(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    engine = FakeEngine()
    monkeypatch.setattr(main, "get_engine_adapter", lambda: engine)
    source = import_asset(client, project_id)
    source_path = tmp_path / "projects" / project_id / source["relative_path"]
    original_bytes = source_path.read_bytes()
    response = client.post(
        f"/api/projects/{project_id}/character-assets/{source['asset_id']}/proportions",
        json={"torso_length": 1.12, "shoulder_width": 1.08, "arm_length": 0.94,
              "leg_length": 1.06, "head_size": 1.1},
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["geometry_edit"]["verified"] is True
    assert result["geometry_edit"]["type"] == "humanoid_body_proportions"
    assert result["geometry_edit"]["changed_bones"]
    assert result["geometry_edit"]["source_relative_path"] == source["relative_path"]
    assert source_path.read_bytes() == original_bytes
    second_proportions = {
        "torso_length": 1.2, "shoulder_width": 1.04, "arm_length": 1.0,
        "leg_length": 1.1, "head_size": 1.0,
    }
    second = client.post(
        f"/api/projects/{project_id}/character-assets/{result['asset_id']}/proportions",
        json=second_proportions,
    )
    assert second.status_code == 201, second.text
    second_result = second.json()
    assert engine.proportion_source_paths == [source_path, source_path]
    assert engine.proportion_values[1]["torso_length"] == pytest.approx(1.2)
    hair = client.post(
        f"/api/projects/{project_id}/character-assets/{second_result['asset_id']}/hair",
        json={"style": "bob", "color": "#4b2d1e"},
    )
    assert hair.status_code == 201, hair.text
    hair_result = hair.json()
    hair_path = tmp_path / "projects" / project_id / hair_result["relative_path"]
    third_proportions = {
        "torso_length": 1.1, "shoulder_width": 1.12, "arm_length": 0.96,
        "leg_length": 1.04, "head_size": 1.08,
    }
    third = client.post(
        f"/api/projects/{project_id}/character-assets/{hair_result['asset_id']}/proportions",
        json=third_proportions,
    )
    assert third.status_code == 201, third.text
    third_result = third.json()
    assert engine.proportion_source_paths[2] == hair_path
    assert engine.proportion_values[2]["torso_length"] == pytest.approx(1.1 / 1.2)
    assert third_result["geometry_edit"]["source_relative_path"] == hair_result["relative_path"]
    assert third_result["geometry_edit"]["source_proportions"] == second_proportions
    assert third_result["geometry_edit_history"][-1]["type"] == "procedural_hair"
    manifest = client.get(
        f"/api/projects/{project_id}/character-assets/{result['asset_id']}/manifest"
    )
    assert manifest.status_code == 200
    assert manifest.json()["geometry_edit"]["proportions"]["torso_length"] == 1.12
    download = client.get(
        f"/api/projects/{project_id}/character-assets/{result['asset_id']}"
    )
    assert download.status_code == 200
    assert download.content.startswith(b"glTF")


def test_body_proportion_edit_rejects_noop_and_out_of_range_values(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    source = import_asset(client, project_id)
    url = f"/api/projects/{project_id}/character-assets/{source['asset_id']}/proportions"
    assert client.post(url, json={}).status_code == 422
    assert client.post(url, json={"head_size": 1.8}).status_code == 422



def test_generated_hairstyle_creates_verified_asset_and_preserves_source(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    source = import_asset(client, project_id)
    source_path = tmp_path / "projects" / project_id / source["relative_path"]
    original_bytes = source_path.read_bytes()
    response = client.post(
        f"/api/projects/{project_id}/character-assets/{source['asset_id']}/hair",
        json={"style": "ponytail", "color": "#2b1b13"},
    )
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["geometry_edit"]["type"] == "procedural_hair"
    assert result["geometry_edit"]["verified"] is True
    assert result["geometry_edit"]["style"] == "ponytail"
    assert result["geometry_edit"]["mesh_count"] >= 2
    assert result["geometry_edit"]["attachment_bone"].lower().endswith("head")
    assert source_path.read_bytes() == original_bytes
    manifest = client.get(
        f"/api/projects/{project_id}/character-assets/{result['asset_id']}/manifest"
    )
    assert manifest.status_code == 200
    assert manifest.json()["geometry_edit"]["color"] == "#2b1b13"


def test_generated_hairstyle_rejects_invalid_style_or_color(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    source = import_asset(client, project_id)
    url = f"/api/projects/{project_id}/character-assets/{source['asset_id']}/hair"
    assert client.post(url, json={"style": "invisible"}).status_code == 422
    assert client.post(url, json={"style": "short", "color": "red"}).status_code == 422


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

def test_customized_character_glb_export_persists_manifest_and_download(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(imported["relative_path"]),
    )
    character_id = created.json()["id"]
    appearance = {
        "materials": {
            "0:Root#material:0": {
                "color": "#e85d3f", "roughness": 0.72, "metalness": 0.08,
                "mesh_name": "Root", "surface_index": 0, "material_name": "Paint",
            }
        },
        "morph_targets": {"0:Face#0:Smile": 0.85},
        "morph_bindings": {
            "0:Face#0:Smile": {"mesh_name": "Face", "target_index": 0, "target_name": "Smile"}
        },
    }
    saved = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json=appearance,
    )
    assert saved.status_code == 200
    exported = client.post(
        f"/api/projects/{project_id}/characters/{character_id}/export",
        json=appearance,
    )
    assert exported.status_code == 201
    result = exported.json()
    assert result["appearance_verified"] is True
    assert result["applied_material_count"] == 1
    assert result["applied_morph_count"] == 1
    downloaded = client.get(result["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.content == make_glb()
    asset_id = result["asset_id"]
    manifest = client.get(f"/api/projects/{project_id}/character-assets/{asset_id}/manifest")
    assert manifest.status_code == 200
    assert manifest.json()["appearance_export_verified"] is True
    assert manifest.json()["source_character_id"] == character_id


def test_customized_character_export_requires_saved_mesh_bindings(tmp_path, monkeypatch):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(imported["relative_path"]),
    )
    character_id = created.json()["id"]
    response = client.post(
        f"/api/projects/{project_id}/characters/{character_id}/export",
        json={"morph_targets": {"face:Smile": 0.8}},
    )
    assert response.status_code == 422
    assert "mesh/target bindings" in response.json()["detail"]


def test_generated_face_geometry_recipe_persists_and_validates_all_controls(
    tmp_path, monkeypatch
):
    client, project_id = setup_project(tmp_path, monkeypatch)
    imported = import_asset(client, project_id)
    created = client.post(
        f"/api/projects/{project_id}/characters",
        json=profile_payload(imported["relative_path"]),
    )
    character_id = created.json()["id"]
    recipe = {
        "face_features": {
            "enabled": True,
            "skin_color": "#bd8068",
            "face_width": 1.12,
            "cheek_fullness": 1.25,
            "jaw_width": 0.88,
            "chin_length": 1.18,
            "mouth_open": 0.78,
        }
    }
    saved = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json=recipe,
    )
    assert saved.status_code == 200
    saved_face = saved.json()["data"]["appearance_recipe"]["face_features"]
    assert saved_face["skin_color"] == "#bd8068"
    assert saved_face["face_width"] == 1.12
    assert saved_face["cheek_fullness"] == 1.25
    assert saved_face["jaw_width"] == 0.88
    assert saved_face["chin_length"] == 1.18
    assert saved_face["mouth_open"] == 0.78

    reopened = client.get(
        f"/api/projects/{project_id}/characters/{character_id}"
    )
    assert reopened.status_code == 200
    assert reopened.json()["data"]["appearance_recipe"]["face_features"] == saved_face

    invalid = client.put(
        f"/api/projects/{project_id}/characters/{character_id}/appearance",
        json={"face_features": {"enabled": True, "mouth_open": 1.5}},
    )
    assert invalid.status_code == 422
