from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import urllib
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "engine" / "godot_runtime.json"


def download_and_verify(url: str, expected_sha256: str, destination: pathlib.Path) -> None:
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=180) as response, destination.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
            output.write(chunk)
    actual = digest.hexdigest()
    if actual.lower() != expected_sha256.lower():
        destination.unlink(missing_ok=True)
        raise RuntimeError(
            f"Godot release SHA-256 mismatch: expected {expected_sha256}, got {actual}."
        )


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def extract_binary(archive_path: pathlib.Path, binary_name: str, output_path: pathlib.Path) -> None:
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
            raise RuntimeError(f"Godot archive contains unsafe paths: {unsafe[:3]!r}")
        matches = [name for name in members if pathlib.PurePosixPath(name).name == binary_name]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one {binary_name} in Godot archive; found {matches!r}."
            )
        with archive.open(matches[0]) as source, output_path.open("wb") as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the pinned Godot Windows runtime.")
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "build" / "godot-runtime")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = args.output_dir / manifest["archive_name"]
    binary_path = args.output_dir / manifest["binary_name"]

    download_and_verify(
        manifest["download_url"],
        manifest["archive_sha256"],
        archive_path,
    )
    try:
        extract_binary(archive_path, manifest["binary_name"], binary_path)
    finally:
        archive_path.unlink(missing_ok=True)

    version = subprocess.run(
        [str(binary_path), "--headless", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=True,
    ).stdout.strip()
    if manifest["version"].split("-")[0] not in version:
        raise RuntimeError(
            f"Downloaded Godot version did not match manifest: {version!r}."
        )

    report = {
        **manifest,
        "binary": str(binary_path),
        "binary_sha256": sha256_file(binary_path),
        "reported_version": version,
        "size_bytes": binary_path.stat().st_size,
    }
    report_path = args.output_dir / "godot-runtime-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
