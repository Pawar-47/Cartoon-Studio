#!/usr/bin/env python3
"""Create an animated humanoid GLB with Mixamo-style bone names."""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

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


def generate_source_fixture(source: Path, output: Path) -> None:
    data = source.read_bytes()
    if len(data) < 28 or data[:4] != b"glTF":
        raise ValueError("Input is not a valid GLB 2.0 file.")
    magic, version, total = struct.unpack_from("<4sII", data, 0)
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if magic != b"glTF" or version != 2 or total != len(data):
        raise ValueError("Only complete GLB 2.0 files are supported.")
    if json_type != 0x4E4F534A:
        raise ValueError("GLB JSON chunk is missing.")
    json_start = 20
    document = json.loads(data[json_start:json_start + json_length].decode("utf-8"))
    bin_header = json_start + json_length
    binary_length, binary_type = struct.unpack_from("<II", data, bin_header)
    if binary_type != 0x004E4942:
        raise ValueError("GLB binary chunk is missing.")
    binary = data[bin_header + 8:bin_header + 8 + binary_length]
    if len(binary) != binary_length:
        raise ValueError("GLB binary chunk is truncated.")

    renamed = 0
    for node in document["nodes"]:
        original = node.get("name")
        if original in NAME_MAP:
            node["name"] = NAME_MAP[original]
            renamed += 1
    if renamed != len(NAME_MAP):
        raise ValueError(f"Expected {len(NAME_MAP)} named bones, found {renamed}.")
    if not document.get("animations"):
        raise ValueError("The source fixture must retain its imported animation.")

    json_bytes = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    binary_bytes = binary + b"\\x00" * ((-len(binary)) % 4)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary_bytes)
    output_bytes = bytearray(struct.pack("<4sII", b"glTF", 2, total_length))
    output_bytes.extend(struct.pack("<II", len(json_bytes), 0x4E4F534A))
    output_bytes.extend(json_bytes)
    output_bytes.extend(struct.pack("<II", len(binary_bytes), 0x004E4942))
    output_bytes.extend(binary_bytes)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(output_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    generate_source_fixture(args.source, args.output)


if __name__ == "__main__":
    main()
