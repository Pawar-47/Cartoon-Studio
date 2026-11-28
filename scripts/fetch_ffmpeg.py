from __future__ import annotations

# ruff: noqa: I001

import argparse
import hashlib
import json
import pathlib
import subprocess
import zipfile
from urllib import request


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "engine" / "ffmpeg_runtime.json"


def download_and_verify(
    url: str, expected_sha256: str, destination: pathlib.Path
) -> None:
    digest = hashlib.sha256()
    with request.urlopen(url, timeout=600) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
    actual = digest.hexdigest()
    if actual.lower() != expected_sha256.lower():
        destination.unlink(missing_ok=True)
        raise RuntimeError(
            "FFmpeg archive SHA-256 mismatch: "
            f"expected {expected_sha256}, got {actual}. "
            "The pinned FFmpeg release does not match its recorded SHA-256; a "
            "dated release should be immutable, so re-pin engine/ffmpeg_runtime.json "
            "only after reviewing the new build's licence and encoders."
        )


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def extract_binary(
    archive_path: pathlib.Path, binary_name: str, output_path: pathlib.Path
) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.namelist()
        unsafe = [
            name
            for name in members
            if (
                pathlib.PurePosixPath(name).is_absolute()
                or ".." in pathlib.PurePosixPath(name).parts
            )
        ]
        if unsafe:
            raise RuntimeError(f"FFmpeg archive contains unsafe paths: {unsafe[:3]!r}")
        matches = [
            name
            for name in members
            if pathlib.PurePosixPath(name).name == binary_name
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one {binary_name} in the FFmpeg archive; "
                f"found {matches!r}."
            )
        with archive.open(matches[0]) as source, output_path.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)


def extract_notices(archive_path: pathlib.Path, notices_dir: pathlib.Path) -> list[str]:
    """Copy the licence and notice files shipped inside the FFmpeg archive."""
    notices_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            name = pathlib.PurePosixPath(info.filename).name
            if info.is_dir():
                continue
            if not name.casefold().startswith(("license", "copying", "readme")):
                continue
            target = notices_dir / name
            with archive.open(info) as source, target.open("wb") as destination:
                while chunk := source.read(1024 * 1024):
                    destination.write(chunk)
            written.append(name)
    return sorted(written)


def encoder_listing(binary_path: pathlib.Path, timeout: int = 30) -> str:
    return subprocess.run(
        [str(binary_path), "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=True,
    ).stdout


def verify_encoders(listing: str, manifest: dict) -> dict[str, list[str] | dict[str, bool]]:
    """Fail unless the build has the required encoders and no GPL-only video encoder."""
    names: set[str] = set()
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        flags = parts[0]
        # Encoder rows look like " V..... libx264 ..." or " A....D aac ...".
        if not 5 <= len(flags) <= 6 or flags[0] not in "VASD":
            continue
        if not all(character == "." or character.isalpha() for character in flags[1:]):
            continue
        if parts[1].startswith("="):
            continue
        names.add(parts[1])
    missing = [name for name in manifest["required_encoders"] if name not in names]
    if missing:
        raise RuntimeError(
            "The FFmpeg build is missing required encoders: " + ", ".join(missing)
        )
    present_allowed = [
        name for name in manifest["allowed_video_encoders"] if name in names
    ]
    if not present_allowed:
        raise RuntimeError(
            "The FFmpeg build has no redistribution-safe video encoder; expected one "
            f"of {manifest['allowed_video_encoders']}."
        )
    forbidden_present = [
        name for name in manifest["forbidden_video_encoders"] if name in names
    ]
    return {
        "encoders": {name: name in names for name in manifest["required_encoders"]},
        "allowed_video_encoders_present": present_allowed,
        "forbidden_video_encoders_present": forbidden_present,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch the pinned LGPL FFmpeg Windows build."
    )
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--output-dir", type=pathlib.Path, default=ROOT / "build" / "ffmpeg"
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / manifest["archive_name"]
    binary_path = args.output_dir / manifest["binary_name"]

    download_and_verify(
        manifest["download_url"], manifest["archive_sha256"], archive_path
    )
    notices: list[str] = []
    try:
        notices = extract_notices(archive_path, args.output_dir / "notices")
        extract_binary(archive_path, manifest["binary_name"], binary_path)
    finally:
        archive_path.unlink(missing_ok=True)

    check = verify_encoders(encoder_listing(binary_path), manifest)
    if not notices:
        raise RuntimeError(
            "The FFmpeg archive shipped no licence or notice file; do not bundle it "
            "without the LGPL text and upstream notices."
        )
    report = {
        **manifest,
        "binary": str(binary_path),
        "binary_sha256": sha256_file(binary_path),
        "size_bytes": binary_path.stat().st_size,
        "notices": notices,
        "encoder_check": check,
    }
    report_path = args.output_dir / "ffmpeg-runtime-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
