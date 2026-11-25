from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REQUIRED_HUMANOID_BONES: dict[str, frozenset[str]] = {
    "hips": frozenset({"hips", "pelvis"}),
    "spine": frozenset({"spine", "spine1", "spine01", "spine001"}),
    "head": frozenset({"head"}),
    "leftUpperLeg": frozenset(
        {"leftupleg", "leftupperleg", "leftthigh", "uplegl", "thighl", "upperlegl"}
    ),
    "leftLowerLeg": frozenset(
        {"leftleg", "leftlowerleg", "leftcalf", "calfl", "lowerlegl", "shinl"}
    ),
    "leftFoot": frozenset({"leftfoot", "footl"}),
    "rightUpperLeg": frozenset(
        {"rightupleg", "rightupperleg", "rightthigh", "uplegr", "thighr", "upperlegr"}
    ),
    "rightLowerLeg": frozenset(
        {"rightleg", "rightlowerleg", "rightcalf", "calfr", "lowerlegr", "shinr"}
    ),
    "rightFoot": frozenset({"rightfoot", "footr"}),
    "leftUpperArm": frozenset({"leftarm", "leftupperarm", "upperarml", "arml"}),
    "leftLowerArm": frozenset({"leftforearm", "leftlowerarm", "forearml", "lowerarml"}),
    "leftHand": frozenset({"lefthand", "handl"}),
    "rightUpperArm": frozenset({"rightarm", "rightupperarm", "upperarmr", "armr"}),
    "rightLowerArm": frozenset({"rightforearm", "rightlowerarm", "forearmr", "lowerarmr"}),
    "rightHand": frozenset({"righthand", "handr"}),
}
_PREFIXES = ("mixamorig", "armature", "def", "jnt", "bone", "jbipc", "jbip")
_ALIAS_TO_CANONICAL = {
    alias: canonical
    for canonical, aliases in REQUIRED_HUMANOID_BONES.items()
    for alias in aliases
}


def _normalise_bone_name(value: Any) -> str:
    leaf = re.split(r"[/|:]", str(value).strip())[-1]
    normalised = re.sub(r"[^a-z0-9]", "", leaf.casefold())
    for prefix in _PREFIXES:
        candidate = normalised.removeprefix(prefix)
        if candidate in _ALIAS_TO_CANONICAL:
            return candidate
    return normalised


def analyze_rig(inspection: Mapping[str, Any]) -> dict[str, Any]:
    """Summarise humanoid bone-name coverage without claiming retarget readiness."""
    skeleton_count = max(0, int(inspection.get("skeleton_count", 0) or 0))
    raw_skeletons = inspection.get("skeletons", [])
    skeletons = raw_skeletons if isinstance(raw_skeletons, list) else []
    required = len(REQUIRED_HUMANOID_BONES)
    if skeleton_count == 0:
        return {
            "status": "no_skeleton", "skeleton_count": 0, "bone_count": 0,
            "required_bone_count": required, "matched_bone_count": 0,
            "bone_mapping": {}, "missing_bones": list(REQUIRED_HUMANOID_BONES),
            "retargeting_ready": False,
            "retargeting_note": "No Skeleton3D was found in the imported model.",
        }
    if not skeletons:
        return {
            "status": "skeleton_details_unavailable", "skeleton_count": skeleton_count,
            "bone_count": 0, "required_bone_count": required, "matched_bone_count": 0,
            "bone_mapping": {}, "missing_bones": list(REQUIRED_HUMANOID_BONES),
            "retargeting_ready": False,
            "retargeting_note": "A skeleton exists, but the worker did not return its bone names.",
        }

    candidates: list[dict[str, Any]] = []
    for skeleton in skeletons:
        if not isinstance(skeleton, Mapping):
            continue
        raw_bones = skeleton.get("bones", [])
        bones = raw_bones if isinstance(raw_bones, list) else []
        mapping: dict[str, str] = {}
        for bone in bones:
            name = bone.get("name", "") if isinstance(bone, Mapping) else bone
            canonical = _ALIAS_TO_CANONICAL.get(_normalise_bone_name(name))
            if canonical and canonical not in mapping:
                mapping[canonical] = str(name)
        missing = [name for name in REQUIRED_HUMANOID_BONES if name not in mapping]
        candidates.append({
            "skeleton_path": str(skeleton.get("node_path", "")),
            "bone_count": int(skeleton.get("bone_count", len(bones)) or len(bones)),
            "bone_mapping": mapping, "missing_bones": missing,
            "matched_bone_count": len(mapping),
        })
    if not candidates:
        return {
            "status": "skeleton_details_unavailable", "skeleton_count": skeleton_count,
            "bone_count": 0, "required_bone_count": required, "matched_bone_count": 0,
            "bone_mapping": {}, "missing_bones": list(REQUIRED_HUMANOID_BONES),
            "retargeting_ready": False,
            "retargeting_note": "Skeleton details were not readable.",
        }

    best = max(candidates, key=lambda item: (item["matched_bone_count"], item["bone_count"]))
    matched = best["matched_bone_count"]
    status = "humanoid_names_complete" if matched == required else (
        "partial_humanoid_names" if matched else "skeleton_unmapped"
    )
    return {
        "status": status, "skeleton_count": skeleton_count,
        "skeleton_path": best["skeleton_path"], "bone_count": best["bone_count"],
        "required_bone_count": required, "matched_bone_count": matched,
        "bone_mapping": best["bone_mapping"], "missing_bones": best["missing_bones"],
        "retargeting_ready": False,
        "retargeting_note": (
            "Bone-name coverage is only a preflight check. Validate rest pose, bone axes, "
            "scale, skin weights and actual motion before declaring this rig retargetable."
        ),
    }
