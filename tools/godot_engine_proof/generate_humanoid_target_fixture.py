from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

NAME_MAP = {
    "Hips": "mixamorig:Hips",
    "Spine": "mixamorig:Spine",
    "Head": "mixamorig:Head",
    "LeftUpperLeg": "mixamorig:LeftUpLeg",
    "LeftLowerLeg": "mixamorig:LeftLeg",
    "LeftFoot": "mixamorig:LeftFoot",
    "RightUpperLeg": "mixamorig:RightUpLeg",
    "RightLowerLeg": "mixamorig:RightLeg",
    "RightFoot": "mixamorig:RightFoot",
    "LeftUpperArm": "mixamorig:LeftArm",
    "LeftLowerArm": "mixamorig:LeftForeArm",
    "LeftHand": "mixamorig:LeftHand",
    "RightUpperArm": "mixamorig:RightArm",
    "RightLowerArm": "mixamorig:RightForeArm",
    "RightHand": "mixamorig:RightHand",
}

REST_TRANSLATIONS = {
    4: [-0.12, -0.18, 0.0],
    5: [0.0, -0.42, 0.0],
    6: [0.0, -0.40, 0.08],
    7: [0.12, -0.18, 0.0],
    8: [0.0, -0.42, 0.0],
    9: [0.0, -0.40, 0.08],
    10: [-0.18, -0.13, 0.0],
    11: [-0.35, 0.0, 0.0],
    12: [-0.32, 0.0, 0.0],
    13: [0.18, -0.13, 0.0],
    14: [0.35, 0.0, 0.0],
    15: [0.32, 0.0, 0.0],
}

JSON_CHUNK = 0x4E4F534A


def read_glb(path: Path) -> tuple[dict[str, Any], list[tuple[int, bytes]]]:
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise ValueError(f"{path} is not a GLB 2.0 file.")
    version, declared_length = struct.unpack_from("<II", raw, 4)
    if version != 2 or declared_length != len(raw):
        raise ValueError(f"{path} has an invalid GLB header.")
    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError("GLB chunk header is truncated.")
        length, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        chunk = raw[offset : offset + length]
        if len(chunk) != length:
            raise ValueError("GLB chunk is truncated.")
        chunks.append((chunk_type, chunk))
        offset += length
    json_chunks = [chunk for kind, chunk in chunks if kind == JSON_CHUNK]
    if len(json_chunks) != 1:
        raise ValueError("GLB must contain exactly one JSON chunk.")
    document = json.loads(json_chunks[0].decode("utf-8").rstrip("\x00 \t\r\n"))
    return document, chunks


def write_glb(path: Path, document: dict[str, Any], chunks: list[tuple[int, bytes]]) -> None:
    json_bytes = json.dumps(
        document, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    encoded_chunks = [(kind, json_bytes if kind == JSON_CHUNK else data) for kind, data in chunks]
    body = bytearray()
    for kind, data in encoded_chunks:
        body.extend(struct.pack("<II", len(data), kind))
        body.extend(data)
    total_length = 12 + len(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, total_length) + body)


def build_target_fixture(source: Path, output: Path) -> None:
    document, chunks = read_glb(source)
    nodes = document.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("Source fixture has no node array.")
    found = {str(node.get("name", "")) for node in nodes if isinstance(node, dict)}
    if not set(NAME_MAP).issubset(found):
        raise ValueError("Source fixture does not contain the expected 15 canonical humanoid bones.")
    for node in nodes:
        if isinstance(node, dict):
            name = str(node.get("name", ""))
            if name in NAME_MAP:
                node["name"] = NAME_MAP[name]
    for index, translation in REST_TRANSLATIONS.items():
        nodes[index]["translation"] = translation
    document["animations"] = []
    write_glb(output, document, chunks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a Mixamo-named, differently proportioned humanoid target GLB."
    )
    base = Path(__file__).resolve().parent / "fixtures"
    parser.add_argument("--source", type=Path, default=base / "proof_humanoid.glb")
    parser.add_argument(
        "--output", type=Path, default=base / "proof_humanoid_target.glb"
    )
    args = parser.parse_args()
    build_target_fixture(args.source, args.output)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
