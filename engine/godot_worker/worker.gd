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
    await process_frame
    var response: Dictionary = await _handle_request(request_value)
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
        response["capabilities"] = [
            "ping", "glb_inspect", "scene_metrics", "skeleton_report", "retarget_glb_pair", "assemble_modular_character"
        ]
        return response

    if operation == "inspect_glb":
        var inspection := _inspect_glb(payload)
        for key in inspection:
            response[key] = inspection[key]
        return response

    if operation == "assemble_modular_character":
        var assembly_result: Dictionary = await _assemble_modular_character(payload)
        for key in assembly_result:
            response[key] = assembly_result[key]
        return response

    if operation == "retarget_glb_pair":
        var retarget_result: Dictionary = await _retarget_glb_pair(payload)
        for key in retarget_result:
            response[key] = retarget_result[key]
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

    var glb_document := _read_glb_json(source_path)
    var animation_count := 0
    var animation_names: Array[String] = []
    var animation_players := scene.find_children("*", "AnimationPlayer", true, false)
    for player in animation_players:
        var animation_player := player as AnimationPlayer
        var player_animation_names := animation_player.get_animation_list()
        animation_count += player_animation_names.size()
        for animation_value in player_animation_names:
            var animation_label := str(animation_value)
            if animation_label.get_file().to_upper() != "RESET" and not animation_names.has(animation_label):
                animation_names.append(animation_label)
    var mesh_nodes := scene.find_children("*", "MeshInstance3D", true, false)
    var mesh_inventory: Array[Dictionary] = []
    for mesh_node in mesh_nodes:
        var mesh_instance := mesh_node as MeshInstance3D
        var mesh_resource := mesh_instance.mesh
        if mesh_resource == null:
            continue
        var surface_names: Array[String] = []
        var material_names: Array[String] = []
        for surface_index in range(mesh_resource.get_surface_count()):
            surface_names.append(str(mesh_resource.surface_get_name(surface_index)))
            var surface_material := mesh_instance.get_active_material(surface_index)
            material_names.append(str(surface_material.resource_name) if surface_material != null else "")
        var blend_shape_names: Array[String] = []
        for shape_index in range(mesh_instance.get_blend_shape_count()):
            blend_shape_names.append(str(mesh_resource.get_blend_shape_name(shape_index)))
        var skeleton_path := str(mesh_instance.get_skeleton_path())
        var bound_skeleton := mesh_instance.get_node_or_null(mesh_instance.get_skeleton_path()) as Skeleton3D if not skeleton_path.is_empty() else null
        var bounds := mesh_resource.get_aabb()
        var slot_candidate := _classify_mesh_slot(
            str(mesh_instance.name) + " " + str(mesh_resource.resource_name) + " " + str(scene.get_path_to(mesh_instance))
        )
        mesh_inventory.append({
            "node_path": str(scene.get_path_to(mesh_instance)),
            "node_name": str(mesh_instance.name),
            "mesh_resource_name": str(mesh_resource.resource_name),
            "mesh_type": mesh_resource.get_class(),
            "surface_count": mesh_resource.get_surface_count(),
            "surface_names": surface_names,
            "material_names": material_names,
            "blend_shape_names": blend_shape_names,
            "skin_bound": mesh_instance.skin != null,
            "skeleton_path": skeleton_path,
            "skeleton_bone_count": bound_skeleton.get_bone_count() if bound_skeleton != null else 0,
            "bounds": {
                "position": [bounds.position.x, bounds.position.y, bounds.position.z],
                "size": [bounds.size.x, bounds.size.y, bounds.size.z]
            },
            "slot_candidate": slot_candidate
        })
    var morph_targets: Array[Dictionary] = []
    for mesh_node in mesh_nodes:
        var mesh_instance := mesh_node as MeshInstance3D
        var array_mesh := mesh_instance.mesh as ArrayMesh
        if array_mesh == null:
            continue
        for shape_index in range(mesh_instance.get_blend_shape_count()):
            var default_info = _glb_morph_default(
                glb_document,
                mesh_instance,
                shape_index,
                mesh_instance.get_blend_shape_value(shape_index)
            )
            morph_targets.append({
                "mesh_path": str(scene.get_path_to(mesh_instance)),
                "mesh_name": str(mesh_instance.name),
                "mesh_resource_name": str(array_mesh.resource_name),
                "index": shape_index,
                "name": str(array_mesh.get_blend_shape_name(shape_index)),
                "default_value": default_info.get(
                    "value",
                    mesh_instance.get_blend_shape_value(shape_index)
                ),
                "default_value_source": default_info.get("source", "godot_runtime")
            })
    var skeleton_nodes := scene.find_children("*", "Skeleton3D", true, false)
    var skeleton_reports: Array[Dictionary] = []
    for skeleton_node in skeleton_nodes:
        var skeleton := skeleton_node as Skeleton3D
        var bones: Array[Dictionary] = []
        for bone_index in range(skeleton.get_bone_count()):
            var parent_index := skeleton.get_bone_parent(bone_index)
            var rest := skeleton.get_bone_rest(bone_index)
            var rest_rotation := rest.basis.get_rotation_quaternion()
            var rest_scale := rest.basis.get_scale()
            bones.append({
                "index": bone_index,
                "name": str(skeleton.get_bone_name(bone_index)),
                "parent_index": parent_index,
                "parent_name": str(skeleton.get_bone_name(parent_index)) if parent_index >= 0 else "",
                "rest_transform": {
                    "origin": [rest.origin.x, rest.origin.y, rest.origin.z],
                    "rotation": [rest_rotation.x, rest_rotation.y, rest_rotation.z, rest_rotation.w],
                    "scale": [rest_scale.x, rest_scale.y, rest_scale.z]
                }
            })
        skeleton_reports.append({
            "node_path": str(scene.get_path_to(skeleton)),
            "bone_count": skeleton.get_bone_count(),
            "bones": bones
        })

    var result := {
        "ok": true,
        "mesh_count": mesh_nodes.size(),
        "mesh_inventory": mesh_inventory,
        "morph_target_count": morph_targets.size(),
        "morph_targets": morph_targets,
        "skeleton_count": skeleton_nodes.size(),
        "skeletons": skeleton_reports,
        "animation_player_count": animation_players.size(),
        "animation_count": animation_count,
        "animation_names": animation_names,
        "node_count": _count_nodes(scene)
    }
    scene.free()
    return result


func _assemble_modular_character(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var base_path := _normalise_path(str(payload.get("base_path", "")))
    var output_path := _normalise_path(str(payload.get("output_path", "")))
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    for path in [base_path, output_path]:
        if not path.to_lower().begins_with(root_prefix.to_lower()):
            return {"error_code": "path_outside_project", "error": "An assembly path resolves outside the project directory."}
    if not base_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(base_path):
        return {"error_code": "base_glb_missing", "error": "The base character GLB does not exist."}
    if not output_path.to_lower().ends_with(".glb") or FileAccess.file_exists(output_path):
        return {"error_code": "invalid_output_path", "error": "Assembly output must be a new .glb file."}

    var parts_value: Variant = payload.get("parts", [])
    if typeof(parts_value) != TYPE_ARRAY or parts_value.size() != 4:
        return {"error_code": "invalid_parts", "error": "Exactly four modular parts are required."}
    var required_slots := ["head", "body", "legs", "feet"]
    var selected_slots: Array[String] = []
    var selected_mesh_keys: Array[String] = []
    for part_value in parts_value:
        if typeof(part_value) != TYPE_DICTIONARY:
            return {"error_code": "invalid_part", "error": "Each modular part must be an object."}
        var part: Dictionary = part_value
        var slot := str(part.get("slot", ""))
        var source_path := _normalise_path(str(part.get("source_path", "")))
        var mesh_path := str(part.get("mesh_path", ""))
        if not required_slots.has(slot) or selected_slots.has(slot):
            return {"error_code": "invalid_slot", "error": "Select exactly one part for each of head, body, legs and feet."}
        if not source_path.to_lower().begins_with(root_prefix.to_lower()) or not source_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(source_path):
            return {"error_code": "invalid_part_path", "error": "A modular part GLB is missing or outside the project."}
        if mesh_path.is_empty() or mesh_path.length() > 1024:
            return {"error_code": "invalid_mesh_path", "error": "A modular part mesh path is invalid."}
        var mesh_key := source_path + "|" + mesh_path
        if selected_mesh_keys.has(mesh_key):
            return {"error_code": "duplicate_mesh", "error": "The same source mesh cannot fill multiple modular slots."}
        selected_mesh_keys.append(mesh_key)
        selected_slots.append(slot)
    for slot in required_slots:
        if not selected_slots.has(slot):
            return {"error_code": "missing_slot", "error": "Missing required modular slot: " + slot}

    var base_document := GLTFDocument.new()
    var base_state := GLTFState.new()
    var import_error := base_document.append_from_file(base_path, base_state)
    if import_error != OK:
        return {"error_code": "base_import_failed", "error": "Godot could not import the base character GLB.", "godot_error": import_error}
    var base_scene := base_document.generate_scene(base_state)
    if base_scene == null:
        return {"error_code": "base_scene_failed", "error": "Godot could not create the base character scene."}
    root.add_child(base_scene)
    await process_frame
    var target_skeletons := base_scene.find_children("*", "Skeleton3D", true, false)
    if target_skeletons.size() != 1:
        base_scene.queue_free()
        return {"error_code": "base_skeleton_count", "error": "The base character must contain exactly one Skeleton3D."}
    var target_skeleton := target_skeletons[0] as Skeleton3D
    var base_animation_names := _scene_animation_names(base_scene)
    var removed_base_meshes: Array[String] = []
    for base_mesh_node in base_scene.find_children("*", "MeshInstance3D", true, false):
        var base_mesh := base_mesh_node as MeshInstance3D
        if base_mesh.skin == null:
            continue
        removed_base_meshes.append(str(base_scene.get_path_to(base_mesh)))
        base_mesh.queue_free()
    await process_frame
    var added_parts: Array[Dictionary] = []
    var total_added := 0

    for part_value in parts_value:
        var part: Dictionary = part_value
        var slot := str(part["slot"])
        var source_path := _normalise_path(str(part["source_path"]))
        var source_document := GLTFDocument.new()
        var source_state := GLTFState.new()
        var source_error := source_document.append_from_file(source_path, source_state)
        if source_error != OK:
            base_scene.queue_free()
            return {"error_code": "part_import_failed", "error": "Godot could not import the " + slot + " part GLB.", "godot_error": source_error}
        var source_scene := source_document.generate_scene(source_state)
        if source_scene == null:
            base_scene.queue_free()
            return {"error_code": "part_scene_failed", "error": "Godot could not create the " + slot + " part scene."}
        root.add_child(source_scene)
        await process_frame
        var mesh_node := source_scene.get_node_or_null(NodePath(str(part["mesh_path"]))) as MeshInstance3D
        if mesh_node == null or mesh_node.mesh == null:
            source_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "part_mesh_missing", "error": "The selected " + slot + " mesh node was not found."}
        if mesh_node.skin == null:
            source_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "part_not_skinned", "error": "The selected " + slot + " mesh is not bound to a skin; rigid parts cannot be safely attached to the shared rig yet."}
        var source_skeleton := mesh_node.get_node_or_null(mesh_node.get_skeleton_path()) as Skeleton3D
        if source_skeleton == null:
            source_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "part_skeleton_missing", "error": "The selected " + slot + " mesh has no resolvable Skeleton3D."}
        if not _skeletons_compatible(source_skeleton, target_skeleton):
            source_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "incompatible_skeleton", "error": "The " + slot + " part uses a different bone order, hierarchy or rest pose. It must be retargeted before assembly."}
        if not _transforms_compatible(source_skeleton.global_transform, target_skeleton.global_transform):
            source_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "incompatible_skeleton_transform", "error": "The " + slot + " part rig has a different world transform; automatic alignment is not safe."}
        var skin_resource := mesh_node.skin
        for bind_index in range(skin_resource.get_bind_count()):
            var bind_name := str(skin_resource.get_bind_name(bind_index))
            if not bind_name.is_empty():
                if source_skeleton.find_bone(bind_name) < 0:
                    source_scene.queue_free()
                    base_scene.queue_free()
                    return {"error_code": "invalid_skin_bind", "error": "The " + slot + " skin references a bone name missing from its skeleton: " + bind_name}
            else:
                var bind_bone := skin_resource.get_bind_bone(bind_index)
                if bind_bone < 0 or bind_bone >= source_skeleton.get_bone_count():
                    source_scene.queue_free()
                    base_scene.queue_free()
                    return {"error_code": "invalid_skin_bind", "error": "The " + slot + " skin contains an out-of-range bone index."}
        var cloned_mesh := mesh_node.duplicate() as MeshInstance3D
        if cloned_mesh == null:
            source_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "mesh_clone_failed", "error": "Godot could not duplicate the " + slot + " mesh."}
        var source_global_transform := mesh_node.global_transform
        base_scene.add_child(cloned_mesh)
        cloned_mesh.owner = base_scene
        cloned_mesh.name = "Modular_" + slot.capitalize()
        cloned_mesh.transform = base_scene.global_transform.affine_inverse() * source_global_transform
        cloned_mesh.set_skeleton_path(NodePath(str(cloned_mesh.get_path_to(target_skeleton))))
        total_added += 1
        added_parts.append({
            "slot": slot,
            "source_path": source_path,
            "mesh_path": str(part["mesh_path"]),
            "mesh_name": str(mesh_node.name),
            "bone_count": source_skeleton.get_bone_count(),
            "skin_bind_count": skin_resource.get_bind_count()
        })
        source_scene.queue_free()
        await process_frame

    var export_document := GLTFDocument.new()
    var export_state := GLTFState.new()
    var export_error := export_document.append_from_scene(base_scene, export_state)
    if export_error != OK:
        base_scene.queue_free()
        return {"error_code": "assembly_export_prepare_failed", "error": "Godot could not prepare the assembled character for GLB export.", "godot_error": export_error}
    var output_error := export_document.write_to_filesystem(export_state, output_path)
    base_scene.queue_free()
    if output_error != OK or not FileAccess.file_exists(output_path):
        if FileAccess.file_exists(output_path):
            DirAccess.remove_absolute(output_path)
        return {"error_code": "assembly_export_failed", "error": "Godot could not write the assembled GLB.", "godot_error": output_error}

    var verification := _inspect_glb({"project_root": project_root, "source_path": output_path})
    if not bool(verification.get("ok", false)):
        DirAccess.remove_absolute(output_path)
        return {"error_code": "assembly_verification_failed", "error": str(verification.get("error", "The exported GLB failed re-import verification."))}
    var verified_animations: Array = verification.get("animation_names", [])
    for animation_name in base_animation_names:
        if not verified_animations.has(animation_name):
            DirAccess.remove_absolute(output_path)
            return {"error_code": "animation_preservation_failed", "error": "The assembled GLB did not preserve base animation clip: " + str(animation_name)}
    var verified_mesh_names: Array[String] = []
    for mesh_entry in verification.get("mesh_inventory", []):
        verified_mesh_names.append(str(mesh_entry.get("node_name", "")))
    for part_entry in added_parts:
        var expected_mesh_name := "Modular_" + str(part_entry["slot"]).capitalize()
        if not verified_mesh_names.has(expected_mesh_name):
            DirAccess.remove_absolute(output_path)
            return {"error_code": "mesh_verification_failed", "error": "The exported GLB did not retain the selected " + str(part_entry["slot"]) + " mesh."}
    verification["added_parts"] = added_parts
    verification["base_animation_names"] = base_animation_names
    verification["base_skinned_meshes_removed"] = removed_base_meshes
    verification["animation_preserved"] = true
    verification["assembly_verified"] = true
    return verification


func _scene_animation_names(scene: Node) -> Array[String]:
    var names: Array[String] = []
    for player_node in scene.find_children("*", "AnimationPlayer", true, false):
        var player := player_node as AnimationPlayer
        for animation_name in player.get_animation_list():
            var label := str(animation_name)
            if label.get_file().to_upper() != "RESET" and not names.has(label):
                names.append(label)
    return names


func _skeletons_compatible(source: Skeleton3D, target: Skeleton3D) -> bool:
    if source.get_bone_count() != target.get_bone_count():
        return false
    for bone_index in range(source.get_bone_count()):
        if source.get_bone_name(bone_index) != target.get_bone_name(bone_index):
            return false
        if source.get_bone_parent(bone_index) != target.get_bone_parent(bone_index):
            return false
        var source_rest := source.get_bone_rest(bone_index)
        var target_rest := target.get_bone_rest(bone_index)
        if not _transforms_compatible(source_rest, target_rest):
            return false
    return true


func _transforms_compatible(source: Transform3D, target: Transform3D) -> bool:
    if source.origin.distance_to(target.origin) > 0.001:
        return false
    if source.basis.x.distance_to(target.basis.x) > 0.001:
        return false
    if source.basis.y.distance_to(target.basis.y) > 0.001:
        return false
    if source.basis.z.distance_to(target.basis.z) > 0.001:
        return false
    return true


func _classify_mesh_slot(source_name: String) -> String:
    var normalized := source_name.to_lower().replace("-", "_").replace(" ", "_")
    var searchable := normalized
    var slot_tokens := {
        "head": ["head", "hair", "face", "skull"],
        "body": ["body", "torso", "chest", "shirt", "jacket", "coat"],
        "legs": ["legs", "leg", "pants", "trousers", "shorts"],
        "feet": ["feet", "foot", "shoes", "shoe", "boots", "boot"]
    }
    for slot_name in ["head", "body", "legs", "feet"]:
        for token in slot_tokens[slot_name]:
            if searchable.contains(token):
                return slot_name
    return ""


func _read_glb_json(path: String) -> Dictionary:
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null or file.get_length() < 20:
        return {}
    file.seek(12)
    var json_length := file.get_32()
    var chunk_type := file.get_32()
    if chunk_type != 0x4E4F534A or json_length <= 0 or json_length > file.get_length() - 20:
        file.close()
        return {}
    var parsed: Variant = JSON.parse_string(file.get_buffer(json_length).get_string_from_utf8())
    file.close()
    if typeof(parsed) == TYPE_DICTIONARY:
        return parsed
    return {}


func _glb_morph_default(
    glb_document: Dictionary,
    mesh_instance: MeshInstance3D,
    shape_index: int,
    runtime_value: float
) -> Dictionary:
    var nodes: Array = glb_document.get("nodes", [])
    var meshes: Array = glb_document.get("meshes", [])
    var matching_nodes: Array[Dictionary] = []
    for node_value in nodes:
        if typeof(node_value) != TYPE_DICTIONARY:
            continue
        var node: Dictionary = node_value
        if str(node.get("name", "")) == str(mesh_instance.name) and node.has("mesh"):
            matching_nodes.append(node)
    if matching_nodes.size() == 1:
        var node: Dictionary = matching_nodes[0]
        var mesh_index := int(node.get("mesh", -1))
        if mesh_index >= 0 and mesh_index < meshes.size():
            var mesh: Dictionary = meshes[mesh_index]
            var weights: Array = node.get("weights", mesh.get("weights", []))
            if shape_index < weights.size():
                return {
                    "value": float(weights[shape_index]),
                    "source": "gltf_node" if node.has("weights") else "gltf_mesh"
                }
    var mesh_name := str((mesh_instance.mesh as Resource).resource_name)
    var matching_meshes: Array[Dictionary] = []
    for mesh_value in meshes:
        if typeof(mesh_value) != TYPE_DICTIONARY:
            continue
        var mesh: Dictionary = mesh_value
        if str(mesh.get("name", "")) == mesh_name:
            matching_meshes.append(mesh)
    if matching_meshes.size() == 1:
        var weights: Array = matching_meshes[0].get("weights", [])
        if shape_index < weights.size():
            return {"value": float(weights[shape_index]), "source": "gltf_mesh"}
    return {"value": runtime_value, "source": "godot_runtime"}


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


func _rename_animation_bone_tracks(
    animation_player: AnimationPlayer,
    original_bone_name: String,
    profile_bone_name: String
) -> void:
    for animation_name in animation_player.get_animation_list():
        var animation := animation_player.get_animation(animation_name)
        if animation == null:
            continue
        for track_index in range(animation.get_track_count()):
            var track_path := animation.track_get_path(track_index)
            var updated_path := str(track_path)
            var changed := false
            for subname_index in range(track_path.get_subname_count()):
                if str(track_path.get_subname(subname_index)) == original_bone_name:
                    updated_path = updated_path.replace(
                        ":" + original_bone_name,
                        ":" + profile_bone_name
                    )
                    changed = true
            if changed:
                animation.track_set_path(track_index, NodePath(updated_path))


func _retarget_glb_pair(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var source_path := _normalise_path(str(payload.get("source_path", "")))
    var target_path := _normalise_path(str(payload.get("target_path", "")))
    var output_path := _normalise_path(str(payload.get("output_path", "")))
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    for asset_path in [source_path, target_path]:
        if not asset_path.to_lower().begins_with(root_prefix.to_lower()):
            return {"error_code": "path_outside_project", "error": "A GLB path resolves outside the project."}
        if not asset_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(asset_path):
            return {"error_code": "invalid_glb_path", "error": "Both source and target GLB files must exist."}
    if not output_path.to_lower().begins_with(root_prefix.to_lower()):
        return {"error_code": "path_outside_project", "error": "The retarget scene path resolves outside the project."}
    if not output_path.to_lower().ends_with(".tscn"):
        return {"error_code": "invalid_output_path", "error": "Retarget output must use the .tscn extension."}
    if FileAccess.file_exists(output_path):
        return {"error_code": "output_exists", "error": "Refusing to overwrite an existing retarget scene."}

    var source_document := GLTFDocument.new()
    var source_state := GLTFState.new()
    var source_error := source_document.append_from_file(source_path, source_state)
    if source_error != OK:
        return {"error_code": "source_import_failed", "error": "Godot could not import the source GLB.", "godot_error": source_error}
    var source_scene := source_document.generate_scene(source_state)
    if source_scene == null:
        return {"error_code": "source_scene_failed", "error": "Godot could not generate the source scene."}

    var target_document := GLTFDocument.new()
    var target_state := GLTFState.new()
    var target_error := target_document.append_from_file(target_path, target_state)
    if target_error != OK:
        source_scene.free()
        return {"error_code": "target_import_failed", "error": "Godot could not import the target GLB.", "godot_error": target_error}
    var target_scene := target_document.generate_scene(target_state)
    if target_scene == null:
        source_scene.free()
        return {"error_code": "target_scene_failed", "error": "Godot could not generate the target scene."}

    var source_skeletons := source_scene.find_children("*", "Skeleton3D", true, false)
    var target_skeletons := target_scene.find_children("*", "Skeleton3D", true, false)
    if source_skeletons.size() != 1 or target_skeletons.size() != 1:
        source_scene.free()
        target_scene.free()
        return {
            "error_code": "ambiguous_skeleton_count",
            "error": "Retargeting requires exactly one Skeleton3D in each imported GLB.",
            "source_skeleton_count": source_skeletons.size(),
            "target_skeleton_count": target_skeletons.size()
        }
    var source_skeleton := source_skeletons[0] as Skeleton3D
    var target_skeleton := target_skeletons[0] as Skeleton3D
    var source_mapping: Dictionary = payload.get("source_profile_mapping", {})
    var target_mapping: Dictionary = payload.get("target_profile_mapping", {})
    var required_profile_bones := [
        "Hips", "Spine", "Head",
        "LeftUpperLeg", "LeftLowerLeg", "LeftFoot",
        "RightUpperLeg", "RightLowerLeg", "RightFoot",
        "LeftUpperArm", "LeftLowerArm", "LeftHand",
        "RightUpperArm", "RightLowerArm", "RightHand"
    ]
    for profile_bone in required_profile_bones:
        if not source_mapping.has(profile_bone) or not target_mapping.has(profile_bone):
            source_scene.free()
            target_scene.free()
            return {"error_code": "incomplete_profile_mapping", "error": "Both rigs must map all 15 core humanoid bones."}

    var source_indices: Array[int] = []
    var target_indices: Array[int] = []
    for profile_bone in required_profile_bones:
        var source_index := int(source_mapping[profile_bone].get("bone_index", -1))
        var target_index := int(target_mapping[profile_bone].get("bone_index", -1))
        if source_index < 0 or source_index >= source_skeleton.get_bone_count():
            source_scene.free()
            target_scene.free()
            return {"error_code": "invalid_source_mapping", "error": "Source humanoid mapping contains an invalid bone index."}
        if target_index < 0 or target_index >= target_skeleton.get_bone_count():
            source_scene.free()
            target_scene.free()
            return {"error_code": "invalid_target_mapping", "error": "Target humanoid mapping contains an invalid bone index."}
        if source_indices.has(source_index) or target_indices.has(target_index):
            source_scene.free()
            target_scene.free()
            return {"error_code": "duplicate_profile_mapping", "error": "A source or target bone is mapped more than once."}
        source_indices.append(source_index)
        target_indices.append(target_index)

    var source_players := source_scene.find_children("*", "AnimationPlayer", true, false)
    if source_players.is_empty():
        source_scene.free()
        target_scene.free()
        return {"error_code": "source_animation_missing", "error": "Source GLB contains no AnimationPlayer."}
    var source_player := source_players[0] as AnimationPlayer

    for profile_bone in required_profile_bones:
        var source_index := int(source_mapping[profile_bone]["bone_index"])
        var source_original_name := source_skeleton.get_bone_name(source_index)
        if source_original_name != profile_bone:
            _rename_animation_bone_tracks(source_player, source_original_name, profile_bone)
        source_skeleton.set_bone_name(source_index, profile_bone)
        target_skeleton.set_bone_name(int(target_mapping[profile_bone]["bone_index"]), profile_bone)

    var target_meshes := target_scene.find_children("*", "MeshInstance3D", true, false)
    var bound_target_meshes: Array[MeshInstance3D] = []
    for mesh_node in target_meshes:
        var mesh := mesh_node as MeshInstance3D
        if mesh.skeleton.is_empty():
            continue
        if mesh.get_node_or_null(mesh.skeleton) == target_skeleton:
            bound_target_meshes.append(mesh)
    if bound_target_meshes.is_empty():
        source_scene.free()
        target_scene.free()
        return {"error_code": "target_skin_missing", "error": "Target GLB has no mesh bound to its humanoid skeleton."}

    var requested_animation := str(payload.get("animation_name", ""))
    var selected_animation := ""
    for animation_name in source_player.get_animation_list():
        var name := str(animation_name)
        if name.to_upper() == "RESET":
            continue
        if requested_animation.is_empty() or name == requested_animation:
            selected_animation = name
            break
    if selected_animation.is_empty():
        source_scene.free()
        target_scene.free()
        return {"error_code": "animation_not_found", "error": "The requested source animation does not exist."}

    source_player.autoplay = selected_animation
    source_player.play(selected_animation)

    var combined_root := Node3D.new()
    combined_root.name = "RetargetedCharacterScene"
    source_scene.name = "SourceCharacter"
    target_scene.name = "TargetCharacter"
    combined_root.add_child(source_scene)
    combined_root.add_child(target_scene)
    root.add_child(combined_root)

    var modifier := RetargetModifier3D.new()
    modifier.name = "RetargetModifier3D"
    target_skeleton.name = "RetargetTargetSkeleton"
    modifier.profile = SkeletonProfileHumanoid.new()
    modifier.use_global_pose = false
    source_skeleton.add_child(modifier)
    var target_parent := target_skeleton.get_parent() as Node3D
    if target_parent == null:
        combined_root.queue_free()
        return {"error_code": "invalid_target_parent", "error": "Target skeleton must have a Node3D parent."}
    var target_global_transform := target_parent.global_transform * target_skeleton.transform
    var modifier_global_transform := modifier.global_transform
    target_skeleton.owner = null
    target_skeleton.reparent(modifier, false)
    target_skeleton.transform = (
        modifier_global_transform.affine_inverse() * target_global_transform
    )
    for mesh in bound_target_meshes:
        mesh.skeleton = mesh.get_path_to(target_skeleton)

    _set_scene_ownership(combined_root, combined_root)
    var packed_scene := PackedScene.new()
    var pack_error := packed_scene.pack(combined_root)
    if pack_error != OK:
        combined_root.queue_free()
        return {"error_code": "scene_pack_failed", "error": "Could not pack the retarget scene.", "godot_error": pack_error}
    var save_error := ResourceSaver.save(packed_scene, output_path)
    if save_error != OK:
        combined_root.queue_free()
        return {"error_code": "scene_save_failed", "error": "Could not save the retarget scene.", "godot_error": save_error}

    var reopened := ResourceLoader.load(output_path) as PackedScene
    if reopened == null:
        combined_root.queue_free()
        return {"error_code": "scene_reopen_failed", "error": "Saved retarget scene could not be reopened."}
    var reopened_instance := reopened.instantiate()
    var reopened_modifier := reopened_instance.find_child("RetargetModifier3D", true, false)
    var reopened_target := reopened_instance.find_child("RetargetTargetSkeleton", true, false)
    var reopened_skin_count := 0
    if reopened_target != null:
        for mesh_node in reopened_instance.find_children("*", "MeshInstance3D", true, false):
            var reopened_mesh := mesh_node as MeshInstance3D
            if not reopened_mesh.skeleton.is_empty() and reopened_mesh.get_node_or_null(reopened_mesh.skeleton) == reopened_target:
                reopened_skin_count += 1
    var scene_reopened := (
        reopened_modifier != null
        and reopened_target != null
        and reopened_skin_count == bound_target_meshes.size()
    )
    var pose_transferred := false
    var source_angle := 0.0
    var target_angle := 0.0
    var source_animation_playing := false
    var source_pose_changed := false
    var target_pose_matches := false
    var sampled_animation_time := 0.0
    if scene_reopened:
        root.add_child(reopened_instance)
        var source_players_after_reopen := reopened_instance.find_children(
            "*", "AnimationPlayer", true, false
        )
        if not source_players_after_reopen.is_empty():
            var reopened_player := source_players_after_reopen[0] as AnimationPlayer
            await process_frame
            source_animation_playing = reopened_player.is_playing()
            var reopened_animation := reopened_player.get_animation(selected_animation)
            if reopened_animation != null:
                sampled_animation_time = reopened_animation.length * 0.37
                reopened_player.seek(sampled_animation_time, true)
            for frame_index in range(3):
                await process_frame
        var reopened_source := reopened_modifier.get_parent() as Skeleton3D
        var source_arm_index := reopened_source.find_bone("LeftUpperArm")
        var target_arm_index := (reopened_target as Skeleton3D).find_bone("LeftUpperArm")
        if source_arm_index >= 0 and target_arm_index >= 0:
            var target_skeleton_after_reopen := reopened_target as Skeleton3D
            var source_pose := reopened_source.get_bone_pose(source_arm_index)
            var target_pose := target_skeleton_after_reopen.get_bone_pose(target_arm_index)
            var source_rest := reopened_source.get_bone_rest(source_arm_index)
            var target_rest := target_skeleton_after_reopen.get_bone_rest(target_arm_index)
            var source_rotation := source_pose.basis.get_rotation_quaternion()
            var target_rotation := target_pose.basis.get_rotation_quaternion()
            source_angle = source_rotation.angle_to(Quaternion.IDENTITY)
            target_angle = target_rotation.angle_to(Quaternion.IDENTITY)

            var source_parent_index := reopened_source.get_bone_parent(source_arm_index)
            var target_parent_index := target_skeleton_after_reopen.get_bone_parent(target_arm_index)
            var source_parent_global_rest := Transform3D.IDENTITY
            var target_parent_global_rest := Transform3D.IDENTITY
            if source_parent_index >= 0:
                source_parent_global_rest = reopened_source.get_bone_global_rest(source_parent_index)
            if target_parent_index >= 0:
                target_parent_global_rest = target_skeleton_after_reopen.get_bone_global_rest(target_parent_index)

            # Match Godot's RetargetModifier3D model-space rest correction. Comparing
            # raw local Euler/Quaternion angles is invalid when source and target
            # rigs have different bone-roll and rest-axis conventions.
            var expected_target_basis := (
                target_parent_global_rest.basis.inverse()
                * source_parent_global_rest.basis
                * source_pose.basis
                * source_rest.basis.inverse()
                * source_parent_global_rest.basis.inverse()
                * target_parent_global_rest.basis
                * target_rest.basis
            )
            var motion_scale_ratio := (
                target_skeleton_after_reopen.get_motion_scale()
                / reopened_source.get_motion_scale()
            )
            var expected_target_origin := (
                target_parent_global_rest.basis.inverse()
                * (
                    source_parent_global_rest.basis
                    * ((source_pose.origin - source_rest.origin) * motion_scale_ratio)
                )
                + target_rest.origin
            )
            source_pose_changed = (
                not source_pose.basis.is_equal_approx(source_rest.basis)
                or not source_pose.origin.is_equal_approx(source_rest.origin)
            )
            target_pose_matches = (
                target_pose.basis.is_equal_approx(expected_target_basis)
                and target_pose.origin.is_equal_approx(expected_target_origin)
            )
            pose_transferred = (
                source_animation_playing
                and source_pose_changed
                and target_pose_matches
            )
    var source_bone_count := source_skeleton.get_bone_count()
    var target_bone_count := target_skeleton.get_bone_count()
    reopened_instance.queue_free()
    combined_root.queue_free()
    await process_frame
    if not scene_reopened:
        DirAccess.remove_absolute(output_path)
        return {"error_code": "scene_reopen_invalid", "error": "Reopened retarget scene is missing its modifier, target skeleton or skin binding."}
    if not pose_transferred:
        DirAccess.remove_absolute(output_path)
        return {
            "error_code": "pose_transfer_failed",
            "error": (
                "The reopened retarget scene did not transfer the animated source upper-arm pose "
                + "to the target skeleton. source_angle_deg="
                + str(rad_to_deg(source_angle))
                + ", target_angle_deg="
                + str(rad_to_deg(target_angle))
                + ", animation_playing="
                + str(source_animation_playing)
                + ", source_pose_changed="
                + str(source_pose_changed)
                + ", target_pose_matches="
                + str(target_pose_matches)
                + ", sample_time="
                + str(sampled_animation_time)
            ),
            "scene_reopened": true
        }

    return {
        "ok": true,
        "output_path": output_path,
        "animation_name": selected_animation,
        "source_bone_count": source_bone_count,
        "target_bone_count": target_bone_count,
        "mapped_bone_count": required_profile_bones.size(),
        "target_skinned_mesh_count": bound_target_meshes.size(),
        "scene_reopened": true,
        "source_animation_playing": source_animation_playing,
        "sampled_animation_time": sampled_animation_time,
        "source_pose_changed": source_pose_changed,
        "target_pose_matches": target_pose_matches,
        "source_pose_angle_degrees": rad_to_deg(source_angle),
        "target_pose_angle_degrees": rad_to_deg(target_angle),
        "pose_transferred": true
    }


func _set_scene_ownership(node: Node, owner_node: Node) -> void:
    for child in node.get_children():
        child.owner = owner_node
        _set_scene_ownership(child, owner_node)
