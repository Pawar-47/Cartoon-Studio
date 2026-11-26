import subprocess
import wave
from pathlib import Path

import pytest

from app.render import (
    RenderDependencyUnavailable,
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
        if command[0] == str(godot):
            movie_path = Path(command[command.index("--write-movie") + 1])
            movie_path.write_bytes(b"fake-avi")
        else:
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
