from pathlib import Path

import pytest

from app.blender_toolchain import BlenderToolchain, BlenderUnavailableError


def test_blender_is_optional_and_reports_shared_asset_domains(tmp_path: Path) -> None:
    worker = BlenderToolchain(tmp_path, executable=tmp_path / "missing-blender")
    status = worker.status()

    assert status["available"] is False
    assert status["supported"] is False
    assert status["supported_asset_kinds"] == [
        "building",
        "character",
        "prop",
        "vegetation",
        "vehicle",
        "world",
    ]
    with pytest.raises(BlenderUnavailableError):
        worker.version()


def test_generation_rejects_unknown_asset_kind_and_unsafe_id(tmp_path: Path) -> None:
    worker = BlenderToolchain(tmp_path, executable=tmp_path / "missing-blender")
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ValueError, match="asset_kind"):
        worker.generate(
            project_root=project,
            asset_id="safe",
            asset_kind="spaceship",  # type: ignore[arg-type]
            name="Car",
        )
    with pytest.raises(ValueError, match="asset_id"):
        worker.generate(
            project_root=project,
            asset_id="../escape",
            asset_kind="prop",
            name="Chest",
        )


def test_missing_blender_does_not_write_project_files(tmp_path: Path) -> None:
    worker = BlenderToolchain(tmp_path, executable=tmp_path / "missing-blender")
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(BlenderUnavailableError):
        worker.generate(
            project_root=project,
            asset_id="chest-01",
            asset_kind="prop",
            name="Treasure Chest",
        )
    assert not (project / "assets").exists()


def test_factory_contains_domain_generators_and_editable_glb_export() -> None:
    script = (
        Path(__file__).resolve().parents[1] / "scripts" / "blender" / "asset_factory.py"
    )
    source = script.read_text(encoding="utf-8")

    for domain in ("character", "world", "prop", "building", "vehicle", "vegetation"):
        assert domain in source
    assert "def building():" in source
    assert "def vehicle():" in source
    assert "def vegetation():" in source
    assert "pakistani_storybook_v1" in source
    for family in (
        "pakistani_charpai_and_chai_set_v1",
        "lahore_haveli_shopfront_v1",
        "pakistani_auto_rickshaw_v1",
        "pakistani_mango_tree_v1",
    ):
        assert family in source
    assert "export_skins=True" in source
    assert "export_morph=True" in source
    assert '"editable_source":True' in source.replace(" ", "")
