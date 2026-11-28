import json
from pathlib import Path

import pytest

from app.animation_library import (
    ACTION_CLIP_NAMES,
    MANIFEST_FILENAME,
    build_clip_manifest,
    clip_name_for_action,
    load_clip_manifest,
    normalize_clip_name,
    validate_clip_manifest,
)
from app.story import AVAILABLE_ACTION_IDS


def _clips() -> list[dict[str, str]]:
    # One clip per distinct canonical name, including a few aliases from the
    # brief's action list. Names mirror the GLB animation list shape.
    names = sorted(set(ACTION_CLIP_NAMES.values()))
    return [
        {"name": name, "file": f"{name.lower()}.glb"}
        for name in names
    ]


def _manifest() -> dict[str, object]:
    return build_clip_manifest(
        _clips(),
        source_url="https://quaternius.itch.io/universal-animation-library/download/example",
        sha256="a" * 64,
    )


def test_every_brief_action_has_a_canonical_clip_name():
    assert set(AVAILABLE_ACTION_IDS).issubset(ACTION_CLIP_NAMES)
    assert clip_name_for_action("walk") == "Walk"
    assert clip_name_for_action("unknown-action") is None


def test_clip_names_normalize_like_the_browser_resolver():
    assert normalize_clip_name("RobotArmature/Walking") == "robotarmaturewalking"
    assert normalize_clip_name("Idle_Gun") == "idlegun"


def test_manifest_maps_every_action_to_an_inventoried_file():
    manifest = _manifest()
    assert validate_clip_manifest(manifest) == sorted(AVAILABLE_ACTION_IDS) + sorted(
        set(ACTION_CLIP_NAMES) - set(AVAILABLE_ACTION_IDS)
    )
    assert manifest["license"] == "CC0-1.0"
    assert manifest["actions"]["wave"] == normalize_clip_name("Wave")
    assert manifest["actions"]["walk_back"] == normalize_clip_name("Walk")
    assert manifest["clip_file"] == sorted({name for name in ACTION_CLIP_NAMES.values()})[0].lower() + ".glb"


def test_manifest_refuses_unknown_or_unsafe_sources():
    with pytest.raises(ValueError, match="HTTPS"):
        build_clip_manifest(_clips(), source_url="http://example.test/pack.zip", sha256="a" * 64)
    with pytest.raises(ValueError, match="SHA-256"):
        build_clip_manifest(
            _clips(), source_url="https://example.test/pack.zip", sha256="not-a-hash"
        )


def test_manifest_refuses_missing_or_duplicate_clips():
    incomplete = [clip for clip in _clips() if clip["name"] != "Walk"]
    with pytest.raises(ValueError, match="missing 'Walk'"):
        build_clip_manifest(
            incomplete, source_url="https://example.test/pack.zip", sha256="a" * 64
        )
    duplicate = _clips() + [{"name": "Walking", "file": "other.glb"}]
    with pytest.raises(ValueError, match="Duplicate clip name"):
        build_clip_manifest(
            duplicate, source_url="https://example.test/pack.zip", sha256="a" * 64
        )


def test_load_manifest_is_optional_and_validates(tmp_path: Path):
    assert load_clip_manifest(tmp_path) is None
    manifest_dir = tmp_path / "animation"
    manifest_dir.mkdir()
    (manifest_dir / MANIFEST_FILENAME).write_text(
        '{"manifest_version": 1, "license": "MIT", "sha256": "' + "a" * 64 + '"}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="CC0"):
        load_clip_manifest(manifest_dir)
    (manifest_dir / MANIFEST_FILENAME).write_text(
        json.dumps(_manifest()), encoding="utf-8"
    )
    assert load_clip_manifest(manifest_dir)["license"] == "CC0-1.0"
