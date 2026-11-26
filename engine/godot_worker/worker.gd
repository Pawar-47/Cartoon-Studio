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
            "ping", "glb_inspect", "scene_metrics", "skeleton_report", "retarget_glb_pair", "assemble_modular_character", "probe_glb_animation", "export_character_appearance", "customize_character_proportions", "add_character_hair"
        ]
        return response

    if operation == "inspect_glb":
        var inspection := _inspect_glb(payload)
        for key in inspection:
            response[key] = inspection[key]
        return response

    if operation == "export_character_appearance":
        var appearance_result: Dictionary = await _export_character_appearance(payload)
        for key in appearance_result:
            response[key] = appearance_result[key]
        return response

    if operation == "customize_character_proportions":
        var proportion_result: Dictionary = await _customize_character_proportions(payload)
        for key in proportion_result:
            response[key] = proportion_result[key]
        return response

    if operation == "add_character_hair":
        var hair_result: Dictionary = await _add_character_hair(payload)
        for key in hair_result:
            response[key] = hair_result[key]
        return response

    if operation == "assemble_modular_character":
        var assembly_result: Dictionary = await _assemble_modular_character(payload)
        for key in assembly_result:
            response[key] = assembly_result[key]
        return response

    if operation == "probe_glb_animation":
        var probe_result: Dictionary = await _probe_glb_animation(payload)
        for key in probe_result:
            response[key] = probe_result[key]
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
        var material_properties: Array[Dictionary] = []
        for surface_index in range(mesh_resource.get_surface_count()):
            surface_names.append(str(mesh_resource.surface_get_name(surface_index)))
            var surface_material := mesh_instance.get_active_material(surface_index)
            material_names.append(str(surface_material.resource_name) if surface_material != null else "")
            if surface_material is BaseMaterial3D:
                var base_material := surface_material as BaseMaterial3D
                var albedo := base_material.albedo_color
                material_properties.append({
                    "color": [albedo.r, albedo.g, albedo.b, albedo.a],
                    "roughness": base_material.roughness,
                    "metalness": base_material.metallic
                })
            else:
                material_properties.append({})
        var blend_shape_names: Array[String] = []
        for shape_index in range(mesh_instance.get_blend_shape_count()):
            blend_shape_names.append(str(mesh_resource.get_blend_shape_name(shape_index)))
        var skeleton_path := str(mesh_instance.get_skeleton_path())
        var bound_skeleton := mesh_instance.get_node_or_null(mesh_instance.get_skeleton_path()) as Skeleton3D if not skeleton_path.is_empty() else null
        var bounds := mesh_resource.get_aabb()
        var slot_candidate := _classify_mesh_slot(
            str(mesh_instance.name) + " " + str(mesh_resource.resource_name) + " " + str(scene.get_path_to(mesh_instance))
        )
        var attachment_bone := ""
        var parent_node := mesh_instance.get_parent()
        if parent_node is BoneAttachment3D:
            attachment_bone = str((parent_node as BoneAttachment3D).bone_name)
        mesh_inventory.append({
            "node_path": str(scene.get_path_to(mesh_instance)),
            "node_name": str(mesh_instance.name),
            "mesh_resource_name": str(mesh_resource.resource_name),
            "mesh_type": mesh_resource.get_class(),
            "surface_count": mesh_resource.get_surface_count(),
            "surface_names": surface_names,
            "material_names": material_names,
            "material_properties": material_properties,
            "blend_shape_names": blend_shape_names,
            "skin_bound": mesh_instance.skin != null,
            "skeleton_path": skeleton_path,
            "skeleton_bone_count": bound_skeleton.get_bone_count() if bound_skeleton != null else 0,
            "attachment_bone": attachment_bone,
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



func _face_material(color_value: String) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = Color.from_string(color_value, Color.WHITE)
    material.roughness = 0.78
    return material


func _add_face_sphere(
    parent: Node,
    scene_owner: Node,
    mesh_name: String,
    position: Vector3,
    scale: Vector3,
    material: StandardMaterial3D
) -> MeshInstance3D:
    var sphere := SphereMesh.new()
    sphere.radial_segments = 20
    sphere.rings = 12
    var instance := MeshInstance3D.new()
    instance.name = mesh_name
    instance.mesh = sphere
    instance.material_override = material
    instance.position = position
    instance.scale = scale
    parent.add_child(instance)
    instance.owner = scene_owner
    return instance


func _add_face_mouth_segment(
    parent: Node,
    scene_owner: Node,
    mesh_name: String,
    start: Vector3,
    finish: Vector3,
    radius: float,
    material: StandardMaterial3D
) -> MeshInstance3D:
    var delta := finish - start
    var capsule := CapsuleMesh.new()
    capsule.radius = radius
    capsule.height = maxf(delta.length() + radius * 2.0, radius * 2.0)
    var instance := MeshInstance3D.new()
    instance.name = mesh_name
    instance.mesh = capsule
    instance.material_override = material
    instance.position = (start + finish) * 0.5
    if delta.length_squared() > 0.000001:
        instance.quaternion = Quaternion(Vector3.UP, delta.normalized())
    parent.add_child(instance)
    instance.owner = scene_owner
    return instance


func _add_character_face_features(scene: Node, recipe: Dictionary) -> Dictionary:
    if not bool(recipe.get("enabled", false)):
        return {"ok": true, "mesh_count": 0, "attachment_bone": ""}

    var skeleton_nodes := scene.find_children("*", "Skeleton3D", true, false)
    if skeleton_nodes.size() != 1:
        return {"ok": false, "error_code": "face_skeleton_count", "error": "Generated face geometry requires exactly one Skeleton3D."}
    var skeleton := skeleton_nodes[0] as Skeleton3D
    var head_bone_name := ""
    var head_bone_index := -1
    for bone_index in range(skeleton.get_bone_count()):
        var bone_name := str(skeleton.get_bone_name(bone_index))
        var parts := bone_name.to_lower().split(":")
        var token := str(parts[parts.size() - 1]).replace("_", "").replace(" ", "")
        if token == "head":
            head_bone_name = bone_name
            head_bone_index = bone_index
            break
    if head_bone_index < 0:
        return {"ok": false, "error_code": "face_head_bone_missing", "error": "The rig has no recognizable Head bone for generated facial geometry."}

    var head_mesh: MeshInstance3D = null
    var head_bounds := AABB()
    var largest_volume := 0.0
    for mesh_node in scene.find_children("*", "MeshInstance3D", true, false):
        var mesh_instance := mesh_node as MeshInstance3D
        if mesh_instance.mesh == null or mesh_instance.skin == null:
            continue
        var bound_skeleton := mesh_instance.get_node_or_null(mesh_instance.get_skeleton_path()) as Skeleton3D
        if bound_skeleton != skeleton:
            continue
        var label := str(mesh_instance.name) + " " + str(mesh_instance.mesh.resource_name) + " " + str(scene.get_path_to(mesh_instance))
        if _classify_mesh_slot(label) != "head":
            continue
        var candidate := _mesh_bounds_in_bone_space(mesh_instance, skeleton, head_bone_index)
        if candidate.size.x <= 0.01 or candidate.size.y <= 0.01 or candidate.size.z <= 0.01:
            continue
        var volume := candidate.size.x * candidate.size.y * candidate.size.z
        if volume <= largest_volume:
            continue
        largest_volume = volume
        head_mesh = mesh_instance
        head_bounds = candidate
    if head_mesh == null:
        return {"ok": false, "error_code": "face_head_mesh_missing", "error": "A skinned head mesh could not be identified for face placement."}

    for attachment_node in scene.find_children("*", "BoneAttachment3D", true, false):
        var old_attachment := attachment_node as BoneAttachment3D
        if str(old_attachment.name) == "CartoonStudio_Face_Attachment":
            old_attachment.queue_free()
    await process_frame

    var center := head_bounds.get_center()
    var width := maxf(maxf(head_bounds.size.x * 0.56, head_bounds.size.y * 0.18), 0.035)
    var height := maxf(maxf(head_bounds.size.y * 0.48, width * 0.55), 0.035)
    var front_info := _head_front_direction(head_mesh, skeleton, head_bone_index, center)
    var front_direction := float(front_info.get("direction", 1.0))
    var front_z := head_bounds.end.z if front_direction > 0.0 else head_bounds.position.z
    front_z += front_direction * maxf(head_bounds.size.z * 0.035, width * 0.025)
    var eye_scale := clampf(float(recipe.get("eye_scale", 1.0)), 0.65, 1.5)
    var eye_spacing := clampf(float(recipe.get("eye_spacing", 1.0)), 0.65, 1.35)
    var smile := clampf(float(recipe.get("smile", 0.35)), -1.0, 1.0)
    var brow_angle := clampf(float(recipe.get("brow_angle", 0.0)), -0.5, 0.5)
    var eye_depth := maxf(width * 0.045, 0.008)
    var eye_width := width * 0.105 * eye_scale
    var eye_height := height * 0.17 * eye_scale
    var eye_y := center.y + height * 0.10
    var eye_offset := width * 0.245 * eye_spacing

    var attachment := BoneAttachment3D.new()
    attachment.name = "CartoonStudio_Face_Attachment"
    attachment.bone_name = head_bone_name
    skeleton.add_child(attachment)
    attachment.owner = scene
    var eye_material := _face_material(str(recipe.get("eye_color", "#ffffff")))
    var iris_material := _face_material(str(recipe.get("iris_color", "#4b83b8")))
    var pupil_material := _face_material("#17191d")
    var brow_material := _face_material(str(recipe.get("brow_color", "#38251c")))
    var nose_material := _face_material(str(recipe.get("nose_color", "#c98768")))
    var mouth_material := _face_material(str(recipe.get("mouth_color", "#612b2b")))
    var mesh_count := 0

    for side_index in range(2):
        var side: float = -1.0 if side_index == 0 else 1.0
        var eye_x: float = center.x + side * eye_offset
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_EyeWhite_" + str(side),
            Vector3(eye_x, eye_y, front_z),
            Vector3(eye_width, eye_height, eye_depth), eye_material)
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_Iris_" + str(side),
            Vector3(eye_x + width * 0.018, eye_y - height * 0.012, front_z + front_direction * eye_depth * 0.88),
            Vector3(eye_width * 0.49, eye_height * 0.57, eye_depth * 0.42), iris_material)
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_Pupil_" + str(side),
            Vector3(eye_x + width * 0.022, eye_y - height * 0.012, front_z + front_direction * eye_depth * 1.22),
            Vector3(eye_width * 0.23, eye_height * 0.34, eye_depth * 0.22), pupil_material)
        var brow := _add_face_sphere(attachment, scene, "CartoonStudio_Face_Brow_" + str(side),
            Vector3(eye_x, eye_y + eye_height * 1.55, front_z + front_direction * eye_depth * 0.12),
            Vector3(eye_width * 1.32, maxf(height * 0.035, 0.006), eye_depth * 0.38), brow_material)
        brow.rotation.z = -side * brow_angle
        mesh_count += 4

    _add_face_sphere(attachment, scene, "CartoonStudio_Face_Nose",
        Vector3(center.x, center.y - height * 0.08, front_z + front_direction * eye_depth * 0.6),
        Vector3(width * 0.055, height * 0.075, eye_depth * 0.8), nose_material)
    mesh_count += 1

    var mouth_y := center.y - height * 0.30
    var mouth_half := width * 0.19
    var mouth_depth := front_z + front_direction * eye_depth * 0.5
    var mouth_points := [
        Vector3(center.x - mouth_half, mouth_y + smile * height * 0.075, mouth_depth),
        Vector3(center.x - mouth_half * 0.5, mouth_y - smile * height * 0.07, mouth_depth),
        Vector3(center.x + mouth_half * 0.5, mouth_y - smile * height * 0.07, mouth_depth),
        Vector3(center.x + mouth_half, mouth_y + smile * height * 0.075, mouth_depth)
    ]
    var mouth_radius := maxf(width * 0.012, 0.003)
    for segment_index in range(mouth_points.size() - 1):
        _add_face_mouth_segment(attachment, scene,
            "CartoonStudio_Face_Mouth_" + str(segment_index),
            mouth_points[segment_index], mouth_points[segment_index + 1],
            mouth_radius, mouth_material)
        mesh_count += 1

    return {
        "ok": true,
        "mesh_count": mesh_count,
        "attachment_bone": head_bone_name,
        "front_direction": front_direction,
        "fit_basis": "head_mesh_bounds"
    }


func _export_character_appearance(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var source_path := _normalise_path(str(payload.get("source_path", "")))
    var output_path := _normalise_path(str(payload.get("output_path", "")))
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    for path in [source_path, output_path]:
        if not path.to_lower().begins_with(root_prefix.to_lower()):
            return {"error_code": "path_outside_project", "error": "An appearance export path resolves outside the project."}
    if not source_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(source_path):
        return {"error_code": "source_glb_missing", "error": "The appearance source GLB does not exist."}
    if not output_path.to_lower().ends_with(".glb") or FileAccess.file_exists(output_path):
        return {"error_code": "invalid_output_path", "error": "Appearance export must create a new GLB file."}
    var materials_value: Variant = payload.get("materials", [])
    var morphs_value: Variant = payload.get("morph_targets", [])
    var face_features_value: Variant = payload.get("face_features", {})
    if typeof(face_features_value) != TYPE_DICTIONARY:
        return {"error_code": "invalid_face_features", "error": "Face features must be an object."}
    var face_features: Dictionary = face_features_value
    var face_enabled := bool(face_features.get("enabled", false))
    if typeof(materials_value) != TYPE_ARRAY or materials_value.size() > 256:
        return {"error_code": "invalid_material_edits", "error": "Material edits must be an array of at most 256 entries."}
    if typeof(morphs_value) != TYPE_ARRAY or morphs_value.size() > 512:
        return {"error_code": "invalid_morph_edits", "error": "Morph edits must be an array of at most 512 entries."}
    if materials_value.is_empty() and morphs_value.is_empty() and not face_enabled:
        return {"error_code": "empty_appearance", "error": "There are no appearance edits to export."}
    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var import_error := document.append_from_file(source_path, state)
    if import_error != OK:
        return {"error_code": "appearance_import_failed", "error": "Godot could not import the appearance source GLB.", "godot_error": import_error}
    var scene := document.generate_scene(state)
    if scene == null:
        return {"error_code": "appearance_scene_failed", "error": "Godot could not generate the appearance source scene."}
    root.add_child(scene)
    await process_frame
    var source_animation_names := _scene_animation_names(scene)
    var mesh_nodes := scene.find_children("*", "MeshInstance3D", true, false)
    var applied_materials: Array[Dictionary] = []
    for material_value in materials_value:
        if typeof(material_value) != TYPE_DICTIONARY:
            scene.queue_free()
            return {"error_code": "invalid_material_edit", "error": "Each material edit must be an object."}
        var edit: Dictionary = material_value
        var mesh_name := str(edit.get("mesh_name", ""))
        var surface_index := int(edit.get("surface_index", -1))
        var matches: Array[MeshInstance3D] = []
        for mesh_node in mesh_nodes:
            if str(mesh_node.name) == mesh_name:
                matches.append(mesh_node as MeshInstance3D)
        if matches.size() != 1:
            scene.queue_free()
            return {"error_code": "material_mesh_ambiguous", "error": "Material edit mesh name must resolve to exactly one mesh: " + mesh_name}
        var mesh_instance := matches[0]
        if mesh_instance.mesh == null or surface_index < 0 or surface_index >= mesh_instance.mesh.get_surface_count():
            scene.queue_free()
            return {"error_code": "material_surface_missing", "error": "Material surface index is invalid for mesh: " + mesh_name}
        var source_material := mesh_instance.get_active_material(surface_index)
        if not (source_material is BaseMaterial3D):
            scene.queue_free()
            return {"error_code": "material_type_unsupported", "error": "Only imported BaseMaterial3D surfaces can be baked safely: " + mesh_name}
        var edited_material := (source_material as BaseMaterial3D).duplicate() as BaseMaterial3D
        if edited_material == null:
            scene.queue_free()
            return {"error_code": "material_clone_failed", "error": "Godot could not clone a material surface."}
        var color_value := str(edit.get("color", ""))
        if not color_value.is_empty():
            edited_material.albedo_color = Color.from_string(color_value, Color.WHITE)
        if edit.has("roughness"):
            edited_material.roughness = float(edit["roughness"])
        if edit.has("metalness"):
            edited_material.metallic = float(edit["metalness"])
        mesh_instance.set_surface_override_material(surface_index, edited_material)
        applied_materials.append({"mesh_name": mesh_name, "mesh_resource_name": str(mesh_instance.mesh.resource_name), "material_name": str(edit.get("material_name", "")), "surface_index": surface_index, "color": color_value, "roughness": edited_material.roughness, "metalness": edited_material.metallic})
    var applied_morphs: Array[Dictionary] = []
    var morph_export_meshes: Array[MeshInstance3D] = []
    for morph_value in morphs_value:
        if typeof(morph_value) != TYPE_DICTIONARY:
            scene.queue_free()
            return {"error_code": "invalid_morph_edit", "error": "Each morph edit must be an object."}
        var morph: Dictionary = morph_value
        var mesh_name := str(morph.get("mesh_name", ""))
        var target_index := int(morph.get("target_index", -1))
        var target_name := str(morph.get("target_name", ""))
        var mesh_matches: Array[MeshInstance3D] = []
        for mesh_node in mesh_nodes:
            if str(mesh_node.name) == mesh_name:
                mesh_matches.append(mesh_node as MeshInstance3D)
        if mesh_matches.size() != 1:
            scene.queue_free()
            return {"error_code": "morph_mesh_ambiguous", "error": "Morph mesh name must resolve to exactly one mesh: " + mesh_name}
        var morph_mesh := mesh_matches[0]
        if morph_mesh.mesh == null or target_index < 0 or target_index >= morph_mesh.get_blend_shape_count():
            scene.queue_free()
            return {"error_code": "morph_target_missing", "error": "Morph target index is invalid for mesh: " + mesh_name}
        var actual_target_name := str(morph_mesh.mesh.get_blend_shape_name(target_index))
        if actual_target_name != target_name:
            scene.queue_free()
            return {"error_code": "morph_target_mismatch", "error": "Morph target name no longer matches its imported index: " + mesh_name}
        var weight := float(morph.get("value", 0.0))
        if weight < -1.0 or weight > 1.0:
            scene.queue_free()
            return {"error_code": "morph_weight_invalid", "error": "Morph weight must be between minus one and one."}
        morph_mesh.set_blend_shape_value(target_index, weight)
        if not morph_export_meshes.has(morph_mesh):
            morph_export_meshes.append(morph_mesh)
        applied_morphs.append({"mesh_name": mesh_name, "target_index": target_index, "target_name": target_name, "value": weight})
    var face_result := await _add_character_face_features(scene, face_features)
    if not bool(face_result.get("ok", false)):
        scene.queue_free()
        return {"error_code": str(face_result.get("error_code", "face_generation_failed")), "error": str(face_result.get("error", "Godot could not generate face geometry."))}
    var export_document := GLTFDocument.new()
    var export_state := GLTFState.new()
    var export_error := export_document.append_from_scene(scene, export_state)
    if export_error != OK:
        scene.queue_free()
        return {"error_code": "appearance_export_prepare_failed", "error": "Godot could not prepare the edited character for GLB export.", "godot_error": export_error}
    var export_meshes: Array[GLTFMesh] = export_state.get_meshes()
    for morph_mesh in morph_export_meshes:
        var mesh_resource_name := str(morph_mesh.mesh.resource_name)
        var matching_mesh_indices: Array[int] = []
        for candidate_index in range(export_meshes.size()):
            var candidate_mesh: GLTFMesh = export_meshes[candidate_index]
            var candidate_name := candidate_mesh.get_original_name()
            if candidate_name.is_empty() and candidate_mesh.get_mesh() != null:
                candidate_name = candidate_mesh.get_mesh().get_name()
            if not mesh_resource_name.is_empty() and candidate_name == mesh_resource_name:
                matching_mesh_indices.append(candidate_index)
        if matching_mesh_indices.size() != 1:
            scene.queue_free()
            return {"error_code": "morph_mesh_export_mapping_failed", "error": "Godot could not uniquely map facial mesh resource " + mesh_resource_name + " to its exported GLTFMesh."}
        var export_mesh: GLTFMesh = export_meshes[matching_mesh_indices[0]]
        var weights: PackedFloat32Array = export_mesh.get_blend_weights()
        if weights.size() != morph_mesh.get_blend_shape_count():
            scene.queue_free()
            return {"error_code": "morph_weight_count_mismatch", "error": "Exported facial mesh blend-weight count does not match its imported blend shapes."}
        for shape_index in range(morph_mesh.get_blend_shape_count()):
            weights[shape_index] = morph_mesh.get_blend_shape_value(shape_index)
        export_mesh.set_blend_weights(weights)
    var output_error := export_document.write_to_filesystem(export_state, output_path)
    scene.queue_free()
    if output_error != OK or not FileAccess.file_exists(output_path):
        if FileAccess.file_exists(output_path):
            DirAccess.remove_absolute(output_path)
        return {"error_code": "appearance_export_failed", "error": "Godot could not write the customized GLB.", "godot_error": output_error}
    var verification := _inspect_glb({"project_root": project_root, "source_path": output_path})
    if not bool(verification.get("ok", false)):
        DirAccess.remove_absolute(output_path)
        return {"error_code": "appearance_reimport_failed", "error": str(verification.get("error", "The customized GLB failed re-import verification."))}
    var verified_material_surfaces: Array[String] = []
    for edit in applied_materials:
        var material_verified := false
        var index := int(edit["surface_index"])
        for mesh_record in verification.get("mesh_inventory", []):
            var node_name_matches := str(mesh_record.get("node_name", "")) == str(edit["mesh_name"])
            var exported_resource_name := str(mesh_record.get("mesh_resource_name", ""))
            var resource_name_matches := exported_resource_name == str(edit["mesh_resource_name"])
            if not resource_name_matches:
                resource_name_matches = exported_resource_name == "customized_" + str(edit["mesh_resource_name"])
            if not node_name_matches and not resource_name_matches:
                continue
            var properties: Array = mesh_record.get("material_properties", [])
            if index >= properties.size() or properties[index].is_empty():
                continue
            var surface_key := str(mesh_record.get("node_name", "")) + ":" + str(index)
            if verified_material_surfaces.has(surface_key):
                continue
            var actual: Dictionary = properties[index]
            var matches_pbr := absf(float(actual.get("roughness", -1.0)) - float(edit["roughness"])) <= 0.02
            matches_pbr = matches_pbr and absf(float(actual.get("metalness", -1.0)) - float(edit["metalness"])) <= 0.02
            if not str(edit["color"]).is_empty():
                var expected_color := Color.from_string(str(edit["color"]), Color.WHITE)
                var actual_color: Array = actual.get("color", [])
                matches_pbr = matches_pbr and actual_color.size() >= 3
                if actual_color.size() >= 3:
                    matches_pbr = matches_pbr and absf(float(actual_color[0]) - expected_color.r) <= 0.02
                    matches_pbr = matches_pbr and absf(float(actual_color[1]) - expected_color.g) <= 0.02
                    matches_pbr = matches_pbr and absf(float(actual_color[2]) - expected_color.b) <= 0.02
            if matches_pbr:
                material_verified = true
                verified_material_surfaces.append(surface_key)
                break
        if not material_verified:
            DirAccess.remove_absolute(output_path)
            return {"error_code": "appearance_material_verification_failed", "error": "Customized material PBR values were not found after GLB export/re-import."}
    var exported_animation_names: Array = verification.get("animation_names", [])
    if exported_animation_names.size() != source_animation_names.size():
        DirAccess.remove_absolute(output_path)
        return {"error_code": "appearance_animation_verification_failed", "error": "Animation clips were lost during appearance export."}
    for animation_name in source_animation_names:
        if not exported_animation_names.has(animation_name):
            DirAccess.remove_absolute(output_path)
            return {"error_code": "appearance_animation_verification_failed", "error": "An animation clip was lost during appearance export: " + str(animation_name)}
    if face_enabled:
        var face_mesh_count := 0
        var face_attachment_verified := false
        for mesh_record in verification.get("mesh_inventory", []):
            if not str(mesh_record.get("node_name", "")).begins_with("CartoonStudio_Face_"):
                continue
            face_mesh_count += 1
            if str(mesh_record.get("attachment_bone", "")) == str(face_result.get("attachment_bone", "")):
                face_attachment_verified = true
        if face_mesh_count < int(face_result.get("mesh_count", 0)) or not face_attachment_verified:
            DirAccess.remove_absolute(output_path)
            return {"error_code": "appearance_face_verification_failed", "error": "Generated facial meshes or their Head-bone attachment did not survive GLB export and re-import."}
        verification["face_features_verified"] = true
        verification["face_attachment_bone"] = str(face_result.get("attachment_bone", ""))
        verification["face_front_direction"] = float(face_result.get("front_direction", 1.0))
        verification["face_fit_basis"] = str(face_result.get("fit_basis", ""))
    else:
        verification["face_features_verified"] = false
        verification["face_attachment_bone"] = ""
        verification["face_front_direction"] = 0.0
    for edit in applied_morphs:
        var morph_verified := false
        for record in verification.get("morph_targets", []):
            if str(record.get("mesh_name", "")) == str(edit["mesh_name"]) and int(record.get("index", -1)) == int(edit["target_index"]) and str(record.get("name", "")) == str(edit["target_name"]):
                if absf(float(record.get("default_value", 0.0)) - float(edit["value"])) <= 0.02:
                    morph_verified = true
                break
        if not morph_verified:
            DirAccess.remove_absolute(output_path)
            return {"error_code": "appearance_morph_verification_failed", "error": "A facial morph value did not survive GLB export/re-import."}
    verification["appearance_verified"] = true
    verification["applied_material_count"] = applied_materials.size()
    verification["applied_morph_count"] = applied_morphs.size()
    verification["applied_face_feature_count"] = int(face_result.get("mesh_count", 0))
    verification["applied_materials"] = applied_materials
    verification["applied_morph_targets"] = applied_morphs
    return verification




func _add_hair_primitive(parent: Node, scene_owner: Node, primitive: Mesh, mesh_name: String, position: Vector3, scale: Vector3, rotation: Vector3, material: StandardMaterial3D) -> void:
    var instance := MeshInstance3D.new()
    instance.name = mesh_name
    instance.mesh = primitive
    instance.material_override = material
    instance.position = position
    instance.scale = scale
    instance.rotation = rotation
    parent.add_child(instance)
    instance.owner = scene_owner


func _transform_aabb(bounds: AABB, transform: Transform3D) -> AABB:
    var minimum := Vector3(INF, INF, INF)
    var maximum := Vector3(-INF, -INF, -INF)
    for x in [bounds.position.x, bounds.end.x]:
        for y in [bounds.position.y, bounds.end.y]:
            for z in [bounds.position.z, bounds.end.z]:
                var point := transform * Vector3(x, y, z)
                minimum = Vector3(
                    minf(minimum.x, point.x),
                    minf(minimum.y, point.y),
                    minf(minimum.z, point.z)
                )
                maximum = Vector3(
                    maxf(maximum.x, point.x),
                    maxf(maximum.y, point.y),
                    maxf(maximum.z, point.z)
                )
    return AABB(minimum, maximum - minimum)


func _mesh_to_bone_transform(mesh_instance: MeshInstance3D, skeleton: Skeleton3D, bone_index: int) -> Transform3D:
    var mesh_to_skeleton := skeleton.global_transform.affine_inverse() * mesh_instance.global_transform
    return skeleton.get_bone_global_rest(bone_index).affine_inverse() * mesh_to_skeleton


func _mesh_bounds_in_bone_space(mesh_instance: MeshInstance3D, skeleton: Skeleton3D, bone_index: int) -> AABB:
    return _transform_aabb(
        mesh_instance.mesh.get_aabb(),
        _mesh_to_bone_transform(mesh_instance, skeleton, bone_index)
    )


func _head_front_direction(
    mesh_instance: MeshInstance3D,
    skeleton: Skeleton3D,
    bone_index: int,
    head_center: Vector3
) -> Dictionary:
    var mesh_to_bone := _mesh_to_bone_transform(mesh_instance, skeleton, bone_index)
    var feature_materials := ["eye", "brow", "mouth", "lip", "face"]
    var feature_center_z := 0.0
    var feature_surface_count := 0
    for surface_index in range(mesh_instance.mesh.get_surface_count()):
        var material := mesh_instance.get_active_material(surface_index)
        var surface_label := str(mesh_instance.mesh.surface_get_name(surface_index))
        if material != null:
            surface_label += " " + str(material.resource_name)
        var is_face_feature := false
        for token in feature_materials:
            if surface_label.to_lower().contains(token):
                is_face_feature = true
                break
        if not is_face_feature:
            continue
        var surface_arrays := mesh_instance.mesh.surface_get_arrays(surface_index)
        if surface_arrays.size() <= Mesh.ARRAY_VERTEX:
            continue
        var vertex_value: Variant = surface_arrays[Mesh.ARRAY_VERTEX]
        if typeof(vertex_value) != TYPE_PACKED_VECTOR3_ARRAY:
            continue
        var vertices: PackedVector3Array = vertex_value
        if vertices.is_empty():
            continue
        var surface_center := Vector3.ZERO
        for vertex in vertices:
            surface_center += mesh_to_bone * vertex
        feature_center_z += surface_center.z / float(vertices.size())
        feature_surface_count += 1
    if feature_surface_count == 0:
        return {"direction": 1.0, "basis": "default_positive_z"}
    return {
        "direction": 1.0 if feature_center_z / float(feature_surface_count) >= head_center.z else -1.0,
        "basis": "face_feature_surfaces"
    }


func _add_character_hair(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var source_path := _normalise_path(str(payload.get("source_path", "")))
    var output_path := _normalise_path(str(payload.get("output_path", "")))
    var style := str(payload.get("style", "short"))
    var hair_color := str(payload.get("color", "#2b1b13"))
    var styles := ["short", "bob", "long", "ponytail", "spiky", "curly", "mohawk"]
    if not styles.has(style):
        return {"error_code": "invalid_hair_style", "error": "Choose a supported generated hairstyle."}
    if hair_color.length() != 7 or not hair_color.begins_with("#"):
        return {"error_code": "invalid_hair_color", "error": "Hair color must be a six-digit hexadecimal color."}
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    for path in [source_path, output_path]:
        if not path.to_lower().begins_with(root_prefix.to_lower()):
            return {"error_code": "path_outside_project", "error": "A hairstyle path resolves outside the project."}
    if not source_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(source_path):
        return {"error_code": "hair_source_missing", "error": "The source character GLB does not exist."}
    if not output_path.to_lower().ends_with(".glb") or FileAccess.file_exists(output_path):
        return {"error_code": "invalid_hair_output", "error": "Hairstyle generation must create a new GLB file."}
    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var import_error := document.append_from_file(source_path, state)
    if import_error != OK:
        return {"error_code": "hair_import_failed", "error": "Godot could not import the source character.", "godot_error": import_error}
    var scene := document.generate_scene(state)
    if scene == null:
        return {"error_code": "hair_scene_failed", "error": "Godot could not create the source character scene."}
    root.add_child(scene)
    await process_frame
    var skeleton_nodes := scene.find_children("*", "Skeleton3D", true, false)
    if skeleton_nodes.size() != 1:
        scene.queue_free()
        return {"error_code": "hair_skeleton_count", "error": "Generated hairstyles require exactly one humanoid Skeleton3D."}
    var skeleton := skeleton_nodes[0] as Skeleton3D
    var head_bone_name := ""
    var head_bone_index := -1
    for bone_index in range(skeleton.get_bone_count()):
        var bone_name := str(skeleton.get_bone_name(bone_index))
        var parts := bone_name.to_lower().split(":")
        var token := str(parts[parts.size() - 1]).replace("_", "").replace(" ", "")
        if token == "head":
            head_bone_name = bone_name
            head_bone_index = bone_index
            break
    if head_bone_name.is_empty():
        scene.queue_free()
        return {"error_code": "hair_head_bone_missing", "error": "The humanoid rig does not contain a recognizable Head bone."}
    for mesh_node in scene.find_children("*", "MeshInstance3D", true, false):
        var mesh_instance := mesh_node as MeshInstance3D
        if str(mesh_instance.name).begins_with("SiraOS_Hair_"):
            mesh_instance.queue_free()
    for attachment_node in scene.find_children("*", "BoneAttachment3D", true, false):
        var old_attachment := attachment_node as BoneAttachment3D
        if str(old_attachment.name).begins_with("SiraOS_Hair_Attachment"):
            old_attachment.queue_free()
    await process_frame
    var min_y := 1.0e20
    var max_y := -1.0e20
    for bone_index in range(skeleton.get_bone_count()):
        var bone_position := skeleton.get_bone_global_rest(bone_index).origin
        min_y = minf(min_y, bone_position.y)
        max_y = maxf(max_y, bone_position.y)
    var radius := maxf(max_y - min_y, 0.8) * 0.075
    var head_bounds := AABB()
    var head_bounds_found := false
    var head_center := Vector3.ZERO
    var head_front_z := radius
    var head_back_z := -radius
    var head_front_direction := 1.0
    var head_front_direction_basis := "skeleton_positive_z"
    var head_mesh_for_orientation: MeshInstance3D = null
    var head_priority := -1
    var largest_head_volume := 0.0
    for mesh_node in scene.find_children("*", "MeshInstance3D", true, false):
        var mesh_instance := mesh_node as MeshInstance3D
        if mesh_instance.mesh == null or mesh_instance.skin == null:
            continue
        var bound_skeleton := mesh_instance.get_node_or_null(mesh_instance.get_skeleton_path()) as Skeleton3D
        if bound_skeleton != skeleton:
            continue
        var mesh_label := str(mesh_instance.name) + " " + str(mesh_instance.mesh.resource_name) + " " + str(scene.get_path_to(mesh_instance))
        if _classify_mesh_slot(mesh_label) != "head":
            continue
        var candidate_bounds := _mesh_bounds_in_bone_space(mesh_instance, skeleton, head_bone_index)
        if candidate_bounds.size.x <= 0.01 or candidate_bounds.size.y <= 0.01 or candidate_bounds.size.z <= 0.01:
            continue
        var candidate_priority := 2 if mesh_label.to_lower().contains("head") else 1
        var candidate_volume := candidate_bounds.size.x * candidate_bounds.size.y * candidate_bounds.size.z
        if candidate_priority < head_priority or (
            candidate_priority == head_priority and candidate_volume <= largest_head_volume
        ):
            continue
        head_priority = candidate_priority
        largest_head_volume = candidate_volume
        head_bounds = candidate_bounds
        head_bounds_found = true
        head_mesh_for_orientation = mesh_instance
    var cap_position := Vector3(0, radius * 0.32, 0)
    var cap_scale := Vector3(radius * 1.08, radius * 0.76, radius * 1.08)
    if head_bounds_found:
        head_center = head_bounds.get_center()
        radius = maxf(head_bounds.size.x, head_bounds.size.z) * 0.5
        var front_orientation := _head_front_direction(
            head_mesh_for_orientation,
            skeleton,
            head_bone_index,
            head_center
        )
        head_front_direction = float(front_orientation["direction"])
        head_front_direction_basis = str(front_orientation["basis"])
        head_front_z = head_bounds.end.z if head_front_direction > 0 else head_bounds.position.z
        head_back_z = head_bounds.position.z if head_front_direction > 0 else head_bounds.end.z
        var cap_half_height := radius * 0.76
        cap_position = Vector3(head_center.x, head_bounds.end.y - cap_half_height, head_center.z)
        cap_scale = Vector3(
            minf(radius * 1.08, head_bounds.size.x * 0.58),
            cap_half_height,
            minf(radius * 1.08, head_bounds.size.z * 0.58)
        )
    var material := StandardMaterial3D.new()
    material.albedo_color = Color.from_string(hair_color, Color(0.12, 0.07, 0.04))
    material.roughness = 0.88
    var attachment := BoneAttachment3D.new()
    attachment.name = "SiraOS_Hair_Attachment"
    attachment.bone_name = head_bone_name
    skeleton.add_child(attachment)
    attachment.owner = scene
    var mesh_count := 0
    var cap := SphereMesh.new()
    cap.radius = 1.0
    cap.height = 2.0
    cap.radial_segments = 20
    cap.rings = 12
    _add_hair_primitive(attachment, scene, cap, "SiraOS_Hair_Cap", cap_position, cap_scale, Vector3.ZERO, material)
    mesh_count += 1
    if style == "short":
        var fringe := CapsuleMesh.new()
        fringe.radius = 0.45
        fringe.height = 0.9
        var fringe_position := Vector3(0, radius * 0.38, -radius * 0.78)
        if head_bounds_found:
            fringe_position = Vector3(
                head_center.x,
                cap_position.y - radius * 0.60,
                head_front_z - head_front_direction * radius * 0.15
            )
        _add_hair_primitive(attachment, scene, fringe, "SiraOS_Hair_Fringe", fringe_position, Vector3(radius * 0.72, radius * 0.32, radius * 0.35), Vector3.ZERO, material)
        mesh_count += 1
    elif style == "bob" or style == "long":
        for side in [-1.0, 1.0]:
            var lock := CapsuleMesh.new()
            lock.radius = 0.38
            lock.height = 2.0 if style == "bob" else 4.2
            var lock_position := Vector3(side * radius * 0.82, -radius * (0.55 if style == "bob" else 1.45), 0)
            if head_bounds_found:
                lock_position = Vector3(
                    head_center.x + side * minf(radius * 0.82, head_bounds.size.x * 0.53),
                    head_center.y - radius * (0.55 if style == "bob" else 1.45),
                    head_center.z
                )
            _add_hair_primitive(attachment, scene, lock, "SiraOS_Hair_Side_" + str(side), lock_position, Vector3(radius * 0.48, radius * (0.8 if style == "bob" else 1.55), radius * 0.48), Vector3(0, 0, side * 0.08), material)
            mesh_count += 1
        if style == "bob":
            var back_bob := SphereMesh.new()
            back_bob.radius = 1.0
            back_bob.height = 2.0
            var back_position := Vector3(0, -radius * 0.45, radius * 0.42)
            if head_bounds_found:
                back_position = Vector3(
                    head_center.x,
                    head_center.y - radius * 0.45,
                    head_back_z + head_front_direction * radius * 0.42
                )
            _add_hair_primitive(attachment, scene, back_bob, "SiraOS_Hair_Back", back_position, Vector3(radius * 0.92, radius * 0.82, radius * 0.65), Vector3.ZERO, material)
            mesh_count += 1
    elif style == "ponytail":
        var tail := CapsuleMesh.new()
        tail.radius = 0.42
        tail.height = 3.8
        var tail_position := Vector3(0, -radius * 0.62, radius * 0.92)
        var tie_position := Vector3(0, -radius * 0.05, radius * 0.78)
        if head_bounds_found:
            var tie_y := head_bounds.end.y - radius * 0.45
            tail_position = Vector3(
                head_center.x,
                tie_y - radius * 1.5,
                head_back_z - head_front_direction * radius * 0.35
            )
            tie_position = Vector3(
                head_center.x,
                tie_y,
                head_back_z - head_front_direction * radius * 0.10
            )
        _add_hair_primitive(attachment, scene, tail, "SiraOS_Hair_Ponytail", tail_position, Vector3(radius * 0.46, radius * 1.3, radius * 0.46), Vector3(0.18, 0, 0), material)
        var tie := SphereMesh.new()
        tie.radius = 1.0
        tie.height = 2.0
        _add_hair_primitive(attachment, scene, tie, "SiraOS_Hair_Tie", tie_position, Vector3(radius * 0.38, radius * 0.28, radius * 0.38), Vector3.ZERO, material)
        mesh_count += 2
    elif style == "spiky":
        for spike_index in range(7):
            var spike := CylinderMesh.new()
            spike.top_radius = 0.0
            spike.bottom_radius = 1.0
            spike.height = 2.0
            spike.radial_segments = 12
            var angle := TAU * float(spike_index) / 7.0
            var spike_position := Vector3(cos(angle) * radius * 0.48, radius * 0.95, sin(angle) * radius * 0.48)
            if head_bounds_found:
                spike_position = Vector3(
                    head_center.x + cos(angle) * radius * 0.48,
                    cap_position.y + radius * 0.55,
                    head_center.z + sin(angle) * radius * 0.48
                )
            _add_hair_primitive(attachment, scene, spike, "SiraOS_Hair_Spike_" + str(spike_index), spike_position, Vector3(radius * 0.28, radius * 0.62, radius * 0.28), Vector3.ZERO, material)
            mesh_count += 1
    elif style == "curly":
        for curl_index in range(12):
            var curl := SphereMesh.new()
            curl.radius = 1.0
            curl.height = 2.0
            curl.radial_segments = 12
            curl.rings = 8
            var angle := TAU * float(curl_index) / 12.0
            var curl_position := Vector3(cos(angle) * radius * 0.78, radius * 0.78, sin(angle) * radius * 0.78)
            if head_bounds_found:
                curl_position = Vector3(
                    head_center.x + cos(angle) * radius * 0.78,
                    cap_position.y + radius * 0.35,
                    head_center.z + sin(angle) * radius * 0.78
                )
            _add_hair_primitive(attachment, scene, curl, "SiraOS_Hair_Curl_" + str(curl_index), curl_position, Vector3.ONE * radius * 0.38, Vector3.ZERO, material)
            mesh_count += 1
    elif style == "mohawk":
        var ridge := CapsuleMesh.new()
        ridge.radius = 0.35
        ridge.height = 3.2
        var ridge_position := Vector3(0, radius * 1.05, 0)
        var ridge_scale := Vector3(radius * 0.36, radius * 1.0, radius * 0.42)
        var ridge_rotation := Vector3.ZERO
        if head_bounds_found:
            ridge_position = Vector3(head_center.x, cap_position.y + radius * 0.40, head_center.z)
            ridge_scale = Vector3(radius * 0.36, radius * 0.42, radius * 1.0)
            ridge_rotation = Vector3(PI * 0.5, 0, 0)
        _add_hair_primitive(attachment, scene, ridge, "SiraOS_Hair_Mohawk", ridge_position, ridge_scale, ridge_rotation, material)
        mesh_count += 1
    var source_animation_names := _scene_animation_names(scene)
    var export_document := GLTFDocument.new()
    var export_state := GLTFState.new()
    var export_error := export_document.append_from_scene(scene, export_state)
    if export_error != OK:
        scene.queue_free()
        return {"error_code": "hair_export_prepare_failed", "error": "Godot could not prepare the hairstyle GLB for export.", "godot_error": export_error}
    var output_error := export_document.write_to_filesystem(export_state, output_path)
    scene.queue_free()
    if output_error != OK or not FileAccess.file_exists(output_path):
        if FileAccess.file_exists(output_path):
            DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_export_failed", "error": "Godot could not write the generated hairstyle GLB.", "godot_error": output_error}
    var verification := _inspect_glb({"project_root": project_root, "source_path": output_path})
    if not bool(verification.get("ok", false)):
        DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_reimport_failed", "error": str(verification.get("error", "The generated hairstyle failed re-import verification."))}
    var exported_animation_names: Array = verification.get("animation_names", [])
    if int(verification.get("skeleton_count", 0)) != 1 or exported_animation_names.size() != source_animation_names.size():
        DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_rig_verification_failed", "error": "The generated hairstyle did not retain the humanoid rig and animation clips."}
    for animation_name in source_animation_names:
        if not exported_animation_names.has(animation_name):
            DirAccess.remove_absolute(output_path)
            return {"error_code": "hair_animation_verification_failed", "error": "A source animation was lost during hairstyle export: " + str(animation_name)}
    var verify_document := GLTFDocument.new()
    var verify_state := GLTFState.new()
    var verify_error := verify_document.append_from_file(output_path, verify_state)
    if verify_error != OK:
        DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_attachment_reimport_failed", "error": "Godot could not reopen the generated hair attachment.", "godot_error": verify_error}
    var verify_scene := verify_document.generate_scene(verify_state)
    if verify_scene == null:
        DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_attachment_scene_failed", "error": "Godot could not rebuild the generated hair attachment."}
    root.add_child(verify_scene)
    await process_frame
    var exported_hair_mesh_count := 0
    var attachment_verified := false
    var exported_cap: MeshInstance3D = null
    var exported_fringe: MeshInstance3D = null
    var exported_ponytail: MeshInstance3D = null
    var exported_tie: MeshInstance3D = null
    for hair_node in verify_scene.find_children("*", "MeshInstance3D", true, false):
        var hair_mesh := hair_node as MeshInstance3D
        if not str(hair_mesh.name).begins_with("SiraOS_Hair_"):
            continue
        exported_hair_mesh_count += 1
        if str(hair_mesh.name) == "SiraOS_Hair_Cap":
            exported_cap = hair_mesh
        elif str(hair_mesh.name) == "SiraOS_Hair_Fringe":
            exported_fringe = hair_mesh
        elif str(hair_mesh.name) == "SiraOS_Hair_Ponytail":
            exported_ponytail = hair_mesh
        elif str(hair_mesh.name) == "SiraOS_Hair_Tie":
            exported_tie = hair_mesh
        var parent_node := hair_mesh.get_parent()
        if parent_node is BoneAttachment3D and str((parent_node as BoneAttachment3D).bone_name) == head_bone_name:
            attachment_verified = true
    verify_scene.queue_free()
    if exported_hair_mesh_count < mesh_count or not attachment_verified:
        DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_attachment_verification_failed", "error": "The hairstyle geometry or its head-bone attachment did not survive GLB export and re-import."}
    if exported_cap == null:
        DirAccess.remove_absolute(output_path)
        return {"error_code": "hair_cap_missing", "error": "The generated hairstyle cap did not survive export and re-import."}
    var cap_clearance_verified := true
    var fringe_front_verified := true
    var ponytail_back_verified := true
    if head_bounds_found:
        var cap_half_height := exported_cap.mesh.get_aabb().size.y * exported_cap.scale.y * 0.5
        var cap_floor := exported_cap.position.y - cap_half_height
        var face_clearance_floor := head_bounds.position.y + head_bounds.size.y * 0.45
        cap_clearance_verified = (
            exported_cap.position.y > head_center.y
            and cap_floor >= face_clearance_floor
        )
        if style == "short":
            fringe_front_verified = exported_fringe != null
            if exported_fringe != null:
                fringe_front_verified = (
                    (exported_fringe.position.z - head_center.z) * head_front_direction > 0
                    and exported_fringe.position.y >= face_clearance_floor
                )
        if style == "ponytail":
            ponytail_back_verified = exported_ponytail != null and exported_tie != null
            if ponytail_back_verified:
                ponytail_back_verified = (
                    (exported_ponytail.position.z - head_back_z) * head_front_direction < 0
                    and (exported_tie.position.z - head_center.z) * head_front_direction < 0
                )
    var placement_verified := cap_clearance_verified and fringe_front_verified and ponytail_back_verified
    if not placement_verified:
        DirAccess.remove_absolute(output_path)
        return {
            "error_code": "hair_placement_verification_failed",
            "error": "The generated hair does not fit the detected head region or requested style orientation."
        }
    verification["hair_verified"] = true
    verification["hair_style"] = style
    verification["hair_color"] = hair_color
    verification["hair_attachment_bone"] = head_bone_name
    verification["hair_mesh_count"] = exported_hair_mesh_count
    verification["hair_attachment_verified"] = attachment_verified
    verification["hair_placement_verified"] = placement_verified
    verification["hair_fit_basis"] = "head_mesh_bounds" if head_bounds_found else "skeleton_fallback"
    verification["hair_cap_position"] = [
        exported_cap.position.x,
        exported_cap.position.y,
        exported_cap.position.z
    ]
    verification["hair_cap_clearance_verified"] = cap_clearance_verified
    verification["hair_fringe_front_verified"] = fringe_front_verified
    verification["hair_ponytail_back_verified"] = ponytail_back_verified
    verification["hair_front_direction"] = head_front_direction
    verification["hair_front_direction_basis"] = head_front_direction_basis
    if head_bounds_found:
        verification["hair_head_bounds_in_bone_space"] = {
            "position": [head_bounds.position.x, head_bounds.position.y, head_bounds.position.z],
            "size": [head_bounds.size.x, head_bounds.size.y, head_bounds.size.z]
        }
    return verification


func _customize_character_proportions(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var source_path := _normalise_path(str(payload.get("source_path", "")))
    var output_path := _normalise_path(str(payload.get("output_path", "")))
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    for path in [source_path, output_path]:
        if not path.to_lower().begins_with(root_prefix.to_lower()):
            return {"error_code": "path_outside_project", "error": "A body-proportion path resolves outside the project."}
    if not source_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(source_path):
        return {"error_code": "source_glb_missing", "error": "The body-proportion source GLB does not exist."}
    if not output_path.to_lower().ends_with(".glb") or FileAccess.file_exists(output_path):
        return {"error_code": "invalid_output_path", "error": "Body-proportion editing must create a new GLB file."}
    var proportions_value: Variant = payload.get("proportions", {})
    if typeof(proportions_value) != TYPE_DICTIONARY:
        return {"error_code": "invalid_proportions", "error": "Body proportions must be an object."}
    var proportions: Dictionary = proportions_value
    var allowed_names := ["torso_length", "shoulder_width", "arm_length", "leg_length", "head_size"]
    var changed_values: Dictionary = {}
    for name in allowed_names:
        var factor := float(proportions.get(name, 1.0))
        if factor < 0.5 or factor > 2.0:
            return {"error_code": "proportion_out_of_range", "error": "Every relative body-proportion factor must be between 0.5 and 2.0."}
        changed_values[name] = factor
    var has_change := false
    for name in changed_values:
        if absf(float(changed_values[name]) - 1.0) >= 0.0001:
            has_change = true
    if not has_change:
        return {"error_code": "empty_proportions", "error": "Change at least one body proportion before applying."}
    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var import_error := document.append_from_file(source_path, state)
    if import_error != OK:
        return {"error_code": "proportion_import_failed", "error": "Godot could not import the body-proportion source GLB.", "godot_error": import_error}
    var scene := document.generate_scene(state)
    if scene == null:
        return {"error_code": "proportion_scene_failed", "error": "Godot could not create the body-proportion scene."}
    root.add_child(scene)
    await process_frame
    var skeleton_nodes := scene.find_children("*", "Skeleton3D", true, false)
    if skeleton_nodes.size() != 1:
        scene.queue_free()
        return {"error_code": "proportion_skeleton_count", "error": "Body-proportion editing requires exactly one humanoid Skeleton3D."}
    var skeleton := skeleton_nodes[0] as Skeleton3D
    var skinned_mesh_count := 0
    for mesh_node in scene.find_children("*", "MeshInstance3D", true, false):
        var mesh := mesh_node as MeshInstance3D
        if mesh.skin != null and mesh.get_node_or_null(mesh.get_skeleton_path()) == skeleton:
            skinned_mesh_count += 1
    if skinned_mesh_count == 0:
        scene.queue_free()
        return {"error_code": "proportion_skin_missing", "error": "The source character has no mesh bound to its humanoid skeleton."}
    var original_bone_rests: Dictionary = {}
    for bone_index in range(skeleton.get_bone_count()):
        original_bone_rests[str(skeleton.get_bone_name(bone_index))] = skeleton.get_bone_rest(bone_index)
    var changed_bones: Array[String] = []
    var mapping_value: Variant = payload.get("bone_mapping", {})
    var bone_mapping: Dictionary = mapping_value if typeof(mapping_value) == TYPE_DICTIONARY else {}
    var groups := [
        {"name": "torso_length", "canonical": ["Spine", "Head"], "aliases": ["spine", "neck", "head"], "mode": "vertical", "minimum": 2},
        {"name": "shoulder_width", "canonical": ["LeftUpperArm", "RightUpperArm"], "aliases": ["shoulder", "upperarm", "leftarm", "rightarm"], "mode": "horizontal", "minimum": 2},
        {"name": "arm_length", "canonical": ["LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm", "RightLowerArm", "RightHand"], "aliases": ["upperarm", "forearm", "lowerarm", "hand", "leftarm", "rightarm"], "mode": "vector", "minimum": 2},
        {"name": "leg_length", "canonical": ["LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"], "aliases": ["upleg", "upperleg", "thigh", "lowerleg", "calf", "shin", "foot", "leftleg", "rightleg"], "mode": "vector", "minimum": 2},
        {"name": "head_size", "canonical": ["Head"], "aliases": ["head"], "mode": "basis", "minimum": 1}
    ]
    for group_value in groups:
        var group: Dictionary = group_value
        var factor := float(changed_values[group["name"]])
        if absf(factor - 1.0) < 0.0001:
            continue
        var selected_bones: Array[int] = []
        if not bone_mapping.is_empty():
            for canonical_name in group["canonical"]:
                var mapped_name := str(bone_mapping.get(canonical_name, ""))
                var mapped_index := skeleton.find_bone(mapped_name) if not mapped_name.is_empty() else -1
                if mapped_index >= 0 and not selected_bones.has(mapped_index):
                    selected_bones.append(mapped_index)
        else:
            var aliases: Array = group["aliases"]
            for candidate_index in range(skeleton.get_bone_count()):
                var candidate_name := str(skeleton.get_bone_name(candidate_index))
                var token_parts := candidate_name.to_lower().split(":")
                var token := str(token_parts[token_parts.size() - 1]).replace("_", "").replace(" ", "").replace(".", "").replace("-", "")
                var matches_alias := false
                for alias_value in aliases:
                    if token.contains(str(alias_value)):
                        matches_alias = true
                        break
                if matches_alias:
                    selected_bones.append(candidate_index)
        var matched := 0
        for bone_index in selected_bones:
            var bone_name := str(skeleton.get_bone_name(bone_index))
            var rest := skeleton.get_bone_rest(bone_index)
            if group["mode"] == "vertical":
                rest.origin.y *= factor
            elif group["mode"] == "horizontal":
                rest.origin.x *= factor
            elif group["mode"] == "vector":
                rest.origin *= factor
            elif group["mode"] == "basis":
                rest.basis = Basis(rest.basis.x * factor, rest.basis.y * factor, rest.basis.z * factor)
            skeleton.set_bone_rest(bone_index, rest)
            var original_rest: Transform3D = original_bone_rests[bone_name]
            var actual_change := original_rest.origin.distance_to(rest.origin) > 0.0001
            actual_change = actual_change or original_rest.basis.x.distance_to(rest.basis.x) > 0.0001
            actual_change = actual_change or original_rest.basis.y.distance_to(rest.basis.y) > 0.0001
            actual_change = actual_change or original_rest.basis.z.distance_to(rest.basis.z) > 0.0001
            if actual_change:
                matched += 1
                if not changed_bones.has(bone_name):
                    changed_bones.append(bone_name)
        if matched < int(group["minimum"]):
            scene.queue_free()
            return {"error_code": "proportion_bones_missing", "error": "The imported rig does not expose enough transformable named bones for " + str(group["name"]) + "."}
    skeleton.reset_bone_poses()
    var expected_bone_rests: Dictionary = {}
    for bone_name in changed_bones:
        expected_bone_rests[bone_name] = skeleton.get_bone_rest(skeleton.find_bone(bone_name))
    var source_animation_names := _scene_animation_names(scene)
    var export_document := GLTFDocument.new()
    var export_state := GLTFState.new()
    var export_error := export_document.append_from_scene(scene, export_state)
    if export_error != OK:
        scene.queue_free()
        return {"error_code": "proportion_export_prepare_failed", "error": "Godot could not prepare the proportioned character for GLB export.", "godot_error": export_error}
    var output_error := export_document.write_to_filesystem(export_state, output_path)
    scene.queue_free()
    if output_error != OK or not FileAccess.file_exists(output_path):
        if FileAccess.file_exists(output_path):
            DirAccess.remove_absolute(output_path)
        return {"error_code": "proportion_export_failed", "error": "Godot could not write the proportioned character GLB.", "godot_error": output_error}
    var verification := _inspect_glb({"project_root": project_root, "source_path": output_path})
    if not bool(verification.get("ok", false)):
        DirAccess.remove_absolute(output_path)
        return {"error_code": "proportion_reimport_failed", "error": str(verification.get("error", "The proportioned GLB failed re-import verification."))}
    var exported_animation_names: Array = verification.get("animation_names", [])
    if int(verification.get("skeleton_count", 0)) != 1 or exported_animation_names.size() != source_animation_names.size():
        DirAccess.remove_absolute(output_path)
        return {"error_code": "proportion_rig_verification_failed", "error": "The proportioned GLB did not retain its skinned humanoid rig and original animation clips."}
    for animation_name in source_animation_names:
        if not exported_animation_names.has(animation_name):
            DirAccess.remove_absolute(output_path)
            return {"error_code": "proportion_animation_verification_failed", "error": "A source animation was lost during body-proportion export: " + str(animation_name)}
    var exported_bones: Array = []
    var output_skeletons: Array = verification.get("skeletons", [])
    if output_skeletons.size() == 1:
        exported_bones = output_skeletons[0].get("bones", [])
    var verified_changed_bones: Array[String] = []
    for output_bone_value in exported_bones:
        var output_bone: Dictionary = output_bone_value
        var output_name := str(output_bone.get("name", ""))
        if not changed_bones.has(output_name):
            continue
        var output_rest: Dictionary = output_bone.get("rest_transform", {})
        var output_origin: Array = output_rest.get("origin", [])
        var output_scale: Array = output_rest.get("scale", [])
        if not expected_bone_rests.has(output_name) or not original_bone_rests.has(output_name):
            continue
        var expected_rest: Transform3D = expected_bone_rests[output_name]
        var original_rest: Transform3D = original_bone_rests[output_name]
        var output_origin_vector := Vector3(float(output_origin[0]), float(output_origin[1]), float(output_origin[2])) if output_origin.size() == 3 else Vector3.ZERO
        var output_scale_vector := Vector3(float(output_scale[0]), float(output_scale[1]), float(output_scale[2])) if output_scale.size() == 3 else Vector3.ONE
        var origin_was_changed := expected_rest.origin.distance_to(original_rest.origin) > 0.0001
        var scale_was_changed := expected_rest.basis.get_scale().distance_to(original_rest.basis.get_scale()) > 0.0001
        var origin_matches := origin_was_changed and output_origin_vector.distance_to(expected_rest.origin) <= 0.002
        var scale_matches := scale_was_changed and output_scale_vector.distance_to(expected_rest.basis.get_scale()) <= 0.002
        if origin_matches or scale_matches:
            verified_changed_bones.append(output_name)
    if verified_changed_bones.is_empty():
        DirAccess.remove_absolute(output_path)
        return {"error_code": "proportion_geometry_verification_failed", "error": "No edited humanoid bone transforms survived GLB export and re-import."}
    verification["proportions_verified"] = true
    verification["applied_proportions"] = changed_values
    verification["changed_bones"] = verified_changed_bones
    verification["source_animation_names"] = source_animation_names
    verification["skinned_mesh_count"] = skinned_mesh_count
    return verification


func _probe_glb_animation(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var source_path := _normalise_path(str(payload.get("source_path", "")))
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    if not source_path.to_lower().begins_with(root_prefix.to_lower()):
        return {"error_code": "path_outside_project", "error": "The animation probe GLB resolves outside the project."}
    if not source_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(source_path):
        return {"error_code": "invalid_glb_path", "error": "Animation probe requires an existing GLB file."}

    var document := GLTFDocument.new()
    var state := GLTFState.new()
    var import_error := document.append_from_file(source_path, state)
    if import_error != OK:
        return {"error_code": "animation_probe_import_failed", "error": "Godot could not import the animation probe GLB.", "godot_error": import_error}
    var scene := document.generate_scene(state)
    if scene == null:
        return {"error_code": "animation_probe_scene_failed", "error": "Godot could not create the animation probe scene."}
    root.add_child(scene)
    await process_frame

    var skeletons := scene.find_children("*", "Skeleton3D", true, false)
    if skeletons.size() != 1:
        scene.queue_free()
        return {"error_code": "animation_probe_skeleton_count", "error": "Animation playback probe requires exactly one Skeleton3D."}
    var skeleton := skeletons[0] as Skeleton3D
    var requested_name := str(payload.get("animation_name", ""))
    var selected_player: AnimationPlayer = null
    var selected_name := ""
    var selected_animation: Animation = null
    for player_node in scene.find_children("*", "AnimationPlayer", true, false):
        var player := player_node as AnimationPlayer
        for animation_value in player.get_animation_list():
            var candidate := str(animation_value)
            if candidate.get_file().to_upper() == "RESET":
                continue
            if not requested_name.is_empty() and candidate != requested_name:
                continue
            var animation := player.get_animation(candidate)
            if animation == null or animation.length <= 0.0:
                continue
            selected_player = player
            selected_name = candidate
            selected_animation = animation
            break
        if selected_player != null:
            break
    if selected_player == null or selected_animation == null:
        scene.queue_free()
        return {"error_code": "animation_not_found", "error": "The requested playable animation clip was not found."}

    var sample_ratio := clampf(float(payload.get("sample_ratio", 0.37)), 0.0, 1.0)
    var sample_time := selected_animation.length * sample_ratio
    selected_player.stop()
    var before_poses: Array[Transform3D] = []
    for bone_index in range(skeleton.get_bone_count()):
        before_poses.append(skeleton.get_bone_pose(bone_index))
    selected_player.play(selected_name)
    selected_player.seek(sample_time, true)
    for frame_index in range(3):
        await process_frame

    var changed_bones: Array[String] = []
    for bone_index in range(skeleton.get_bone_count()):
        var after_pose := skeleton.get_bone_pose(bone_index)
        if not _transforms_compatible(before_poses[bone_index], after_pose):
            changed_bones.append(skeleton.get_bone_name(bone_index))

    var skinned_mesh_count := 0
    for mesh_node in scene.find_children("*", "MeshInstance3D", true, false):
        var mesh := mesh_node as MeshInstance3D
        if mesh.skin == null:
            continue
        var bound_skeleton := mesh.get_node_or_null(mesh.get_skeleton_path()) as Skeleton3D
        if bound_skeleton == skeleton:
            skinned_mesh_count += 1

    var attachment_bones: Array[String] = []
    for attachment_node in scene.find_children("*", "BoneAttachment3D", true, false):
        var attachment := attachment_node as BoneAttachment3D
        if skeleton.find_bone(attachment.bone_name) >= 0 and not attachment_bones.has(attachment.bone_name):
            attachment_bones.append(attachment.bone_name)

    var result := {
        "ok": true,
        "animation_name": selected_name,
        "animation_duration": selected_animation.length,
        "sample_time": sample_time,
        "sample_ratio": sample_ratio,
        "bone_count": skeleton.get_bone_count(),
        "changed_bone_count": changed_bones.size(),
        "changed_bones": changed_bones,
        "pose_changed": not changed_bones.is_empty(),
        "skinned_mesh_count": skinned_mesh_count,
        "bone_attachment_bones": attachment_bones
    }
    scene.queue_free()
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

    var accessories_value: Variant = payload.get("accessories", [])
    if typeof(accessories_value) != TYPE_ARRAY or accessories_value.size() > 8:
        return {"error_code": "invalid_accessories", "error": "A character can include at most eight accessories."}
    for accessory_value in accessories_value:
        if typeof(accessory_value) != TYPE_DICTIONARY:
            return {"error_code": "invalid_accessory", "error": "Each accessory must be an object."}
        var accessory: Dictionary = accessory_value
        var accessory_path := _normalise_path(str(accessory.get("source_path", "")))
        var accessory_mesh_path := str(accessory.get("mesh_path", ""))
        if not accessory_path.to_lower().begins_with(root_prefix.to_lower()) or not accessory_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(accessory_path):
            return {"error_code": "invalid_accessory_path", "error": "An accessory GLB is missing or outside the project."}
        if accessory_mesh_path.is_empty() or accessory_mesh_path.length() > 1024:
            return {"error_code": "invalid_accessory_mesh", "error": "An accessory mesh path is invalid."}
        var accessory_key := accessory_path + "|" + accessory_mesh_path
        if selected_mesh_keys.has(accessory_key):
            return {"error_code": "duplicate_accessory", "error": "A source mesh cannot be used as both a body part and an accessory."}
        selected_mesh_keys.append(accessory_key)

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

    var added_accessories: Array[Dictionary] = []
    for accessory_index in range(accessories_value.size()):
        var accessory: Dictionary = accessories_value[accessory_index]
        var accessory_path := _normalise_path(str(accessory["source_path"]))
        var accessory_document := GLTFDocument.new()
        var accessory_state := GLTFState.new()
        var accessory_error := accessory_document.append_from_file(accessory_path, accessory_state)
        if accessory_error != OK:
            base_scene.queue_free()
            return {"error_code": "accessory_import_failed", "error": "Godot could not import accessory " + str(accessory_index + 1) + ".", "godot_error": accessory_error}
        var accessory_scene := accessory_document.generate_scene(accessory_state)
        if accessory_scene == null:
            base_scene.queue_free()
            return {"error_code": "accessory_scene_failed", "error": "Godot could not create accessory " + str(accessory_index + 1) + "."}
        root.add_child(accessory_scene)
        await process_frame
        var accessory_mesh := accessory_scene.get_node_or_null(NodePath(str(accessory["mesh_path"]))) as MeshInstance3D
        if accessory_mesh == null or accessory_mesh.mesh == null:
            accessory_scene.queue_free()
            base_scene.queue_free()
            return {"error_code": "accessory_mesh_missing", "error": "The selected accessory mesh was not found."}
        var accessory_name := "ModularAccessory_" + str(accessory_index + 1)
        var accessory_bone := str(accessory.get("attachment_bone", ""))
        if accessory_mesh.skin != null:
            var accessory_skeleton := accessory_mesh.get_node_or_null(accessory_mesh.get_skeleton_path()) as Skeleton3D
            if accessory_skeleton == null or not _skeletons_compatible(accessory_skeleton, target_skeleton):
                accessory_scene.queue_free()
                base_scene.queue_free()
                return {"error_code": "accessory_skeleton_incompatible", "error": "A skinned accessory must use the same compatible skeleton as the base character."}
            if not _transforms_compatible(accessory_skeleton.global_transform, target_skeleton.global_transform):
                accessory_scene.queue_free()
                base_scene.queue_free()
                return {"error_code": "accessory_transform_incompatible", "error": "A skinned accessory has a different rig transform and cannot be safely attached."}
            var accessory_skin := accessory_mesh.skin
            for bind_index in range(accessory_skin.get_bind_count()):
                var bind_name := str(accessory_skin.get_bind_name(bind_index))
                if not bind_name.is_empty():
                    if accessory_skeleton.find_bone(bind_name) < 0:
                        accessory_scene.queue_free()
                        base_scene.queue_free()
                        return {"error_code": "accessory_skin_bind_invalid", "error": "The accessory skin references a missing bone: " + bind_name}
                else:
                    var bind_bone := accessory_skin.get_bind_bone(bind_index)
                    if bind_bone < 0 or bind_bone >= accessory_skeleton.get_bone_count():
                        accessory_scene.queue_free()
                        base_scene.queue_free()
                        return {"error_code": "accessory_skin_bind_invalid", "error": "The accessory skin contains an invalid bone index."}
            var skinned_clone := accessory_mesh.duplicate() as MeshInstance3D
            var accessory_global_transform := accessory_mesh.global_transform
            base_scene.add_child(skinned_clone)
            skinned_clone.owner = base_scene
            skinned_clone.name = accessory_name
            skinned_clone.transform = base_scene.global_transform.affine_inverse() * accessory_global_transform
            skinned_clone.set_skeleton_path(NodePath(str(skinned_clone.get_path_to(target_skeleton))))
        else:
            var source_attachment := accessory_mesh.get_parent() as BoneAttachment3D
            if accessory_bone.is_empty() and source_attachment != null:
                accessory_bone = str(source_attachment.bone_name)
            if source_attachment == null or accessory_bone.is_empty() or target_skeleton.find_bone(accessory_bone) < 0:
                accessory_scene.queue_free()
                base_scene.queue_free()
                return {"error_code": "accessory_attachment_missing", "error": "An unskinned accessory must be parented to a valid BoneAttachment3D on the source rig."}
            if str(source_attachment.bone_name) != accessory_bone:
                accessory_scene.queue_free()
                base_scene.queue_free()
                return {"error_code": "accessory_attachment_mismatch", "error": "The selected accessory attachment bone does not match its source node."}
            var target_attachment := BoneAttachment3D.new()
            target_attachment.name = "ModularAccessoryAttachment_" + str(accessory_index + 1)
            target_attachment.bone_name = accessory_bone
            target_skeleton.add_child(target_attachment)
            target_attachment.owner = base_scene
            target_attachment.transform = source_attachment.transform
            var static_clone := accessory_mesh.duplicate() as MeshInstance3D
            target_attachment.add_child(static_clone)
            static_clone.owner = base_scene
            static_clone.name = accessory_name
            static_clone.transform = accessory_mesh.transform
        added_accessories.append({
            "mesh_name": str(accessory_mesh.name),
            "output_name": accessory_name,
            "source_path": accessory_path,
            "mesh_path": str(accessory["mesh_path"]),
            "attachment_bone": accessory_bone
        })
        accessory_scene.queue_free()
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
    for accessory_entry in added_accessories:
        if not verified_mesh_names.has(str(accessory_entry["output_name"])):
            DirAccess.remove_absolute(output_path)
            return {"error_code": "accessory_verification_failed", "error": "The exported GLB did not retain a selected accessory."}
    verification["added_parts"] = added_parts
    verification["added_accessories"] = added_accessories
    verification["base_animation_names"] = base_animation_names
    verification["base_meshes_removed"] = removed_base_meshes
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
