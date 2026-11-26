from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from typing import Any

RECIPE_SCHEMA_VERSION = 1
MASTER_TEMPLATE_ID = "cartoon-studio.stylized-adult.v1"
GENERATOR_VERSION = "0.1.0"

MORPH_TARGETS = (
    "head_width",
    "jaw_width",
    "chin_length",
    "cheek_fullness",
    "eye_spacing",
    "nose_width",
    "mouth_width",
    "torso_width",
    "shoulder_width",
    "leg_length",
)

# Each component is an ellipsoid with its own semantic region. The surfaces are
# combined into one indexed mesh; morph targets therefore deform real vertices.
_COMPONENTS = (
    ("torso", (0.0, 1.48, 0.0), (0.47, 0.64, 0.29)),
    ("neck", (0.0, 2.12, 0.0), (0.17, 0.22, 0.16)),
    ("head", (0.0, 2.62, 0.0), (0.43, 0.53, 0.37)),
    ("ear", (-0.415, 2.64, 0.0), (0.095, 0.145, 0.075)),
    ("ear", (0.415, 2.64, 0.0), (0.095, 0.145, 0.075)),
    ("eye", (-0.155, 2.76, -0.325), (0.083, 0.088, 0.052)),
    ("eye", (0.155, 2.76, -0.325), (0.083, 0.088, 0.052)),
    ("nose", (0.0, 2.61, -0.365), (0.09, 0.145, 0.085)),
    ("mouth", (0.0, 2.405, -0.337), (0.145, 0.043, 0.035)),
    ("upper_arm", (-0.54, 1.66, 0.0), (0.17, 0.39, 0.17)),
    ("upper_arm", (0.54, 1.66, 0.0), (0.17, 0.39, 0.17)),
    ("forearm", (-0.61, 1.13, 0.0), (0.135, 0.34, 0.135)),
    ("forearm", (0.61, 1.13, 0.0), (0.135, 0.34, 0.135)),
    ("hand", (-0.62, 0.72, -0.005), (0.14, 0.16, 0.12)),
    ("hand", (0.62, 0.72, -0.005), (0.14, 0.16, 0.12)),
    ("thigh", (-0.205, 0.58, 0.0), (0.205, 0.43, 0.205)),
    ("thigh", (0.205, 0.58, 0.0), (0.205, 0.43, 0.205)),
    ("shin", (-0.205, -0.04, 0.0), (0.155, 0.36, 0.16)),
    ("shin", (0.205, -0.04, 0.0), (0.155, 0.36, 0.16)),
    ("foot", (-0.205, -0.39, -0.105), (0.17, 0.13, 0.28)),
    ("foot", (0.205, -0.39, -0.105), (0.17, 0.13, 0.28)),
)

_RECIPE_PARAMETERS = {
    "head_width": (-1.0, 1.0),
    "jaw_width": (-1.0, 1.0),
    "chin_length": (-1.0, 1.0),
    "cheek_fullness": (-1.0, 1.0),
    "eye_spacing": (-1.0, 1.0),
    "nose_width": (-1.0, 1.0),
    "mouth_width": (-1.0, 1.0),
    "torso_width": (-1.0, 1.0),
    "shoulder_width": (-1.0, 1.0),
    "leg_length": (-1.0, 1.0),
}


def default_character_recipe(character_id: str = "character-foundry-preview") -> dict[str, Any]:
    if not isinstance(character_id, str) or not character_id.strip():
        raise ValueError("character_id must be a non-empty string.")
    return {
        "schema_version": RECIPE_SCHEMA_VERSION,
        "character_id": character_id,
        "master_template_id": MASTER_TEMPLATE_ID,
        "generator_version": GENERATOR_VERSION,
        "parameters": {name: 0.0 for name in MORPH_TARGETS},
        "expression_weights": {},
        "clothing_asset_ids": [],
        "hair_asset_id": None,
        "accessory_asset_ids": [],
        "rig_profile_id": None,
        "generated_asset": None,
    }


def validate_character_recipe(recipe: Any) -> dict[str, Any]:
    if not isinstance(recipe, dict):
        raise ValueError("Character recipe must be an object.")
    if recipe.get("schema_version") != RECIPE_SCHEMA_VERSION:
        raise ValueError("Unsupported character recipe schema version.")
    if recipe.get("master_template_id") != MASTER_TEMPLATE_ID:
        raise ValueError("Unknown master character template.")
    character_id = recipe.get("character_id")
    if not isinstance(character_id, str) or not character_id.strip():
        raise ValueError("Character recipe requires a non-empty character_id.")
    parameters = recipe.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("Character recipe parameters must be an object.")
    unknown = set(parameters) - set(_RECIPE_PARAMETERS)
    if unknown:
        raise ValueError(f"Unknown character parameters: {', '.join(sorted(unknown))}.")
    normalized = default_character_recipe(character_id)
    for name, value in parameters.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Parameter {name} must be numeric.")
        lower, upper = _RECIPE_PARAMETERS[name]
        numeric = float(value)
        if not math.isfinite(numeric) or not lower <= numeric <= upper:
            raise ValueError(f"Parameter {name} must be between {lower} and {upper}.")
        normalized["parameters"][name] = numeric
    for key in ("clothing_asset_ids", "accessory_asset_ids"):
        values = recipe.get(key, [])
        if not isinstance(values, list) or any(
            not isinstance(item, str) or not item.strip() for item in values
        ):
            raise ValueError(f"{key} must be a list of non-empty asset IDs.")
        normalized[key] = list(values)
    for key in ("hair_asset_id", "rig_profile_id"):
        value = recipe.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{key} must be null or a non-empty string.")
        normalized[key] = value
    expression_weights = recipe.get("expression_weights", {})
    if not isinstance(expression_weights, dict):
        raise ValueError("expression_weights must be an object.")
    normalized["expression_weights"] = dict(expression_weights)
    normalized["generated_asset"] = recipe.get("generated_asset")
    return normalized


def _ellipsoid(
    center: tuple[float, float, float],
    radii: tuple[float, float, float],
    rings: int = 12,
    segments: int = 20,
) -> tuple[list[tuple[float, float, float]], list[int], list[tuple[float, float, float]]]:
    vertices: list[tuple[float, float, float]] = []
    local: list[tuple[float, float, float]] = []
    for ring in range(rings + 1):
        latitude = -math.pi / 2 + math.pi * ring / rings
        for segment in range(segments):
            longitude = 2 * math.pi * segment / segments
            unit = (
                math.cos(latitude) * math.cos(longitude),
                math.sin(latitude),
                math.cos(latitude) * math.sin(longitude),
            )
            local.append(unit)
            vertices.append(tuple(
                center[axis] + radii[axis] * unit[axis] for axis in range(3)
            ))
    indices: list[int] = []
    for ring in range(rings):
        for segment in range(segments):
            a = ring * segments + segment
            b = ring * segments + (segment + 1) % segments
            c = (ring + 1) * segments + (segment + 1) % segments
            d = (ring + 1) * segments + segment
            indices.extend((a, b, d, b, c, d))
    return vertices, indices, local


def _morph_delta(
    target: str,
    group: str,
    center: tuple[float, float, float],
    radii: tuple[float, float, float],
    unit: tuple[float, float, float],
    point: tuple[float, float, float],
) -> tuple[float, float, float]:
    x, y, z = point
    nx, ny, nz = unit
    dx = dy = dz = 0.0
    if target == "head_width" and group in {"head", "ear"}:
        dx = x * 0.16
    elif target == "jaw_width" and group == "head" and ny < 0.18:
        dx = x * 0.24 * min(1.0, (0.18 - ny) / 0.85)
    elif target == "chin_length" and group == "head" and ny < -0.22:
        dy = -0.15 * min(1.0, (-ny - 0.22) / 0.78)
    elif (
        target == "cheek_fullness" and group == "head"
        and -0.05 < ny < 0.52 and nz < -0.35 and abs(nx) > 0.28
    ):
        dz = -0.075
    elif target == "eye_spacing" and group == "eye":
        dx = math.copysign(0.075, center[0])
    elif target == "nose_width" and group == "nose":
        dx = x * 0.32
    elif target == "mouth_width" and group == "mouth":
        dx = x * 0.30
    elif target == "torso_width" and group == "torso":
        dx = x * 0.18
    elif target == "shoulder_width" and group in {"torso", "upper_arm"}:
        if group == "torso":
            dx = x * 0.15 * max(0.0, min(1.0, (y - 1.35) / 0.75))
        else:
            dx = math.copysign(0.075, center[0])
    elif target == "leg_length" and group in {"thigh", "shin", "foot"}:
        pivot = 0.95
        dy = (y - pivot) * 0.13
    return (dx, dy, dz)


def _build_geometry() -> tuple[
    list[tuple[float, float, float]], list[int],
    dict[str, list[tuple[float, float, float]]]
]:
    positions: list[tuple[float, float, float]] = []
    indices: list[int] = []
    deltas = {name: [] for name in MORPH_TARGETS}
    for group, center, radii in _COMPONENTS:
        component, component_indices, local = _ellipsoid(center, radii)
        offset = len(positions)
        positions.extend(component)
        indices.extend(offset + index for index in component_indices)
        for target in MORPH_TARGETS:
            deltas[target].extend(
                _morph_delta(target, group, center, radii, unit, point)
                for unit, point in zip(local, component, strict=True)
            )
    return positions, indices, deltas


def build_master_character_glb() -> bytes:
    positions, indices, morphs = _build_geometry()
    binary = bytearray()
    buffer_views: list[dict[str, Any]] = []
    accessors: list[dict[str, Any]] = []

    def add_view(payload: bytes, target: int | None = None) -> int:
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        binary.extend(payload)
        view: dict[str, Any] = {
            "buffer": 0,
            "byteOffset": offset,
            "byteLength": len(payload),
        }
        if target is not None:
            view["target"] = target
        buffer_views.append(view)
        return len(buffer_views) - 1

    def add_accessor(
        payload: bytes,
        component_type: int,
        count: int,
        accessor_type: str,
        target: int | None = None,
        bounds: tuple[list[float], list[float]] | None = None,
    ) -> int:
        view_index = add_view(payload, target)
        accessor: dict[str, Any] = {
            "bufferView": view_index,
            "componentType": component_type,
            "count": count,
            "type": accessor_type,
        }
        if bounds is not None:
            accessor["min"], accessor["max"] = bounds
        accessors.append(accessor)
        return len(accessors) - 1

    flat_positions = [coordinate for point in positions for coordinate in point]
    position_bytes = struct.pack(f"<{len(flat_positions)}f", *flat_positions)
    mins = [min(point[axis] for point in positions) for axis in range(3)]
    maxs = [max(point[axis] for point in positions) for axis in range(3)]
    position_accessor = add_accessor(
        position_bytes, 5126, len(positions), "VEC3", 34962, (mins, maxs)
    )
    index_bytes = struct.pack(f"<{len(indices)}I", *indices)
    index_accessor = add_accessor(index_bytes, 5125, len(indices), "SCALAR", 34963)

    target_accessors = []
    for name in MORPH_TARGETS:
        flat = [coordinate for point in morphs[name] for coordinate in point]
        payload = struct.pack(f"<{len(flat)}f", *flat)
        target_accessors.append({
            "POSITION": add_accessor(payload, 5126, len(positions), "VEC3", 34962)
        })

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": f"Cartoon Studio Character Foundry {GENERATOR_VERSION}",
            "extras": {"masterTemplate": MASTER_TEMPLATE_ID},
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "CartoonStudio_StylizedAdult", "mesh": 0}],
        "meshes": [{
            "name": "StylizedAdult_MasterMesh",
            "weights": [0.0] * len(MORPH_TARGETS),
            "extras": {"targetNames": list(MORPH_TARGETS)},
            "primitives": [{
                "attributes": {"POSITION": position_accessor},
                "indices": index_accessor,
                "material": 0,
                "mode": 4,
                "targets": target_accessors,
            }],
        }],
        "materials": [{
            "name": "WarmCartoonSkin",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.82, 0.53, 0.37, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.82,
            },
        }],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    json_chunk = json.dumps(gltf, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    while len(json_chunk) % 4:
        json_chunk += b" "
    while len(binary) % 4:
        binary.append(0)
    total_length = 12 + 8 + len(json_chunk) + 8 + len(binary)
    return b"".join((
        struct.pack("<4sII", b"glTF", 2, total_length),
        struct.pack("<I4s", len(json_chunk), b"JSON"),
        json_chunk,
        struct.pack("<I4s", len(binary), b"BIN\x00"),
        bytes(binary),
    ))


def write_master_character(
    output_path: str | Path,
    recipe_path: str | Path | None = None,
    character_id: str = "character-foundry-preview",
) -> tuple[Path, Path]:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    glb_bytes = build_master_character_glb()
    output.write_bytes(glb_bytes)
    recipe = default_character_recipe(character_id)
    recipe["generated_asset"] = {
        "filename": output.name,
        "sha256": __import__("hashlib").sha256(glb_bytes).hexdigest(),
        "format": "glb",
        "generator_version": GENERATOR_VERSION,
        "morph_targets": list(MORPH_TARGETS),
    }
    recipe_output = Path(recipe_path) if recipe_path else output.with_suffix(".recipe.json")
    recipe_output.parent.mkdir(parents=True, exist_ok=True)
    recipe_output.write_text(
        json.dumps(recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output, recipe_output
