extends SceneTree

const PROTOCOL_VERSION := 1


func _initialize() -> void:
    call_deferred("_execute")


func _execute() -> void:
    var arguments := OS.get_cmdline_user_args()
    var request_path := _argument_value(arguments, "--request")
    var response_path := _argument_value(arguments, "--response")
    if request_path.is_empty() or response_path.is_empty():
        push_error("Worker requires --request and --response paths.")
        quit(64)
        return

    if not FileAccess.file_exists(request_path):
        push_error("Worker request file does not exist.")
        quit(66)
        return

    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(request_path))
    if typeof(parsed) != TYPE_DICTIONARY:
        _write_response(response_path, _error_response("", "INVALID_REQUEST", "Request must be a JSON object."), 2)
        return

    var response := _dispatch(parsed)
    var exit_code := 0 if response.get("status") == "ok" else 2
    _write_response(response_path, response, exit_code)


func _argument_value(arguments: PackedStringArray, name: String) -> String:
    for index in range(arguments.size() - 1):
        if arguments[index] == name:
            return arguments[index + 1]
    return ""


func _dispatch(request: Dictionary) -> Dictionary:
    var request_id := str(request.get("request_id", ""))
    if int(request.get("protocol_version", 0)) != PROTOCOL_VERSION:
        return _error_response(request_id, "PROTOCOL_MISMATCH", "Unsupported worker protocol version.")

    var action := str(request.get("action", ""))
    if action == "handshake":
        return {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "status": "ok",
            "engine": _engine_info(),
            "capabilities": ["handshake", "glb.inspect", "scene.metrics"]
        }
    if action != "inspect_glb":
        return _error_response(request_id, "UNKNOWN_ACTION", "Unsupported worker action.")

    var root_path := _normalise_path(str(request.get("project_root", "")))
    var asset_path := _normalise_path(str(request.get("asset_path", "")))
    if root_path.is_empty() or asset_path.is_empty():
        return _error_response(request_id, "INVALID_PATH", "Project and asset paths are required.")
    if not DirAccess.dir_exists_absolute(root_path):
        return _error_response(request_id, "INVALID_PROJECT", "Project directory does not exist.")

    var root_prefix := root_path.trim_suffix("/") + "/"
    if not asset_path.to_lower().begins_with(root_prefix.to_lower()):
        return _error_response(request_id, "PATH_OUTSIDE_PROJECT", "The GLB path resolves outside the supplied project directory.")
    if asset_path.get_extension().to_lower() != "glb":
        return _error_response(request_id, "INVALID_FORMAT", "Only .glb assets are supported.")
    if not FileAccess.file_exists(asset_path):
        return _error_response(request_id, "ASSET_NOT_FOUND", "The GLB asset does not exist.")

    var gltf_state := GLTFState.new()
    gltf_state.base_path = asset_path.get_base_dir()
    var gltf_document := GLTFDocument.new()
    var import_error := gltf_document.append_from_file(asset_path, gltf_state, 0, asset_path.get_base_dir())
    if import_error != OK:
        return _error_response(request_id, "GLTF_IMPORT_FAILED", "Godot could not import the GLB: " + error_string(import_error))

    var imported_scene := gltf_document.generate_scene(gltf_state)
    if imported_scene == null:
        return _error_response(request_id, "GLTF_SCENE_FAILED", "Godot imported the GLB state but could not generate a scene.")

    var metrics := {
        "mesh_count": 0,
        "skeleton_count": 0,
        "animation_player_count": 0,
        "animation_count": 0
    }
    _count_nodes(imported_scene, metrics)
    var response := {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "status": "ok",
        "engine": _engine_info(),
        "asset": {
            "file_name": asset_path.get_file(),
            "file_size_bytes": FileAccess.get_file_as_bytes(asset_path).size()
        },
        "metrics": metrics
    }
    imported_scene.free()
    return response


func _normalise_path(value: String) -> String:
    return value.replace("\\", "/").simplify_path()


func _count_nodes(node: Node, metrics: Dictionary) -> void:
    if node is MeshInstance3D:
        metrics["mesh_count"] = int(metrics["mesh_count"]) + 1
    if node is Skeleton3D:
        metrics["skeleton_count"] = int(metrics["skeleton_count"]) + 1
    if node is AnimationPlayer:
        metrics["animation_player_count"] = int(metrics["animation_player_count"]) + 1
        metrics["animation_count"] = int(metrics["animation_count"]) + (node as AnimationPlayer).get_animation_list().size()
    for child in node.get_children():
        _count_nodes(child, metrics)


func _engine_info() -> Dictionary:
    return {
        "name": "Godot Engine",
        "version": str(Engine.get_version_info().get("string", "unknown")),
        "renderer": str(RenderingServer.get_current_rendering_method())
    }


func _error_response(request_id: String, code: String, message: String) -> Dictionary:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "status": "error",
        "error_code": code,
        "message": message,
        "engine": _engine_info()
    }


func _write_response(path: String, response: Dictionary, exit_code: int) -> void:
    var output := FileAccess.open(path, FileAccess.WRITE)
    if output == null:
        push_error("Could not write worker response: " + path)
        quit(70)
        return
    output.store_string(JSON.stringify(response, "  "))
    output.flush()
    output.close()
    quit(exit_code)
