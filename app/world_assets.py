"""Curated, integrity-pinned Kenney CC0 models for World Builder."""

from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

SOURCE_REPOSITORY = "Hidencod/tge-assets"
SOURCE_COMMIT = "e5bd31ec8b339b25d66dd5816a21dd517bd1ae87"
SOURCE_LICENSE = "CC0-1.0"
MAX_ASSET_BYTES = 2 * 1024 * 1024

ASSETS: dict[str, dict[str, Any]] = {
    "road-straight": {
        "name": "Road Straight", "category": "road",
        "source_path": "city-kit-roads/road-straight.glb", "size": 16696,
        "git_blob_sha1": "8707b6f3bf7c6f5fda3bb01f164a9ef0b09f6eb2",
    },
    "road-crossroad": {
        "name": "Road Crossroad", "category": "road",
        "source_path": "city-kit-roads/road-crossroad.glb", "size": 21532,
        "git_blob_sha1": "5e0204d012bbd64e861eb10699c0ddac915dadb6",
    },
    "road-curve": {
        "name": "Road Curve", "category": "road",
        "source_path": "city-kit-roads/road-curve.glb", "size": 35356,
        "git_blob_sha1": "7eb1e51f6d9a29d167d907f49d326b16c8a95b0c",
    },
    "road-bend": {
        "name": "Road Bend", "category": "road",
        "source_path": "city-kit-roads/road-bend.glb", "size": 31616,
        "git_blob_sha1": "241878bb63fec4d0dbf6f338bbf0cc3eb89dbc9d",
    },
    "road-roundabout": {
        "name": "Road Roundabout", "category": "road",
        "source_path": "city-kit-roads/road-roundabout.glb", "size": 117328,
        "git_blob_sha1": "80de836555b5a85287767291816e804515b44cb1",
    },
    "traffic-light": {
        "name": "Traffic Light", "category": "street",
        "source_path": "city-kit-roads/traffic-light.glb", "size": 31796,
        "git_blob_sha1": "39d39733a048bf5c83b9dda85203c926ae5bc258",
    },
    "road-sign-stop": {
        "name": "Stop Sign", "category": "street",
        "source_path": "city-kit-roads/road-sign-stop.glb", "size": 22172,
        "git_blob_sha1": "c6457263d88da000e7bbdc6abae10a90c27d7b97",
    },
    "road-sign-street": {
        "name": "Street Sign", "category": "street",
        "source_path": "city-kit-roads/road-sign-street.glb", "size": 27400,
        "git_blob_sha1": "9a396210dd01ea14cb34525109cbd88aba84da6b",
    },
    "building-type-a": {
        "name": "Suburban House A", "category": "building",
        "source_path": "city-kit-suburban/building-type-a.glb", "size": 110408,
        "git_blob_sha1": "4aa2f0d0014f1383fad54acebd53cdf73baa2837",
    },
    "building-type-b": {
        "name": "Suburban House B", "category": "building",
        "source_path": "city-kit-suburban/building-type-b.glb", "size": 158540,
        "git_blob_sha1": "2d30737ee91302a856e2a02e9fffe73f102e80c3",
    },
    "building-type-c": {
        "name": "Suburban House C", "category": "building",
        "source_path": "city-kit-suburban/building-type-c.glb", "size": 111408,
        "git_blob_sha1": "defa674771e61714a07e13a55758f6125bd0a7a5",
    },
    "building-type-d": {
        "name": "Suburban House D", "category": "building",
        "source_path": "city-kit-suburban/building-type-d.glb", "size": 159184,
        "git_blob_sha1": "a80aee888858ada62c511d16ea919e50783c541a",
    },
    "building-type-e": {
        "name": "Suburban House E", "category": "building",
        "source_path": "city-kit-suburban/building-type-e.glb", "size": 157316,
        "git_blob_sha1": "781540fa66867080ff6a136cfac4468f554f4eb4",
    },
    "building-type-f": {
        "name": "Suburban House F", "category": "building",
        "source_path": "city-kit-suburban/building-type-f.glb", "size": 150356,
        "git_blob_sha1": "1b482decbc24b3af83660fe47a17858b6b634266",
    },
    "nature-tree-default": {
        "name": "Tree Default", "category": "nature",
        "source_path": "nature-kit/tree-default.glb", "size": 9428,
        "git_blob_sha1": "f47828217006ceb71f2df2d37bfb361b44935344",
    },
    "nature-tree-oak": {
        "name": "Oak Tree", "category": "nature",
        "source_path": "nature-kit/tree-oak.glb", "size": 14644,
        "git_blob_sha1": "0eee1d26da24da9daedcc48adf4f62689ec869a5",
    },
    "nature-tree-palm": {
        "name": "Palm Tree", "category": "nature",
        "source_path": "nature-kit/tree-palm.glb", "size": 13616,
        "git_blob_sha1": "dda114da2a44d99ebb1c59e9e7c42714a6b8f371",
    },
    "nature-plant-bush": {
        "name": "Bush", "category": "nature",
        "source_path": "nature-kit/plant-bush.glb", "size": 4396,
        "git_blob_sha1": "11055bbb53a36b6b294eeffc4aabc73214faabed",
    },
    "nature-rock-large": {
        "name": "Large Rock", "category": "nature",
        "source_path": "nature-kit/rock-largea.glb", "size": 7552,
        "git_blob_sha1": "3df13f56ceaa9da68e02a55e60a6961a33499d42",
    },
    "car-sedan": {
        "name": "Sedan", "category": "vehicle",
        "source_path": "car-kit/sedan.glb", "size": 184504,
        "git_blob_sha1": "bcae84827ec41907f7f8ac8a314fa670cd372da1",
    },
    "car-hatchback": {
        "name": "Sport Hatchback", "category": "vehicle",
        "source_path": "car-kit/hatchback-sports.glb", "size": 210092,
        "git_blob_sha1": "b60257c4dc57b54d93c37f6f8ee94c8be23569d1",
    },
    "car-van": {
        "name": "Van", "category": "vehicle",
        "source_path": "car-kit/van.glb", "size": 187952,
        "git_blob_sha1": "6ab9114050b899242a6147c282b16f6e4e2ea902",
    },
    "car-taxi": {
        "name": "Taxi", "category": "vehicle",
        "source_path": "car-kit/taxi.glb", "size": 187896,
        "git_blob_sha1": "86c40f0a72018bbf4d66f108928fb9a6a7093e0d",
    },
    "car-ambulance": {
        "name": "Ambulance", "category": "vehicle",
        "source_path": "car-kit/ambulance.glb", "size": 245804,
        "git_blob_sha1": "86944003e688aea478605ee74d8b7b9fbae6200c",
    },
    "car-truck": {
        "name": "Truck", "category": "vehicle",
        "source_path": "car-kit/truck.glb", "size": 188652,
        "git_blob_sha1": "ab33daad2e0b7d32f4ab1016dc18711988ecc750",
    },
    "furniture-bench": {
        "name": "Bench", "category": "furniture",
        "source_path": "furniture-kit/bench.glb", "size": 10756,
        "git_blob_sha1": "7897dd0652ad3c6e94ae1dbdbbfc6180dab6b4e8",
    },
    "furniture-chair": {
        "name": "Chair", "category": "furniture",
        "source_path": "furniture-kit/chair.glb", "size": 10756,
        "git_blob_sha1": "2d57af4fef2a32910e3af9283d1e45f177068d63",
    },
    "furniture-table": {
        "name": "Table", "category": "furniture",
        "source_path": "furniture-kit/table.glb", "size": 8196,
        "git_blob_sha1": "8add1baf8a97bd813524a441c947a9e1457f4b13",
    },
}


class WorldAssetError(RuntimeError):
    """Raised when a curated world asset cannot be installed safely."""


def list_world_assets(query: str = "", category: str = "") -> list[dict[str, Any]]:
    needle = query.strip().casefold()
    selected = []
    for asset_id, spec in ASSETS.items():
        if category and spec["category"] != category:
            continue
        if needle and needle not in asset_id.casefold() and needle not in spec["name"].casefold():
            continue
        selected.append({
            "id": asset_id,
            "name": spec["name"],
            "category": spec["category"],
            "size": spec["size"],
            "license": SOURCE_LICENSE,
            "pack": spec["source_path"].split("/", 1)[0],
        })
    return selected


def _git_blob_sha1(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def _download_asset(asset_id: str, expected_size: int) -> bytes:
    spec = ASSETS[asset_id]
    url = (
        f"https://raw.githubusercontent.com/{SOURCE_REPOSITORY}/"
        f"{SOURCE_COMMIT}/packs/{spec['source_path']}"
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "Cartoon-Studio/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(MAX_ASSET_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise WorldAssetError(
            f"Could not download {spec['name']}: {error}"
        ) from error
    if len(data) != expected_size or len(data) > MAX_ASSET_BYTES:
        raise WorldAssetError(
            f"Downloaded size check failed for {spec['name']}."
        )
    if _git_blob_sha1(data) != spec["git_blob_sha1"]:
        raise WorldAssetError(f"Integrity check failed for {spec['name']}.")
    if not data.startswith(b"glTF"):
        raise WorldAssetError(
            f"{spec['name']} is not a valid binary glTF file."
        )
    return data


def install_world_asset(project_root: Path, asset_id: str) -> dict[str, Any]:
    spec = ASSETS.get(asset_id)
    if spec is None:
        raise KeyError(asset_id)
    root = Path(project_root).resolve(strict=True)
    if not root.is_dir():
        raise WorldAssetError("Project root is not a directory.")
    relative = PurePosixPath("assets/world-library") / f"{asset_id}.glb"
    destination = root.joinpath(*relative.parts).resolve(strict=False)
    if root not in destination.parents:
        raise WorldAssetError(
            "World asset destination escapes the project directory."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        existing = destination.read_bytes()
        if (
            len(existing) == spec["size"]
            and _git_blob_sha1(existing) == spec["git_blob_sha1"]
        ):
            return {
                "id": asset_id,
                "name": spec["name"],
                "relative_path": relative.as_posix(),
                "size": len(existing),
                "cached": True,
                "license": SOURCE_LICENSE,
            }
        destination.unlink()
    data = _download_asset(asset_id, int(spec["size"]))
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{asset_id}-",
        suffix=".tmp",
        dir=destination.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary_name).replace(destination)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return {
        "id": asset_id,
        "name": spec["name"],
        "relative_path": relative.as_posix(),
        "size": len(data),
        "cached": False,
        "license": SOURCE_LICENSE,
    }
