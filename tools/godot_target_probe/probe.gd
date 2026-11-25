extends Node3D

const INTERACTIVE_SECONDS := 12.0
const MOVIE_FRAME_LIMIT := 240

var _mode := "interactive"
var _report_path := "user://godot_target_probe_report.json"
var _start_ticks := 0
var _frame_count := 0
var _frame_times: Array[float] = []
var _moving_nodes: Array[Node3D] = []
var _finished := false
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
    _read_user_arguments()
    _rng.seed = 472026
    _build_scene()
    _start_ticks = Time.get_ticks_msec()

    print("Cartoon Studio target probe")
    print("Godot: ", Engine.get_version_info().get("string", "unknown"))
    print("Renderer: ", RenderingServer.get_current_rendering_method())
    print("GPU: ", RenderingServer.get_video_adapter_name())


func _process(delta: float) -> void:
    _frame_count += 1
    for moving_node in _moving_nodes:
        moving_node.rotate_y(delta * 0.45)

    if _mode == "movie":
        if _frame_count > 24:
            _frame_times.append(delta)
        if _frame_count >= MOVIE_FRAME_LIMIT:
            _finish()
    else:
        var elapsed_seconds := float(Time.get_ticks_msec() - _start_ticks) / 1000.0
        if elapsed_seconds >= 2.0:
            _frame_times.append(delta)
        if elapsed_seconds >= INTERACTIVE_SECONDS:
            _finish()


func _read_user_arguments() -> void:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--mode="):
            _mode = argument.trim_prefix("--mode=")
        elif argument.begins_with("--report="):
            _report_path = argument.trim_prefix("--report=")


func _build_scene() -> void:
    var world := WorldEnvironment.new()
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color(0.48, 0.66, 0.82)
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color(0.66, 0.69, 0.75)
    environment.ambient_light_energy = 0.65
    world.environment = environment
    add_child(world)

    var ground_mesh := PlaneMesh.new()
    ground_mesh.size = Vector2(90.0, 90.0)
    var ground := MeshInstance3D.new()
    ground.mesh = ground_mesh
    ground.material_override = _toon_material(Color(0.24, 0.48, 0.29))
    ground.position.y = -0.08
    add_child(ground)

    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-52.0, 34.0, 0.0)
    sun.light_energy = 1.25
    sun.shadow_enabled = true
    add_child(sun)

    _build_buildings()
    _build_trees()
    _build_character_proxies()

    var camera := Camera3D.new()
    camera.position = Vector3(31.0, 25.0, 36.0)
    camera.fov = 55.0
    camera.current = true
    add_child(camera)
    camera.look_at(Vector3.ZERO, Vector3.UP)


func _build_buildings() -> void:
    var palette := [
        Color(0.82, 0.60, 0.43),
        Color(0.72, 0.75, 0.79),
        Color(0.84, 0.77, 0.58),
        Color(0.59, 0.69, 0.72),
        Color(0.77, 0.57, 0.54)
    ]
    for x in range(10):
        for z in range(10):
            var height := _rng.randf_range(3.0, 9.0)
            var mesh := BoxMesh.new()
            mesh.size = Vector3(2.4, height, 2.4)
            var building := MeshInstance3D.new()
            building.mesh = mesh
            building.material_override = _toon_material(palette[_rng.randi_range(0, palette.size() - 1)])
            building.position = Vector3((x - 4.5) * 5.0, height * 0.5, (z - 4.5) * 5.0)
            add_child(building)


func _build_trees() -> void:
    for index in range(48):
        var x := _rng.randf_range(-32.0, 32.0)
        var z := _rng.randf_range(-32.0, 32.0)

        var trunk_mesh := CylinderMesh.new()
        trunk_mesh.top_radius = 0.18
        trunk_mesh.bottom_radius = 0.25
        trunk_mesh.height = 1.8
        var trunk := MeshInstance3D.new()
        trunk.mesh = trunk_mesh
        trunk.material_override = _toon_material(Color(0.34, 0.22, 0.13))
        trunk.position = Vector3(x, 0.9, z)
        add_child(trunk)

        var crown_mesh := SphereMesh.new()
        crown_mesh.radius = _rng.randf_range(0.9, 1.35)
        crown_mesh.height = crown_mesh.radius * 2.0
        var crown := MeshInstance3D.new()
        crown.mesh = crown_mesh
        crown.material_override = _toon_material(Color(0.16, 0.42, 0.20))
        crown.position = Vector3(x, 2.35, z)
        add_child(crown)


func _build_character_proxies() -> void:
    var colors := [
        Color(0.86, 0.39, 0.30),
        Color(0.30, 0.54, 0.82),
        Color(0.84, 0.70, 0.28),
        Color(0.57, 0.40, 0.76)
    ]
    for index in range(12):
        var capsule_mesh := CapsuleMesh.new()
        capsule_mesh.radius = 0.42
        capsule_mesh.height = 1.8
        var character := MeshInstance3D.new()
        character.mesh = capsule_mesh
        character.material_override = _toon_material(colors[index % colors.size()])
        character.position = Vector3(
            _rng.randf_range(-12.0, 12.0),
            0.9,
            _rng.randf_range(-12.0, 12.0)
        )
        add_child(character)
        _moving_nodes.append(character)


func _toon_material(color: Color) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.roughness = 0.82
    material.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
    material.specular_mode = BaseMaterial3D.SPECULAR_TOON
    return material


func _finish() -> void:
    if _finished:
        return
    _finished = true
    _write_report()
    get_tree().quit()


func _write_report() -> void:
    var sorted_times := _frame_times.duplicate()
    sorted_times.sort()

    var average_delta := 0.0
    var min_delta := 0.0
    var max_delta := 0.0
    var p95_delta := 0.0
    if not sorted_times.is_empty():
        for value in sorted_times:
            average_delta += value
        average_delta /= float(sorted_times.size())
        min_delta = sorted_times[0]
        max_delta = sorted_times[sorted_times.size() - 1]
        var p95_index := int(floor(float(sorted_times.size() - 1) * 0.95))
        p95_delta = sorted_times[p95_index]

    var viewport_size := get_viewport().get_visible_rect().size
    var report := {
        "mode": _mode,
        "godot_version": Engine.get_version_info(),
        "renderer": RenderingServer.get_current_rendering_method(),
        "rendering_driver": RenderingServer.get_current_rendering_driver_name(),
        "gpu_name": RenderingServer.get_video_adapter_name(),
        "gpu_vendor": RenderingServer.get_video_adapter_vendor(),
        "gpu_api_version": RenderingServer.get_video_adapter_api_version(),
        "gpu_driver_info": OS.get_video_adapter_driver_info().join(" | "),
        "viewport_width": int(viewport_size.x),
        "viewport_height": int(viewport_size.y),
        "frames_total": _frame_count,
        "frames_measured": sorted_times.size(),
        "average_fps": (1.0 / average_delta) if average_delta > 0.0 else 0.0,
        "average_frame_ms": average_delta * 1000.0,
        "p95_frame_ms": p95_delta * 1000.0,
        "min_frame_ms": min_delta * 1000.0,
        "max_frame_ms": max_delta * 1000.0,
        "static_memory_mb": float(Performance.get_monitor(Performance.MEMORY_STATIC)) / 1048576.0,
        "object_count": int(Performance.get_monitor(Performance.OBJECT_COUNT)),
        "draw_calls_last_frame": int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)),
        "render_objects_last_frame": int(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME)),
        "directional_shadows_enabled": true
    }

    var file := FileAccess.open(_report_path, FileAccess.WRITE)
    if file == null:
        push_error("Could not write probe report to: " + _report_path)
        return
    file.store_string(JSON.stringify(report, "\t"))
    file.close()
    print("Probe report written: ", _report_path)
