import os
import subprocess
import wave
from pathlib import Path

import pytest

from app.render import (
    RenderDependencyUnavailable,
    RenderExecutionError,
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
    _write_silent_wav(audio_path, 5)
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

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0] == str(ffmpeg) and "-encoders" in command:
            encoders = " V..... libx264\n A..... aac\n S..... mov_text\n"
            return subprocess.CompletedProcess(
                command, 0, stdout=encoders, stderr=""
            )
        if command[0] == str(ffmpeg) and command[-2:] == ["null", "-"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[0] == str(godot):
            movie_path = Path(command[command.index("--write-movie") + 1])
            movie_path.write_bytes(b"fake-avi")
        elif command[0] == str(ffmpeg):
            Path(command[-1]).write_bytes(b"fake-mp4")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    result = render_episode_video(
        scene_paths,
        [1, 1, 1, 1, 1],
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
    assert result["duration_seconds"] == 5
    assert result["fps"] == 24
    assert result["size_bytes"] == len(b"fake-mp4")
    godot_calls = [call for call in calls if call[0] == str(godot)]
    assert len(godot_calls) == 5
    assert all("--write-movie" in call for call in godot_calls)
    assert all(call[call.index("--quit-after") + 1] == "24" for call in godot_calls)
    assert calls[-1][0] == str(ffmpeg)
    assert "-c:v" in calls[-1] and "libx264" in calls[-1]
    assert "-c:a" in calls[-1] and "aac" in calls[-1]
    assert "-c:s" in calls[-1] and "mov_text" in calls[-1]
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
    output = result.stdout + "\\n" + result.stderr
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
    scene_path.write_text("[gd_scene format=3]\\n", encoding="utf-8")
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
            command, 0, stdout=" A..... aac\\n S..... mov_text\\n", stderr=""
        )

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    with pytest.raises(RenderDependencyUnavailable, match="libx264"):
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


def test_render_removes_mp4_when_stream_decode_verification_fails(
    tmp_path, monkeypatch
):
    project_root = tmp_path / "project"
    project_root.mkdir()
    scene_path = project_root / "scene.tscn"
    scene_path.write_text("[gd_scene format=3]\\n", encoding="utf-8")
    audio_path = project_root / "dialogue.wav"
    _write_silent_wav(audio_path, 1)
    subtitles_path = project_root / "subtitles.srt"
    subtitles_path.write_text(
        "1\\n00:00:00,000 --> 00:00:01,000\\nالسلام علیکم!\\n",
        encoding="utf-8",
    )
    godot = tmp_path / "Godot.exe"
    ffmpeg = tmp_path / "ffmpeg.exe"
    godot.write_bytes(b"godot-test")
    ffmpeg.write_bytes(b"ffmpeg-test")
    output = project_root / "renders" / "episode.mp4"

    def fake_run(command, **kwargs):
        if command[0] == str(ffmpeg) and "-encoders" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=" V..... libx264\\n A..... aac\\n S..... mov_text\\n",
                stderr="",
            )
        if command[0] == str(godot):
            Path(command[command.index("--write-movie") + 1]).write_bytes(b"fake-avi")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[0] == str(ffmpeg) and command[-2:] == ["null", "-"]:
            return subprocess.CompletedProcess(
                command, 1, stdout="", stderr="Could not find codec parameters"
            )
        output_path = Path(command[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake-mp4")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    with pytest.raises(RenderExecutionError, match="decode check"):
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
