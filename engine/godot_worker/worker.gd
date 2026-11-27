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
            "ping", "glb_inspect", "scene_metrics", "skeleton_report", "retarget_glb_pair", "assemble_modular_character", "probe_glb_animation", "export_character_appearance", "customize_character_proportions", "add_character_hair", "export_world_scene", "export_episode_scenes"
        ]
        return response

    if operation == "export_episode_scenes":
        var episode_result: Dictionary = await _export_episode_scenes(payload)
        for key in episode_result:
            response[key] = episode_result[key]
        return response

    if operation == "export_world_scene":
        var world_result: Dictionary = _export_world_scene(payload)
        for key in world_result:
            response[key] = world_result[key]
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


func _face_surface_matches(label: String, tokens: Array[String]) -> bool:
    var normalized := label.to_lower()
    for token in tokens:
        if token == "eye" and (normalized.contains("brow") or normalized.contains("eyebrow")):
            continue
        if normalized.contains(token):
            return true
    return false


func _named_surface_bounds_in_bone_space(
    mesh_instance: MeshInstance3D,
    skeleton: Skeleton3D,
    bone_index: int,
    tokens: Array[String],
    split_center_x: float = 0.0,
    x_side: int = 0
) -> Dictionary:
    var bounds := AABB()
    var has_bounds := false
    var matched_surfaces: Array[int] = []
    var mesh_to_bone := _mesh_to_bone_transform(mesh_instance, skeleton, bone_index)
    for surface_index in range(mesh_instance.mesh.get_surface_count()):
        var surface_label := str(mesh_instance.mesh.surface_get_name(surface_index))
        var material := mesh_instance.get_active_material(surface_index)
        if material != null:
            surface_label += " " + str(material.resource_name)
        if not _face_surface_matches(surface_label, tokens):
            continue
        var arrays := mesh_instance.mesh.surface_get_arrays(surface_index)
        if arrays.size() <= Mesh.ARRAY_VERTEX:
            continue
        var vertex_value: Variant = arrays[Mesh.ARRAY_VERTEX]
        if typeof(vertex_value) != TYPE_PACKED_VECTOR3_ARRAY:
            continue
        var vertices: PackedVector3Array = vertex_value
        for vertex in vertices:
            var point := mesh_to_bone * vertex
            if x_side < 0 and point.x >= split_center_x:
                continue
            if x_side > 0 and point.x <= split_center_x:
                continue
            if not has_bounds:
                bounds = AABB(point, Vector3.ZERO)
                has_bounds = true
            else:
                bounds = bounds.expand(point)
        if not matched_surfaces.has(surface_index):
            matched_surfaces.append(surface_index)
    return {"bounds": bounds, "surface_indices": matched_surfaces, "found": has_bounds}


func _face_surface_depth_at(
    mesh_instance: MeshInstance3D,
    skeleton: Skeleton3D,
    bone_index: int,
    surface_indices: Array[int],
    point: Vector2,
    direction: float,
    fallback: float
) -> float:
    var best_depth := fallback
    var found := false
    var mesh_to_bone := _mesh_to_bone_transform(mesh_instance, skeleton, bone_index)
    for surface_index in surface_indices:
        var arrays := mesh_instance.mesh.surface_get_arrays(surface_index)
        if arrays.size() <= Mesh.ARRAY_VERTEX:
            continue
        var vertex_value: Variant = arrays[Mesh.ARRAY_VERTEX]
        if typeof(vertex_value) != TYPE_PACKED_VECTOR3_ARRAY:
            continue
        var source_vertices: PackedVector3Array = vertex_value
        var vertices := PackedVector3Array()
        vertices.resize(source_vertices.size())
        for vertex_index in range(source_vertices.size()):
            vertices[vertex_index] = mesh_to_bone * source_vertices[vertex_index]
        var indices := PackedInt32Array()
        if arrays.size() > Mesh.ARRAY_INDEX:
            var index_value: Variant = arrays[Mesh.ARRAY_INDEX]
            if typeof(index_value) == TYPE_PACKED_INT32_ARRAY:
                indices = index_value
        var triangle_count := indices.size() if not indices.is_empty() else vertices.size()
        for triangle_start in range(0, triangle_count - 2, 3):
            var ia := indices[triangle_start] if not indices.is_empty() else triangle_start
            var ib := indices[triangle_start + 1] if not indices.is_empty() else triangle_start + 1
            var ic := indices[triangle_start + 2] if not indices.is_empty() else triangle_start + 2
            if ia >= vertices.size() or ib >= vertices.size() or ic >= vertices.size():
                continue
            var a: Vector3 = vertices[ia]
            var b: Vector3 = vertices[ib]
            var c: Vector3 = vertices[ic]
            var denominator := (b.y - c.y) * (a.x - c.x) + (c.x - b.x) * (a.y - c.y)
            if absf(denominator) < 0.0000001:
                continue
            var weight_a := ((b.y - c.y) * (point.x - c.x) + (c.x - b.x) * (point.y - c.y)) / denominator
            var weight_b := ((c.y - a.y) * (point.x - c.x) + (a.x - c.x) * (point.y - c.y)) / denominator
            var weight_c := 1.0 - weight_a - weight_b
            if weight_a < -0.001 or weight_b < -0.001 or weight_c < -0.001:
                continue
            var depth := weight_a * a.z + weight_b * b.z + weight_c * c.z
            if not found or (direction > 0.0 and depth > best_depth) or (direction < 0.0 and depth < best_depth):
                best_depth = depth
                found = true
    return best_depth


func _generated_face_front_depth(
    bounds: AABB,
    center: Vector3,
    x: float,
    y: float,
    face_width: float,
    cheek_fullness: float,
    jaw_width: float,
    front_direction: float
) -> float:
    var t := clampf((bounds.position.y + bounds.size.y - y) / maxf(bounds.size.y, 0.001), 0.025, 0.975)
    var ring_angle := PI * t
    var profile := maxf(sin(ring_angle), 0.025)
    var lower_face := clampf((t - 0.58) / 0.42, 0.0, 1.0)
    var jaw_profile := lerpf(1.0, clampf(jaw_width, 0.7, 1.3), pow(lower_face, 1.2))
    var cheek_distance := (t - 0.47) / 0.14
    var cheek_profile := 1.0 + (clampf(cheek_fullness, 0.5, 1.5) - 1.0) * exp(-cheek_distance * cheek_distance)
    var x_radius := maxf(bounds.size.x * 0.5 * pow(profile, 0.72) * jaw_profile * cheek_profile * face_width, 0.001)
    var z_radius := bounds.size.z * 0.5 * pow(profile, 0.72) * lerpf(0.92, 1.0, cheek_profile - 0.5)
    var side_ratio := clampf((x - center.x) / x_radius, -0.97, 0.97)
    return center.z + front_direction * z_radius * sqrt(1.0 - side_ratio * side_ratio)


func _make_generated_face_head_mesh(
    bounds: AABB,
    center: Vector3,
    face_width: float,
    cheek_fullness: float,
    jaw_width: float,
    chin_length: float,
    front_direction: float
) -> ArrayMesh:
    const RING_COUNT := 18
    const SEGMENT_COUNT := 28
    var tool := SurfaceTool.new()
    tool.begin(Mesh.PRIMITIVE_TRIANGLES)
    for ring_index in range(RING_COUNT + 1):
        var t := float(ring_index) / float(RING_COUNT)
        var ring_angle := PI * t
        var vertical := cos(ring_angle)
        var profile := maxf(sin(ring_angle), 0.025)
        var lower_face := clampf((t - 0.58) / 0.42, 0.0, 1.0)
        var chin_profile := lerpf(1.0, clampf(chin_length, 0.65, 1.4), pow(lower_face, 1.7))
        var jaw_profile := lerpf(1.0, clampf(jaw_width, 0.7, 1.3), pow(lower_face, 1.2))
        var cheek_distance := (t - 0.47) / 0.14
        var cheek_profile := 1.0 + (clampf(cheek_fullness, 0.5, 1.5) - 1.0) * exp(-cheek_distance * cheek_distance)
        var x_radius := bounds.size.x * 0.5 * pow(profile, 0.72) * jaw_profile * cheek_profile * face_width
        var z_radius := bounds.size.z * 0.5 * pow(profile, 0.72) * lerpf(0.92, 1.0, cheek_profile - 0.5)
        var y_offset := vertical * bounds.size.y * 0.5
        if t > 0.84:
            y_offset -= (chin_profile - 1.0) * bounds.size.y * 0.08
        for segment_index in range(SEGMENT_COUNT + 1):
            var u := float(segment_index) / float(SEGMENT_COUNT)
            var angle := TAU * u
            var point := Vector3(
                center.x + cos(angle) * x_radius,
                center.y + y_offset,
                center.z + sin(angle) * z_radius * front_direction
            )
            tool.set_uv(Vector2(u, t))
            tool.add_vertex(point)
    var row_width := SEGMENT_COUNT + 1
    for ring_index in range(RING_COUNT):
        for segment_index in range(SEGMENT_COUNT):
            var a := ring_index * row_width + segment_index
            var b := (ring_index + 1) * row_width + segment_index
            var c := b + 1
            var d := a + 1
            if front_direction > 0.0:
                tool.add_index(a)
                tool.add_index(d)
                tool.add_index(b)
                tool.add_index(b)
                tool.add_index(d)
                tool.add_index(c)
            else:
                tool.add_index(a)
                tool.add_index(b)
                tool.add_index(d)
                tool.add_index(b)
                tool.add_index(c)
                tool.add_index(d)
    tool.generate_normals()
    return tool.commit()


func _suppress_imported_face_surfaces(mesh_instance: MeshInstance3D) -> Array[Dictionary]:
    var suppressed: Array[Dictionary] = []
    var replaceable_tokens: Array[String] = ["skin", "eye", "brow", "eyebrow", "nose", "nostril", "ear", "mustache", "moustache"]
    for surface_index in range(mesh_instance.mesh.get_surface_count()):
        var surface_name := str(mesh_instance.mesh.surface_get_name(surface_index))
        var material := mesh_instance.get_active_material(surface_index)
        var label := surface_name + " " + (str(material.resource_name) if material != null else "")
        if not _face_surface_matches(label, replaceable_tokens):
            continue
        var hidden_material := StandardMaterial3D.new()
        hidden_material.resource_name = "CartoonStudio_Hidden_" + surface_name
        hidden_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
        hidden_material.albedo_color = Color(1.0, 1.0, 1.0, 0.0)
        hidden_material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
        mesh_instance.set_surface_override_material(surface_index, hidden_material)
        suppressed.append({"mesh_name": str(mesh_instance.name), "surface_index": surface_index, "surface_name": surface_name})
    return suppressed


func _compute_face_normals(vertices: PackedVector3Array, center: Vector3) -> PackedVector3Array:
    var normals := PackedVector3Array()
    normals.resize(vertices.size())
    for i in range(vertices.size()):
        normals[i] = (vertices[i] - center).normalized()
    return normals


func _compute_face_uvs(count: int) -> PackedVector2Array:
    var uvs := PackedVector2Array()
    uvs.resize(count)
    return uvs


func _replace_skin_surface_with_generated_face(
    mesh_instance: MeshInstance3D,
    skin_surface_index: int,
    head_bone_index: int,
    bounds: AABB,
    center: Vector3,
    face_width: float,
    cheek_fullness: float,
    jaw_width: float,
    chin_length: float,
    front_direction: float,
    skin_material: BaseMaterial3D
) -> Dictionary:
    var mesh := mesh_instance.mesh
    if not (mesh is ArrayMesh):
        return {"ok": false, "error_code": "face_mesh_not_array_mesh", "error": "Head mesh is not an ArrayMesh."}

    var face_geometry := _make_generated_face_head_mesh(
        bounds, center, face_width, cheek_fullness, jaw_width, chin_length, front_direction
    )
    var face_arrays := face_geometry.surface_get_arrays(0)
    if face_arrays.size() <= Mesh.ARRAY_VERTEX:
        return {"ok": false, "error_code": "face_geometry_no_vertices", "error": "Generated face geometry has no vertex data."}

    var face_vertices: PackedVector3Array = face_arrays[Mesh.ARRAY_VERTEX]
    var face_indices: PackedInt32Array = PackedInt32Array()
    if face_arrays.size() > Mesh.ARRAY_INDEX:
        var idx_value := face_arrays[Mesh.ARRAY_INDEX] as PackedInt32Array
        if typeof(idx_value) == TYPE_PACKED_INT32_ARRAY:
            face_indices = idx_value

    var face_normals := PackedVector3Array()
    if face_arrays.size() > Mesh.ARRAY_NORMAL:
        face_normals = face_arrays[Mesh.ARRAY_NORMAL]
    var face_uvs := PackedVector2Array()
    if face_arrays.size() > Mesh.ARRAY_TEX_UV:
        face_uvs = face_arrays[Mesh.ARRAY_TEX_UV]

    var vertex_count: int = face_vertices.size()

    var new_arrays: Array = []
    new_arrays.resize(Mesh.ARRAY_MAX)
    new_arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array(face_vertices)
    if face_normals.size() == vertex_count:
        new_arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array(face_normals)
    else:
        new_arrays[Mesh.ARRAY_NORMAL] = _compute_face_normals(face_vertices, center)

    # Tangents intentionally omitted (null): all-zero tangents are invalid and the
    # generated skin material has no normal map.
    new_arrays[Mesh.ARRAY_TANGENT] = null

    if face_uvs.size() == vertex_count:
        new_arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array(face_uvs)
    else:
        new_arrays[Mesh.ARRAY_TEX_UV] = _compute_face_uvs(vertex_count)

    var bones := PackedInt32Array()
    var weights := PackedFloat32Array()
    bones.resize(vertex_count * 4)
    weights.resize(vertex_count * 4)
    for i in range(vertex_count):
        bones[i * 4] = head_bone_index
        weights[i * 4] = 1.0
    new_arrays[Mesh.ARRAY_BONES] = bones
    new_arrays[Mesh.ARRAY_WEIGHTS] = weights

    if not face_indices.is_empty():
        new_arrays[Mesh.ARRAY_INDEX] = face_indices

    var new_mesh := ArrayMesh.new()
    var surface_count := mesh.get_surface_count()
    var new_surface_index := -1
    for i in range(surface_count):
        if i == skin_surface_index:
            continue
        var surf_arrays := mesh.surface_get_arrays(i)
        if surf_arrays.size() > Mesh.ARRAY_VERTEX:
            new_mesh.add_surface_from_arrays(
                Mesh.PRIMITIVE_TRIANGLES,
                surf_arrays,
                [],
                {},
                0
            )
            var new_idx := new_mesh.get_surface_count() - 1
            new_mesh.surface_set_name(new_idx, mesh.surface_get_name(i))
            var mat := mesh_instance.get_active_material(i)
            if mat != null:
                new_mesh.surface_set_material(new_idx, mat)

    # Add the generated face exactly once, after the original surfaces.
    var added_idx := new_mesh.add_surface_from_arrays(
        Mesh.PRIMITIVE_TRIANGLES,
        new_arrays,
        [],
        {},
        0
    )
    if added_idx < 0:
        return {"ok": false, "error_code": "face_surface_add_failed", "error": "add_surface_from_arrays() returned -1 for generated face surface."}
    new_surface_index = added_idx
    new_mesh.surface_set_name(new_surface_index, "CartoonStudio_GeneratedFace")
    if skin_material != null:
        new_mesh.surface_set_material(new_surface_index, skin_material)

    mesh_instance.mesh = new_mesh

    return {
        "ok": true,
        "skin_surface_replaced": true,
        "new_surface_index": new_surface_index,
        "vertex_count": vertex_count,
        "head_bone_index": head_bone_index,
    }


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
        if token == "head" or (
            token.begins_with("head") and token.substr(4).is_valid_int()
        ):
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
        if mesh_instance.mesh == null:
            continue
        var label := str(mesh_instance.name) + " " + str(mesh_instance.mesh.resource_name) + " " + str(scene.get_path_to(mesh_instance))
        var is_named_head := _classify_mesh_slot(label) == "head"
        var has_face_morphs := mesh_instance.get_blend_shape_count() > 0
        if not is_named_head and not has_face_morphs:
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

    var skin_surface := _named_surface_bounds_in_bone_space(
        head_mesh, skeleton, head_bone_index, ["skin"]
    )
    if not bool(skin_surface.get("found", false)):
        return {"ok": false, "error_code": "face_template_skin_surface_missing", "error": "The imported head does not have a separable skin surface to replace with the generated face template."}
    head_bounds = skin_surface["bounds"]
    var eye_surface := _named_surface_bounds_in_bone_space(
        head_mesh, skeleton, head_bone_index, ["eye"]
    )
    var brow_surface := _named_surface_bounds_in_bone_space(
        head_mesh, skeleton, head_bone_index, ["brow", "eyebrow"]
    )
    var left_eye_surface := _named_surface_bounds_in_bone_space(
        head_mesh, skeleton, head_bone_index, ["eye"], head_bounds.get_center().x, -1
    )
    var right_eye_surface := _named_surface_bounds_in_bone_space(
        head_mesh, skeleton, head_bone_index, ["eye"], head_bounds.get_center().x, 1
    )
    var center := head_bounds.get_center()
    var face_width := clampf(float(recipe.get("face_width", 1.0)), 0.8, 1.25)
    var cheek_fullness := clampf(float(recipe.get("cheek_fullness", 1.0)), 0.5, 1.5)
    var jaw_width := clampf(float(recipe.get("jaw_width", 1.0)), 0.7, 1.3)
    var chin_length := clampf(float(recipe.get("chin_length", 1.0)), 0.65, 1.4)
    var ear_size := clampf(float(recipe.get("ear_size", 1.0)), 0.6, 1.5)
    var nose_width := clampf(float(recipe.get("nose_width", 1.0)), 0.65, 1.5)
    var nose_height := clampf(float(recipe.get("nose_height", 1.0)), 0.65, 1.5)
    var mouth_width := clampf(float(recipe.get("mouth_width", 1.0)), 0.65, 1.5)
    var moustache_enabled := bool(recipe.get("moustache_enabled", false))
    var moustache_size := clampf(float(recipe.get("moustache_size", 1.0)), 0.6, 1.5)
    var width := maxf(maxf(head_bounds.size.x * 0.56, head_bounds.size.y * 0.18), 0.035) * face_width
    var height := maxf(maxf(head_bounds.size.y * 0.48, width * 0.55), 0.035)
    var front_info := _head_front_direction(head_mesh, skeleton, head_bone_index, center)
    var front_direction := float(front_info.get("direction", 1.0))
    var eye_scale := clampf(float(recipe.get("eye_scale", 1.0)), 0.65, 1.5)
    var eye_spacing := clampf(float(recipe.get("eye_spacing", 1.0)), 0.65, 1.35)
    var smile := clampf(float(recipe.get("smile", 0.35)), -1.0, 1.0)
    var mouth_open := clampf(float(recipe.get("mouth_open", 0.0)), 0.0, 1.0)
    var brow_angle := clampf(float(recipe.get("brow_angle", 0.0)), -0.5, 0.5)
    var eye_depth := maxf(width * 0.045, 0.008)
    var eye_bounds: AABB = eye_surface["bounds"] if bool(eye_surface.get("found", false)) else AABB()
    var eye_center: Vector3 = eye_bounds.get_center() if bool(eye_surface.get("found", false)) else Vector3(center.x, center.y + height * 0.10, center.z)
    var eye_y: float = eye_center.y
    var front_z := _generated_face_front_depth(head_bounds, center, center.x, eye_y, face_width, cheek_fullness, jaw_width, front_direction)
    var eye_width := width * 0.105 * eye_scale
    var eye_height := height * 0.17 * eye_scale
    if bool(eye_surface.get("found", false)):
        eye_width = minf(eye_width, maxf(eye_bounds.size.x * 0.12, 0.005))
        eye_height = minf(eye_height, maxf(eye_bounds.size.y * 0.45, 0.005))
    var eye_offset := maxf(eye_bounds.size.x * 0.25, width * 0.18) * eye_spacing if bool(eye_surface.get("found", false)) else width * 0.245 * eye_spacing
    var nose_y: float = eye_y - head_bounds.size.y * 0.08
    var mouth_y: float = eye_y - head_bounds.size.y * 0.27
    var brow_y: float = brow_surface["bounds"].get_center().y if bool(brow_surface.get("found", false)) else eye_y + eye_height * 1.15
    var skin_surface_indices: Array[int] = skin_surface.get("surface_indices", [])
    var nose_surface_z := _generated_face_front_depth(head_bounds, center, center.x, nose_y, face_width, cheek_fullness, jaw_width, front_direction)
    var mouth_surface_z := _generated_face_front_depth(head_bounds, center, center.x, mouth_y, face_width, cheek_fullness, jaw_width, front_direction)
    var brow_surface_z := _generated_face_front_depth(head_bounds, center, center.x, brow_y, face_width, cheek_fullness, jaw_width, front_direction)
    var generated_skin_color := str(recipe.get("skin_color", "#c98768"))
    if bool(recipe.get("skin_color_auto", true)):
        for surface_index in skin_surface_indices:
            var source_skin_material := head_mesh.get_active_material(surface_index)
            if source_skin_material is BaseMaterial3D:
                generated_skin_color = (source_skin_material as BaseMaterial3D).albedo_color.to_html(false)
                break
    var generated_nose_color := generated_skin_color if bool(recipe.get("nose_color_auto", true)) else str(recipe.get("nose_color", generated_skin_color))
    var replaced_surfaces := _suppress_imported_face_surfaces(head_mesh)

    var attachment := BoneAttachment3D.new()
    attachment.name = "CartoonStudio_Face_Attachment"
    attachment.bone_name = head_bone_name
    skeleton.add_child(attachment)
    attachment.owner = scene
    var eye_material := _face_material(str(recipe.get("eye_color", "#ffffff")))
    var iris_material := _face_material(str(recipe.get("iris_color", "#4b83b8")))
    var pupil_material := _face_material("#17191d")
    var brow_material := _face_material(str(recipe.get("brow_color", "#38251c")))
    var nose_material := _face_material(generated_nose_color)
    var mouth_material := _face_material(str(recipe.get("mouth_color", "#612b2b")))
    var moustache_material := _face_material(str(recipe.get("moustache_color", "#38251c")))
    var skin_material := _face_material(generated_skin_color)
    var mesh_count := 0
    var skin_replaced := false
    var replaced_surface_index := -1
    if skin_surface_indices.size() > 0:
        var skin_index := int(skin_surface_indices[0])
        var replacement := _replace_skin_surface_with_generated_face(
            head_mesh,
            skin_index,
            head_bone_index,
            head_bounds,
            center,
            face_width,
            cheek_fullness,
            jaw_width,
            chin_length,
            front_direction,
            skin_material,
        )
        if bool(replacement.get("ok", false)):
            skin_replaced = true
            replaced_surface_index = int(replacement.get("new_surface_index", -1))
        # Re-apply hidden materials to non-skin face surfaces lost during mesh replacement.
        _suppress_imported_face_surfaces(head_mesh)

    for side_index in range(2):
        var side: float = -1.0 if side_index == 0 else 1.0
        var ear_x := center.x + side * (head_bounds.size.x * 0.5 + width * 0.025)
        var ear_y: float = eye_y - head_bounds.size.y * 0.055
        var ear_surface_x := center.x + side * head_bounds.size.x * 0.46
        var ear_z := _generated_face_front_depth(
            head_bounds, center, ear_surface_x, ear_y, face_width, cheek_fullness, jaw_width, front_direction
        ) + front_direction * eye_depth * 0.25
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_Ear_" + str(side_index),
            Vector3(ear_x, ear_y, ear_z),
            Vector3(width * 0.11 * ear_size, height * 0.14 * ear_size, eye_depth * 0.78 * ear_size), skin_material)
        mesh_count += 1
        var inner_ear_z := _generated_face_front_depth(
            head_bounds, center, ear_surface_x, ear_y, face_width, cheek_fullness, jaw_width, front_direction
        ) + front_direction * eye_depth * 0.62
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_EarInner_" + str(side_index),
            Vector3(ear_x, ear_y, inner_ear_z),
            Vector3(width * 0.035 * ear_size, height * 0.075 * ear_size, eye_depth * 0.3 * ear_size), _face_material("#a96859"))
        mesh_count += 1

    for side_index in range(2):
        var side: float = -1.0 if side_index == 0 else 1.0
        var side_surface: Dictionary = left_eye_surface if side_index == 0 else right_eye_surface
        var eye_x: float = side_surface["bounds"].get_center().x if bool(side_surface.get("found", false)) else center.x + side * eye_offset
        eye_x = center.x + (eye_x - center.x) * eye_spacing if bool(side_surface.get("found", false)) else eye_x
        var eye_z := _generated_face_front_depth(head_bounds, center, eye_x, eye_y, face_width, cheek_fullness, jaw_width, front_direction)
        eye_z += front_direction * maxf(eye_depth * 0.08, 0.001)
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_EyeWhite_" + str(side),
            Vector3(eye_x, eye_y, eye_z),
            Vector3(eye_width, eye_height, eye_depth), eye_material)
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_Iris_" + str(side),
            Vector3(eye_x + width * 0.018, eye_y - height * 0.012, eye_z + front_direction * eye_depth * 0.82),
            Vector3(eye_width * 0.49, eye_height * 0.57, eye_depth * 0.42), iris_material)
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_Pupil_" + str(side),
            Vector3(eye_x + width * 0.022, eye_y - height * 0.012, eye_z + front_direction * eye_depth * 1.16),
            Vector3(eye_width * 0.23, eye_height * 0.34, eye_depth * 0.22), pupil_material)
        var brow := _add_face_sphere(attachment, scene, "CartoonStudio_Face_Brow_" + str(side),
            Vector3(eye_x, brow_y, brow_surface_z + front_direction * eye_depth * 0.08),
            Vector3(eye_width * 1.32, maxf(eye_height * 0.24, 0.004), eye_depth * 0.3), brow_material)
        brow.rotation.z = -side * brow_angle
        mesh_count += 4

    var nose_bridge_y := eye_y - (eye_y - nose_y) * 0.42
    var nose_bridge_z := _generated_face_front_depth(head_bounds, center, center.x, nose_bridge_y, face_width, cheek_fullness, jaw_width, front_direction)
    _add_face_sphere(attachment, scene, "CartoonStudio_Face_NoseBridge",
        Vector3(center.x, nose_bridge_y, nose_bridge_z + front_direction * eye_depth * 0.32),
        Vector3(width * 0.025 * nose_width, height * 0.075 * nose_height, eye_depth * 0.45), nose_material)
    mesh_count += 1
    _add_face_sphere(attachment, scene, "CartoonStudio_Face_Nose",
        Vector3(center.x, nose_y, nose_surface_z + front_direction * eye_depth * 0.42),
        Vector3(width * 0.05 * nose_width, height * 0.055 * nose_height, eye_depth * 0.62), nose_material)
    mesh_count += 1
    var nostril_material := _face_material("#633e36")
    for side_index in range(2):
        var side: float = -1.0 if side_index == 0 else 1.0
        var nostril_x := center.x + side * width * 0.027 * nose_width
        var nostril_y: float = nose_y - head_bounds.size.y * 0.025
        var nostril_z := _generated_face_front_depth(head_bounds, center, nostril_x, nostril_y, face_width, cheek_fullness, jaw_width, front_direction)
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_Nostril_" + str(side_index),
            Vector3(nostril_x, nostril_y, nostril_z + front_direction * eye_depth * 0.82),
            Vector3(width * 0.016 * nose_width, height * 0.018 * nose_height, eye_depth * 0.19), nostril_material)
        mesh_count += 1

    var mouth_half := width * 0.19 * mouth_width
    if moustache_enabled:
        var moustache_y := mouth_y + height * 0.15
        for side_index in range(2):
            var side: float = -1.0 if side_index == 0 else 1.0
            var moustache_x := center.x + side * width * 0.078 * moustache_size
            var moustache_z := _generated_face_front_depth(
                head_bounds, center, moustache_x, moustache_y,
                face_width, cheek_fullness, jaw_width, front_direction
            )
            var moustache_lobe := _add_face_sphere(attachment, scene,
                "CartoonStudio_Face_Moustache_" + str(side_index),
                Vector3(moustache_x, moustache_y, moustache_z + front_direction * eye_depth * 0.38),
                Vector3(width * 0.075 * moustache_size, height * 0.032 * moustache_size, eye_depth * 0.42),
                moustache_material
            )
            moustache_lobe.rotation.z = -side * 0.16
            mesh_count += 1
    var mouth_depth := mouth_surface_z + front_direction * eye_depth * 0.38
    var mouth_opening := _add_face_sphere(attachment, scene, "CartoonStudio_Face_MouthOpening",
        Vector3(center.x, mouth_y, mouth_depth),
        Vector3(mouth_half, height * 0.13, eye_depth * 0.62), mouth_material)
    mouth_opening.visible = mouth_open > 0.08
    mesh_count += 1
    var mouth_points := [
        Vector3(center.x - mouth_half, mouth_y + smile * height * 0.075, _generated_face_front_depth(head_bounds, center, center.x - mouth_half, mouth_y + smile * height * 0.075, face_width, cheek_fullness, jaw_width, front_direction) + front_direction * eye_depth * 0.42),
        Vector3(center.x - mouth_half * 0.5, mouth_y - smile * height * 0.07, _generated_face_front_depth(head_bounds, center, center.x - mouth_half * 0.5, mouth_y - smile * height * 0.07, face_width, cheek_fullness, jaw_width, front_direction) + front_direction * eye_depth * 0.42),
        Vector3(center.x + mouth_half * 0.5, mouth_y - smile * height * 0.07, _generated_face_front_depth(head_bounds, center, center.x + mouth_half * 0.5, mouth_y - smile * height * 0.07, face_width, cheek_fullness, jaw_width, front_direction) + front_direction * eye_depth * 0.42),
        Vector3(center.x + mouth_half, mouth_y + smile * height * 0.075, _generated_face_front_depth(head_bounds, center, center.x + mouth_half, mouth_y + smile * height * 0.075, face_width, cheek_fullness, jaw_width, front_direction) + front_direction * eye_depth * 0.42)
    ]
    var mouth_radius := maxf(width * 0.012, 0.003)
    for segment_index in range(mouth_points.size() - 1):
        var mouth_segment := _add_face_mouth_segment(attachment, scene,
            "CartoonStudio_Face_Mouth_" + str(segment_index),
            mouth_points[segment_index], mouth_points[segment_index + 1],
            mouth_radius, mouth_material)
        mouth_segment.visible = mouth_open <= 0.08
        mesh_count += 1
    if mouth_open > 0.45:
        var tongue_material := _face_material("#c65f72")
        _add_face_sphere(attachment, scene, "CartoonStudio_Face_MouthTongue",
            Vector3(center.x, mouth_y - height * 0.035, mouth_depth + front_direction * eye_depth * 0.62),
            Vector3(mouth_half * 0.52, height * 0.025, eye_depth * 0.2), tongue_material)
        mesh_count += 1

    return {
        "ok": true,
        "mesh_count": mesh_count,
        "attachment_bone": head_bone_name,
        "front_direction": front_direction,
        "fit_basis": "generated_head_template",
        "head_mesh_name": str(head_mesh.name),
        "skin_replaced": skin_replaced,
        "replaced_surface_index": replaced_surface_index,
        "replaced_surfaces": replaced_surfaces,
        "eye_anchor": [eye_center.x, eye_center.y, front_z],
        "nose_anchor": [center.x, nose_y, nose_surface_z],
        "mouth_anchor": [center.x, mouth_y, mouth_surface_z]
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
        var generated_face_surface_found := false
        for mesh_record in verification.get("mesh_inventory", []):
            if str(mesh_record.get("node_name", "")).begins_with("CartoonStudio_Face_"):
                face_mesh_count += 1
                if str(mesh_record.get("attachment_bone", "")) == str(face_result.get("attachment_bone", "")):
                    face_attachment_verified = true
            var surface_names: Array = mesh_record.get("surface_names", [])
            for surface_name in surface_names:
                if str(surface_name) == "CartoonStudio_GeneratedFace":
                    generated_face_surface_found = true
        if face_mesh_count < int(face_result.get("mesh_count", 0)) or not face_attachment_verified:
            DirAccess.remove_absolute(output_path)
            return {"error_code": "appearance_face_verification_failed", "error": "Generated facial meshes or their Head-bone attachment did not survive GLB export and re-import."}
        if bool(face_result.get("skin_replaced", false)) and not generated_face_surface_found:
            DirAccess.remove_absolute(output_path)
            return {"error_code": "appearance_face_replacement_verification_failed", "error": "Generated face surface was not found on the head mesh after export and re-import."}
        verification["face_features_verified"] = true
        verification["face_attachment_bone"] = str(face_result.get("attachment_bone", ""))
        verification["face_front_direction"] = float(face_result.get("front_direction", 1.0))
        verification["face_fit_basis"] = str(face_result.get("fit_basis", ""))
        verification["face_skin_replaced"] = bool(face_result.get("skin_replaced", false))
        verification["face_eye_anchor"] = face_result.get("eye_anchor", [])
        verification["face_nose_anchor"] = face_result.get("nose_anchor", [])
        verification["face_mouth_anchor"] = face_result.get("mouth_anchor", [])
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



func _world_material(color_value: String, roughness: float = 0.86) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = Color.from_string(color_value, Color.WHITE)
    material.roughness = roughness
    return material


func _world_add_box(parent: Node3D, node_name: String, size: Vector3, position: Vector3, color_value: String) -> MeshInstance3D:
    var mesh_node := MeshInstance3D.new()
    mesh_node.name = node_name
    var mesh := BoxMesh.new()
    mesh.size = size
    mesh_node.mesh = mesh
    mesh_node.material_override = _world_material(color_value)
    mesh_node.position = position
    parent.add_child(mesh_node)
    return mesh_node


func _world_add_sphere(parent: Node3D, node_name: String, radius: float, position: Vector3, color_value: String) -> MeshInstance3D:
    var mesh_node := MeshInstance3D.new()
    mesh_node.name = node_name
    var mesh := SphereMesh.new()
    mesh.radius = radius
    mesh.height = radius * 2.0
    mesh_node.mesh = mesh
    mesh_node.material_override = _world_material(color_value)
    mesh_node.position = position
    parent.add_child(mesh_node)
    return mesh_node




func _world_add_cylinder(parent: Node3D, node_name: String, radius: float, height: float, position: Vector3, color_value: String) -> MeshInstance3D:
    var mesh_node := MeshInstance3D.new()
    mesh_node.name = node_name
    var mesh := CylinderMesh.new()
    mesh.top_radius = radius
    mesh.bottom_radius = radius
    mesh.height = height
    mesh_node.mesh = mesh
    mesh_node.material_override = _world_material(color_value)
    mesh_node.position = position
    parent.add_child(mesh_node)
    return mesh_node

func _export_world_scene(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var output_path := _normalise_path(str(payload.get("output_path", "")))
    var output_glb_path := _normalise_path(str(payload.get("output_glb_path", "")))
    var world_value: Variant = payload.get("world", {})
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    if not output_path.to_lower().begins_with(root_prefix.to_lower()) or not output_path.to_lower().ends_with(".tscn"):
        return {"error_code": "path_outside_project", "error": "World scene output must be a project-local .tscn file."}
    if not output_glb_path.to_lower().begins_with(root_prefix.to_lower()) or not output_glb_path.to_lower().ends_with(".glb"):
        return {"error_code": "path_outside_project", "error": "World preview output must be a project-local .glb file."}
    if FileAccess.file_exists(output_path) or FileAccess.file_exists(output_glb_path):
        return {"error_code": "output_exists", "error": "Refusing to overwrite an existing world export."}
    if typeof(world_value) != TYPE_DICTIONARY:
        return {"error_code": "invalid_world", "error": "World layout must be a JSON object."}
    var world: Dictionary = world_value
    var objects_value: Variant = world.get("objects", [])
    if typeof(objects_value) != TYPE_ARRAY or objects_value.size() > 100:
        return {"error_code": "invalid_objects", "error": "World layout supports up to 100 objects."}
    var sky_name := str(world.get("sky", "day"))
    if not ["day", "sunset", "night"].has(sky_name):
        return {"error_code": "invalid_sky", "error": "Unsupported world lighting preset."}
    var theme_name := str(world.get("theme", "small_town"))
    if not ["small_town", "village", "market", "park"].has(theme_name):
        return {"error_code": "invalid_theme", "error": "Unsupported world theme."}
    var ground_color := str(world.get("ground_color", "#789b58"))
    var root := Node3D.new()
    root.name = "CartoonWorld"
    root.set_meta("world_name", str(world.get("name", "Cartoon World")))
    root.set_meta("world_theme", str(world.get("theme", "small_town")))

    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    var sky_color := Color("#8bc9ed")
    var light_color := Color("#fff1d1")
    var ambient_color := Color("#a8bfd0")
    var light_energy := 1.0
    if sky_name == "sunset":
        sky_color = Color("#ef9b72")
        light_color = Color("#ffc18a")
        ambient_color = Color("#c88979")
        light_energy = 0.78
    elif sky_name == "night":
        sky_color = Color("#18243f")
        light_color = Color("#9bb7ef")
        ambient_color = Color("#53658b")
        light_energy = 0.34
    environment.background_color = sky_color
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = ambient_color
    environment.ambient_light_energy = 0.7
    var world_environment := WorldEnvironment.new()
    world_environment.name = "WorldEnvironment"
    world_environment.environment = environment
    root.add_child(world_environment)

    var sunlight := DirectionalLight3D.new()
    sunlight.name = "Sunlight"
    sunlight.rotation_degrees = Vector3(-48.0, -32.0, 0.0)
    sunlight.light_color = light_color
    sunlight.light_energy = light_energy
    sunlight.shadow_enabled = true
    root.add_child(sunlight)

    var world_camera := Camera3D.new()
    world_camera.name = "WorldCamera"
    world_camera.position = Vector3(92.0, 76.0, 105.0)
    world_camera.look_at(Vector3.ZERO, Vector3.UP)
    world_camera.current = true
    root.add_child(world_camera)

    _world_add_box(root, "Ground", Vector3(100.0, 0.5, 100.0), Vector3(0.0, -0.28, 0.0), ground_color)
    var object_count := 0
    for object_value in objects_value:
        if typeof(object_value) != TYPE_DICTIONARY:
            continue
        var item: Dictionary = object_value
        var kind := str(item.get("kind", ""))
        if not ["road", "building", "shop", "school", "hospital", "office", "police_station", "tree", "vehicle", "lamp", "park", "garage", "indoor_room", "playground", "furniture", "water_body", "streetlight"].has(kind):
            continue
        var x := (float(item.get("x", 50.0)) - 50.0) * 0.9
        var z := (float(item.get("y", 50.0)) - 50.0) * 0.9
        var width := clampf(float(item.get("width", 12.0)) * 0.72, 1.5, 72.0)
        var depth := clampf(float(item.get("height", 8.0)) * 0.72, 1.5, 44.0)
        var rotation := float(item.get("rotation", 0.0))
        var tint := str(item.get("color", "#c89b67"))
        var anchor := Node3D.new()
        anchor.name = "WorldObject_%03d_%s" % [object_count + 1, kind]
        anchor.position = Vector3(x, 0.0, z)
        anchor.rotation_degrees.y = -rotation
        anchor.set_meta("label", str(item.get("label", kind.capitalize())))
        root.add_child(anchor)

        if kind == "road":
            _world_add_box(anchor, "RoadSurface", Vector3(width, 0.12, depth), Vector3.ZERO, "#4b4d50")
            _world_add_box(anchor, "RoadMarking", Vector3(maxf(0.15, width * 0.018), 0.025, depth * 0.82), Vector3(0.0, 0.075, 0.0), "#f5e7b2")
        elif kind == "building" or kind == "shop":
            var body_height := clampf(depth * 0.72, 2.8, 12.0)
            _world_add_box(anchor, "BuildingBody", Vector3(width * 0.78, body_height, depth * 0.72), Vector3(0.0, body_height * 0.5, 0.0), tint)
            _world_add_box(anchor, "Roof", Vector3(width * 0.9, 0.65, depth * 0.84), Vector3(0.0, body_height + 0.25, 0.0), "#854f3d")
            _world_add_box(anchor, "Door", Vector3(width * 0.12, body_height * 0.42, 0.12), Vector3(0.0, body_height * 0.21, depth * 0.37), "#49352b")
            for window_index in range(2):
                var window_x := (float(window_index) - 0.5) * width * 0.38
                _world_add_box(anchor, "Window_%d" % window_index, Vector3(width * 0.18, body_height * 0.2, 0.1), Vector3(window_x, body_height * 0.62, depth * 0.37), "#9dd8e8")
            if kind == "shop":
                _world_add_box(anchor, "ShopAwning", Vector3(width * 0.86, 0.38, depth * 0.2), Vector3(0.0, body_height * 0.72, depth * 0.45), "#d95d4f")
        elif kind in ["school", "hospital", "office", "police_station"]:
            var body_height := clampf(depth * 0.72, 2.8, 14.0)
            _world_add_box(anchor, "BuildingBody", Vector3(width * 0.78, body_height, depth * 0.72), Vector3(0.0, body_height * 0.5, 0.0), tint)
            _world_add_box(anchor, "Roof", Vector3(width * 0.92, 0.65, depth * 0.84), Vector3(0.0, body_height + 0.25, 0.0), "#6a5c4d")
            _world_add_box(anchor, "Door", Vector3(width * 0.1, body_height * 0.42, 0.12), Vector3(0.0, body_height * 0.21, depth * 0.37), "#49352b")
            for window_index in range(3):
                var window_x := (float(window_index) - 1.0) * width * 0.3
                _world_add_box(anchor, "Window_%d" % window_index, Vector3(width * 0.16, body_height * 0.18, 0.1), Vector3(window_x, body_height * 0.6, depth * 0.37), "#9dd8e8")
        elif kind == "garage":
            var body_height := clampf(depth * 0.6, 2.4, 10.0)
            _world_add_box(anchor, "GarageBody", Vector3(width * 0.82, body_height, depth * 0.78), Vector3(0.0, body_height * 0.5, 0.0), tint)
            _world_add_box(anchor, "GarageRoof", Vector3(width * 0.9, 0.5, depth * 0.86), Vector3(0.0, body_height + 0.2, 0.0), "#5a5a5a")
            _world_add_box(anchor, "GarageDoor", Vector3(width * 0.62, body_height * 0.5, 0.12), Vector3(0.0, body_height * 0.25, depth * 0.4), "#8a7a6a")
        elif kind == "indoor_room":
            _world_add_box(anchor, "RoomFloor", Vector3(width, 0.12, depth), Vector3.ZERO, "#e8dcc8")
            _world_add_box(anchor, "RoomWalls", Vector3(width * 0.98, clampf(depth * 0.5, 2.0, 6.0), depth * 0.98), Vector3(0.0, clampf(depth * 0.25, 1.0, 3.0), 0.0), "#f4ede0")
        elif kind == "playground":
            var body_height := clampf(depth * 0.6, 2.4, 10.0)
            _world_add_box(anchor, "PlaygroundSurface", Vector3(width, 0.16, depth), Vector3.ZERO, "#7aa85b")
            _world_add_box(anchor, "Slide", Vector3(width * 0.3, body_height * 0.5, depth * 0.25), Vector3(-width * 0.2, body_height * 0.25, depth * 0.2), "#e85a4f")
            _world_add_sphere(anchor, "ClimbingDome", maxf(1.2, minf(width, depth) * 0.25), Vector3(width * 0.2, maxf(1.2, depth * 0.2), -depth * 0.15), "#a8a8a8")
        elif kind == "furniture":
            var seat_height := clampf(depth * 0.45, 0.4, 0.9)
            _world_add_box(anchor, "FurnitureBase", Vector3(width, seat_height, depth), Vector3(0.0, seat_height * 0.5, 0.0), tint)
            _world_add_box(anchor, "FurnitureTop", Vector3(width * 1.05, 0.1, depth * 1.05), Vector3(0.0, seat_height + 0.05, 0.0), "#8a7a6a")
        elif kind == "water_body":
            _world_add_box(anchor, "WaterSurface", Vector3(width, 0.06, depth), Vector3.ZERO, "#5b9bd5")
            _world_add_box(anchor, "WaterBank", Vector3(width * 1.1, 0.12, depth * 1.1), Vector3.ZERO, "#8a9ba8")
        elif kind == "streetlight":
            var pole_height := clampf(depth * 0.9, 3.0, 6.0)
            var pole := MeshInstance3D.new()
            pole.name = "StreetlightPole"
            var pole_mesh := CylinderMesh.new()
            pole_mesh.top_radius = 0.08
            pole_mesh.bottom_radius = 0.12
            pole_mesh.height = pole_height
            pole.mesh = pole_mesh
            pole.material_override = _world_material("#444b50")
            pole.position.y = pole_height * 0.5
            anchor.add_child(pole)
            _world_add_sphere(anchor, "StreetlightLamp", 0.4, Vector3(0.0, pole_height + 0.15, 0.0), "#ffe6a1")
        elif kind == "tree":
            var trunk := MeshInstance3D.new()
            trunk.name = "Trunk"
            var trunk_mesh := CylinderMesh.new()
            trunk_mesh.top_radius = 0.28
            trunk_mesh.bottom_radius = 0.42
            trunk_mesh.height = maxf(2.0, depth * 0.48)
            trunk.mesh = trunk_mesh
            trunk.material_override = _world_material("#795139")
            trunk.position.y = trunk_mesh.height * 0.5
            anchor.add_child(trunk)
            _world_add_sphere(anchor, "Canopy", maxf(1.1, minf(width, depth) * 0.32), Vector3(0.0, trunk_mesh.height + 1.0, 0.0), tint)
        elif kind == "vehicle":
            _world_add_box(anchor, "VehicleBody", Vector3(width, 0.85, depth * 0.7), Vector3(0.0, 0.85, 0.0), tint)
            _world_add_box(anchor, "Cabin", Vector3(width * 0.48, 0.75, depth * 0.58), Vector3(0.0, 1.55, 0.0), "#a9d9e8")
            for wheel_x in [-width * 0.34, width * 0.34]:
                for wheel_z in [-depth * 0.28, depth * 0.28]:
                    var wheel := MeshInstance3D.new()
                    wheel.name = "Wheel"
                    var wheel_mesh := CylinderMesh.new()
                    wheel_mesh.top_radius = 0.34
                    wheel_mesh.bottom_radius = 0.34
                    wheel_mesh.height = 0.22
                    wheel.mesh = wheel_mesh
                    wheel.material_override = _world_material("#24272a")
                    wheel.position = Vector3(wheel_x, 0.38, wheel_z)
                    wheel.rotation_degrees.z = 90.0
                    anchor.add_child(wheel)
        elif kind == "lamp":
            var pole := MeshInstance3D.new()
            pole.name = "LampPost"
            var pole_mesh := CylinderMesh.new()
            pole_mesh.top_radius = 0.09
            pole_mesh.bottom_radius = 0.14
            pole_mesh.height = maxf(3.0, depth)
            pole.mesh = pole_mesh
            pole.material_override = _world_material("#444b50")
            pole.position.y = pole_mesh.height * 0.5
            anchor.add_child(pole)
            _world_add_sphere(anchor, "LampHead", 0.38, Vector3(0.0, pole_mesh.height + 0.25, 0.0), "#ffe6a1")
        elif kind == "park":
            _world_add_box(anchor, "ParkGrass", Vector3(width, 0.16, depth), Vector3(0.0, 0.08, 0.0), "#5eaa61")
            _world_add_box(anchor, "ParkPath", Vector3(width * 0.16, 0.08, depth * 0.9), Vector3(0.0, 0.2, 0.0), "#d6c29c")
        object_count += 1


    var theme_prop_count := 0
    if theme_name == "market":
        for stall_index in range(3):
            var stall := Node3D.new()
            stall.name = "MarketStall_%02d" % (stall_index + 1)
            stall.position = Vector3(-20.0 + float(stall_index) * 20.0, 0.0, -15.0)
            root.add_child(stall)
            _world_add_box(stall, "Counter", Vector3(7.0, 1.0, 3.2), Vector3(0.0, 0.75, 0.0), "#9a6846")
            for post_x in [-3.1, 3.1]:
                for post_z in [-1.25, 1.25]:
                    _world_add_cylinder(stall, "CanopyPost", 0.12, 3.2, Vector3(post_x, 1.6, post_z), "#6d4b36")
            var canopy_color: String = "#d85f52"
            if stall_index == 1:
                canopy_color = "#e2b34e"
            elif stall_index == 2:
                canopy_color = "#4f91a4"
            _world_add_box(stall, "StripedCanopy", Vector3(7.8, 0.42, 4.0), Vector3(0.0, 3.25, 0.0), canopy_color)
            _world_add_box(stall, "FrontSign", Vector3(4.2, 0.75, 0.18), Vector3(0.0, 2.35, 1.72), "#f4dfb6")
        theme_prop_count = 3
    elif theme_name == "village":
        var village_well := Node3D.new()
        village_well.name = "VillageWell"
        village_well.position = Vector3(0.0, 0.0, -12.0)
        root.add_child(village_well)
        _world_add_cylinder(village_well, "StoneWell", 1.7, 1.5, Vector3(0.0, 0.75, 0.0), "#a69b83")
        _world_add_cylinder(village_well, "WellOpening", 1.15, 0.16, Vector3(0.0, 1.55, 0.0), "#51483f")
        _world_add_box(village_well, "WellRoof", Vector3(4.6, 0.28, 3.4), Vector3(0.0, 3.4, 0.0), "#81533a")
        for fence_index in range(8):
            var fence_angle := TAU * float(fence_index) / 8.0
            var fence_post := Node3D.new()
            fence_post.name = "VillageFence_%02d" % (fence_index + 1)
            fence_post.position = Vector3(cos(fence_angle) * 13.0, 0.0, sin(fence_angle) * 13.0 + 18.0)
            fence_post.rotation_degrees.y = -rad_to_deg(fence_angle)
            root.add_child(fence_post)
            _world_add_box(fence_post, "FencePost", Vector3(0.35, 1.6, 0.35), Vector3.ZERO, "#896344")
            _world_add_box(fence_post, "FenceRail", Vector3(3.4, 0.22, 0.24), Vector3(0.0, 0.75, -1.5), "#b58a5e")
        theme_prop_count = 9
    elif theme_name == "park":
        for bench_index in range(3):
            var bench := Node3D.new()
            bench.name = "ParkBench_%02d" % (bench_index + 1)
            bench.position = Vector3(-16.0 + float(bench_index) * 16.0, 0.0, -10.0)
            bench.rotation_degrees.y = float(bench_index) * 35.0
            root.add_child(bench)
            _world_add_box(bench, "Seat", Vector3(4.0, 0.28, 1.0), Vector3(0.0, 1.0, 0.0), "#9b6946")
            _world_add_box(bench, "BackRest", Vector3(4.0, 1.1, 0.24), Vector3(0.0, 1.65, -0.38), "#b27b4e")
            for leg_x in [-1.55, 1.55]:
                _world_add_box(bench, "BenchLeg", Vector3(0.22, 0.95, 0.22), Vector3(leg_x, 0.48, 0.0), "#444b50")
        for flower_index in range(8):
            var flower_x := -24.0 + float(flower_index) * 6.8
            var flower_color: String = "#e7a2a4"
            if flower_index % 3 == 1:
                flower_color = "#f3d16c"
            elif flower_index % 3 == 2:
                flower_color = "#a6a8dc"
            _world_add_sphere(root, "ParkFlower_%02d" % flower_index, 0.42, Vector3(flower_x, 0.45, 18.0), flower_color)
        theme_prop_count = 11
    else:
        var bus_stop := Node3D.new()
        bus_stop.name = "TownBusStop"
        bus_stop.position = Vector3(0.0, 0.0, -16.0)
        root.add_child(bus_stop)
        for shelter_x in [-3.0, 3.0]:
            _world_add_box(bus_stop, "ShelterPost", Vector3(0.22, 3.1, 0.22), Vector3(shelter_x, 1.55, 0.0), "#46535b")
        _world_add_box(bus_stop, "ShelterRoof", Vector3(7.0, 0.35, 3.2), Vector3(0.0, 3.15, 0.0), "#477f94")
        _world_add_box(bus_stop, "BusBench", Vector3(4.4, 0.35, 0.85), Vector3(0.0, 0.85, 0.0), "#9a6846")
        _world_add_box(bus_stop, "StopSign", Vector3(1.8, 1.4, 0.16), Vector3(0.0, 2.35, 1.65), "#e4c65d")
        theme_prop_count = 1

    var packed := PackedScene.new()
    _set_scene_ownership(root, root)
    var pack_error := packed.pack(root)
    if pack_error != OK:
        root.free()
        return {"error_code": "scene_pack_failed", "error": "Godot could not pack the generated world scene.", "godot_error": pack_error}
    var save_error := ResourceSaver.save(packed, output_path)
    if save_error != OK:
        root.free()
        return {"error_code": "scene_save_failed", "error": "Godot could not save the generated world scene.", "godot_error": save_error}
    var gltf_document := GLTFDocument.new()
    var gltf_state := GLTFState.new()
    var append_error := gltf_document.append_from_scene(root, gltf_state)
    if append_error != OK:
        root.free()
        DirAccess.remove_absolute(output_path)
        return {"error_code": "glb_build_failed", "error": "Godot could not convert the world scene to glTF.", "godot_error": append_error}
    var glb_error := gltf_document.write_to_filesystem(gltf_state, output_glb_path)
    root.free()
    if glb_error != OK:
        DirAccess.remove_absolute(output_path)
        DirAccess.remove_absolute(output_glb_path)
        return {"error_code": "glb_save_failed", "error": "Godot could not save the world preview GLB.", "godot_error": glb_error}
    var reopened := ResourceLoader.load(output_path) as PackedScene
    if reopened == null:
        DirAccess.remove_absolute(output_path)
        DirAccess.remove_absolute(output_glb_path)
        return {"error_code": "scene_reopen_failed", "error": "The saved world scene could not be reopened."}
    var reopened_root := reopened.instantiate()
    var reopened_objects := reopened_root.get_children().size()
    reopened_root.free()
    return {
        "ok": true,
        "output_path": output_path,
        "output_glb_path": output_glb_path,
        "glb_exported": FileAccess.file_exists(output_glb_path),
        "world_name": str(world.get("name", "Cartoon World")),
        "object_count": object_count,
        "theme_prop_count": theme_prop_count,
        "world_theme": theme_name,
        "scene_reopened": true,
        "scene_child_count": reopened_objects,
        "lighting_preset": sky_name
    }



func _episode_action_pose(action_id: String) -> Dictionary:
    var offset := Vector3.ZERO
    var rotation := Vector3.ZERO
    match action_id:
        "walk", "walk_back", "run", "strafe_left", "strafe_right":
            if action_id == "walk":
                offset.z = -1.0
            elif action_id == "walk_back":
                offset.z = 0.8
            elif action_id == "run":
                offset.z = -1.8
            elif action_id == "strafe_left":
                offset.x = -1.0
            else:
                offset.x = 1.0
        "jump_start", "jump_air", "jump_land", "jump_running":
            offset.y = 1.2 if action_id == "jump_air" else 0.65
        "fall", "stumble_recover":
            rotation.z = 0.65
        "wave", "talk_gestures", "point", "thumbs_up", "clap", "cheer":
            rotation.y = 0.18
            rotation.z = -0.16
        "bow":
            rotation.x = 0.35
        "dance_groove", "dance_bounce", "laugh":
            rotation.y = 0.3
            rotation.z = 0.2
        "crouch", "pick_up", "put_down", "sweep":
            offset.y = -0.35
            rotation.x = 0.18
        "drive_car", "sit_passenger", "lean_wall", "phone_call", "texting":
            rotation.x = -0.12
        "open_door", "push", "use_press", "punch", "hit":
            rotation.y = -0.22
    return {"offset": offset, "rotation": rotation}


func _episode_expression_values(expression_id: String) -> Dictionary:
    match expression_id:
        "happy":
            return {"mouth_open": 0.22, "brow_angle": -0.08, "eye_scale": 1.05}
        "laughing":
            return {"mouth_open": 0.9, "brow_angle": -0.08, "eye_scale": 1.12}
        "angry":
            return {"mouth_open": 0.16, "brow_angle": 0.42, "eye_scale": 0.92}
        "sad":
            return {"mouth_open": 0.08, "brow_angle": 0.2, "eye_scale": 0.96}
        "crying":
            return {"mouth_open": 0.38, "brow_angle": 0.24, "eye_scale": 0.92}
        "surprised":
            return {"mouth_open": 0.86, "brow_angle": -0.42, "eye_scale": 1.35}
        "afraid":
            return {"mouth_open": 0.68, "brow_angle": -0.3, "eye_scale": 1.28}
        "determined":
            return {"mouth_open": 0.1, "brow_angle": 0.3, "eye_scale": 0.96}
        _:
            return {"mouth_open": 0.0, "brow_angle": 0.0, "eye_scale": 1.0}


func _add_episode_expression_tracks(
    animation: Animation,
    scene_root: Node3D,
    character_anchor: Node3D,
    expression_id: String,
    start_time: float,
    middle_time: float,
    end_time: float,
    animate_mouth: bool = true
) -> int:
    var expression := _episode_expression_values(expression_id)
    var mouth_open := float(expression["mouth_open"])
    var brow_angle := float(expression["brow_angle"])
    var eye_scale := float(expression["eye_scale"])
    var track_count := 0
    var face_nodes := character_anchor.find_children("*", "MeshInstance3D", true, false)
    for node_value in face_nodes:
        var face_node := node_value as MeshInstance3D
        var face_name := str(face_node.name)
        var node_path := str(scene_root.get_path_to(face_node))
        if animate_mouth and face_name == "CartoonStudio_Face_MouthOpening":
            var mouth_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(mouth_track, NodePath(node_path + ":visible"))
            animation.track_insert_key(mouth_track, start_time, face_node.visible)
            animation.track_insert_key(mouth_track, middle_time, mouth_open > 0.08)
            animation.track_insert_key(mouth_track, end_time, face_node.visible)
            var mouth_scale_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(mouth_scale_track, NodePath(node_path + ":scale"))
            var closed_scale := face_node.scale
            var open_scale := closed_scale
            open_scale.y = closed_scale.y * clampf(mouth_open, 0.12, 1.0)
            animation.track_insert_key(mouth_scale_track, start_time, closed_scale)
            animation.track_insert_key(mouth_scale_track, middle_time, open_scale)
            animation.track_insert_key(mouth_scale_track, end_time, closed_scale)
            track_count += 2
        elif animate_mouth and face_name.begins_with("CartoonStudio_Face_Mouth_"):
            var line_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(line_track, NodePath(node_path + ":visible"))
            animation.track_insert_key(line_track, start_time, face_node.visible)
            animation.track_insert_key(line_track, middle_time, mouth_open <= 0.08)
            animation.track_insert_key(line_track, end_time, face_node.visible)
            track_count += 1
        elif face_name.begins_with("CartoonStudio_Face_Brow_"):
            var side := -1.0 if face_name.ends_with("-1") else 1.0
            var brow_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(brow_track, NodePath(node_path + ":rotation"))
            var base_rotation := face_node.rotation
            var expression_rotation := base_rotation
            expression_rotation.z = -side * brow_angle
            animation.track_insert_key(brow_track, start_time, base_rotation)
            animation.track_insert_key(brow_track, middle_time, expression_rotation)
            animation.track_insert_key(brow_track, end_time, base_rotation)
            track_count += 1
        elif face_name.begins_with("CartoonStudio_Face_EyeWhite_") or face_name.begins_with("CartoonStudio_Face_Iris_") or face_name.begins_with("CartoonStudio_Face_Pupil_"):
            var eye_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(eye_track, NodePath(node_path + ":scale"))
            var base_eye_scale := face_node.scale
            animation.track_insert_key(eye_track, start_time, base_eye_scale)
            animation.track_insert_key(eye_track, middle_time, base_eye_scale * eye_scale)
            animation.track_insert_key(eye_track, end_time, base_eye_scale)
            track_count += 1
    return track_count


func _add_dialogue_speech_tracks(
    animation: Animation,
    scene_root: Node3D,
    character_anchor: Node3D,
    line: Dictionary,
    start_time: float,
    end_time: float
) -> Dictionary:
    var face_nodes := character_anchor.find_children("*", "MeshInstance3D", true, false)
    var mouth_opening: MeshInstance3D = null
    var mouth_lines: Array[MeshInstance3D] = []
    for node_value in face_nodes:
        var face_node := node_value as MeshInstance3D
        var face_name := str(face_node.name)
        if face_name == "CartoonStudio_Face_MouthOpening":
            mouth_opening = face_node
        elif face_name.begins_with("CartoonStudio_Face_Mouth_"):
            mouth_lines.append(face_node)
    if mouth_opening == null or end_time - start_time <= 0.12:
        return {"track_count": 0, "keyframe_count": 0, "audio_driven": false}

    var audio_duration := maxf(
        0.0,
        float(line.get("audio_duration_seconds", end_time - start_time))
    )
    if audio_duration > 0.0:
        end_time = minf(maxf(end_time, start_time + audio_duration), animation.length)
    var mouth_node_path := str(scene_root.get_path_to(mouth_opening))
    var visibility_track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(visibility_track, NodePath(mouth_node_path + ":visible"))
    var scale_track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(scale_track, NodePath(mouth_node_path + ":scale"))
    var closed_scale := mouth_opening.scale
    closed_scale.y *= 0.08
    var open_scale := mouth_opening.scale

    var audio_envelope_value: Variant = line.get("audio_envelope", [])
    if typeof(audio_envelope_value) == TYPE_ARRAY and not audio_envelope_value.is_empty():
        var line_tracks: Array[int] = []
        for mouth_line in mouth_lines:
            var line_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(
                line_track,
                NodePath(str(scene_root.get_path_to(mouth_line)) + ":visible")
            )
            line_tracks.append(line_track)
            animation.track_insert_key(line_track, start_time, true)
        animation.track_insert_key(visibility_track, start_time, false)
        animation.track_insert_key(scale_track, start_time, closed_scale)
        var keyframe_count := 2
        var last_time := start_time
        for point_value in audio_envelope_value:
            if typeof(point_value) != TYPE_DICTIONARY:
                continue
            var point: Dictionary = point_value
            var key_time := clampf(
                start_time + float(point.get("time", 0.0)),
                start_time,
                end_time
            )
            if key_time <= last_time:
                continue
            var openness := clampf(float(point.get("openness", 0.0)), 0.0, 1.0)
            var is_open := openness >= 0.10
            animation.track_insert_key(visibility_track, key_time, is_open)
            animation.track_insert_key(
                scale_track,
                key_time,
                closed_scale.lerp(open_scale, openness)
            )
            for line_track in line_tracks:
                animation.track_insert_key(line_track, key_time, not is_open)
                keyframe_count += 1
            keyframe_count += 2
            last_time = key_time
        animation.track_insert_key(visibility_track, end_time, false)
        animation.track_insert_key(scale_track, end_time, closed_scale)
        for line_track in line_tracks:
            animation.track_insert_key(line_track, end_time, true)
            keyframe_count += 1
        keyframe_count += 2
        return {
            "track_count": 2 + line_tracks.size(),
            "keyframe_count": keyframe_count,
            "beat_count": audio_envelope_value.size(),
            "audio_driven": true
        }

    var text_value := str(line.get("text", "")).strip_edges()
    var delivery := str(line.get("delivery", "natural")).to_lower()
    var cadence := 1.0
    if delivery in ["excited", "fast", "urgent", "shouting"]:
        cadence = 0.72
    elif delivery in ["slow", "calm", "sad", "whisper"]:
        cadence = 1.3
    var estimated_syllables := maxi(1, int(ceil(float(maxi(text_value.length(), 1)) / 3.0)))
    var beat_count := clampi(int(ceil(float(estimated_syllables) / cadence)), 2, 28)
    var line_duration := end_time - start_time
    var lead_pause := minf(0.12, line_duration * 0.08)
    var tail_pause := minf(0.12, line_duration * 0.08)
    var active_start := start_time + lead_pause
    var active_end := maxf(active_start, end_time - tail_pause)
    var beat_period := (active_end - active_start) / float(beat_count)
    animation.track_insert_key(visibility_track, start_time, false)
    animation.track_insert_key(scale_track, start_time, closed_scale)
    var keyframe_count := 2
    for beat_index in range(beat_count):
        var beat_start := active_start + float(beat_index) * beat_period
        var open_time := minf(beat_start + beat_period * 0.10, active_end)
        var close_time := minf(beat_start + beat_period * 0.52, active_end)
        if close_time <= open_time:
            continue
        animation.track_insert_key(visibility_track, open_time, true)
        animation.track_insert_key(visibility_track, close_time, false)
        animation.track_insert_key(scale_track, open_time, open_scale)
        animation.track_insert_key(scale_track, close_time, closed_scale)
        keyframe_count += 4
    animation.track_insert_key(visibility_track, end_time, false)
    animation.track_insert_key(scale_track, end_time, closed_scale)
    keyframe_count += 2
    var track_count := 2
    for mouth_line in mouth_lines:
        var line_track := animation.add_track(Animation.TYPE_VALUE)
        animation.track_set_path(
            line_track,
            NodePath(str(scene_root.get_path_to(mouth_line)) + ":visible")
        )
        animation.track_insert_key(line_track, start_time, true)
        for beat_index in range(beat_count):
            var beat_start := active_start + float(beat_index) * beat_period
            var open_time := minf(beat_start + beat_period * 0.10, active_end)
            var close_time := minf(beat_start + beat_period * 0.52, active_end)
            if close_time <= open_time:
                continue
            animation.track_insert_key(line_track, open_time, false)
            animation.track_insert_key(line_track, close_time, true)
            keyframe_count += 2
        animation.track_insert_key(line_track, end_time, true)
        keyframe_count += 2
        track_count += 1
    return {
        "track_count": track_count,
        "keyframe_count": keyframe_count,
        "beat_count": beat_count,
        "audio_driven": false
    }


func _episode_bone_role(bone_name: String) -> String:
    var token := bone_name.to_lower()
    for prefix in ["mixamorig:", "mixamorig", "armature:", "armature|", "def-"]:
        token = token.replace(prefix, "")
    token = token.replace("_", "").replace("-", "").replace(" ", "").replace(".", "")
    if token in ["leftarm", "leftupperarm", "upperarml", "arml", "armjointl1"] or token.ends_with("leftarm"):
        return "left_upper_arm"
    if token in ["rightarm", "rightupperarm", "upperarmr", "armr", "armjointr1"] or token.ends_with("rightarm"):
        return "right_upper_arm"
    if token in ["leftforearm", "leftlowerarm", "forearml", "lowerarml", "armjointl2"] or token.ends_with("leftforearm"):
        return "left_lower_arm"
    if token in ["rightforearm", "rightlowerarm", "forearmr", "lowerarmr", "armjointr2"] or token.ends_with("rightforearm"):
        return "right_lower_arm"
    if token in ["leftupleg", "leftupperleg", "leftthigh", "uplegl", "thighl", "upperlegl", "legjointl1"]:
        return "left_upper_leg"
    if token in ["rightupleg", "rightupperleg", "rightthigh", "uplegr", "thighr", "upperlegr", "legjointr1"]:
        return "right_upper_leg"
    if token in ["leftleg", "leftlowerleg", "leftcalf", "calfl", "lowerlegl", "shinl", "legjointl2"]:
        return "left_lower_leg"
    if token in ["rightleg", "rightlowerleg", "rightcalf", "calfr", "lowerlegr", "shinr", "legjointr2"]:
        return "right_lower_leg"
    if token in ["spine", "spine1", "spine2", "spine01", "spine001", "chest", "upperchest", "torsojoint2"]:
        return "spine"
    if token in ["head", "head2", "neckjoint2"]:
        return "head"
    return ""


func _episode_action_bone_rotation(action_id: String, role: String, phase: float) -> Vector3:
    var side := 1.0 if role.begins_with("left_") else -1.0
    var cycle := sin(phase * TAU)
    match action_id:
        "walk", "walk_back", "run", "strafe_left", "strafe_right":
            var intensity := 0.72 if action_id == "run" else 0.42
            if role.ends_with("upper_leg"):
                return Vector3(cycle * intensity * side, 0.0, 0.0)
            if role.ends_with("lower_leg"):
                return Vector3(maxf(0.0, -cycle * side) * intensity * 0.8, 0.0, 0.0)
            if role.ends_with("upper_arm"):
                return Vector3(-cycle * intensity * 0.72 * side, 0.0, 0.0)
            if role.ends_with("lower_arm"):
                return Vector3(0.0, 0.0, 0.08 * side)
        "wave":
            if role == "right_upper_arm":
                return Vector3(0.0, 0.0, -1.05)
            if role == "right_lower_arm":
                return Vector3(-0.85, 0.0, 0.0)
        "clap":
            if role.ends_with("upper_arm"):
                return Vector3(0.0, 0.0, 0.48 * side)
            if role.ends_with("lower_arm"):
                return Vector3(-0.95, 0.0, 0.0)
        "jump_start", "jump_air", "jump_land", "jump_running":
            if role.ends_with("upper_arm"):
                return Vector3(0.0, 0.0, 0.82 * side)
            if role.ends_with("upper_leg"):
                return Vector3(-0.28, 0.0, 0.0)
            if role == "spine":
                return Vector3(-0.12, 0.0, 0.0)
        "cheer", "thumbs_up":
            if role.ends_with("upper_arm"):
                return Vector3(0.0, 0.0, 1.0 * side)
            if role.ends_with("lower_arm"):
                return Vector3(-0.45, 0.0, 0.0)
        "punch", "hit":
            if role == "right_upper_arm":
                return Vector3(-0.15, 0.0, -0.85)
            if role == "right_lower_arm":
                return Vector3(-0.25, 0.0, 0.0)
        "dance_groove", "dance_bounce", "laugh":
            if role.ends_with("upper_leg"):
                return Vector3(cycle * 0.28 * side, 0.0, 0.0)
            if role.ends_with("upper_arm"):
                return Vector3(0.0, 0.0, cycle * 0.45 * side)
            if role == "spine":
                return Vector3(0.0, cycle * 0.12, 0.0)
        "crouch", "pick_up", "put_down", "sweep":
            if role.ends_with("upper_leg"):
                return Vector3(0.45, 0.0, 0.0)
            if role.ends_with("lower_leg"):
                return Vector3(-0.62, 0.0, 0.0)
            if role == "spine":
                return Vector3(0.22, 0.0, 0.0)
        "bow":
            if role == "spine":
                return Vector3(0.42, 0.0, 0.0)
    return Vector3.ZERO


func _add_episode_skeletal_action_tracks(
    animation: Animation,
    scene_root: Node3D,
    character_anchor: Node3D,
    action_id: String,
    start_time: float,
    end_time: float
) -> Dictionary:
    var skeleton_nodes := character_anchor.find_children("*", "Skeleton3D", true, false)
    var track_count := 0
    var keyframe_count := 0
    var is_cyclic := action_id in ["walk", "walk_back", "run", "strafe_left", "strafe_right", "dance_groove", "dance_bounce"]
    var sample_count := 5 if is_cyclic else 3
    for skeleton_value in skeleton_nodes:
        var skeleton := skeleton_value as Skeleton3D
        if skeleton == null:
            continue
        var skeleton_path := str(scene_root.get_path_to(skeleton))
        for bone_index in range(skeleton.get_bone_count()):
            var role := _episode_bone_role(skeleton.get_bone_name(bone_index))
            if role.is_empty():
                continue
            var rotations: Array[Quaternion] = []
            var base_rotation := skeleton.get_bone_pose_rotation(bone_index)
            var has_motion := false
            for sample_index in range(sample_count):
                var phase := float(sample_index) / float(sample_count - 1)
                var delta := _episode_action_bone_rotation(action_id, role, phase)
                if delta.length_squared() > 0.0001:
                    has_motion = true
                rotations.append(base_rotation * Basis.from_euler(delta).get_rotation_quaternion())
            if not has_motion:
                continue
            var track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(
                track,
                NodePath(skeleton_path + ":bones/" + str(bone_index) + "/rotation")
            )
            for sample_index in range(sample_count):
                var phase := float(sample_index) / float(sample_count - 1)
                var key_time := lerpf(start_time, end_time, phase)
                animation.track_insert_key(track, key_time, rotations[sample_index])
                keyframe_count += 1
            track_count += 1
    return {"track_count": track_count, "keyframe_count": keyframe_count}


func _build_episode_timeline(
    scene_root: Node3D,
    scene_data: Dictionary,
    character_anchors: Dictionary
) -> Dictionary:
    var duration := float(scene_data.get("duration_seconds", 30))
    var animation := Animation.new()
    animation.length = duration
    var track_count := 0
    var action_count := 0
    var expression_cue_count := 0
    var speech_cue_count := 0
    var speech_mouth_keyframe_count := 0
    var audio_driven_speech_cue_count := 0
    var audio_envelope_keyframe_count := 0
    var skeletal_animation_track_count := 0
    var skeletal_animation_keyframe_count := 0
    var camera := Camera3D.new()
    camera.name = "EpisodeCamera"
    camera.position = Vector3(0.0, 7.0, 16.0)
    camera.look_at(Vector3(0.0, 1.0, 0.0), Vector3.UP)
    camera.current = true
    scene_root.add_child(camera)
    var camera_position_track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(camera_position_track, NodePath("EpisodeCamera:position"))
    animation.track_insert_key(camera_position_track, 0.0, camera.position)
    var camera_rotation_track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(camera_rotation_track, NodePath("EpisodeCamera:rotation"))
    animation.track_insert_key(camera_rotation_track, 0.0, camera.rotation)
    var camera_fov_track := animation.add_track(Animation.TYPE_VALUE)
    animation.track_set_path(camera_fov_track, NodePath("EpisodeCamera:fov"))
    animation.track_insert_key(camera_fov_track, 0.0, camera.fov)
    track_count += 3
    var actions_value: Variant = scene_data.get("actions", [])
    if typeof(actions_value) == TYPE_ARRAY:
        for action_value in actions_value:
            if typeof(action_value) != TYPE_DICTIONARY:
                continue
            var cue: Dictionary = action_value
            var character_id := str(cue.get("character_id", ""))
            if not character_anchors.has(character_id):
                continue
            var anchor: Node3D = character_anchors[character_id]
            var pose := _episode_action_pose(str(cue.get("action_id", "idle")))
            var start_time := clampf(float(cue.get("start_seconds", 0.0)), 0.0, duration)
            var end_time := clampf(
                start_time + float(cue.get("duration_seconds", 1.0)),
                start_time,
                duration
            )
            var middle_time := lerpf(start_time, end_time, 0.5)
            var base_position := anchor.position
            var base_rotation := anchor.rotation
            var position_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(
                position_track,
                NodePath("Cast/Character_" + character_id + ":position")
            )
            animation.track_insert_key(position_track, start_time, base_position)
            animation.track_insert_key(
                position_track,
                middle_time,
                base_position + pose["offset"]
            )
            animation.track_insert_key(position_track, end_time, base_position)
            var rotation_track := animation.add_track(Animation.TYPE_VALUE)
            animation.track_set_path(
                rotation_track,
                NodePath("Cast/Character_" + character_id + ":rotation")
            )
            animation.track_insert_key(rotation_track, start_time, base_rotation)
            animation.track_insert_key(
                rotation_track,
                middle_time,
                base_rotation + pose["rotation"]
            )
            animation.track_insert_key(rotation_track, end_time, base_rotation)
            track_count += 2
            var skeletal_result := _add_episode_skeletal_action_tracks(
                animation, scene_root, anchor, str(cue.get("action_id", "idle")),
                start_time, end_time
            )
            var skeletal_tracks := int(skeletal_result.get("track_count", 0))
            skeletal_animation_track_count += skeletal_tracks
            skeletal_animation_keyframe_count += int(skeletal_result.get("keyframe_count", 0))
            track_count += skeletal_tracks
            var expression_id := str(cue.get("expression", "neutral"))
            if expression_id != "neutral":
                var expression_tracks := _add_episode_expression_tracks(
                    animation,
                    scene_root,
                    anchor,
                    expression_id,
                    start_time,
                    middle_time,
                    end_time
                )
                track_count += expression_tracks
                if expression_tracks > 0:
                    expression_cue_count += 1
            action_count += 1
    var dialogue_value: Variant = scene_data.get("dialogue", [])
    if typeof(dialogue_value) == TYPE_ARRAY:
        for dialogue_entry in dialogue_value:
            if typeof(dialogue_entry) != TYPE_DICTIONARY:
                continue
            var line: Dictionary = dialogue_entry
            var speaker_id := str(line.get("character_id", ""))
            var emotion_id := str(line.get("emotion", "neutral"))
            if emotion_id == "neutral" or not character_anchors.has(speaker_id):
                continue
            var dialogue_start := clampf(float(line.get("start_seconds", 0.0)), 0.0, duration)
            var dialogue_end := clampf(
                dialogue_start + float(line.get("duration_seconds", 1.0)),
                dialogue_start,
                duration
            )
            var dialogue_middle := lerpf(dialogue_start, dialogue_end, 0.5)
            var dialogue_tracks := _add_episode_expression_tracks(
                animation,
                scene_root,
                character_anchors[speaker_id],
                emotion_id,
                dialogue_start,
                dialogue_middle,
                dialogue_end,
                false
            )
            track_count += dialogue_tracks
            if dialogue_tracks > 0:
                expression_cue_count += 1
    if typeof(dialogue_value) == TYPE_ARRAY:
        for dialogue_entry in dialogue_value:
            if typeof(dialogue_entry) != TYPE_DICTIONARY:
                continue
            var line: Dictionary = dialogue_entry
            var speaker_id := str(line.get("character_id", ""))
            if not character_anchors.has(speaker_id):
                continue
            var dialogue_start := clampf(float(line.get("start_seconds", 0.0)), 0.0, duration)
            var dialogue_end := clampf(
                dialogue_start + float(line.get("duration_seconds", 1.0)),
                dialogue_start,
                duration
            )
            var speech_result := _add_dialogue_speech_tracks(
                animation,
                scene_root,
                character_anchors[speaker_id],
                line,
                dialogue_start,
                dialogue_end
            )
            track_count += int(speech_result.get("track_count", 0))
            var line_keyframes := int(speech_result.get("keyframe_count", 0))
            speech_mouth_keyframe_count += line_keyframes
            if line_keyframes > 0:
                speech_cue_count += 1
            if bool(speech_result.get("audio_driven", false)):
                audio_driven_speech_cue_count += 1
                audio_envelope_keyframe_count += line_keyframes
    var camera_value: Variant = scene_data.get("camera", [])
    var camera_cue_count := 0
    if typeof(camera_value) == TYPE_ARRAY:
        for camera_entry in camera_value:
            if typeof(camera_entry) != TYPE_DICTIONARY:
                continue
            var cue: Dictionary = camera_entry
            var shot := str(cue.get("shot", "wide"))
            var movement := str(cue.get("movement", "locked"))
            var target := Vector3(0.0, 1.0, 0.0)
            var target_id := str(cue.get("target", "all"))
            if character_anchors.has(target_id):
                var target_anchor: Node3D = character_anchors[target_id]
                target = target_anchor.position + Vector3(0.0, 1.2, 0.0)
            var distance := 16.0
            var height := 7.0
            var field_of_view := 70.0
            if shot == "medium":
                distance = 10.0
                height = 5.0
                field_of_view = 55.0
            elif shot == "close":
                distance = 5.0
                height = 2.5
                field_of_view = 42.0
            var start_position := target + Vector3(0.0, height, distance)
            var end_position := start_position
            if movement == "orbit":
                end_position += Vector3(3.0, 0.0, -1.5)
            elif movement == "dolly":
                end_position += Vector3(0.0, 0.0, -3.0)
            var start_rotation := Basis.looking_at(
                target - start_position, Vector3.UP
            ).get_euler()
            var end_rotation := Basis.looking_at(
                target - end_position, Vector3.UP
            ).get_euler()
            var start_time := clampf(float(cue.get("start_seconds", 0.0)), 0.0, duration)
            var end_time := clampf(
                start_time + float(cue.get("duration_seconds", 1.0)),
                start_time,
                duration
            )
            animation.track_insert_key(camera_position_track, start_time, start_position)
            animation.track_insert_key(camera_position_track, end_time, end_position)
            animation.track_insert_key(camera_rotation_track, start_time, start_rotation)
            animation.track_insert_key(camera_rotation_track, end_time, end_rotation)
            animation.track_insert_key(camera_fov_track, start_time, field_of_view)
            animation.track_insert_key(camera_fov_track, end_time, field_of_view)
            camera_cue_count += 1
    var timeline_player := AnimationPlayer.new()
    timeline_player.name = "EpisodeTimeline"
    timeline_player.root_node = NodePath("..")
    scene_root.add_child(timeline_player)
    var library := AnimationLibrary.new()
    var library_error := library.add_animation("EpisodeTimeline", animation)
    if library_error != OK:
        return {"ok": false, "error_code": "episode_timeline_library_failed", "godot_error": library_error}
    var player_error := timeline_player.add_animation_library("", library)
    if player_error != OK:
        return {"ok": false, "error_code": "episode_timeline_player_failed", "godot_error": player_error}
    timeline_player.autoplay = "EpisodeTimeline"
    timeline_player.play("EpisodeTimeline")
    return {
        "ok": true,
        "animation_track_count": track_count,
        "skeletal_animation_track_count": skeletal_animation_track_count,
        "skeletal_animation_keyframe_count": skeletal_animation_keyframe_count,
        "action_cue_count": action_count,
        "expression_cue_count": expression_cue_count,
        "speech_cue_count": speech_cue_count,
        "speech_mouth_keyframe_count": speech_mouth_keyframe_count,
        "audio_driven_speech_cue_count": audio_driven_speech_cue_count,
        "audio_envelope_keyframe_count": audio_envelope_keyframe_count,
        "camera_cue_count": camera_cue_count
    }


func _export_episode_scenes(payload: Dictionary) -> Dictionary:
    var project_root := _normalise_path(str(payload.get("project_root", "")))
    var world_scene_path := _normalise_path(str(payload.get("world_scene_path", "")))
    var output_directory := _normalise_path(str(payload.get("output_directory", "")))
    var episode_value: Variant = payload.get("episode", {})
    var assets_value: Variant = payload.get("character_assets", [])
    if project_root.is_empty() or not DirAccess.dir_exists_absolute(project_root):
        return {"error_code": "invalid_project_root", "error": "A valid episode project root is required."}
    var root_prefix := project_root.trim_suffix("/") + "/"
    if not world_scene_path.to_lower().begins_with(root_prefix.to_lower()) or not world_scene_path.to_lower().ends_with(".tscn") or not FileAccess.file_exists(world_scene_path):
        return {"error_code": "invalid_world_scene", "error": "A project-local exported world scene is required."}
    if not output_directory.to_lower().begins_with(root_prefix.to_lower()):
        return {"error_code": "invalid_output_directory", "error": "Episode output must stay inside the project."}
    if typeof(episode_value) != TYPE_DICTIONARY or typeof(assets_value) != TYPE_ARRAY:
        return {"error_code": "invalid_episode", "error": "Episode plan and character assets are required."}
    var episode: Dictionary = episode_value
    var scenes_value: Variant = episode.get("scenes", [])
    if typeof(scenes_value) != TYPE_ARRAY or scenes_value.size() < 5 or scenes_value.size() > 7:
        return {"error_code": "invalid_scenes", "error": "Episode must contain five to seven scenes."}
    var assets_by_id: Dictionary = {}
    for asset_value in assets_value:
        if typeof(asset_value) != TYPE_DICTIONARY:
            return {"error_code": "invalid_character_asset", "error": "Character asset entries must be objects."}
        var asset: Dictionary = asset_value
        var character_id := str(asset.get("id", ""))
        var asset_path := _normalise_path(str(asset.get("asset_path", "")))
        if character_id.is_empty() or assets_by_id.has(character_id):
            return {"error_code": "invalid_character_asset", "error": "Character asset IDs must be unique."}
        if not asset_path.to_lower().begins_with(root_prefix.to_lower()) or not asset_path.to_lower().ends_with(".glb") or not FileAccess.file_exists(asset_path):
            return {"error_code": "invalid_character_asset_path", "error": "Character GLB must exist inside the project."}
        assets_by_id[character_id] = asset
    var world_packed := ResourceLoader.load(world_scene_path) as PackedScene
    if world_packed == null:
        return {"error_code": "world_scene_load_failed", "error": "Godot could not load the exported world scene."}
    var episode_characters: Dictionary = {}
    var characters_value: Variant = episode.get("characters", [])
    if typeof(characters_value) != TYPE_ARRAY:
        return {"error_code": "invalid_characters", "error": "Episode characters must be an array."}
    for character_value in characters_value:
        if typeof(character_value) == TYPE_DICTIONARY:
            var character: Dictionary = character_value
            episode_characters[str(character.get("id", ""))] = character
    var generated_scenes: Array[Dictionary] = []
    for scene_value in scenes_value:
        if typeof(scene_value) != TYPE_DICTIONARY:
            return {"error_code": "invalid_scene", "error": "Episode scene entries must be objects."}
        var scene_data: Dictionary = scene_value
        var scene_id := str(scene_data.get("id", ""))
        if scene_id.is_empty():
            return {"error_code": "invalid_scene_id", "error": "Episode scene ID is invalid."}
        var scene_root := Node3D.new()
        scene_root.name = "Episode_" + scene_id
        scene_root.set_meta("episode_title", str(episode.get("title", "Episode")))
        scene_root.set_meta("scene_title", str(scene_data.get("title", scene_id)))
        scene_root.set_meta("scene_id", scene_id)
        scene_root.set_meta("duration_seconds", int(scene_data.get("duration_seconds", 0)))
        scene_root.set_meta("location_id", str(scene_data.get("location_id", "")))
        scene_root.set_meta("environment_description", str(scene_data.get("environment_description", "")))
        scene_root.set_meta("lighting", str(scene_data.get("lighting", "")))
        scene_root.set_meta("dialogue_json", JSON.stringify(scene_data.get("dialogue", [])))
        scene_root.set_meta("actions_json", JSON.stringify(scene_data.get("actions", [])))
        scene_root.set_meta("camera_json", JSON.stringify(scene_data.get("camera", [])))
        scene_root.set_meta("audio_json", JSON.stringify(scene_data.get("audio", [])))
        scene_root.set_meta("props_json", JSON.stringify(scene_data.get("props", [])))
        var world_instance := world_packed.instantiate()
        world_instance.name = "EstablishedWorld"
        scene_root.add_child(world_instance)
        var cast_root := Node3D.new()
        cast_root.name = "Cast"
        scene_root.add_child(cast_root)
        var scene_character_ids: Variant = scene_data.get("character_ids", [])
        if typeof(scene_character_ids) != TYPE_ARRAY:
            scene_root.free()
            return {"error_code": "invalid_scene_cast", "error": "Scene character IDs must be an array."}
        var placed_count := 0
        var character_anchors: Dictionary = {}
        for character_id_value in scene_character_ids:
            var character_id := str(character_id_value)
            if not episode_characters.has(character_id) or not assets_by_id.has(character_id):
                scene_root.free()
                return {"error_code": "missing_character_asset", "error": "Every scene character must have a linked GLB asset."}
            var character_data: Dictionary = episode_characters[character_id]
            var asset_data: Dictionary = assets_by_id[character_id]
            var gltf_document := GLTFDocument.new()
            var gltf_state := GLTFState.new()
            var import_error := gltf_document.append_from_file(str(asset_data.get("asset_path", "")), gltf_state)
            if import_error != OK:
                scene_root.free()
                return {"error_code": "character_import_failed", "error": "Godot could not import character " + character_id, "godot_error": import_error}
            var character_scene := gltf_document.generate_scene(gltf_state)
            if character_scene == null:
                scene_root.free()
                return {"error_code": "character_scene_failed", "error": "Godot could not generate character " + character_id}
            var character_anchor := Node3D.new()
            character_anchor.name = "Character_" + character_id
            character_anchor.set_meta("character_id", character_id)
            character_anchor.set_meta("character_name", str(character_data.get("name", character_id)))
            character_anchor.position = Vector3((float(placed_count) - float(scene_character_ids.size() - 1) * 0.5) * 2.8, 0.0, 4.0)
            cast_root.add_child(character_anchor)
            character_anchors[character_id] = character_anchor
            character_scene.name = "Model"
            character_anchor.add_child(character_scene)
            placed_count += 1
        var timeline_result := _build_episode_timeline(
            scene_root, scene_data, character_anchors
        )
        if not bool(timeline_result.get("ok", false)):
            scene_root.free()
            return timeline_result
        var output_path := output_directory.path_join(scene_id + ".tscn")
        var output_glb_path := output_directory.path_join(scene_id + ".glb")
        if FileAccess.file_exists(output_path) or FileAccess.file_exists(output_glb_path):
            scene_root.free()
            return {"error_code": "episode_output_exists", "error": "Refusing to overwrite an existing episode scene."}
        _set_scene_ownership(scene_root, scene_root)
        var packed_scene := PackedScene.new()
        var pack_error := packed_scene.pack(scene_root)
        if pack_error != OK:
            scene_root.free()
            return {"error_code": "episode_scene_pack_failed", "error": "Godot could not pack episode scene.", "godot_error": pack_error}
        var save_error := ResourceSaver.save(packed_scene, output_path)
        if save_error != OK:
            scene_root.free()
            return {"error_code": "episode_scene_save_failed", "error": "Godot could not save episode scene.", "godot_error": save_error}
        var gltf_export := GLTFDocument.new()
        var gltf_export_state := GLTFState.new()
        var append_error := gltf_export.append_from_scene(scene_root, gltf_export_state)
        if append_error != OK:
            scene_root.free()
            return {"error_code": "episode_preview_failed", "error": "Godot could not prepare episode preview.", "godot_error": append_error}
        var glb_error := gltf_export.write_to_filesystem(gltf_export_state, output_glb_path)
        scene_root.free()
        if glb_error != OK:
            return {"error_code": "episode_preview_save_failed", "error": "Godot could not save episode preview.", "godot_error": glb_error}
        var reopened := ResourceLoader.load(output_path) as PackedScene
        if reopened == null:
            return {"error_code": "episode_scene_reopen_failed", "error": "Generated episode scene could not be reopened."}
        var reopened_root := reopened.instantiate()
        var reopened_cast := reopened_root.get_node_or_null("Cast")
        var reopened_character_count := reopened_cast.get_child_count() if reopened_cast != null else 0
        reopened_root.free()
        generated_scenes.append({
            "scene_id": scene_id,
            "title": str(scene_data.get("title", scene_id)),
            "duration_seconds": int(scene_data.get("duration_seconds", 0)),
            "character_count": placed_count,
            "dialogue_line_count": scene_data.get("dialogue", []).size(),
            "scene_path": output_path,
            "preview_path": output_glb_path,
            "scene_reopened": true,
            "reopened_character_count": reopened_character_count,
            "animation_track_count": timeline_result["animation_track_count"],
            "skeletal_animation_track_count": timeline_result["skeletal_animation_track_count"],
            "skeletal_animation_keyframe_count": timeline_result["skeletal_animation_keyframe_count"],
            "action_cue_count": timeline_result["action_cue_count"],
            "expression_cue_count": timeline_result["expression_cue_count"],
            "speech_cue_count": timeline_result["speech_cue_count"],
            "speech_mouth_keyframe_count": timeline_result["speech_mouth_keyframe_count"],
            "audio_driven_speech_cue_count": timeline_result["audio_driven_speech_cue_count"],
            "audio_envelope_keyframe_count": timeline_result["audio_envelope_keyframe_count"],
            "camera_cue_count": timeline_result["camera_cue_count"]
        })
    return {
        "ok": true,
        "episode_title": str(episode.get("title", "Episode")),
        "scene_count": generated_scenes.size(),
        "scenes": generated_scenes
    }

