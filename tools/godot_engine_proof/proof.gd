extends Node3D

const PROOF_FRAME_LIMIT := 72
var _frame_count := 0
var _report_path := "user://godot_engine_proof_report.json"
var _errors: Array[String] = []
var _checks := {
    "glb_imported": false,
    "glb_contains_mesh": false,
    "animation_created": false,
    "animation_playing": false,
    "scene_saved": false,
    "scene_reopened": false,
    "retarget_modifier_created": false,
    "retarget_source_animation_playing": false,
    "retarget_different_rest_lengths": false,
    "retarget_pose_transferred": false,
    "retarget_scene_reopened": false
}
var _saved_scene_path := "user://cartoon_studio_engine_proof_saved.tscn"
var _retarget_source: Skeleton3D
var _retarget_target: Skeleton3D


func _ready() -> void:
    _read_arguments()
    _build_camera_and_light()
    _import_glb_fixture()
    _build_animated_character_proxy()
    _build_humanoid_retarget_pair()
    _save_and_reopen_scene()
    print("CARTOON_STUDIO_ENGINE_PROOF_START")
    print("Godot: ", Engine.get_version_info().get("string", "unknown"))
    print("Renderer: ", RenderingServer.get_current_rendering_method())
    print("Adapter: ", RenderingServer.get_video_adapter_name())


func _process(_delta: float) -> void:
    _frame_count += 1
    if _frame_count >= PROOF_FRAME_LIMIT:
        _finish()


func _read_arguments() -> void:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            _report_path = argument.trim_prefix("--report=")


func _build_camera_and_light() -> void:
    var camera := Camera3D.new()
    camera.name = "ProofCamera"
    camera.position = Vector3(3.2, 2.5, 5.5)
    camera.current = true
    add_child(camera)
    camera.look_at(Vector3.ZERO, Vector3.UP)

    var light := DirectionalLight3D.new()
    light.name = "ProofKeyLight"
    light.rotation_degrees = Vector3(-42.0, -28.0, 0.0)
    light.light_energy = 1.4
    add_child(light)


func _import_glb_fixture() -> void:
    var imported := load("res://fixtures/proof_triangle.glb") as PackedScene
    if imported == null:
        _errors.append("GLB fixture did not import as a PackedScene.")
        return

    _checks["glb_imported"] = true
    var instance := imported.instantiate()
    instance.name = "ImportedGLB"
    instance.position = Vector3(-1.2, 0.0, 0.0)
    add_child(instance)

    var meshes := instance.find_children("*", "MeshInstance3D", true, false)
    if meshes.is_empty():
        _errors.append("Imported GLB contains no MeshInstance3D.")
    else:
        _checks["glb_contains_mesh"] = true


func _build_animated_character_proxy() -> void:
    var mesh := MeshInstance3D.new()
    mesh.name = "AnimatedCube"
    var box := BoxMesh.new()
    box.size = Vector3(0.9, 1.4, 0.9)
    mesh.mesh = box
    mesh.position = Vector3(0.9, 0.7, 0.0)

    var material := StandardMaterial3D.new()
    material.albedo_color = Color(0.22, 0.58, 0.88)
    material.roughness = 0.8
    material.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
    mesh.material_override = material
    add_child(mesh)

    var player := AnimationPlayer.new()
    player.name = "AnimationPlayer"
    player.root_node = NodePath("..")
    add_child(player)

    var library := AnimationLibrary.new()
    var animation := Animation.new()
    animation.resource_name = "ProofSpin"
    animation.length = 1.5
    animation.loop_mode = Animation.LOOP_LINEAR
    var track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(track, NodePath("AnimatedCube:rotation"))
    animation.track_insert_key(track, 0.0, Vector3.ZERO)
    animation.track_insert_key(track, 1.5, Vector3(0.0, TAU, 0.0))

    var library_error := library.add_animation("proof_spin", animation)
    if library_error != OK:
        _errors.append("Could not add proof animation to library: %s" % library_error)
        return
    player.add_animation_library("", library)
    _checks["animation_created"] = true
    player.play("proof_spin")
    _checks["animation_playing"] = player.is_playing()


func _create_humanoid_skeleton(skeleton_name: String, arm_length: float, leg_length: float) -> Skeleton3D:
    var skeleton := Skeleton3D.new()
    skeleton.name = skeleton_name
    var bone_specs := [
        {"name": "Hips", "parent": -1, "position": Vector3(0.0, 1.0, 0.0)},
        {"name": "Spine", "parent": 0, "position": Vector3(0.0, 0.2, 0.0)},
        {"name": "Neck", "parent": 1, "position": Vector3(0.0, 0.25, 0.0)},
        {"name": "Head", "parent": 2, "position": Vector3(0.0, 0.12, 0.0)},
        {"name": "LeftUpperLeg", "parent": 0, "position": Vector3(-0.12, -0.15, 0.0)},
        {"name": "LeftLowerLeg", "parent": 4, "position": Vector3(0.0, -leg_length, 0.0)},
        {"name": "LeftFoot", "parent": 5, "position": Vector3(0.0, -leg_length, 0.08)},
        {"name": "RightUpperLeg", "parent": 0, "position": Vector3(0.12, -0.15, 0.0)},
        {"name": "RightLowerLeg", "parent": 7, "position": Vector3(0.0, -leg_length, 0.0)},
        {"name": "RightFoot", "parent": 8, "position": Vector3(0.0, -leg_length, 0.08)},
        {"name": "LeftShoulder", "parent": 1, "position": Vector3(-0.12, 0.12, 0.0)},
        {"name": "LeftUpperArm", "parent": 10, "position": Vector3(-arm_length, 0.0, 0.0)},
        {"name": "LeftLowerArm", "parent": 11, "position": Vector3(-arm_length, 0.0, 0.0)},
        {"name": "LeftHand", "parent": 12, "position": Vector3(-0.12, 0.0, 0.0)},
        {"name": "RightShoulder", "parent": 1, "position": Vector3(0.12, 0.12, 0.0)},
        {"name": "RightUpperArm", "parent": 14, "position": Vector3(arm_length, 0.0, 0.0)},
        {"name": "RightLowerArm", "parent": 15, "position": Vector3(arm_length, 0.0, 0.0)},
        {"name": "RightHand", "parent": 16, "position": Vector3(0.12, 0.0, 0.0)}
    ]
    for bone_spec in bone_specs:
        var bone_index := skeleton.get_bone_count()
        skeleton.add_bone(bone_spec["name"])
        skeleton.set_bone_parent(bone_index, bone_spec["parent"])
        skeleton.set_bone_rest(
            bone_index,
            Transform3D(Basis.IDENTITY, bone_spec["position"])
        )
    return skeleton


func _build_humanoid_retarget_pair() -> void:
    _retarget_source = _create_humanoid_skeleton("SourceSkeleton", 0.28, 0.34)
    _retarget_source.position = Vector3(1.4, 0.0, 0.0)
    add_child(_retarget_source)

    var modifier := RetargetModifier3D.new()
    modifier.name = "RetargetModifier3D"
    _retarget_source.add_child(modifier)

    _retarget_target = _create_humanoid_skeleton("TargetSkeleton", 0.42, 0.46)
    _retarget_target.position = Vector3(1.1, 0.0, 0.0)
    modifier.add_child(_retarget_target)
    modifier.profile = SkeletonProfileHumanoid.new()
    _checks["retarget_modifier_created"] = (
        modifier.profile is SkeletonProfileHumanoid
        and _retarget_target.get_bone_count() == _retarget_source.get_bone_count()
    )

    var player := AnimationPlayer.new()
    player.name = "RetargetAnimationPlayer"
    player.root_node = NodePath("..")
    add_child(player)

    var library := AnimationLibrary.new()
    var animation := Animation.new()
    animation.resource_name = "ArmRaise"
    animation.length = 6.0
    var track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(track, NodePath("SourceSkeleton:bones/11/rotation"))
    animation.track_insert_key(track, 0.0, Quaternion.IDENTITY)
    animation.track_insert_key(track, 3.0, Quaternion(Vector3.FORWARD, deg_to_rad(40.0)))
    animation.track_insert_key(track, 6.0, Quaternion.IDENTITY)

    var library_error := library.add_animation("arm_raise", animation)
    if library_error != OK:
        _errors.append("Could not add humanoid retarget animation: %s" % library_error)
        return
    player.add_animation_library("", library)
    player.play("arm_raise")
    _checks["retarget_source_animation_playing"] = player.is_playing()
    var source_arm := _retarget_source.find_bone("LeftUpperArm")
    var target_arm := _retarget_target.find_bone("LeftUpperArm")
    if source_arm < 0 or target_arm < 0:
        _errors.append("Humanoid retarget proof could not find LeftUpperArm on both skeletons.")
        return
    _checks["retarget_different_rest_lengths"] = not is_equal_approx(
        _retarget_source.get_bone_rest(source_arm).origin.length(),
        _retarget_target.get_bone_rest(target_arm).origin.length()
    )


func _save_and_reopen_scene() -> void:
    _set_saved_scene_ownership(self)
    var packed := PackedScene.new()
    var pack_error := packed.pack(self)
    if pack_error != OK:
        _errors.append("Could not pack proof scene: %s" % pack_error)
        return

    var save_error := ResourceSaver.save(packed, _saved_scene_path)
    if save_error != OK:
        _errors.append("Could not save proof scene: %s" % save_error)
        return
    _checks["scene_saved"] = true

    var reopened := ResourceLoader.load(_saved_scene_path) as PackedScene
    if reopened == null:
        _errors.append("Saved proof scene could not be reopened.")
        return
    var instance := reopened.instantiate()
    if instance.get_node_or_null("AnimatedCube") == null:
        _errors.append("Reopened scene is missing AnimatedCube.")
    elif instance.get_node_or_null("ImportedGLB") == null:
        _errors.append("Reopened scene is missing imported GLB instance.")
    elif instance.get_node_or_null("AnimationPlayer") == null:
        _errors.append("Reopened scene is missing AnimationPlayer.")
    elif instance.get_node_or_null("SourceSkeleton/RetargetModifier3D/TargetSkeleton") == null:
        _errors.append("Reopened scene is missing the humanoid retarget pair.")
    else:
        _checks["scene_reopened"] = true
        _checks["retarget_scene_reopened"] = true
    instance.free()


func _finish() -> void:
    set_process(false)
    if _retarget_source != null and _retarget_target != null:
        var source_arm := _retarget_source.find_bone("LeftUpperArm")
        var target_arm := _retarget_target.find_bone("LeftUpperArm")
        if source_arm >= 0 and target_arm >= 0:
            var source_rotation := _retarget_source.get_bone_pose_rotation(source_arm)
            var target_rotation := _retarget_target.get_bone_pose_rotation(target_arm)
            var source_angle := source_rotation.angle_to(Quaternion.IDENTITY)
            var target_angle := target_rotation.angle_to(Quaternion.IDENTITY)
            _checks["retarget_pose_transferred"] = (
                source_angle > deg_to_rad(15.0)
                and absf(source_angle - target_angle) < deg_to_rad(2.0)
            )
    var passed := _errors.is_empty()
    for check_name in _checks:
        if not _checks[check_name]:
            passed = false
            if not _errors.has("Check failed: " + check_name):
                _errors.append("Check failed: " + check_name)

    var report := {
        "proof": "cartoon_studio_godot_native_worker",
        "godot_version": Engine.get_version_info().get("string", "unknown"),
        "renderer": RenderingServer.get_current_rendering_method(),
        "adapter": RenderingServer.get_video_adapter_name(),
        "checks": _checks,
        "frames_completed": _frame_count,
        "passed": passed,
        "errors": _errors
    }
    var absolute_dir := ProjectSettings.globalize_path(_report_path.get_base_dir())
    DirAccess.make_dir_recursive_absolute(absolute_dir)
    var file := FileAccess.open(_report_path, FileAccess.WRITE)
    if file == null:
        push_error("Could not write proof report: " + _report_path)
        get_tree().quit(2)
        return
    file.store_string(JSON.stringify(report, "  "))
    file.close()
    print("CARTOON_STUDIO_ENGINE_PROOF_RESULT=", JSON.stringify(report))
    get_tree().quit(0 if passed else 1)


func _set_saved_scene_ownership(parent: Node) -> void:
    for child in parent.get_children():
        child.owner = self
        _set_saved_scene_ownership(child)
