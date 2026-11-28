import os
import subprocess
import wave
from pathlib import Path

import pytest

from app.render import (
    VIDEO_ENCODER_PREFERENCE,
    RenderDependencyUnavailable,
    RenderExecutionError,
    RenderPathError,
    _enforce_scene_cache_limit,
    _find_ffmpeg,
    _write_render_project,
    render_episode_video,
)


def _write_silent_wav(path, duration_seconds):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(22050)
        output.writeframes(b"\x00\x00" * (duration_seconds * 22050))


def test_render_episode_video_uses_godot_movie_maker_and_muxes_audio_subtitles(
    tmp_path, monkeypatch
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scene_paths = []
    for index in range(1, 6):
        scene_path = project_root / f"scene-{index}.tscn"
        scene_path.write_text("[gd_scene format=3]\n", encoding="utf-8")
        scene_paths.append(scene_path)
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 7)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nالسلام علیکم!\n",
        encoding="utf-8",
    )
    godot = tmp_path / "Godot.exe"
    ffmpeg = tmp_path / "ffmpeg.exe"
    godot.write_bytes(b"godot-test")
    ffmpeg.write_bytes(b"ffmpeg-test")
    calls = []
    concat_contents = ""

    def fake_run(command, **kwargs):
        nonlocal concat_contents
        calls.append(command)
        if command[0] == str(ffmpeg) and "-encoders" in command:
            # The bundled LGPL build: AAC and mov_text, VP9 but no GPL libx264.
            encoders = (
                " V..... libvpx-vp9   libvpx VP9\n"
                " A..... aac         AAC\n"
                " S..... mov_text    mov_text\n"
            )
            return subprocess.CompletedProcess(
                command, 0, stdout=encoders, stderr=""
            )
        if command[0] == str(ffmpeg) and "-progress" in command and "pipe:1" in command:
            return subprocess.CompletedProcess(
                command, 0, stdout="out_time_us=7000000\nprogress=end\n", stderr=""
            )
        if command[0] == str(godot):
            movie_path = Path(command[command.index("--write-movie") + 1])
            movie_path.write_bytes(b"fake-avi")
            frames = command[command.index("--quit-after") + 1]
            fps = command[command.index("--fixed-fps") + 1]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=f"Movie Maker finished recording: {frames} frames at {fps} FPS",
                stderr="",
            )
        if command[0] == str(ffmpeg) and "-c:v" in command:
            concat_path = Path(command[command.index("-i") + 1])
            concat_contents = concat_path.read_text(encoding="utf-8")
            Path(command[-1]).write_bytes(b"fake-mp4")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[0] == str(ffmpeg):
            Path(command[-1]).write_bytes(b"fake-mp4")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    result = render_episode_video(
        scene_paths,
        [1, 2, 1, 2, 1],
        audio_path,
        subtitles_path,
        project_root / "renders" / "episode.mp4",
        project_root,
        godot,
        ffmpeg_executable=ffmpeg,
        fps=24,
        width=640,
        height=360,
    )
    assert result["duration_seconds"] == 7
    assert result["fps"] == 24
    assert result["size_bytes"] == len(b"fake-mp4")
    godot_calls = [call for call in calls if call[0] == str(godot)]
    assert len(godot_calls) == 5
    assert concat_contents == "".join(
        f"file 'scene-{index:02d}.avi'\n" for index in range(1, 6)
    )
    assert all("--write-movie" in call for call in godot_calls)
    assert [call[call.index("--quit-after") + 1] for call in godot_calls] == [
        "24",
        "48",
        "24",
        "48",
        "24",
    ]
    mux_calls = [call for call in calls if "-c:v" in call]
    assert len(mux_calls) == 1
    assert mux_calls[0][0] == str(ffmpeg)
    # VP9 is the redistribution-safe encoder of the bundled LGPL build; the
    # GPL libx264 encoder must never be selected.
    assert mux_calls[0][mux_calls[0].index("-c:v") + 1] == "libvpx-vp9"
    assert "libx264" not in mux_calls[0]
    assert result["video_encoder"] == "libvpx-vp9"
    assert "-c:a" in mux_calls[0] and "aac" in mux_calls[0]
    assert "-c:s" in mux_calls[0] and "mov_text" in mux_calls[0]
    assert calls[-1][0] == str(ffmpeg)
    assert "-progress" in calls[-1] and "pipe:1" in calls[-1]
    assert Path(result["video_path"]).read_bytes() == b"fake-mp4"


def test_render_requires_ffmpeg_before_starting_godot(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scene_paths = []
    for index in range(1, 6):
        scene_path = project_root / f"scene-{index}.tscn"
        scene_path.write_text("[gd_scene format=3]\n", encoding="utf-8")
        scene_paths.append(scene_path)
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 5)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text("", encoding="utf-8")
    godot = tmp_path / "Godot.exe"
    godot.write_bytes(b"godot-test")
    monkeypatch.setattr("app.render.shutil.which", lambda _: None)
    monkeypatch.delenv("CARTOON_STUDIO_FFMPEG", raising=False)
    with pytest.raises(RenderDependencyUnavailable, match="FFmpeg was not found"):
        render_episode_video(
            scene_paths,
            [1, 1, 1, 1, 1],
            audio_path,
            subtitles_path,
            project_root / "renders" / "episode.mp4",
            project_root,
            godot,
        )


@pytest.mark.skipif(
    not os.environ.get("CARTOON_STUDIO_GODOT_PATH"),
    reason="The pinned Godot runtime is only provisioned in engine-enabled CI.",
)
def test_godot_movie_maker_renders_an_episode_scene(tmp_path):
    godot = Path(os.environ["CARTOON_STUDIO_GODOT_PATH"])
    render_project = tmp_path / "render-project"
    render_project.mkdir()
    _write_render_project(render_project)
    scene_path = tmp_path / "episode-scene.tscn"
    scene_path.write_text(
        """[gd_scene load_steps=2 format=3]

[sub_resource type="SphereMesh" id="SphereMesh_test"]

[node name="EpisodeScene" type="Node3D"]

[node name="EpisodeCamera" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 5)
current = true

[node name="Sphere" type="MeshInstance3D" parent="."]
mesh = SubResource("SphereMesh_test")
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "movie-smoke.avi"
    command = [
        str(godot),
        "--path",
        str(render_project),
        "--write-movie",
        str(output_path),
        "--fixed-fps",
        "24",
        "--resolution",
        "640x360",
        "--rendering-method",
        "gl_compatibility",
        "--disable-vsync",
        "--quit-after",
        "24",
        "--",
        str(scene_path),
    ]
    result = subprocess.run(
        command,
        cwd=render_project,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = result.stdout + "\n" + result.stderr
    assert result.returncode == 0, output[-6000:]
    assert "24 frames at 24 FPS" in output
    assert output_path.is_file()
    assert output_path.stat().st_size > 1024


def test_render_rejects_ffmpeg_without_required_mp4_encoders_before_godot(
    tmp_path, monkeypatch
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scene_path = project_root / "scene.tscn"
    scene_path.write_text("[gd_scene format=3]\n", encoding="utf-8")
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 1)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text("", encoding="utf-8")
    godot = tmp_path / "Godot.exe"
    ffmpeg = tmp_path / "ffmpeg.exe"
    godot.write_bytes(b"godot-test")
    ffmpeg.write_bytes(b"ffmpeg-test")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout=" A..... aac\n S..... mov_text\n", stderr=""
        )

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    with pytest.raises(RenderDependencyUnavailable, match="no redistribution-safe video encoder"):
        render_episode_video(
            [scene_path],
            [1],
            audio_path,
            subtitles_path,
            project_root / "renders" / "episode.mp4",
            project_root,
            godot,
            ffmpeg_executable=ffmpeg,
        )
    assert len(calls) == 1
    assert "-encoders" in calls[0]


@pytest.mark.parametrize(
    ("verification_returncode", "verification_stdout", "verification_stderr", "error_match"),
    [
        (1, "", "Could not find codec parameters", "decode check"),
        (0, "out_time_us=4000000\nprogress=end\n", "", "duration does not match"),
    ],
)
def test_render_removes_mp4_when_final_verification_fails(
    tmp_path,
    monkeypatch,
    verification_returncode,
    verification_stdout,
    verification_stderr,
    error_match,
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scene_path = project_root / "scene.tscn"
    scene_path.write_text("[gd_scene format=3]\n", encoding="utf-8")
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 1)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nالسلام علیکم!\n",
        encoding="utf-8",
    )
    godot = tmp_path / "Godot.exe"
    ffmpeg = tmp_path / "ffmpeg.exe"
    godot.write_bytes(b"godot-test")
    ffmpeg.write_bytes(b"ffmpeg-test")
    output = project_root / "renders" / "episode.mp4"
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == str(ffmpeg) and "-encoders" in command:
            # A build that offers VP9 beside the GPL libx264: the
            # redistribution-safe encoder must still be the one chosen.
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    " V..... libvpx-vp9   libvpx VP9\n"
                    " V..... libx264     libx264 H.264\n"
                    " A..... aac         AAC\n"
                    " S..... mov_text    mov_text\n"
                ),
                stderr="",
            )
        if command[0] == str(godot):
            Path(command[command.index("--write-movie") + 1]).write_bytes(b"fake-avi")
            frames = command[command.index("--quit-after") + 1]
            fps = command[command.index("--fixed-fps") + 1]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=f"{frames} frames at {fps} FPS",
                stderr="",
            )
        if command[0] == str(ffmpeg) and "-progress" in command and "pipe:1" in command:
            return subprocess.CompletedProcess(
                command,
                verification_returncode,
                stdout=verification_stdout,
                stderr=verification_stderr,
            )
        output_path = Path(command[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-mp4")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    with pytest.raises(RenderExecutionError, match=error_match):
        render_episode_video(
            [scene_path],
            [1],
            audio_path,
            subtitles_path,
            output,
            project_root,
            godot,
            ffmpeg_executable=ffmpeg,
        )
    assert not output.exists()
    mux_calls = [call for call in calls if "-c:v" in call]
    assert len(mux_calls) == 1
    assert mux_calls[0][mux_calls[0].index("-c:v") + 1] == "libvpx-vp9"
    assert "libx264" not in mux_calls[0]


def _fake_render_commands(godot, ffmpeg, godot_renders):
    """Return a subprocess.run fake that renders movies without Godot or FFmpeg."""

    def fake_run(command, **kwargs):
        if command[0] == str(ffmpeg) and "-encoders" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    " V..... libvpx-vp9   libvpx VP9\n"
                    " A..... aac         AAC\n"
                    " S..... mov_text    mov_text\n"
                ),
                stderr="",
            )
        if command[0] == str(godot):
            movie_path = Path(command[command.index("--write-movie") + 1])
            movie_path.write_bytes(b"scene-movie")
            godot_renders.append(Path(command[command.index("--") + 1]).name)
            frames = command[command.index("--quit-after") + 1]
            fps = command[command.index("--fixed-fps") + 1]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=f"{frames} frames at {fps} FPS",
                stderr="",
            )
        if command[0] == str(ffmpeg) and "-progress" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="out_time_us=2000000\nprogress=end\n",
                stderr="",
            )
        Path(command[-1]).write_bytes(b"fake-mp4")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    return fake_run


def test_scene_cache_reuses_finished_scenes_and_invalidates_an_edited_one(
    tmp_path, monkeypatch
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scenes = []
    for index in (1, 2):
        scene_path = project_root / f"scene-{index}.tscn"
        scene_path.write_text(
            f"[gd_scene format=3]\n; scene {index}\n", encoding="utf-8"
        )
        scenes.append(scene_path)
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 2)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text("", encoding="utf-8")
    godot = tmp_path / "Godot.exe"
    ffmpeg = tmp_path / "ffmpeg.exe"
    godot.write_bytes(b"godot-test")
    ffmpeg.write_bytes(b"ffmpeg-test")
    cache_directory = project_root / "render_cache"
    godot_renders = []
    monkeypatch.setattr(
        "app.render.subprocess.run",
        _fake_render_commands(godot, ffmpeg, godot_renders),
    )

    def render(name):
        return render_episode_video(
            scenes,
            [1, 1],
            audio_path,
            subtitles_path,
            project_root / "renders" / name,
            project_root,
            godot,
            ffmpeg_executable=ffmpeg,
            cache_directory=cache_directory,
        )

    first = render("first.mp4")
    assert first["rendered_scene_count"] == 2
    assert first["cached_scene_count"] == 0
    assert sorted(godot_renders) == ["scene-1.tscn", "scene-2.tscn"]
    assert len(list(cache_directory.glob("scene-*.avi"))) == 2

    second = render("second.mp4")
    assert second["rendered_scene_count"] == 0
    assert second["cached_scene_count"] == 2
    assert len(godot_renders) == 2
    assert Path(second["video_path"]).read_bytes() == b"fake-mp4"

    scenes[1].write_text("[gd_scene format=3]\n; scene 2 edited\n", encoding="utf-8")
    third = render("third.mp4")
    assert third["rendered_scene_count"] == 1
    assert third["cached_scene_count"] == 1
    assert godot_renders.count("scene-1.tscn") == 1
    assert godot_renders.count("scene-2.tscn") == 2


def test_scene_cache_must_stay_inside_the_episode_project(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scene_path = project_root / "scene.tscn"
    scene_path.write_text("[gd_scene format=3]\n", encoding="utf-8")
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 1)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text("", encoding="utf-8")
    godot = tmp_path / "Godot.exe"
    ffmpeg = tmp_path / "ffmpeg.exe"
    godot.write_bytes(b"godot-test")
    ffmpeg.write_bytes(b"ffmpeg-test")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=" V..... libvpx-vp9\n A..... aac\n S..... mov_text\n",
            stderr="",
        )

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    with pytest.raises(RenderPathError, match="scene cache"):
        render_episode_video(
            [scene_path],
            [1],
            audio_path,
            subtitles_path,
            project_root / "renders" / "episode.mp4",
            project_root,
            godot,
            ffmpeg_executable=ffmpeg,
            cache_directory=tmp_path / "outside-cache",
        )


def test_scene_cache_limit_drops_the_oldest_movies(tmp_path):
    cache_root = tmp_path / "render_cache"
    cache_root.mkdir()
    for index, written_at in enumerate((100, 200, 300), start=1):
        path = cache_root / f"scene-0{index}-key{index}.avi"
        path.write_bytes(b"x" * 10)
        os.utime(path, (written_at, written_at))

    _enforce_scene_cache_limit(cache_root, limit_bytes=1000)
    assert len(list(cache_root.glob("scene-*.avi"))) == 3

    _enforce_scene_cache_limit(cache_root, limit_bytes=15)
    remaining = sorted(path.name for path in cache_root.glob("scene-*.avi"))
    assert remaining == ["scene-03-key3.avi"]


def _proof_scene_source(camera_height: float) -> str:
    return f"""[gd_scene load_steps=2 format=3]

[sub_resource type="SphereMesh" id="SphereMesh_proof"]

[node name="EpisodeScene" type="Node3D"]

[node name="EpisodeCamera" type="Camera3D" parent="."]
transform = Transform3D(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, {camera_height}, 5)
current = true

[node name="Sphere" type="MeshInstance3D" parent="."]
mesh = SubResource("SphereMesh_proof")
"""


def test_real_media_render_produces_a_playable_mp4(tmp_path):
    """Render an episode with the real Godot runtime and FFmpeg binaries.

    The mocked tests cover the render logic; this one proves the production
    chain on actual media. It runs only where the pinned Godot build and a
    redistribution-safe FFmpeg are provisioned (the `real-media` Windows CI job),
    and is skipped everywhere else.
    """
    if os.environ.get("CARTOON_STUDIO_REAL_MEDIA") != "1":
        pytest.skip("The real-media render runs only in the dedicated CI job.")
    godot_path = os.environ.get("CARTOON_STUDIO_GODOT_PATH", "")
    if not godot_path or not Path(godot_path).is_file():
        pytest.skip("The pinned Godot runtime is only provisioned in CI.")
    try:
        ffmpeg = _find_ffmpeg(os.environ.get("CARTOON_STUDIO_FFMPEG") or None)
    except RenderDependencyUnavailable as error:
        pytest.skip(f"No FFmpeg is provisioned for a real-media render: {error}")

    proof_root = Path(os.environ.get("CARTOON_STUDIO_PROOF_DIR") or tmp_path)
    project_root = proof_root / "project"
    project_root.mkdir(parents=True, exist_ok=True)
    scene_paths = [project_root / "scene-1.tscn", project_root / "scene-2.tscn"]
    for index, scene_path in enumerate(scene_paths, start=1):
        scene_path.write_text(
            _proof_scene_source(1 + index * 0.4), encoding="utf-8"
        )
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 2)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nالسلام علیکم!\n", encoding="utf-8"
    )

    result = render_episode_video(
        scene_paths,
        [1, 1],
        audio_path,
        subtitles_path,
        project_root / "renders" / "episode.mp4",
        project_root,
        Path(godot_path),
        ffmpeg_executable=ffmpeg,
        width=640,
        height=360,
        cache_directory=project_root / "render_cache",
    )

    assert result["duration_seconds"] == 2
    assert result["video_encoder"] in VIDEO_ENCODER_PREFERENCE
    assert result["rendered_scene_count"] == 2
    assert result["cached_scene_count"] == 0
    video = Path(result["video_path"])
    assert video.is_file() and video.stat().st_size > 1024
    assert len(list((project_root / "render_cache").glob("scene-*.avi"))) == 2
