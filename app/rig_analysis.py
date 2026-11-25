from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

# The keys are Godot SkeletonProfileHumanoid bone names. This is deliberately a
# conservative core mapping: optional spine/neck/shoulder/finger bones are not
# guessed and are not counted as required for the first retarget preflight.
REQUIRED_HUMANOID_BONES: dict[str, frozenset[str]] = {
    "Hips": frozenset({"hips", "pelvis"}),
    "Spine": frozenset({"spine", "spine1", "spine01", "spine001"}),
    "Head": frozenset({"head"}),
    "LeftUpperLeg": frozenset(
        {"leftupleg", "leftupperleg", "leftthigh", "uplegl", "thighl", "upperlegl"}
    ),
    "LeftLowerLeg": frozenset(
        {"leftleg", "leftlowerleg", "leftcalf", "calfl", "lowerlegl", "shinl"}
    ),
    "LeftFoot": frozenset({"leftfoot", "footl"}),
    "RightUpperLeg": frozenset(
        {"rightupleg", "rightupperleg", "rightthigh", "uplegr", "thighr", "upperlegr"}
    ),
    "RightLowerLeg": frozenset(
        {"rightleg", "rightlowerleg", "rightcalf", "calfr", "lowerlegr", "shinr"}
    ),
    "RightFoot": frozenset({"rightfoot", "footr"}),
    "LeftUpperArm": frozenset({"leftarm", "leftupperarm", "upperarml", "arml"}),
    "LeftLowerArm": frozenset({"leftforearm", "leftlowerarm", "forearml", "lowerarml"}),
    "LeftHand": frozenset({"lefthand", "handl"}),
    "RightUpperArm": frozenset({"rightarm", "rightupperarm", "upperarmr", "armr"}),
    "RightLowerArm": frozenset({"rightforearm", "rightlowerarm", "forearmr", "lowerarmr"}),
    "RightHand": frozenset({"righthand", "handr"}),
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


def _empty_result(status: str, skeleton_count: int, note: str) -> dict[str, Any]:
    return {
        "status": status,
        "skeleton_count": skeleton_count,
        "bone_count": 0,
        "required_bone_count": len(REQUIRED_HUMANOID_BONES),
        "matched_bone_count": 0,
        "bone_mapping": {},
        "godot_profile_mapping": {},
        "missing_bones": list(REQUIRED_HUMANOID_BONES),
        "ambiguous_bones": [],
        "unmapped_bones": [],
        "retargeting_ready": False,
        "retargeting_note": note,
    }



def _validate_humanoid_hierarchy(
    profile_mapping: Mapping[str, Mapping[str, Any]],
    bones: list[Any],
) -> dict[str, Any]:
    """Validate required parent chains when Godot supplied indexed hierarchy data."""
    if not bones or not all(
        isinstance(bone, Mapping) and "parent_index" in bone and "index" in bone
        for bone in bones
    ):
        return {
            "status": "not_available",
            "checked_relationships": 0,
            "issues": [],
            "note": "Indexed parent data was not supplied by the importer.",
        }

    parents: dict[int, int] = {}
    for fallback_index, bone in enumerate(bones):
        try:
            index = int(bone.get("index", fallback_index))
            parent = int(bone.get("parent_index", -1))
        except (TypeError, ValueError):
            return {
                "status": "invalid",
                "checked_relationships": 0,
                "issues": ["A bone contains a non-integer index or parent index."],
                "note": "The imported skeleton hierarchy is malformed.",
            }
        parents[index] = parent

    issues: list[str] = []
    for index, parent in parents.items():
        if parent != -1 and parent not in parents:
            issues.append(f"Bone index {index} references missing parent index {parent}.")
        if parent == index:
            issues.append(f"Bone index {index} is its own parent.")

    def is_descendant(child_index: int, ancestor_index: int) -> bool:
        visited: set[int] = set()
        current = child_index
        while current in parents and current not in visited:
            visited.add(current)
            parent = parents[current]
            if parent == ancestor_index:
                return True
            if parent == -1 or parent not in parents:
                return False
            current = parent
        if current in visited:
            issues.append(f"Parent cycle detected while traversing bone index {child_index}.")
        return False

    required_chains = (
        ("Spine", "Hips"),
        ("Head", "Spine"),
        ("LeftUpperLeg", "Hips"),
        ("LeftLowerLeg", "LeftUpperLeg"),
        ("LeftFoot", "LeftLowerLeg"),
        ("RightUpperLeg", "Hips"),
        ("RightLowerLeg", "RightUpperLeg"),
        ("RightFoot", "RightLowerLeg"),
        ("LeftUpperArm", "Spine"),
        ("LeftLowerArm", "LeftUpperArm"),
        ("LeftHand", "LeftLowerArm"),
        ("RightUpperArm", "Spine"),
        ("RightLowerArm", "RightUpperArm"),
        ("RightHand", "RightLowerArm"),
    )
    checked = 0
    for child_name, ancestor_name in required_chains:
        child = profile_mapping.get(child_name)
        ancestor = profile_mapping.get(ancestor_name)
        if child is None or ancestor is None:
            continue
        child_index = int(child["bone_index"])
        ancestor_index = int(ancestor["bone_index"])
        checked += 1
        if child_index not in parents or ancestor_index not in parents:
            issues.append(f"{child_name} or {ancestor_name} has no indexed hierarchy entry.")
        elif not is_descendant(child_index, ancestor_index):
            issues.append(
                f"{child_name} (index {child_index}) is not a descendant of "
                f"{ancestor_name} (index {ancestor_index})."
            )

    status = "invalid" if issues else "valid" if checked == len(required_chains) else "incomplete"
    return {
        "status": status,
        "checked_relationships": checked,
        "issues": issues,
        "note": (
            "Required humanoid parent chains are structurally consistent."
            if status == "valid"
            else "Required humanoid parent chains need correction or review."
        ),
    }

def analyze_rig(inspection: Mapping[str, Any]) -> dict[str, Any]:
    """Build a conservative indexed Godot humanoid mapping from one GLB skeleton."""
    try:
        skeleton_count = max(0, int(inspection.get("skeleton_count", 0) or 0))
    except (TypeError, ValueError):
        skeleton_count = 0
    raw_skeletons = inspection.get("skeletons", [])
    skeletons = raw_skeletons if isinstance(raw_skeletons, list) else []
    if skeleton_count == 0:
        return _empty_result(
            "no_skeleton", 0, "No Skeleton3D was found in the imported model."
        )
    if not skeletons:
        return _empty_result(
            "skeleton_details_unavailable",
            skeleton_count,
            "A skeleton exists, but the worker did not return its bone names.",
        )

    candidates: list[dict[str, Any]] = []
    for skeleton in skeletons:
        if not isinstance(skeleton, Mapping):
            continue
        raw_bones = skeleton.get("bones", [])
        bones = raw_bones if isinstance(raw_bones, list) else []
        matches: dict[str, list[dict[str, Any]]] = {}
        unmapped: list[dict[str, Any]] = []
        for fallback_index, bone in enumerate(bones):
            if isinstance(bone, Mapping):
                name = str(bone.get("name", ""))
                index_value = bone.get("index", fallback_index)
                parent_value = bone.get("parent_index", -1)
                parent_name = str(bone.get("parent_name", ""))
            else:
                name = str(bone)
                index_value = fallback_index
                parent_value = -1
                parent_name = ""
            try:
                index = int(index_value)
            except (TypeError, ValueError):
                index = fallback_index
            try:
                parent_index = int(parent_value)
            except (TypeError, ValueError):
                parent_index = -1
            canonical = _ALIAS_TO_CANONICAL.get(_normalise_bone_name(name))
            if canonical is None:
                if name:
                    unmapped.append({"bone_index": index, "source_name": name})
                continue
            matches.setdefault(canonical, []).append({
                "bone_index": index,
                "source_name": name,
                "parent_index": parent_index,
                "parent_name": parent_name,
            })

        mapping: dict[str, str] = {}
        profile_mapping: dict[str, dict[str, Any]] = {}
        ambiguous: list[dict[str, Any]] = []
        for canonical, entries in matches.items():
            if len(entries) != 1:
                ambiguous.append({
                    "profile_bone": canonical,
                    "candidates": entries,
                })
                continue
            entry = entries[0]
            mapping[canonical] = entry["source_name"]
            profile_mapping[canonical] = entry

        missing = [name for name in REQUIRED_HUMANOID_BONES if name not in profile_mapping]
        bone_count_value = skeleton.get("bone_count", len(bones))
        try:
            bone_count = max(0, int(bone_count_value or len(bones)))
        except (TypeError, ValueError):
            bone_count = len(bones)
        hierarchy_validation = _validate_humanoid_hierarchy(profile_mapping, bones)
        candidates.append({
            "skeleton_path": str(skeleton.get("node_path", "")),
            "bone_count": bone_count,
            "hierarchy_validation": hierarchy_validation,
            "bone_mapping": mapping,
            "godot_profile_mapping": profile_mapping,
            "missing_bones": missing,
            "ambiguous_bones": ambiguous,
            "unmapped_bones": unmapped,
            "matched_bone_count": len(profile_mapping),
        })

    if not candidates:
        return _empty_result(
            "skeleton_details_unavailable",
            skeleton_count,
            "Skeleton details were not readable.",
        )

    # Never combine separate Skeleton3D nodes into a synthetic humanoid.
    best = max(
        candidates,
        key=lambda item: (
            item["matched_bone_count"],
            -len(item["ambiguous_bones"]),
            item["bone_count"],
        ),
    )
    matched = best["matched_bone_count"]
    ambiguous_count = len(best["ambiguous_bones"])
    status = (
        "humanoid_names_complete"
        if matched == len(REQUIRED_HUMANOID_BONES) and not ambiguous_count
        else "ambiguous_humanoid_names"
        if ambiguous_count
        else "partial_humanoid_names"
        if matched
        else "skeleton_unmapped"
    )
    return {
        "status": status,
        "skeleton_count": skeleton_count,
        "skeleton_path": best["skeleton_path"],
        "bone_count": best["bone_count"],
        "required_bone_count": len(REQUIRED_HUMANOID_BONES),
        "matched_bone_count": matched,
        "bone_mapping": best["bone_mapping"],
        "godot_profile_mapping": best["godot_profile_mapping"],
        "missing_bones": best["missing_bones"],
        "ambiguous_bones": best["ambiguous_bones"],
        "unmapped_bones": best["unmapped_bones"],
        "hierarchy_validation": best["hierarchy_validation"],
        "retargeting_ready": False,
        "retargeting_note": (
            "This indexed mapping is a name-based preflight only. Validate hierarchy, "
            "rest pose, bone axes, scale, skin weights and real motion before retargeting. "
            "The imported GLB is not modified."
        ),
    }
