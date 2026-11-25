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
    "scene_reopened": false
}
var _saved_scene_path := "user://cartoon_studio_engine_proof_saved.tscn"


func _ready() -> void:
    _read_arguments()
    _build_camera_and_light()
    _import_glb_fixture()
    _build_animated_character_proxy()
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


func _save_and_reopen_scene() -> void:
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
    else:
        _checks["scene_reopened"] = true
    instance.free()


func _finish() -> void:
    set_process(false)
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
