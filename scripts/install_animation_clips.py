"""Install a reviewed CC0 animation clip pack into a project.

The Universal Animation Library is published as CC0 on its own page and on
itch.io, but the download is gated behind itch.io's purchase flow and the
archive bytes are not stable. This script therefore does not download blindly:
the owner downloads the ZIP once, and this tool verifies its hash and extracts
only GLB files before writing a manifest that maps the brief's action IDs to
those files. The mapping is checked against every action; a missing clip is a
hard error rather than a silent procedural fallback.

Usage:
    python scripts/install_animation_clips.py <archive.zip> <project_dir> \
        --source-url https://quaternius.itch.io/universal-animation-library \
        --sha256 <hash printed by your local sha256sum>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from app.animation_library import (
    ACTION_CLIP_NAMES,
    LICENSE,
    LICENSE_SOURCE,
    MANIFEST_FILENAME,
    build_clip_manifest,
    normalize_clip_name,
)
from app.story import AVAILABLE_ACTION_IDS

MAX_ARCHIVE_BYTES = 200 * 1024 * 1024
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,119}\.glb$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _glb_json(data: bytes) -> str:
    """Return the JSON chunk of a GLB, refusing a malformed header."""
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError("The animation clip is not a GLB file.")
    json_length = int.from_bytes(data[12:16], "little")
    if data[16:20] != b"JSON" or json_length > len(data) - 20:
        raise ValueError("The animation clip has an invalid JSON chunk.")
    return data[20 : 20 + json_length].decode("utf-8")


def install_clips(archive: Path, project_dir: Path, source_url: str, sha256: str) -> dict[str, object]:
    """Verify, extract and index a CC0 clip pack; return the written manifest."""
    archive = Path(archive).resolve(strict=True)
    project_dir = Path(project_dir).resolve(strict=True)
    if not project_dir.is_dir():
        raise ValueError("The project directory does not exist.")
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("The clip archive exceeds its 200 MiB safety limit.")
    actual = _sha256(archive)
    if actual != sha256.lower():
        raise ValueError(
            f"Clip archive SHA-256 mismatch: expected {sha256.lower()}, received {actual}. "
            "Re-review the upstream release before updating the pinned hash."
        )
    if not source_url.startswith("https://"):
        raise ValueError("The clip source URL must use HTTPS.")
    clips_dir = project_dir / "animation_clips"
    clips_dir.mkdir(exist_ok=True)
    # The pack is one animated GLB containing many named clips; the manifest
    # looks clips up by normalised glTF animation name, not by file.
    inventory: list[dict[str, str]] = []
    bundle_path = Path("animation_library.glb")
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            name = Path(entry.filename).name
            if entry.is_dir() or not name.lower().endswith(".glb"):
                continue
            if not SAFE_NAME.fullmatch(name):
                raise ValueError(f"Unsafe animation clip file name: {entry.filename!r}")
            if entry.file_size > MAX_ARCHIVE_BYTES:
                raise ValueError(f"Animation clip {name!r} exceeds its size limit.")
            data = bundle.read(entry)
            if len(data) > MAX_ARCHIVE_BYTES:
                raise ValueError(f"Animation clip {name!r} expanded beyond its size limit.")
            (clips_dir / name).write_bytes(data)
            bundle_path = Path(name)
            # glTF animation names are the clip identity. Record them for the
            # inventory and for the action mapping check below.
            document = json.loads(_glb_json(data))
            for animation in document.get("animations", []):
                label = str(animation.get("name", ""))
                if label:
                    inventory.append({"name": label, "file": name})
    if not inventory:
        raise ValueError("The installed GLB contains no named animation clips.")
    names = {normalize_clip_name(item["name"]) for item in inventory}
    missing = sorted(
        name
        for name in set(ACTION_CLIP_NAMES.values())
        if normalize_clip_name(name) not in names
    )
    if missing:
        raise ValueError(
            "The installed pack does not cover every brief action. Missing clips: "
            + ", ".join(missing)
            + f". Required action IDs: {len(AVAILABLE_ACTION_IDS)}."
        )
    manifest = build_clip_manifest(
        inventory, source_url=source_url, sha256=actual, license_source=LICENSE_SOURCE
    )
    manifest["clip_file"] = bundle_path.name
    (clips_dir / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    manifest = install_clips(args.archive, args.project_dir, args.source_url, args.sha256)
    print(
        f"Installed {len(manifest['clips'])} CC0 clips "
        f"({len(manifest['actions'])} action mappings) under {LICENSE}."
    )


if __name__ == "__main__":
    main()
