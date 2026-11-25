from pathlib import Path

from tools.godot_engine_proof.generate_mixamo_source_fixture import (
    generate_mixamo_source_fixture,
)
from tools.godot_engine_proof.generate_retarget_target_fixture import (
    _read_glb,
    generate_target_fixture,
)


def test_retarget_target_fixture_is_reproducible(tmp_path):
    fixture_dir = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
    )
    source = fixture_dir / "proof_humanoid.glb"
    expected = fixture_dir / "proof_humanoid_retarget_target.glb"
    generated = tmp_path / "generated-target.glb"

    generate_target_fixture(source, generated)

    assert generated.read_bytes() == expected.read_bytes()

    source_document, _ = _read_glb(source.read_bytes())
    target_document, _ = _read_glb(expected.read_bytes())
    assert source_document["skins"][0]["joints"] != (
        target_document["skins"][0]["joints"]
    )
    source_nodes = {node.get("name"): node for node in source_document["nodes"]}
    target_nodes = {node.get("name"): node for node in target_document["nodes"]}
    assert source_nodes["Spine"]["children"] != (
        target_nodes["mixamorig:Spine"]["children"]
    )
    assert target_nodes["mixamorig:LeftArm"]["name"] == "mixamorig:LeftArm"
    assert target_document["animations"] == []
    assert source_nodes["LeftLowerArm"]["translation"] != (
        target_nodes["mixamorig:LeftForeArm"]["translation"]
    )


def test_mixamo_source_fixture_is_reproducible_and_keeps_animation(tmp_path):
    fixture_dir = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "godot_engine_proof"
        / "fixtures"
    )
    source = fixture_dir / "proof_humanoid.glb"
    expected = fixture_dir / "proof_humanoid_source_mixamo.glb"
    generated = tmp_path / "generated-mixamo-source.glb"

    generate_mixamo_source_fixture(source, generated)

    assert generated.read_bytes() == expected.read_bytes()
    document, _ = _read_glb(generated.read_bytes())
    assert len(document["animations"]) == 1
    assert any(
        node.get("name") == "mixamorig:LeftArm" for node in document["nodes"]
    )
