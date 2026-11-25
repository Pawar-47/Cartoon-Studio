import argparse
import hashlib
import pathlib
import urllib.request


SOURCE_COMMIT = "eba30de865cfbf31ac736f792defd9a60ff28d57"
SOURCE_URL = (
    "https://raw.githubusercontent.com/mrdoob/three.js/"
    f"{SOURCE_COMMIT}/examples/models/gltf/RobotExpressive/RobotExpressive.glb"
)
EXPECTED_SHA256 = "047f5e5fb3bb6d378bd1df16ca6137f2a596c99b3a1b5690b4020c05aaf6f319"
MAX_ASSET_BYTES = 2 * 1024 * 1024


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_fixture(output_dir: pathlib.Path) -> pathlib.Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "robot_expressive_cc0.glb"
    if target.is_file() and sha256(target.read_bytes()) == EXPECTED_SHA256:
        print(f"Verified cached fixture: {target}")
        return target

    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Cartoon-Studio-fixture-fetcher"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read(MAX_ASSET_BYTES + 1)
    if len(payload) > MAX_ASSET_BYTES:
        raise RuntimeError("RobotExpressive fixture exceeds the 2 MiB safety limit.")
    actual_sha256 = sha256(payload)
    if actual_sha256 != EXPECTED_SHA256:
        raise RuntimeError(
            "RobotExpressive fixture checksum mismatch: "
            f"expected {EXPECTED_SHA256}, received {actual_sha256}."
        )

    temporary = target.with_suffix(".glb.download")
    temporary.write_bytes(payload)
    temporary.replace(target)
    print(f"Fetched and verified CC0 facial-morph fixture: {target}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a pinned CC0 facial morph GLB test fixture."
    )
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=pathlib.Path("tests/fixtures/third_party"),
    )
    args = parser.parse_args()
    fetch_fixture(args.output_dir)


if __name__ == "__main__":
    main()
