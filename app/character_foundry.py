from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from pathlib import Path
from typing import Any

RECIPE_SCHEMA_VERSION = 1
MASTER_TEMPLATE_ID = "cartoon-studio.stylized-adult.v1"
FEMALE_MASTER_TEMPLATE_ID = "cartoon-studio.stylized-adult-female.v1"
MASTER_TEMPLATE_IDS = {MASTER_TEMPLATE_ID, FEMALE_MASTER_TEMPLATE_ID}
GENERATOR_VERSION = "0.6.0"


RIG_PROFILE_ID = "cartoon-studio.humanoid.v1"
CLOTHING_ASSET_ID = "cartoon-studio.casual-outfit.v1"

# Parent-first humanoid hierarchy. Local translations define the bind pose.
_BONES = (
    ("Hips", None, (0.0, 0.95, 0.0)),
    ("Spine", "Hips", (0.0, 0.50, 0.0)),
    ("Chest", "Spine", (0.0, 0.42, 0.0)),
    ("Neck", "Chest", (0.0, 0.28, 0.0)),
    ("Head", "Neck", (0.0, 0.18, 0.0)),
    ("LeftShoulder", "Chest", (-0.40, 0.08, 0.0)),
    ("LeftUpperArm", "LeftShoulder", (-0.16, -0.04, 0.0)),
    ("LeftLowerArm", "LeftUpperArm", (-0.07, -0.48, 0.0)),
    ("LeftHand", "LeftLowerArm", (-0.01, -0.42, 0.0)),
    ("RightShoulder", "Chest", (0.40, 0.08, 0.0)),
    ("RightUpperArm", "RightShoulder", (0.16, -0.04, 0.0)),
    ("RightLowerArm", "RightUpperArm", (0.07, -0.48, 0.0)),
    ("RightHand", "RightLowerArm", (0.01, -0.42, 0.0)),
    ("LeftUpperLeg", "Hips", (-0.205, -0.35, 0.0)),
    ("LeftLowerLeg", "LeftUpperLeg", (0.0, -0.62, 0.0)),
    ("LeftFoot", "LeftLowerLeg", (0.0, -0.36, -0.10)),
    ("RightUpperLeg", "Hips", (0.205, -0.35, 0.0)),
    ("RightLowerLeg", "RightUpperLeg", (0.0, -0.62, 0.0)),
    ("RightFoot", "RightLowerLeg", (0.0, -0.36, -0.10)),
)


def _component_bone_name(group: str, center: tuple[float, float, float]) -> str:
    side = "Left" if center[0] < 0.0 else "Right"
    return {
        "torso": "Chest",
        "neck": "Neck",
        "head": "Head",
        "ear": "Head",
        "eye": "Head",
        "nose": "Head",
        "mouth": "Head",
        "upper_arm": f"{side}UpperArm",
        "forearm": f"{side}LowerArm",
        "hand": f"{side}Hand",
        "thigh": f"{side}UpperLeg",
        "shin": f"{side}LowerLeg",
        "foot": f"{side}Foot",
        "shirt": "Chest",
        "shirt_sleeve": f"{side}UpperArm",
        "pants_waist": "Hips",
        "pants_thigh": f"{side}UpperLeg",
        "pants_shin": f"{side}LowerLeg",
    }[group]


def _bone_global_positions() -> dict[str, tuple[float, float, float]]:
    positions: dict[str, tuple[float, float, float]] = {}
    for name, parent, translation in _BONES:
        if parent is None:
            positions[name] = translation
        else:
            parent_position = positions[parent]
            positions[name] = tuple(
                parent_position[axis] + translation[axis] for axis in range(3)
            )
    return positions


_BONE_POSITIONS = _bone_global_positions()


def _component_skin_weights(
    group: str,
    center: tuple[float, float, float],
    point: tuple[float, float, float],
) -> tuple[tuple[str, float], ...]:
    side = "Left" if center[0] < 0.0 else "Right"
    candidates = {
        "torso": ("Hips", "Spine", "Chest"),
        "neck": ("Chest", "Neck", "Head"),
        "head": ("Head",),
        "ear": ("Head",),
        "eye": ("Head",),
        "nose": ("Head",),
        "mouth": ("Head",),
        "upper_arm": (f"{side}Shoulder", f"{side}UpperArm", f"{side}LowerArm"),
        "forearm": (f"{side}UpperArm", f"{side}LowerArm", f"{side}Hand"),
        "hand": (f"{side}LowerArm", f"{side}Hand"),
        "thigh": ("Hips", f"{side}UpperLeg", f"{side}LowerLeg"),
        "shin": (f"{side}UpperLeg", f"{side}LowerLeg", f"{side}Foot"),
        "foot": (f"{side}LowerLeg", f"{side}Foot"),
        "shirt": ("Hips", "Spine", "Chest"),
        "shirt_sleeve": (f"{side}Shoulder", f"{side}UpperArm", f"{side}LowerArm"),
        "pants_waist": ("Hips", f"{side}UpperLeg"),
        "pants_thigh": ("Hips", f"{side}UpperLeg", f"{side}LowerLeg"),
        "pants_shin": (f"{side}UpperLeg", f"{side}LowerLeg", f"{side}Foot"),
    }[group]
    sigma = 0.42
    weighted = []
    for name in candidates:
        joint = _BONE_POSITIONS[name]
        distance_squared = sum(
            (point[axis] - joint[axis]) ** 2 for axis in range(3)
        )
        weighted.append((name, math.exp(-distance_squared / (2.0 * sigma**2))))
    total = sum(weight for _, weight in weighted)
    normalized = [(name, weight / total) for name, weight in weighted]
    return tuple(sorted(normalized, key=lambda item: item[1], reverse=True)[:4])

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

_CLOTHING_COMPONENTS = (
    ("shirt", (0.0, 1.48, 0.0), (0.505, 0.675, 0.325)),
    ("shirt_sleeve", (-0.54, 1.66, 0.0), (0.185, 0.405, 0.185)),
    ("shirt_sleeve", (0.54, 1.66, 0.0), (0.185, 0.405, 0.185)),
    ("pants_waist", (0.0, 0.60, 0.0), (0.455, 0.205, 0.245)),
    ("pants_thigh", (-0.205, 0.58, 0.0), (0.222, 0.445, 0.222)),
    ("pants_thigh", (0.205, 0.58, 0.0), (0.222, 0.445, 0.222)),
    ("pants_shin", (-0.205, -0.04, 0.0), (0.172, 0.375, 0.178)),
    ("pants_shin", (0.205, -0.04, 0.0), (0.172, 0.375, 0.178)),
)

def _components_for_template(
    template_id: str,
) -> tuple[
    tuple[tuple[str, tuple[float, float, float], tuple[float, float, float]], ...],
    tuple[tuple[str, tuple[float, float, float], tuple[float, float, float]], ...],
]:
    if template_id == MASTER_TEMPLATE_ID:
        return _COMPONENTS, _CLOTHING_COMPONENTS
    if template_id != FEMALE_MASTER_TEMPLATE_ID:
        raise ValueError("Unknown master character template.")

    body = []
    for group, center, radii in _COMPONENTS:
        if group == "torso":
            body.extend((
                ("torso", (0.0, 1.58, 0.0), (0.405, 0.54, 0.275)),
                ("torso", (0.0, 1.12, 0.0), (0.49, 0.34, 0.30)),
            ))
        elif group == "upper_arm":
            side = -1.0 if center[0] < 0.0 else 1.0
            body.append((group, (side * 0.51, center[1], center[2]),
                         (0.155, radii[1], radii[2])))
        elif group == "thigh":
            side = -1.0 if center[0] < 0.0 else 1.0
            body.append((group, (side * 0.22, center[1], center[2]),
                         (0.22, 0.44, 0.21)))
        else:
            body.append((group, center, radii))

    clothing = []
    for group, center, radii in _CLOTHING_COMPONENTS:
        if group == "shirt":
            clothing.extend((
                ("shirt", (0.0, 1.58, 0.0), (0.435, 0.57, 0.305)),
                ("shirt", (0.0, 1.16, 0.0), (0.515, 0.36, 0.325)),
            ))
        elif group == "shirt_sleeve":
            side = -1.0 if center[0] < 0.0 else 1.0
            clothing.append((group, (side * 0.51, center[1], center[2]),
                             (0.17, radii[1], radii[2])))
        elif group == "pants_waist":
            clothing.append((group, center, (0.505, 0.22, 0.265)))
        elif group == "pants_thigh":
            side = -1.0 if center[0] < 0.0 else 1.0
            clothing.append((group, (side * 0.22, center[1], center[2]),
                             (0.237, 0.455, 0.232)))
        else:
            clothing.append((group, center, radii))
    return tuple(body), tuple(clothing)


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


def default_character_recipe(
    character_id: str = "character-foundry-preview",
    master_template_id: str = MASTER_TEMPLATE_ID,
) -> dict[str, Any]:
    if not isinstance(character_id, str) or not character_id.strip():
        raise ValueError("character_id must be a non-empty string.")
    if (
        not isinstance(master_template_id, str)
        or master_template_id not in MASTER_TEMPLATE_IDS
    ):
        raise ValueError("Unknown master character template.")
    return {
        "schema_version": RECIPE_SCHEMA_VERSION,
        "character_id": character_id,
        "master_template_id": master_template_id,
        "generator_version": GENERATOR_VERSION,
        "parameters": {name: 0.0 for name in MORPH_TARGETS},
        "expression_weights": {},
        "clothing_asset_ids": [CLOTHING_ASSET_ID],
        "hair_asset_id": None,
        "hair_style": "short",
        "hair_color": "#2b1b13",
        "accessory_asset_ids": [],
        "rig_profile_id": RIG_PROFILE_ID,
        "generated_asset": None,
    }


def validate_character_recipe(recipe: Any) -> dict[str, Any]:
    if not isinstance(recipe, dict):
        raise ValueError("Character recipe must be an object.")
    if recipe.get("schema_version") != RECIPE_SCHEMA_VERSION:
        raise ValueError("Unsupported character recipe schema version.")
    master_template_id = recipe.get("master_template_id")
    if master_template_id not in MASTER_TEMPLATE_IDS:
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
    normalized = default_character_recipe(character_id, master_template_id)
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
    unknown_clothing = set(normalized["clothing_asset_ids"]) - {CLOTHING_ASSET_ID}
    if unknown_clothing:
        raise ValueError(f"Unknown Foundry clothing assets: {', '.join(sorted(unknown_clothing))}.")
    for key in ("hair_asset_id", "rig_profile_id"):
        value = recipe.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{key} must be null or a non-empty string.")
        normalized[key] = value
    hair_style = recipe.get("hair_style", "short")
    if hair_style not in {"short", "bob", "long", "ponytail", "spiky", "curly", "mohawk"}:
        raise ValueError("Unsupported Foundry hairstyle.")
    hair_color = recipe.get("hair_color", "#2b1b13")
    if not isinstance(hair_color, str) or re.fullmatch(r"#[0-9a-fA-F]{6}", hair_color) is None:
        raise ValueError("hair_color must be a six-digit hexadecimal color.")
    normalized["hair_style"] = hair_style
    normalized["hair_color"] = hair_color.lower()
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
) -> tuple[
    list[tuple[float, float, float]], list[int],
    list[tuple[float, float, float]], list[tuple[float, float, float]]
]:
    vertices: list[tuple[float, float, float]] = []
    local: list[tuple[float, float, float]] = []
    normals: list[tuple[float, float, float]] = []
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
            normal = tuple(unit[axis] / radii[axis] for axis in range(3))
            normal_length = math.sqrt(sum(value * value for value in normal))
            normals.append(tuple(value / normal_length for value in normal))
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
            indices.extend((a, d, b, b, d, c))
    return vertices, indices, local, normals


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
    elif target == "torso_width" and group in {"torso", "shirt"}:
        dx = x * 0.18
    elif target == "shoulder_width" and group in {"torso", "upper_arm", "shirt", "shirt_sleeve"}:
        if group in {"torso", "shirt"}:
            dx = x * 0.15 * max(0.0, min(1.0, (y - 1.35) / 0.75))
        else:
            dx = math.copysign(0.075, center[0])
    elif target == "leg_length" and group in {
        "thigh", "shin", "foot", "pants_thigh", "pants_shin", "pants_waist"
    }:
        pivot = 0.95
        dy = (y - pivot) * 0.13
    return (dx, dy, dz)


def _build_geometry(
    components: tuple[tuple[str, tuple[float, float, float], tuple[float, float, float]], ...]
) -> tuple[
    list[tuple[float, float, float]], list[int],
    dict[str, list[tuple[float, float, float]]], list[tuple[tuple[str, float], ...]],
    list[tuple[float, float, float]]
]:
    # Build the torso, head, neck and limbs as one smooth implicit surface.
    # Facial details remain separate meshes so their silhouettes stay crisp.
    core = tuple(item for item in components if item[0] not in {"eye", "nose", "mouth"})
    details = tuple(item for item in components if item[0] in {"eye", "nose", "mouth"})
    step = 0.085
    padding = 0.12
    lower = [min(c[1][a] - c[2][a] for c in core) - padding for a in range(3)]
    upper = [max(c[1][a] + c[2][a] for c in core) + padding for a in range(3)]
    axes = [
        [
            lower[a] + i * step
            for i in range(int(math.ceil((upper[a] - lower[a]) / step)) + 1)
        ]
        for a in range(3)
    ]
    nx, ny, nz = (len(axis) for axis in axes)

    def field(point: tuple[float, float, float]) -> float:
        value = float("inf")
        for _, center, radii in core:
            q = math.sqrt(sum(((point[a]-center[a])/radii[a])**2 for a in range(3)))
            distance = (q - 1.0) * min(radii)
            k = 0.20
            h = max(k - abs(value-distance), 0.0) / k if math.isfinite(value) else 0.0
            value = min(value, distance) - h*h*k*0.25 if math.isfinite(value) else distance
        return value

    samples = [field((x,y,z)) for z in axes[2] for y in axes[1] for x in axes[0]]
    def grid_id(x: int, y: int, z: int) -> int:
        return (z * ny + y) * nx + x

    # Estimate the implicit-field gradient from the already sampled grid.
    # Interpolating these gradients avoids six additional field evaluations
    # for every generated surface vertex.
    gradient_cache: dict[int, tuple[float, float, float]] = {}

    def grid_gradient(index: int) -> tuple[float, float, float]:
        cached = gradient_cache.get(index)
        if cached is not None:
            return cached
        z, remainder = divmod(index, nx * ny)
        y, x = divmod(remainder, nx)
        coordinates = (x, y, z)
        dimensions = (nx, ny, nz)
        gradient = []
        for axis in range(3):
            low = max(coordinates[axis] - 1, 0)
            high = min(coordinates[axis] + 1, dimensions[axis] - 1)
            low_point = list(coordinates)
            high_point = list(coordinates)
            low_point[axis] = low
            high_point[axis] = high
            low_id = grid_id(*low_point)
            high_id = grid_id(*high_point)
            distance = axes[axis][high] - axes[axis][low]
            gradient.append(
                (samples[high_id] - samples[low_id]) / distance
                if distance > 0.0 else 0.0
            )
        result = tuple(gradient)
        gradient_cache[index] = result
        return result

    positions: list[tuple[float,float,float]] = []
    indices: list[int] = []
    normals: list[tuple[float,float,float]] = []
    edge_vertices: dict[tuple[int,int],int] = {}
    tetrahedra = ((0,5,1,6),(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6))
    cube_offsets = ((0,0,0),(1,0,0),(0,1,0),(1,1,0),(0,0,1),(1,0,1),(0,1,1),(1,1,1))
    tetra_edges = ((0,1),(0,2),(0,3),(1,2),(1,3),(2,3))

    def vertex_for(
        a: int,
        b: int,
        pa: tuple[float, float, float],
        pb: tuple[float, float, float],
        va: float,
        vb: float,
    ) -> int:
        key = (min(a,b),max(a,b))
        if key in edge_vertices:
            return edge_vertices[key]
        t = va / (va-vb) if abs(va-vb)>1e-12 else 0.5
        point = tuple(pa[i] + t*(pb[i]-pa[i]) for i in range(3))
        index = len(positions)
        positions.append(point)
        gradient_a = grid_gradient(a)
        gradient_b = grid_gradient(b)
        gradient = tuple(
            gradient_a[axis] + t * (gradient_b[axis] - gradient_a[axis])
            for axis in range(3)
        )
        length = math.sqrt(sum(v*v for v in gradient)) or 1.0
        normals.append(tuple(v/length for v in gradient))
        edge_vertices[key] = index
        return index

    for z in range(nz-1):
        for y in range(ny-1):
            for x in range(nx-1):
                ids = [grid_id(x+o[0],y+o[1],z+o[2]) for o in cube_offsets]
                vals = [samples[i] for i in ids]
                if min(vals) > 0 or max(vals) < 0:
                    continue
                pts = [(axes[0][x+o[0]],axes[1][y+o[1]],axes[2][z+o[2]]) for o in cube_offsets]
                for tet in tetrahedra:
                    crossings = []
                    for ea,eb in tetra_edges:
                        ia,ib = tet[ea],tet[eb]
                        if (vals[ia] < 0) != (vals[ib] < 0):
                            crossings.append(vertex_for(ids[ia],ids[ib],pts[ia],pts[ib],vals[ia],vals[ib]))
                    if len(crossings) == 3:
                        indices.extend(crossings)
                    elif len(crossings) == 4:
                        center = tuple(sum(positions[i][a] for i in crossings)/4 for a in range(3))
                        n = tuple(sum(normals[i][a] for i in crossings) for a in range(3))
                        nl = math.sqrt(sum(v*v for v in n)) or 1.0
                        n = tuple(v/nl for v in n)
                        u = tuple(positions[crossings[0]][a]-center[a] for a in range(3))
                        ul = math.sqrt(sum(v*v for v in u)) or 1.0
                        u = tuple(v/ul for v in u)
                        v = (n[1]*u[2]-n[2]*u[1],n[2]*u[0]-n[0]*u[2],n[0]*u[1]-n[1]*u[0])
                        ordered = sorted(crossings,key=lambda i: math.atan2(
                            sum((positions[i][a]-center[a])*v[a] for a in range(3)),
                            sum((positions[i][a]-center[a])*u[a] for a in range(3))))
                        indices.extend((ordered[0],ordered[1],ordered[2],ordered[0],ordered[2],ordered[3]))

    # Retain distinct facial forms as conventional ellipsoids.
    for group, center, radii in details:
        component, faces, _, component_normals = _ellipsoid(center,radii)
        offset = len(positions)
        positions.extend(component)
        normals.extend(component_normals)
        indices.extend(offset+i for i in faces)

    # Marching-tetrahedra edge order is not a winding guarantee. Orient every
    # triangle against its interpolated vertex normals for reliable GLB culling.
    for face_offset in range(0, len(indices), 3):
        first, second, third = indices[face_offset:face_offset + 3]
        a, b, c = positions[first], positions[second], positions[third]
        ab = tuple(b[axis] - a[axis] for axis in range(3))
        ac = tuple(c[axis] - a[axis] for axis in range(3))
        face_normal = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        expected = tuple(
            normals[first][axis] + normals[second][axis] + normals[third][axis]
            for axis in range(3)
        )
        if sum(face_normal[axis] * expected[axis] for axis in range(3)) < 0.0:
            indices[face_offset + 1], indices[face_offset + 2] = third, second

    deltas = {name: [] for name in MORPH_TARGETS}
    vertex_weights = []
    for point in positions:
        candidates = []
        for group, center, radii in components:
            unit = tuple((point[a]-center[a])/radii[a] for a in range(3))
            distance = abs(math.sqrt(sum(v*v for v in unit))-1.0)
            candidates.append((distance,group,center,radii,unit))
        candidates.sort(key=lambda item:item[0])
        chosen = candidates[:3]
        influence = [math.exp(-item[0]*8.0) for item in chosen]
        total = sum(influence) or 1.0
        for target in MORPH_TARGETS:
            delta = [0.0,0.0,0.0]
            for weight,item in zip(influence,chosen,strict=True):
                _,group,center,radii,unit = item
                change = _morph_delta(target,group,center,radii,unit,point)
                for axis in range(3):
                    delta[axis] += change[axis]*weight/total
            deltas[target].append(tuple(delta))
        blended: dict[str,float] = {}
        for weight,item in zip(influence,chosen,strict=True):
            _,group,center,_,_ = item
            for bone,bone_weight in _component_skin_weights(group,center,point):
                blended[bone] = blended.get(bone,0.0) + weight*bone_weight/total
        strongest = sorted(
            blended.items(), key=lambda pair: pair[1], reverse=True
        )[:4]
        strongest_total = sum(weight for _, weight in strongest)
        if strongest_total <= 0.0:
            strongest = [("Hips", 1.0)]
        else:
            strongest = [
                (bone, weight / strongest_total)
                for bone, weight in strongest
            ]
        vertex_weights.append(tuple(strongest))
    return positions,indices,deltas,vertex_weights,normals


def _build_hair_geometry(style: str) -> tuple[
    list[tuple[float, float, float]], list[int],
    dict[str, list[tuple[float, float, float]]],
    list[tuple[tuple[str, float], ...]], list[tuple[float, float, float]]
]:
    """Build a separate, head-skinned hairstyle mesh from editable recipe data."""
    shapes = [(0.0, 2.94, 0.015, 0.445, 0.245, 0.385)]
    if style in {"short", "bob", "long", "ponytail", "curly"}:
        shapes.extend(((-0.355, 2.72, 0.015, 0.105, 0.25, 0.14),
                       (0.355, 2.72, 0.015, 0.105, 0.25, 0.14)))
    if style == "bob":
        shapes.extend(((-0.365, 2.43, 0.025, 0.12, 0.40, 0.16),
                       (0.365, 2.43, 0.025, 0.12, 0.40, 0.16),
                       (0.0, 2.40, 0.22, 0.36, 0.39, 0.16)))
    elif style == "long":
        shapes.extend(((-0.37, 2.15, 0.02, 0.115, 0.72, 0.15),
                       (0.37, 2.15, 0.02, 0.115, 0.72, 0.15),
                       (0.0, 2.12, 0.22, 0.35, 0.70, 0.15)))
    elif style == "ponytail":
        shapes.extend(((0.32, 2.48, 0.18, 0.16, 0.18, 0.16),
                       (0.38, 2.02, 0.23, 0.14, 0.55, 0.14),
                       (0.37, 2.68, 0.18, 0.17, 0.08, 0.17)))
    elif style == "spiky":
        for index in range(7):
            x = (index - 3) * 0.105
            shapes.append((x, 3.12 - abs(x) * 0.12, 0.0, 0.075, 0.22, 0.075))
    elif style == "curly":
        for row in range(2):
            for index in range(5):
                x = (index - 2) * 0.16
                shapes.append((x, 3.02 - row * 0.13, 0.0, 0.105, 0.115, 0.11))
    elif style == "mohawk":
        shapes = [(0.0, 2.94, 0.015, 0.445, 0.245, 0.385)]
        for index in range(5):
            shapes.append((0.0, 3.10 + index * 0.015, 0.0, 0.115, 0.18, 0.16))
    positions: list[tuple[float, float, float]] = []
    indices: list[int] = []
    normals: list[tuple[float, float, float]] = []
    for x, y, z, rx, ry, rz in shapes:
        vertices, faces, _, vertex_normals = _ellipsoid((x, y, z), (rx, ry, rz), 10, 16)
        offset = len(positions)
        positions.extend(vertices)
        normals.extend(vertex_normals)
        indices.extend(offset + index for index in faces)
    morphs = {name: [] for name in MORPH_TARGETS}
    weights = []
    for point in positions:
        for name in MORPH_TARGETS:
            morphs[name].append((point[0] * 0.16, 0.0, 0.0) if name == "head_width" else (0.0, 0.0, 0.0))
        weights.append((("Head", 1.0),))
    return positions, indices, morphs, weights, normals


def build_master_character_glb(recipe: dict[str, Any] | None = None) -> bytes:
    normalized_recipe = validate_character_recipe(
        recipe if recipe is not None else default_character_recipe()
    )
    body_components, clothing_components = _components_for_template(
        normalized_recipe["master_template_id"]
    )
    body = _build_geometry(body_components)
    hair = _build_hair_geometry(normalized_recipe["hair_style"])
    clothing = (
        _build_geometry(clothing_components)
        if CLOTHING_ASSET_ID in normalized_recipe["clothing_asset_ids"]
        else None
    )
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

    bone_names = [bone[0] for bone in _BONES]
    bone_indices = {name: index for index, name in enumerate(bone_names)}

    def make_primitive(
        geometry: tuple[
            list[tuple[float, float, float]], list[int],
            dict[str, list[tuple[float, float, float]]], list[str],
            list[tuple[float, float, float]]
        ],
        material_index: int,
    ) -> dict[str, Any]:
        positions, indices, morphs, vertex_weights, normals = geometry
        flat_positions = [coordinate for point in positions for coordinate in point]
        mins = [min(point[axis] for point in positions) for axis in range(3)]
        maxs = [max(point[axis] for point in positions) for axis in range(3)]
        position_accessor = add_accessor(
            struct.pack(f"<{len(flat_positions)}f", *flat_positions),
            5126, len(positions), "VEC3", 34962, (mins, maxs)
        )
        flat_normals = [coordinate for normal in normals for coordinate in normal]
        normal_accessor = add_accessor(
            struct.pack(f"<{len(flat_normals)}f", *flat_normals),
            5126, len(normals), "VEC3", 34962
        )
        index_accessor = add_accessor(
            struct.pack(f"<{len(indices)}I", *indices),
            5125, len(indices), "SCALAR", 34963
        )
        target_accessors = []
        for name in MORPH_TARGETS:
            flat = [coordinate for point in morphs[name] for coordinate in point]
            target_accessors.append({
                "POSITION": add_accessor(
                    struct.pack(f"<{len(flat)}f", *flat),
                    5126, len(positions), "VEC3", 34962
                )
            })
        joint_values = []
        weight_values = []
        for influences in vertex_weights:
            padded = list(influences[:4])
            padded.extend([("Hips", 0.0)] * (4 - len(padded)))
            joint_values.extend(bone_indices[name] for name, _ in padded)
            weight_values.extend(weight for _, weight in padded)
        joints_accessor = add_accessor(
            struct.pack(f"<{len(joint_values)}H", *joint_values),
            5123, len(positions), "VEC4", 34962
        )
        weights_accessor = add_accessor(
            struct.pack(f"<{len(weight_values)}f", *weight_values),
            5126, len(positions), "VEC4", 34962
        )
        return {
            "attributes": {
                "POSITION": position_accessor,
                "NORMAL": normal_accessor,
                "JOINTS_0": joints_accessor,
                "WEIGHTS_0": weights_accessor,
            },
            "indices": index_accessor,
            "material": material_index,
            "mode": 4,
            "targets": target_accessors,
        }

    primitives = [make_primitive(body, 0)]
    if clothing is not None:
        primitives.append(make_primitive(clothing, 1))
    hair_material_index = 2 if clothing is not None else 1
    primitives.append(make_primitive(hair, hair_material_index))

    bone_node_start = 1
    bone_node_indices = {
        name: bone_node_start + index for index, name in enumerate(bone_names)
    }
    global_positions: dict[str, tuple[float, float, float]] = {}
    bone_nodes: list[dict[str, Any]] = []
    bone_children: dict[str, list[int]] = {name: [] for name in bone_names}
    for name, parent, translation in _BONES:
        if parent is None:
            global_positions[name] = translation
        else:
            parent_position = global_positions[parent]
            global_positions[name] = tuple(
                parent_position[axis] + translation[axis] for axis in range(3)
            )
            bone_children[parent].append(bone_node_indices[name])
        bone_nodes.append({"name": name, "translation": list(translation)})
    for name, _, _ in _BONES:
        children = bone_children[name]
        if children:
            bone_nodes[bone_names.index(name)]["children"] = children

    inverse_bind_values: list[float] = []
    for name in bone_names:
        x, y, z = global_positions[name]
        inverse_bind_values.extend((
            1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            -x, -y, -z, 1.0,
        ))
    inverse_bind_accessor = add_accessor(
        struct.pack(f"<{len(inverse_bind_values)}f", *inverse_bind_values),
        5126, len(bone_names), "MAT4"
    )

    materials = [{
        "name": "WarmCartoonSkin",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.82, 0.53, 0.37, 1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.82,
        },
    }]
    if clothing is not None:
        materials.append({
            "name": "FoundryCasualCloth",
            "pbrMetallicRoughness": {
                "baseColorFactor": [0.12, 0.34, 0.72, 1.0],
                "metallicFactor": 0.0,
                "roughnessFactor": 0.92,
            },
        })
    hair_color = normalized_recipe["hair_color"]
    materials.append({
        "name": "FoundryHair",
        "pbrMetallicRoughness": {
            "baseColorFactor": [int(hair_color[i:i + 2], 16) / 255 for i in (1, 3, 5)] + [1.0],
            "metallicFactor": 0.0,
            "roughnessFactor": 0.88,
        },
    })

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": f"Cartoon Studio Character Foundry {GENERATOR_VERSION}",
            "extras": {"masterTemplate": normalized_recipe["master_template_id"]},
        },
        "scene": 0,
        "scenes": [{"nodes": [0, bone_node_start]}],
        "nodes": [{
            "name": (
                "CartoonStudio_StylizedAdultFemale"
                if normalized_recipe["master_template_id"] == FEMALE_MASTER_TEMPLATE_ID
                else "CartoonStudio_StylizedAdultMale"
            ),
            "mesh": 0, "skin": 0
        }, *bone_nodes],
        "skins": [{
            "name": "CartoonStudio_Humanoid_v1",
            "inverseBindMatrices": inverse_bind_accessor,
            "skeleton": bone_node_start,
            "joints": [bone_node_indices[name] for name in bone_names],
        }],
        "meshes": [{
            "name": (
                "StylizedAdultFemale_MasterMesh"
                if normalized_recipe["master_template_id"] == FEMALE_MASTER_TEMPLATE_ID
                else "StylizedAdultMale_MasterMesh"
            ),
            "weights": [normalized_recipe["parameters"][name] for name in MORPH_TARGETS],
            "extras": {
                "targetNames": list(MORPH_TARGETS),
                "clothingAssetIds": normalized_recipe["clothing_asset_ids"],
                "hairStyle": normalized_recipe["hair_style"],
                "hairColor": normalized_recipe["hair_color"],
            },
            "primitives": primitives,
        }],
        "materials": materials,
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
    recipe: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    normalized_recipe = validate_character_recipe(
        recipe if recipe is not None else default_character_recipe(character_id)
    )
    glb_bytes = build_master_character_glb(normalized_recipe)
    output.write_bytes(glb_bytes)
    normalized_recipe["generated_asset"] = {
        "filename": output.name,
        "sha256": hashlib.sha256(glb_bytes).hexdigest(),
        "format": "glb",
        "generator_version": GENERATOR_VERSION,
        "morph_targets": list(MORPH_TARGETS),
        "morph_weights": [normalized_recipe["parameters"][name] for name in MORPH_TARGETS],
        "rig_profile_id": RIG_PROFILE_ID,
        "bone_names": [bone[0] for bone in _BONES],
        "clothing_asset_ids": normalized_recipe["clothing_asset_ids"],
        "hair_style": normalized_recipe["hair_style"],
        "hair_color": normalized_recipe["hair_color"],
    }
    recipe_output = Path(recipe_path) if recipe_path else output.with_suffix(".recipe.json")
    recipe_output.parent.mkdir(parents=True, exist_ok=True)
    recipe_output.write_text(
        json.dumps(normalized_recipe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output, recipe_output
