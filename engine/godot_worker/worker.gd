extends SceneTree

const PROTOCOL_VERSION := 1


func _initialize() -> void:
    var arguments := OS.get_cmdline_user_args()
    var request_path := _argument_value(arguments, "--request-file=")
    var response_path := _argument_value(arguments, "--response-file=")
    if request_path.is_empty() or response_path.is_empty():
        push_error("Missing --request-file or --response-file argument.")
        quit(2)
        return

    var request_text := FileAccess.get_file_as_string(request_path)
    var request_value: Variant = JSON.parse_string(request_text)
    var response := _handle_request(request_value)
    var response_file := FileAccess.open(response_path, FileAccess.WRITE)
    if response_file == null:
        push_error("Could not write worker response: " + response_path)
        quit(3)
        return

    response_file.store_string(JSON.stringify(response))
    response_file.flush()
    response_file.close()
    quit(0 if bool(response.get("ok", false)) else 1)


func _argument_value(arguments: PackedStringArray, prefix: String) -> String:
    for argument in arguments:
        if argument.begins_with(prefix):
            return argument.trim_prefix(prefix)
    return ""


func _handle_request(request_value: Variant) -> Dictionary:
    if typeof(request_value) != TYPE_DICTIONARY:
        return _error_response("", "invalid_request", "Request must be a JSON object.")

    var request: Dictionary = request_value
    var request_id := str(request.get("request_id", ""))
    var response := {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "engine_version": Engine.get_version_info().get("string", "unknown"),
        "renderer": RenderingServer.get_current_rendering_method(),
        "ok": false
    }

    if int(request.get("protocol_version", -1)) != PROTOCOL_VERSION:
        response["error_code"] = "protocol_mismatch"
        response["error"] = "Unsupported worker protocol version."
        return response

    var operation := str(request.get("operation", ""))
    var payload: Variant = request.get("payload", {})
    if typeof(payload) != TYPE_DICTIONARY:
        response["error_code"] = "invalid_payload"
        response["error"] = "Request payload must be a JSON object."
        return response

    if operation == "ping":
        response["ok"] = true
        response["capabilities"] = ["ping", "glb_inspect", "scene_metrics", "skeleton_report"]
        return response

    if operation == "inspect_glb":
        var inspection := _inspect_glb(payload)
        for key in inspection:
            response[key] = inspection[key]
        return response

    response["error_code"] = "unsupported_operation"
    response["error"] = "Unsupported worker operation: " + operation
    return response


func _inspect_glb(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var source_path := _normalise_path(str(payload.get("source_path", "")))
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {
            "error_code": "invalid_project_root",
            "error": "A valid project root is required."
        }
    var root_prefix := project_root.trim_suffix("/") + "/"
    if not source_path.to_lower().begins_with(root_prefix.to_lower()):
        return {
            "error_code": "path_outside_project",
            "error": "The GLB path resolves outside the supplied project directory."
        }
    if source_path.is_empty() or not source_path.to_lower().ends_with(".glb"):
        return {
            "error_code": "invalid_glb_path",
            "error": "A GLB file path is required."
        }
    if not FileAccess.file_exists(source_path):
        return {
            "error_code": "glb_not_found",
            "error": "The requested GLB file does not exist."
        }

    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var import_error := document.append_from_file(source_path, state)
    if import_error != OK:
        return {
            "error_code": "glb_import_failed",
            "error": "Godot could not import the GLB file.",
            "godot_error": import_error
        }

    var scene := document.generate_scene(state)
    if scene == null:
        return {
            "error_code": "glb_scene_failed",
            "error": "Godot imported the GLB but did not generate a scene."
        }

    var animation_count := 0
    var animation_players := scene.find_children("*", "AnimationPlayer", true, false)
    for player in animation_players:
        animation_count += (player as AnimationPlayer).get_animation_list().size()
    var skeleton_nodes := scene.find_children("*", "Skeleton3D", true, false)
    var skeleton_reports: Array[Dictionary] = []
    for skeleton_node in skeleton_nodes:
        var skeleton := skeleton_node as Skeleton3D
        var bones: Array[Dictionary] = []
        for bone_index in range(skeleton.get_bone_count()):
            var parent_index := skeleton.get_bone_parent(bone_index)
            bones.append({
                "index": bone_index,
                "name": str(skeleton.get_bone_name(bone_index)),
                "parent_index": parent_index,
                "parent_name": str(skeleton.get_bone_name(parent_index)) if parent_index >= 0 else ""
            })
        skeleton_reports.append({
            "node_path": str(scene.get_path_to(skeleton)),
            "bone_count": skeleton.get_bone_count(),
            "bones": bones
        })

    var result := {
        "ok": true,
        "mesh_count": scene.find_children("*", "MeshInstance3D", true, false).size(),
        "skeleton_count": skeleton_nodes.size(),
        "skeletons": skeleton_reports,
        "animation_player_count": animation_players.size(),
        "animation_count": animation_count,
        "node_count": _count_nodes(scene)
    }
    scene.free()
    return result


func _normalise_path(value: String) -> String:
    return value.replace("\\", "/").simplify_path()


func _count_nodes(node: Node) -> int:
    var total := 1
    for child in node.get_children():
        total += _count_nodes(child)
    return total


func _error_response(request_id: String, code: String, message: String) -> Dictionary:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "request_id": request_id,
        "engine_version": Engine.get_version_info().get("string", "unknown"),
        "renderer": RenderingServer.get_current_rendering_method(),
        "ok": false,
        "error_code": code,
        "error": message
    }
