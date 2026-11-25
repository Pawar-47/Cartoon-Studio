from pathlib import Path

from tools.godot_engine_proof.generate_retarget_target_fixture import (
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
