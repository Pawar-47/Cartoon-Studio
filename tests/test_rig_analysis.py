from __future__ import annotations

from app.rig_analysis import analyze_rig  # noqa: I001


MIXAMO_HUMANOID = [
    "mixamorig:Hips", "mixamorig:Spine", "mixamorig:Head",
    "mixamorig:LeftUpLeg", "mixamorig:LeftLeg", "mixamorig:LeftFoot",
    "mixamorig:RightUpLeg", "mixamorig:RightLeg", "mixamorig:RightFoot",
    "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand",
    "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand",
]


def test_mixamo_style_bones_receive_complete_name_coverage_without_false_ready_claim():
    result = analyze_rig({"skeleton_count": 1, "skeletons": [{
        "node_path": "Character/Armature/Skeleton3D",
        "bone_count": len(MIXAMO_HUMANOID),
        "bones": [{"name": name} for name in MIXAMO_HUMANOID],
    }]})
    assert result["status"] == "humanoid_names_complete"
    assert result["matched_bone_count"] == 15
    assert result["missing_bones"] == []
    assert result["retargeting_ready"] is False
    assert "rest pose" in result["retargeting_note"]


def test_partial_skeleton_reports_missing_humanoid_bones():
    result = analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bone_count": 3, "bones": [{"name": "Hips"}, {"name": "Spine"}, {"name": "Head"}],
    }]})
    assert result["status"] == "partial_humanoid_names"
    assert result["matched_bone_count"] == 3
    assert "leftUpperLeg" in result["missing_bones"]


def test_multiple_skeletons_are_not_combined_into_a_fake_humanoid():
    result = analyze_rig({"skeleton_count": 2, "skeletons": [
        {"bone_count": 2, "bones": [{"name": "Hips"}, {"name": "Spine"}]},
        {"bone_count": 2, "bones": [{"name": "Head"}, {"name": "LeftArm"}]},
    ]})
    assert result["matched_bone_count"] == 2
    assert result["status"] == "partial_humanoid_names"


def test_missing_skeleton_is_reported_explicitly():
    result = analyze_rig({"skeleton_count": 0, "skeletons": []})
    assert result["status"] == "no_skeleton"
    assert result["retargeting_ready"] is False
