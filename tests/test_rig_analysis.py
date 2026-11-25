def _analyze_rig(inspection):
    from app.rig_analysis import analyze_rig

    return analyze_rig(inspection)


MIXAMO_HUMANOID = [
    "mixamorig:Hips", "mixamorig:Spine", "mixamorig:Head",
    "mixamorig:LeftUpLeg", "mixamorig:LeftLeg", "mixamorig:LeftFoot",
    "mixamorig:RightUpLeg", "mixamorig:RightLeg", "mixamorig:RightFoot",
    "mixamorig:LeftArm", "mixamorig:LeftForeArm", "mixamorig:LeftHand",
    "mixamorig:RightArm", "mixamorig:RightForeArm", "mixamorig:RightHand",
]


def test_mixamo_style_bones_receive_complete_name_coverage_without_false_ready_claim():
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
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
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bone_count": 3, "bones": [{"name": "Hips"}, {"name": "Spine"}, {"name": "Head"}],
    }]})
    assert result["status"] == "partial_humanoid_names"
    assert result["matched_bone_count"] == 3
    assert "LeftUpperLeg" in result["missing_bones"]


def test_multiple_skeletons_are_not_combined_into_a_fake_humanoid():
    result = _analyze_rig({"skeleton_count": 2, "skeletons": [
        {"bone_count": 2, "bones": [{"name": "Hips"}, {"name": "Spine"}]},
        {"bone_count": 2, "bones": [{"name": "Head"}, {"name": "LeftArm"}]},
    ]})
    assert result["matched_bone_count"] == 2
    assert result["status"] == "partial_humanoid_names"


def test_missing_skeleton_is_reported_explicitly():
    result = _analyze_rig({"skeleton_count": 0, "skeletons": []})
    assert result["status"] == "no_skeleton"
    assert result["retargeting_ready"] is False
    assert result["hierarchy_validation"]["status"] == "not_available"
    assert result["rest_pose_summary"]["status"] == "not_available"



def test_mapping_preserves_godot_profile_bone_names_and_source_indices():
    bones = [
        {"index": 0, "name": "mixamorig:Hips", "parent_index": -1, "parent_name": ""},
        {"index": 1, "name": "mixamorig:Spine", "parent_index": 0, "parent_name": "mixamorig:Hips"},
        {"index": 2, "name": "mixamorig:Head", "parent_index": 1, "parent_name": "mixamorig:Spine"},
    ]
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{"bones": bones}]})
    assert result["godot_profile_mapping"]["Hips"] == {
        "bone_index": 0, "source_name": "mixamorig:Hips",
        "parent_index": -1, "parent_name": "",
    }
    assert result["godot_profile_mapping"]["Spine"]["parent_index"] == 0
    assert result["bone_mapping"]["Head"] == "mixamorig:Head"
    assert result["retargeting_ready"] is False


def test_duplicate_aliases_are_reported_as_ambiguous_not_silently_selected():
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bones": [
            {"index": 0, "name": "Hips"},
            {"index": 1, "name": "Pelvis"},
            {"index": 2, "name": "Spine"},
        ],
    }]})
    assert result["status"] == "ambiguous_humanoid_names"
    assert "Hips" not in result["godot_profile_mapping"]
    assert "Hips" in result["missing_bones"]
    ambiguity = result["ambiguous_bones"][0]
    assert ambiguity["profile_bone"] == "Hips"
    assert [item["bone_index"] for item in ambiguity["candidates"]] == [0, 1]


def test_unmapped_bones_are_reported_without_polluting_profile_mapping():
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bones": [
            {"index": 0, "name": "Root"},
            {"index": 1, "name": "Hips"},
            {"index": 2, "name": "FaceControl"},
        ],
    }]})
    assert result["bone_mapping"] == {"Hips": "Hips"}
    assert result["unmapped_bones"] == [
        {"bone_index": 0, "source_name": "Root"},
        {"bone_index": 2, "source_name": "FaceControl"},
    ]


def test_best_skeleton_prefers_unambiguous_mapping_over_duplicate_candidates():
    result = _analyze_rig({"skeleton_count": 2, "skeletons": [
        {"bone_count": 4, "bones": [
            {"index": 0, "name": "Hips"},
            {"index": 1, "name": "Pelvis"},
            {"index": 2, "name": "Spine"},
        ]},
        {"bone_count": 2, "bones": [
            {"index": 0, "name": "Hips"},
            {"index": 1, "name": "Spine"},
        ]},
    ]})
    assert result["skeleton_path"] == ""
    assert result["ambiguous_bones"] == []
    assert result["matched_bone_count"] == 2



def test_valid_indexed_humanoid_hierarchy_is_reported_separately_from_retarget_readiness():
    names = [
        ("Hips", -1), ("Spine", 0), ("Head", 1),
        ("LeftUpperLeg", 0), ("LeftLowerLeg", 3), ("LeftFoot", 4),
        ("RightUpperLeg", 0), ("RightLowerLeg", 6), ("RightFoot", 7),
        ("LeftUpperArm", 1), ("LeftLowerArm", 9), ("LeftHand", 10),
        ("RightUpperArm", 1), ("RightLowerArm", 12), ("RightHand", 13),
    ]
    bones = [
        {"index": index, "name": name, "parent_index": parent}
        for index, (name, parent) in enumerate(names)
    ]
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bone_count": len(bones), "bones": bones,
    }]})
    assert result["hierarchy_validation"]["status"] == "valid"
    assert result["hierarchy_validation"]["checked_relationships"] == 14
    assert result["hierarchy_validation"]["issues"] == []
    assert result["retargeting_ready"] is False


def test_invalid_humanoid_parent_chain_is_reported_without_claiming_retarget_failure():
    names = [
        ("Hips", -1), ("Spine", 0), ("Head", 1),
        ("LeftUpperLeg", 0), ("LeftLowerLeg", 3), ("LeftFoot", 4),
        ("RightUpperLeg", 0), ("RightLowerLeg", 6), ("RightFoot", 7),
        ("LeftUpperArm", 1), ("LeftLowerArm", 9), ("LeftHand", 10),
        ("RightUpperArm", 1), ("RightLowerArm", 12), ("RightHand", 13),
    ]
    bones = [
        {"index": index, "name": name, "parent_index": parent}
        for index, (name, parent) in enumerate(names)
    ]
    bones[4]["parent_index"] = 0
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bone_count": len(bones), "bones": bones,
    }]})
    validation = result["hierarchy_validation"]
    assert validation["status"] == "invalid"
    assert any("LeftLowerLeg" in issue for issue in validation["issues"])
    assert result["retargeting_ready"] is False


def test_hierarchy_validation_is_explicitly_unavailable_for_legacy_name_only_data():
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bones": [{"name": name} for name in MIXAMO_HUMANOID],
    }]})
    assert result["hierarchy_validation"]["status"] == "not_available"



def test_partial_humanoid_hierarchy_is_not_misreported_as_fully_valid():
    bones = [
        {"index": 0, "name": "Hips", "parent_index": -1},
        {"index": 1, "name": "Spine", "parent_index": 0},
        {"index": 2, "name": "Head", "parent_index": 1},
    ]
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bone_count": 3, "bones": bones,
    }]})
    assert result["hierarchy_validation"]["status"] == "incomplete"
    assert result["hierarchy_validation"]["checked_relationships"] == 2



def test_rest_pose_transforms_are_preserved_and_summarized_without_readiness_claim():
    bones = [
        {
            "index": 0,
            "name": "Hips",
            "parent_index": -1,
            "rest_transform": {
                "origin": [0.0, 1.0, 0.0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1],
            },
        },
        {
            "index": 1,
            "name": "Spine",
            "parent_index": 0,
            "rest_transform": {
                "origin": [0.0, 0.25, 0.0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1],
            },
        },
        {
            "index": 2,
            "name": "Head",
            "parent_index": 1,
            "rest_transform": {
                "origin": [0.0, 0.15, 0.0],
                "rotation": [0, 0, 0, 1],
                "scale": [1, 1, 1],
            },
        },
    ]
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{
        "bone_count": 3, "bones": bones,
    }]})
    assert result["godot_profile_mapping"]["Spine"]["rest_transform"]["origin"] == [0.0, 0.25, 0.0]
    summary = result["rest_pose_summary"]
    assert summary["status"] == "available"
    assert summary["measured_bone_count"] == 3
    assert summary["local_offset_lengths"]["Spine"] == 0.25
    assert result["retargeting_ready"] is False


def test_rest_pose_summary_ignores_malformed_or_non_finite_transforms():
    bones = [
        {"index": 0, "name": "Hips", "parent_index": -1,
         "rest_transform": {"origin": [float("nan"), 0, 0]}},
        {"index": 1, "name": "Spine", "parent_index": 0,
         "rest_transform": {"origin": ["bad", 0, 0]}},
    ]
    result = _analyze_rig({"skeleton_count": 1, "skeletons": [{"bones": bones}]})
    assert result["rest_pose_summary"]["status"] == "not_available"
    assert result["rest_pose_summary"]["measured_bone_count"] == 0

def test_common_dcc_humanoid_naming_conventions_map_without_guessing():
    naming_sets = {
        "3ds_max_biped": [
            "Bip01 Pelvis", "Bip01 Spine", "Bip01 Head",
            "Bip01 L Thigh", "Bip01 L Calf", "Bip01 L Foot",
            "Bip01 R Thigh", "Bip01 R Calf", "Bip01 R Foot",
            "Bip01 L UpperArm", "Bip01 L Forearm", "Bip01 L Hand",
            "Bip01 R UpperArm", "Bip01 R Forearm", "Bip01 R Hand",
        ],
        "character_creator": [
            "CC_Base_Hip", "CC_Base_Spine01", "CC_Base_Head",
            "CC_Base_L_Thigh", "CC_Base_L_Calf", "CC_Base_L_Foot",
            "CC_Base_R_Thigh", "CC_Base_R_Calf", "CC_Base_R_Foot",
            "CC_Base_L_Upperarm", "CC_Base_L_Forearm", "CC_Base_L_Hand",
            "CC_Base_R_Upperarm", "CC_Base_R_Forearm", "CC_Base_R_Hand",
        ],
        "unreal_mannequin": [
            "pelvis", "spine_01", "head",
            "thigh_l", "calf_l", "foot_l",
            "thigh_r", "calf_r", "foot_r",
            "upperarm_l", "lowerarm_l", "hand_l",
            "upperarm_r", "lowerarm_r", "hand_r",
        ],
        "blender_rigify_deform": [
            "DEF-hips", "DEF-spine", "DEF-head",
            "DEF-thigh.L", "DEF-shin.L", "DEF-foot.L",
            "DEF-thigh.R", "DEF-shin.R", "DEF-foot.R",
            "DEF-upper_arm.L", "DEF-forearm.L", "DEF-hand.L",
            "DEF-upper_arm.R", "DEF-forearm.R", "DEF-hand.R",
        ],
    }
    for rig_name, names in naming_sets.items():
        result = _analyze_rig({
            "skeleton_count": 1,
            "skeletons": [{
                "node_path": f"Imported/{rig_name}/Skeleton3D",
                "bone_count": len(names),
                "bones": [{"name": name} for name in names],
            }],
        })
        assert result["matched_bone_count"] == 15, rig_name
        assert result["missing_bones"] == [], rig_name
        assert result["ambiguous_bones"] == [], rig_name
        assert result["retargeting_ready"] is False, rig_name


def test_duplicate_indexed_bone_ids_are_rejected_as_malformed_hierarchy():
    result = _analyze_rig({
        "skeleton_count": 1,
        "skeletons": [{
            "bones": [
                {"index": 0, "name": "Hips", "parent_index": -1},
                {"index": 0, "name": "Spine", "parent_index": 0},
            ],
        }],
    })
    validation = result["hierarchy_validation"]
    assert validation["status"] == "invalid"
    assert validation["checked_relationships"] == 0
    assert "Duplicate bone index 0" in validation["issues"][0]


def test_negative_and_out_of_range_parent_indices_are_rejected():
    negative = _analyze_rig({
        "skeleton_count": 1,
        "skeletons": [{
            "bones": [{"index": -1, "name": "Hips", "parent_index": -1}],
        }],
    })
    invalid_parent = _analyze_rig({
        "skeleton_count": 1,
        "skeletons": [{
            "bones": [{"index": 0, "name": "Hips", "parent_index": -2}],
        }],
    })
    assert negative["hierarchy_validation"]["status"] == "invalid"
    assert invalid_parent["hierarchy_validation"]["status"] == "invalid"




def test_robot_expressive_imported_bone_names_map_to_humanoid_profile():
    names = [
        "Hips", "Abdomen", "Head_2",
        "UpperLeg.L", "LowerLeg.L", "Foot.L",
        "UpperLeg.R", "LowerLeg.R", "Foot.R",
        "UpperArm.L", "LowerArm.L", "Palm2.L",
        "UpperArm.R", "LowerArm.R", "Palm2.R",
    ]
    parents = [-1, 0, 1, 0, 3, 4, 0, 6, 7, 1, 9, 10, 1, 12, 13]
    bones = [
        {"index": index, "name": name, "parent_index": parents[index]}
        for index, name in enumerate(names)
    ]

    result = _analyze_rig({
        "skeleton_count": 1,
        "skeletons": [{"bone_count": len(bones), "bones": bones}],
    })

    assert result["status"] == "humanoid_names_complete"
    assert result["matched_bone_count"] == 15
    assert result["missing_bones"] == []
    assert result["hierarchy_validation"]["status"] == "valid"
    assert result["godot_profile_mapping"]["Head"]["source_name"] == "Head_2"
    assert result["godot_profile_mapping"]["LeftHand"]["source_name"] == "Palm2.L"
    assert result["godot_profile_mapping"]["RightHand"]["source_name"] == "Palm2.R"
