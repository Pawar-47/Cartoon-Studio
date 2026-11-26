from __future__ import annotations

import json
import struct

import pytest

from scripts import generate_foundry_master

from app.character_foundry import (
    CLOTHING_ASSET_ID,
    MASTER_TEMPLATE_ID,
    MORPH_TARGETS,
    RIG_PROFILE_ID,
    build_master_character_glb,
    default_character_recipe,
    validate_character_recipe,
    write_master_character,
)


def _read_glb(data: bytes) -> dict:
    magic, version, total_length = struct.unpack_from("<4sII", data)
    assert magic == b"glTF"
    assert version == 2
    assert total_length == len(data)
    json_length, chunk_type = struct.unpack_from("<I4s", data, 12)
    assert chunk_type == b"JSON"
    return json.loads(data[20:20 + json_length])


def test_default_recipe_is_versioned_and_engine_neutral() -> None:
    recipe = default_character_recipe("hero-01")
    assert recipe["character_id"] == "hero-01"
    assert recipe["master_template_id"] == MASTER_TEMPLATE_ID
    assert recipe["schema_version"] == 1
    assert set(recipe["parameters"]) == set(MORPH_TARGETS)
    assert validate_character_recipe(recipe) == recipe


@pytest.mark.parametrize(
    ("parameter", "value"),
    [("jaw_width", 1.1), ("eye_spacing", float("nan")), ("nose_width", "wide")],
)
def test_recipe_rejects_invalid_morph_values(parameter: str, value: object) -> None:
    recipe = default_character_recipe()
    recipe["parameters"][parameter] = value
    with pytest.raises(ValueError):
        validate_character_recipe(recipe)


def test_recipe_rejects_unknown_template_and_parameter() -> None:
    recipe = default_character_recipe()
    recipe["master_template_id"] = "imported.glb"
    with pytest.raises(ValueError, match="template"):
        validate_character_recipe(recipe)
    recipe = default_character_recipe()
    recipe["parameters"]["eye_color"] = 0.5
    with pytest.raises(ValueError, match="Unknown character parameters"):
        validate_character_recipe(recipe)


def test_generated_master_glb_contains_real_morph_geometry() -> None:
    document = _read_glb(build_master_character_glb())
    mesh = document["meshes"][0]
    primitive = mesh["primitives"][0]
    assert len(primitive["targets"]) == len(MORPH_TARGETS)
    assert mesh["extras"]["targetNames"] == list(MORPH_TARGETS)
    assert primitive["attributes"]["POSITION"] < len(document["accessors"])
    assert document["asset"]["extras"]["masterTemplate"] == MASTER_TEMPLATE_ID
    assert document["nodes"][0]["name"] == "CartoonStudio_StylizedAdult"
    assert document["nodes"][0]["skin"] == 0
    assert len(document["skins"][0]["joints"]) == 19
    assert document["skins"][0]["skeleton"] == 1
    inverse_bind = document["accessors"][document["skins"][0]["inverseBindMatrices"]]
    assert inverse_bind["type"] == "MAT4"
    assert inverse_bind["count"] == len(document["skins"][0]["joints"])
    attributes = primitive["attributes"]
    assert {"NORMAL", "JOINTS_0", "WEIGHTS_0"} <= set(attributes)
    assert document["accessors"][attributes["JOINTS_0"]]["componentType"] == 5123
    assert document["accessors"][attributes["WEIGHTS_0"]]["componentType"] == 5126
    assert len(mesh["primitives"]) == 2
    assert mesh["primitives"][1]["material"] == 1
    assert document["materials"][1]["name"] == "FoundryCasualCloth"
    assert mesh["extras"]["clothingAssetIds"] == [CLOTHING_ASSET_ID]


def test_generated_morph_targets_have_nonzero_vertex_deltas() -> None:
    data = build_master_character_glb()
    document = _read_glb(data)
    json_length = struct.unpack_from("<I", data, 12)[0]
    binary_start = 20 + json_length + 8
    buffer_start = binary_start
    for target in document["meshes"][0]["primitives"][0]["targets"]:
        accessor = document["accessors"][target["POSITION"]]
        view = document["bufferViews"][accessor["bufferView"]]
        start = buffer_start + view.get("byteOffset", 0)
        values = struct.unpack_from(f"<{accessor['count'] * 3}f", data, start)
        assert any(abs(value) > 1e-7 for value in values)


def test_master_export_writes_replayable_recipe(tmp_path) -> None:
    glb_path, recipe_path = write_master_character(tmp_path / "hero.glb")
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    assert glb_path.read_bytes().startswith(b"glTF")
    assert recipe["generated_asset"]["filename"] == "hero.glb"
    assert recipe["generated_asset"]["sha256"]
    assert recipe["generated_asset"]["morph_targets"] == list(MORPH_TARGETS)
    assert recipe["generated_asset"]["rig_profile_id"] == RIG_PROFILE_ID
    assert len(recipe["generated_asset"]["bone_names"]) == 19
    assert recipe["generated_asset"]["clothing_asset_ids"] == [CLOTHING_ASSET_ID]
    assert validate_character_recipe(recipe)["character_id"] == "character-foundry-preview"



def test_fitted_clothing_has_real_body_refit_morph_targets() -> None:
    data = build_master_character_glb()
    document = _read_glb(data)
    json_length = struct.unpack_from("<I", data, 12)[0]
    binary_start = 20 + json_length + 8
    clothing = document["meshes"][0]["primitives"][1]
    target_names = document["meshes"][0]["extras"]["targetNames"]
    for name in ("torso_width", "shoulder_width", "leg_length"):
        target = clothing["targets"][target_names.index(name)]
        accessor = document["accessors"][target["POSITION"]]
        view = document["bufferViews"][accessor["bufferView"]]
        start = binary_start + view.get("byteOffset", 0)
        values = struct.unpack_from(f"<{accessor['count'] * 3}f", data, start)
        assert any(abs(value) > 1e-7 for value in values), name



def test_recipe_morph_values_are_applied_to_body_and_clothing() -> None:
    recipe = default_character_recipe("custom-hero")
    recipe["parameters"]["head_width"] = 0.65
    recipe["parameters"]["torso_width"] = -0.3
    recipe["parameters"]["leg_length"] = 0.8
    document = _read_glb(build_master_character_glb(recipe))
    mesh = document["meshes"][0]
    expected = [recipe["parameters"][name] for name in MORPH_TARGETS]
    assert mesh["weights"] == expected
    assert len(mesh["primitives"]) == 2
    assert all(len(primitive["targets"]) == len(MORPH_TARGETS) for primitive in mesh["primitives"])



def test_master_export_preserves_custom_recipe_parameters(tmp_path) -> None:
    recipe = default_character_recipe("custom-export")
    recipe["parameters"]["head_width"] = 0.7
    recipe["parameters"]["leg_length"] = -0.4
    recipe["clothing_asset_ids"] = []
    glb_path, recipe_path = write_master_character(
        tmp_path / "custom.glb", recipe=recipe
    )
    document = _read_glb(glb_path.read_bytes())
    saved = json.loads(recipe_path.read_text(encoding="utf-8"))
    expected = [recipe["parameters"][name] for name in MORPH_TARGETS]
    assert document["meshes"][0]["weights"] == expected
    assert len(document["meshes"][0]["primitives"]) == 1
    assert saved["character_id"] == "custom-export"
    assert saved["parameters"] == recipe["parameters"]
    assert saved["generated_asset"]["morph_weights"] == expected



def test_generator_cli_loads_and_exports_saved_recipe(tmp_path, monkeypatch) -> None:
    recipe = default_character_recipe("cli-hero")
    recipe["parameters"]["head_width"] = 0.55
    recipe["parameters"]["torso_width"] = -0.25
    recipe["clothing_asset_ids"] = []
    input_path = tmp_path / "input.recipe.json"
    input_path.write_text(json.dumps(recipe), encoding="utf-8")
    output_path = tmp_path / "cli-hero.glb"
    recipe_output = tmp_path / "cli-hero.saved.json"
    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_foundry_master",
            "--output", str(output_path),
            "--recipe", str(recipe_output),
            "--recipe-input", str(input_path),
        ],
    )

    assert generate_foundry_master.main() == 0

    generated = _read_glb(output_path.read_bytes())
    saved_recipe = json.loads(recipe_output.read_text(encoding="utf-8"))
    expected_weights = [recipe["parameters"][name] for name in MORPH_TARGETS]
    assert generated["meshes"][0]["weights"] == expected_weights
    assert len(generated["meshes"][0]["primitives"]) == 1
    assert saved_recipe["character_id"] == "cli-hero"
    assert saved_recipe["parameters"] == recipe["parameters"]


def test_recipe_can_disable_fitted_clothing() -> None:
    recipe = default_character_recipe()
    recipe["clothing_asset_ids"] = []
    document = _read_glb(build_master_character_glb(recipe))
    assert len(document["meshes"][0]["primitives"]) == 1
    assert document["meshes"][0]["extras"]["clothingAssetIds"] == []
