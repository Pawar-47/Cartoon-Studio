extends Node3D


func _ready() -> void:
    var user_arguments := OS.get_cmdline_user_args()
    if user_arguments.is_empty():
        push_error("Episode render runner requires an absolute scene path.")
        get_tree().quit(2)
        return

    var scene_path := str(user_arguments[0])
    var packed_scene := load(scene_path) as PackedScene
    if packed_scene == null:
        push_error("Could not load episode scene: " + scene_path)
        get_tree().quit(3)
        return

    var episode_scene := packed_scene.instantiate()
    add_child(episode_scene)

    var episode_camera := episode_scene.find_child(
        "EpisodeCamera",
        true,
        false
    ) as Camera3D
    if episode_camera != null:
        episode_camera.current = true

    var timeline := episode_scene.find_child(
        "EpisodeTimeline",
        true,
        false
    ) as AnimationPlayer
    if timeline != null:
        timeline.play("EpisodeTimeline")
