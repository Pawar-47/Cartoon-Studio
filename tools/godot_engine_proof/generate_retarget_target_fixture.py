#!/usr/bin/env python3
"""Generate a reordered, differently proportioned humanoid target GLB fixture.

The source fixture remains untouched. This generator only uses the Python standard
library and updates JOINTS_0 plus inverse-bind matrices when changing skin joint order
and rest translations.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

JOINT_ORDER = (0, 10, 13, 1, 4, 7, 2, 11, 14, 3, 5, 8, 12, 6, 9)
REST_FACTORS = {
    "LeftLowerArm": 1.32,
    "RightLowerArm": 1.32,
    "LeftHand": 1.18,
    "RightHand": 1.18,
    "LeftLowerLeg": 1.20,
    "RightLowerLeg": 1.20,
    "LeftFoot": 1.10,
    "RightFoot": 1.10,
}


def _read_glb(data: bytes) -> tuple[dict, bytearray]:
    if len(data) < 28 or data[:4] != b"glTF":
        raise ValueError("Input is not a valid GLB file.")
    magic, version, total_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or total_length != len(data):
        raise ValueError("Only complete glTF 2.0 binary files are supported.")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError("GLB JSON chunk is missing.")
    json_start = 20
    document = json.loads(data[json_start : json_start + json_length].decode("utf-8"))
    bin_header = json_start + json_length
    bin_length, bin_type = struct.unpack_from("<II", data, bin_header)
    if bin_type != 0x004E4942:
        raise ValueError("GLB binary chunk is missing.")
    binary = bytearray(data[bin_header + 8 : bin_header + 8 + bin_length])
    if len(binary) != bin_length:
        raise ValueError("GLB binary chunk is truncated.")
    return document, binary


def _global_translations(nodes: list[dict]) -> dict[int, tuple[float, float, float]]:
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child_index in node.get("children", []):
            if child_index in parents:
                raise ValueError("Fixture contains a node with multiple parents.")
            parents[child_index] = parent_index

    cache: dict[int, tuple[float, float, float]] = {}

    def visit(index: int) -> tuple[float, float, float]:
        if index in cache:
            return cache[index]
        node = nodes[index]
        if "matrix" in node or "rotation" in node or "scale" in node:
            raise ValueError("Fixture generator expects translation-only joint nodes.")
        local = node.get("translation", [0.0, 0.0, 0.0])
        parent = parents.get(index)
        if parent is None:
            result = tuple(float(value) for value in local)
        else:
            parent_global = visit(parent)
            result = tuple(parent_global[axis] + float(local[axis]) for axis in range(3))
        cache[index] = result
        return result

    for index in range(len(nodes)):
        visit(index)
    return cache


def generate_target_fixture(source_path: Path, output_path: Path) -> None:
    document, binary = _read_glb(source_path.read_bytes())
    nodes = document["nodes"]
    node_by_name = {node.get("name"): index for index, node in enumerate(nodes)}
    for name, factor in REST_FACTORS.items():
        if name not in node_by_name:
            raise ValueError(f"Required fixture bone is missing: {name}")
        node = nodes[node_by_name[name]]
        translation = list(node.get("translation", [0.0, 0.0, 0.0]))
        axis = 0 if name.endswith("LowerArm") or name.endswith("Hand") else 1
        translation[axis] = float(translation[axis]) * factor
        node["translation"] = translation

    skin = document["skins"][0]
    old_joints = list(skin["joints"])
    if len(old_joints) != len(JOINT_ORDER) or sorted(JOINT_ORDER) != list(range(len(old_joints))):
        raise ValueError("Fixture joint order does not match the generator permutation.")
    old_to_new = {old_index: new_index for new_index, old_index in enumerate(JOINT_ORDER)}

    primitive = document["meshes"][0]["primitives"][0]
    joints_accessor = document["accessors"][primitive["attributes"]["JOINTS_0"]]
    if joints_accessor["componentType"] != 5121 or joints_accessor["type"] != "VEC4":
        raise ValueError("Fixture JOINTS_0 must use unsigned-byte VEC4 data.")
    joints_view = document["bufferViews"][joints_accessor["bufferView"]]
    joints_offset = joints_view.get("byteOffset", 0) + joints_accessor.get("byteOffset", 0)
    joints_stride = joints_view.get("byteStride", 4)
    for row in range(joints_accessor["count"]):
        for column in range(4):
            offset = joints_offset + row * joints_stride + column
            old_index = binary[offset]
            if old_index not in old_to_new:
                raise ValueError(f"JOINTS_0 contains unknown joint index {old_index}.")
            binary[offset] = old_to_new[old_index]

    global_positions = _global_translations(nodes)
    inverse_bind_accessor = document["accessors"][skin["inverseBindMatrices"]]
    if (
        inverse_bind_accessor["componentType"] != 5126
        or inverse_bind_accessor["type"] != "MAT4"
        or inverse_bind_accessor["count"] != len(old_joints)
    ):
        raise ValueError("Fixture inverse-bind accessor is not a 15-matrix FLOAT MAT4 array.")
    inverse_bind_view = document["bufferViews"][inverse_bind_accessor["bufferView"]]
    inverse_bind_offset = (
        inverse_bind_view.get("byteOffset", 0)
        + inverse_bind_accessor.get("byteOffset", 0)
    )
    for new_index, old_index in enumerate(JOINT_ORDER):
        node_index = old_joints[old_index]
        x, y, z = global_positions[node_index]
        matrix = [0.0] * 16
        matrix[0] = matrix[5] = matrix[10] = matrix[15] = 1.0
        matrix[12], matrix[13], matrix[14] = -x, -y, -z
        struct.pack_into("<16f", binary, inverse_bind_offset + new_index * 64, *matrix)

    skin["joints"] = [old_joints[index] for index in JOINT_ORDER]
    document["buffers"][0]["byteLength"] = len(binary)
    json_bytes = json.dumps(document, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    binary_bytes = bytes(binary)
    binary_bytes += b"\x00" * ((-len(binary_bytes)) % 4)
    total_length = 12 + 8 + len(json_bytes) + 8 + len(binary_bytes)
    output = bytearray()
    output.extend(struct.pack("<4sII", b"glTF", 2, total_length))
    output.extend(struct.pack("<II", len(json_bytes), 0x4E4F534A))
    output.extend(json_bytes)
    output.extend(struct.pack("<II", len(binary_bytes), 0x004E4942))
    output.extend(binary_bytes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    generate_target_fixture(arguments.source, arguments.output)


if __name__ == "__main__":
    main()
