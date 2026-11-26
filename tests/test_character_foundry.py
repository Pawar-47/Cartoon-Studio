from __future__ import annotations

import json
import struct

import pytest

from app.character_foundry import (
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
    assert len(document["accessors"]) == 2 + len(MORPH_TARGETS)
    assert document["asset"]["extras"]["masterTemplate"] == MASTER_TEMPLATE_ID
    assert document["nodes"][0]["name"] == "CartoonStudio_StylizedAdult"
    assert document["nodes"][0]["skin"] == 0
    assert len(document["skins"][0]["joints"]) == 19
    assert document["skins"][0]["skeleton"] == 1
    attributes = primitive["attributes"]
    assert {"JOINTS_0", "WEIGHTS_0"} <= set(attributes)
    assert document["accessors"][attributes["JOINTS_0"]]["componentType"] == 5123
    assert document["accessors"][attributes["WEIGHTS_0"]]["componentType"] == 5126


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
    assert validate_character_recipe(recipe)["character_id"] == "character-foundry-preview"
