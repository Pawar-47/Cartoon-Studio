#!/usr/bin/env python3
"""Generate a reordered, differently proportioned humanoid target GLB fixture.

The source fixture remains untouched. This generator only uses the Python standard
library and updates JOINTS_0 plus inverse-bind matrices when changing skin joint order
and rest translations.
"""
from __future__ import annotations

import argparse
import json
import math
import struct
from pathlib import Path

JOINT_ORDER = (0, 10, 13, 1, 4, 7, 2, 11, 14, 3, 5, 8, 12, 6, 9)
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
REST_ROLL_DEGREES = {
    "LeftUpperArm": 24.0,
    "LeftLowerArm": -32.0,
    "RightUpperArm": -24.0,
    "RightLowerArm": 32.0,
}
REST_SCALES = {
    "LeftUpperArm": (1.0, 1.08, 0.94),
    "LeftLowerArm": (1.0, 0.92, 1.06),
    "RightUpperArm": (1.0, 0.94, 1.08),
    "RightLowerArm": (1.0, 1.06, 0.92),
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


def _matrix_multiply(left: list[list[float]], right: list[list[float]]) -> list[list[float]]:
    return [
        [
            sum(left[row][index] * right[index][column] for index in range(3))
            for column in range(3)
        ]
        for row in range(3)
    ]


def _matrix_vector(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    ]


def _quaternion_matrix(value: list[float]) -> list[list[float]]:
    if len(value) != 4:
        raise ValueError("GLTF node rotation must be an XYZW quaternion.")
    x, y, z, w = (float(component) for component in value)
    length = math.sqrt(x * x + y * y + z * z + w * w)
    if length < 1e-12:
        raise ValueError("GLTF node rotation quaternion cannot be zero.")
    x, y, z, w = x / length, y / length, z / length, w / length
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def _global_transforms(
    nodes: list[dict],
) -> dict[int, tuple[list[list[float]], list[float]]]:
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child_index in node.get("children", []):
            if child_index in parents:
                raise ValueError("Fixture contains a node with multiple parents.")
            parents[child_index] = parent_index

    cache: dict[int, tuple[list[list[float]], list[float]]] = {}

    def visit(index: int) -> tuple[list[list[float]], list[float]]:
        if index in cache:
            return cache[index]
        node = nodes[index]
        if "matrix" in node:
            raise ValueError("Fixture generator expects decomposed TRS joint nodes.")
        translation = [float(value) for value in node.get("translation", [0.0, 0.0, 0.0])]
        scale = [float(value) for value in node.get("scale", [1.0, 1.0, 1.0])]
        if len(translation) != 3 or len(scale) != 3:
            raise ValueError("GLTF node translation and scale must be VEC3 values.")
        local = _quaternion_matrix(node.get("rotation", [0.0, 0.0, 0.0, 1.0]))
        for row in range(3):
            for column in range(3):
                local[row][column] *= scale[column]
        parent = parents.get(index)
        if parent is None:
            result = (local, translation)
        else:
            parent_linear, parent_translation = visit(parent)
            global_linear = _matrix_multiply(parent_linear, local)
            transformed_translation = _matrix_vector(parent_linear, translation)
            global_translation = [
                parent_translation[axis] + transformed_translation[axis]
                for axis in range(3)
            ]
            result = (global_linear, global_translation)
        cache[index] = result
        return result

    for node_index in range(len(nodes)):
        visit(node_index)
    return cache


def _inverse_bind_matrix(
    transform: tuple[list[list[float]], list[float]],
) -> list[float]:
    matrix, translation = transform
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    if abs(determinant) < 1e-12:
        raise ValueError("A target joint has a singular rest transform.")
    inverse = [
        [(e * i - f * h) / determinant, (c * h - b * i) / determinant, (b * f - c * e) / determinant],
        [(f * g - d * i) / determinant, (a * i - c * g) / determinant, (c * d - a * f) / determinant],
        [(d * h - e * g) / determinant, (b * g - a * h) / determinant, (a * e - b * d) / determinant],
    ]
    inverse_translation = [
        -value for value in _matrix_vector(inverse, translation)
    ]
    # glTF MAT4 accessors are stored column-major.
    return [
        inverse[0][0], inverse[1][0], inverse[2][0], 0.0,
        inverse[0][1], inverse[1][1], inverse[2][1], 0.0,
        inverse[0][2], inverse[1][2], inverse[2][2], 0.0,
        inverse_translation[0], inverse_translation[1], inverse_translation[2], 1.0,
    ]


def _multiply_quaternions(left: list[float], right: list[float]) -> list[float]:
    x1, y1, z1, w1 = left
    x2, y2, z2, w2 = right
    return [
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ]


def _roll_quaternion(degrees: float) -> list[float]:
    half_angle = math.radians(degrees) / 2.0
    return [math.sin(half_angle), 0.0, 0.0, math.cos(half_angle)]


def generate_target_fixture(
    source_path: Path,
    output_path: Path,
    *,
    rest_roll_degrees: dict[str, float] | None = None,
    rest_scales: dict[str, tuple[float, float, float]] | None = None,
) -> None:
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

    for name, degrees in (rest_roll_degrees or {}).items():
        if name not in node_by_name:
            raise ValueError(f"Required fixture bone is missing: {name}")
        node = nodes[node_by_name[name]]
        current_rotation = list(node.get("rotation", [0.0, 0.0, 0.0, 1.0]))
        node["rotation"] = _multiply_quaternions(
            current_rotation, _roll_quaternion(float(degrees))
        )

    for name, scale in (rest_scales or {}).items():
        if name not in node_by_name:
            raise ValueError(f"Required fixture bone is missing: {name}")
        if len(scale) != 3 or any(float(value) <= 0 for value in scale):
            raise ValueError(f"Bone scale must contain three positive values: {name}")
        nodes[node_by_name[name]]["scale"] = [float(value) for value in scale]

    spine_index = node_by_name.get("Spine")
    if spine_index is None:
        raise ValueError("Required fixture bone is missing: Spine.")
    nodes[spine_index]["children"] = [
        node_by_name["LeftUpperArm"],
        node_by_name["RightUpperArm"],
        node_by_name["Head"],
    ]

    skin = document["skins"][0]
    old_joints = list(skin["joints"])
    if len(old_joints) != len(JOINT_ORDER) or sorted(JOINT_ORDER) != list(
        range(len(old_joints))
    ):
        raise ValueError(
            "Fixture joint order does not match the generator permutation."
        )
    old_to_new = {
        old_index: new_index for new_index, old_index in enumerate(JOINT_ORDER)
    }

    primitive = document["meshes"][0]["primitives"][0]
    joints_accessor = document["accessors"][primitive["attributes"]["JOINTS_0"]]
    if joints_accessor["componentType"] != 5121 or joints_accessor["type"] != "VEC4":
        raise ValueError("Fixture JOINTS_0 must use unsigned-byte VEC4 data.")
    joints_view = document["bufferViews"][joints_accessor["bufferView"]]
    joints_offset = joints_view.get("byteOffset", 0) + joints_accessor.get(
        "byteOffset", 0
    )
    joints_stride = joints_view.get("byteStride", 4)
    for row in range(joints_accessor["count"]):
        for column in range(4):
            offset = joints_offset + row * joints_stride + column
            old_index = binary[offset]
            if old_index not in old_to_new:
                raise ValueError(f"JOINTS_0 contains unknown joint index {old_index}.")
            binary[offset] = old_to_new[old_index]

    global_transforms = _global_transforms(nodes)
    inverse_bind_accessor = document["accessors"][skin["inverseBindMatrices"]]
    if (
        inverse_bind_accessor["componentType"] != 5126
        or inverse_bind_accessor["type"] != "MAT4"
        or inverse_bind_accessor["count"] != len(old_joints)
    ):
        raise ValueError(
            "Fixture inverse-bind accessor is not a 15-matrix FLOAT MAT4 array."
        )
    inverse_bind_view = document["bufferViews"][inverse_bind_accessor["bufferView"]]
    inverse_bind_offset = (
        inverse_bind_view.get("byteOffset", 0)
        + inverse_bind_accessor.get("byteOffset", 0)
    )
    for new_index, old_index in enumerate(JOINT_ORDER):
        node_index = old_joints[old_index]
        matrix = _inverse_bind_matrix(global_transforms[node_index])
        struct.pack_into("<16f", binary, inverse_bind_offset + new_index * 64, *matrix)

    skin["joints"] = [old_joints[index] for index in JOINT_ORDER]
    for canonical_name, imported_name in NAME_MAP.items():
        nodes[node_by_name[canonical_name]]["name"] = imported_name
    document["animations"] = []
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
