import hashlib
import json
import struct
import zipfile
from pathlib import Path

import pytest

from app.animation_library import ACTION_CLIP_NAMES, MANIFEST_FILENAME, load_clip_manifest
from scripts.install_animation_clips import install_clips


def _glb(animation_names: list[str]) -> bytes:
    document = {"asset": {"version": "2.0"}, "animations": [
        {"name": name, "channels": [], "samplers": []} for name in animation_names
    ]}
    payload = json.dumps(document).encode("utf-8")
    payload += b" " * (-len(payload) % 4)
    header = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(payload))
    chunk = struct.pack("<II", len(payload), 0x4E4F534A) + payload
    return header + chunk


def test_installer_accepts_a_complete_hash_verified_pack(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    archive = tmp_path / "pack.zip"
    names = sorted(set(ACTION_CLIP_NAMES.values()))
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("pack/animation_library.glb", _glb(names))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = install_clips(
        archive, project, "https://quaternius.itch.io/universal-animation-library", digest
    )
    clips_dir = project / "animation_clips"
    assert (clips_dir / "animation_library.glb").is_file()
    installed = load_clip_manifest(clips_dir)
    assert installed == manifest
    assert installed["clip_file"] == "animation_library.glb"


def test_installer_refuses_a_bad_hash_without_writing(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("animation_library.glb", _glb(["Idle"]))
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        install_clips(archive, project, "https://quaternius.itch.io/x", "0" * 64)
    assert not (project / "animation_clips").exists()


def test_installer_requires_every_brief_action(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("animation_library.glb", _glb(["Idle"]))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Missing clips"):
        install_clips(archive, project, "https://quaternius.itch.io/x", digest)
