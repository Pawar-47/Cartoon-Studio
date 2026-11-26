from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
import wave
from pathlib import Path


class RenderDependencyUnavailable(RuntimeError):
    pass


class RenderPathError(RuntimeError):
    pass


class RenderExecutionError(RuntimeError):
    pass


RENDER_FPS = 24
RENDER_WIDTH = 1280
RENDER_HEIGHT = 720
RENDER_TIMEOUT_SECONDS = 14_400


def _project_file(path: Path, root: Path, suffix: str) -> Path:
    resolved = Path(path).resolve(strict=True)
    if resolved == root or root not in resolved.parents:
        raise RenderPathError("Render inputs must remain inside the episode project.")
    if not resolved.is_file() or resolved.suffix.lower() != suffix:
        raise RenderPathError(f"Episode render requires an existing {suffix} file.")
    return resolved


def _find_ffmpeg(explicit_path: str | Path | None = None) -> Path:
    candidate = (
        str(explicit_path)
        if explicit_path
        else os.environ.get("CARTOON_STUDIO_FFMPEG", "").strip()
        or shutil.which("ffmpeg")
    )
    if not candidate:
        raise RenderDependencyUnavailable(
            "FFmpeg was not found. Install a Windows FFmpeg build, add ffmpeg.exe to PATH, "
            "and restart Cartoon Studio. Free builds are listed at https://ffmpeg.org/download.html."
        )
    executable = Path(candidate).expanduser().resolve(strict=False)
    if not executable.is_file():
        raise RenderDependencyUnavailable("The configured FFmpeg executable does not exist.")
    return executable


def _verify_ffmpeg_encoders(executable: Path) -> None:
    try:
        result = subprocess.run(
            [str(executable), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RenderDependencyUnavailable(
            "FFmpeg could not be started to verify its MP4 encoding support."
        ) from error
    available = result.stdout + "\n" + result.stderr
    required = ("libx264", "aac", "mov_text")
    missing = [encoder for encoder in required if encoder not in available]
    if result.returncode != 0 or missing:
        missing_text = ", ".join(missing) if missing else "encoder listing"
        raise RenderDependencyUnavailable(
            "The configured FFmpeg build cannot create the required MP4. "
            f"Missing encoders: {missing_text}. Install a full Windows build with "
            "libx264, AAC and mov_text support."
        )


def _verify_rendered_mp4(
    executable: Path,
    video_path: Path,
    timeout: float,
    expected_duration: float,
) -> None:
    try:
        result = subprocess.run(
            [
                str(executable),
                "-v",
                "error",
                "-i",
                str(video_path),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-map",
                "0:s:0",
                "-progress",
                "pipe:1",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=max(1.0, timeout),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RenderExecutionError(
            "FFmpeg could not verify the completed episode MP4."
        ) from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()[-2500:]
        raise RenderExecutionError(
            f"The final MP4 failed its video/audio/subtitle decode check. {detail}".strip()
        )

    timestamps = re.findall(r"^out_time_us=(\d+)$", result.stdout, flags=re.MULTILINE)
    if not timestamps:
        raise RenderExecutionError(
            "FFmpeg decoded the final MP4 but did not report its verified duration."
        )
    actual_duration = int(timestamps[-1]) / 1_000_000
    tolerance = max(0.25, 1 / RENDER_FPS)
    if abs(actual_duration - expected_duration) > tolerance:
        raise RenderExecutionError(
            "The final MP4 duration does not match the episode timeline: "
            f"expected {expected_duration:.3f}s, decoded {actual_duration:.3f}s."
        )


def _write_render_project(project_directory: Path) -> None:
    (project_directory / "project.godot").write_text(
        """config_version=5

[application]
config/name="Cartoon Studio Episode Renderer"
run/main_scene="res://render_runner.tscn"

[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/size/window_width_override=1280
window/size/window_height_override=720
window/stretch/mode="viewport"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
""",
        encoding="utf-8",
    )
    (project_directory / "render_runner.tscn").write_text(
        """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://render_runner.gd" id="1"]

[node name="EpisodeRenderRunner" type="Node3D"]
script = ExtResource("1")
""",
        encoding="utf-8",
    )
    runner_source = (
        Path(__file__).resolve().parent.parent
        / "engine"
        / "godot_worker"
        / "render_runner.gd"
    )
    if not runner_source.is_file():
        raise RenderDependencyUnavailable("The Godot episode render runner is missing.")
    shutil.copy2(runner_source, project_directory / "render_runner.gd")


def render_episode_video(
    scene_paths: list[Path],
    scene_durations: list[int],
    audio_path: Path,
    subtitles_path: Path,
    output_path: Path,
    project_root: Path,
    godot_executable: Path,
    ffmpeg_executable: str | Path | None = None,
    fps: int = RENDER_FPS,
    width: int = RENDER_WIDTH,
    height: int = RENDER_HEIGHT,
    timeout_seconds: int = RENDER_TIMEOUT_SECONDS,
) -> dict:
    root = Path(project_root).resolve(strict=True)
    if not root.is_dir():
        raise RenderPathError("The episode project directory does not exist.")
    if not 1 <= len(scene_paths) <= 7 or len(scene_paths) != len(scene_durations):
        raise RenderPathError("Episode video requires matching scene files and durations.")
    if any(
        isinstance(duration, bool)
        or not isinstance(duration, int)
        or duration <= 0
        for duration in scene_durations
    ):
        raise RenderPathError("Episode scene durations must be positive whole seconds.")
    if fps not in {24, 25, 30} or width < 640 or height < 360 or width % 2 or height % 2:
        raise RenderPathError("Episode render settings are outside the supported range.")
    if timeout_seconds <= 0:
        raise RenderPathError("Episode render timeout must be positive.")
    scenes = [_project_file(path, root, ".tscn") for path in scene_paths]
    audio_file = _project_file(audio_path, root, ".wav")
    subtitles_file = _project_file(subtitles_path, root, ".srt")
    godot = Path(godot_executable).resolve(strict=False)
    if not godot.is_file():
        raise RenderDependencyUnavailable("The pinned Godot runtime is not installed.")
    ffmpeg = _find_ffmpeg(ffmpeg_executable)
    _verify_ffmpeg_encoders(ffmpeg)
    output = Path(output_path).resolve(strict=False)
    if output == root or root not in output.parents or output.suffix.lower() != ".mp4":
        raise RenderPathError("The final MP4 must be saved inside the episode project.")
    if output.exists():
        raise RenderPathError("Refusing to overwrite an existing episode MP4.")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with wave.open(str(audio_file), "rb") as audio:
            audio_duration = audio.getnframes() / audio.getframerate()
    except (OSError, wave.Error) as error:
        raise RenderPathError("The episode dialogue mix is not a readable WAV file.") from error
    total_duration = sum(scene_durations)
    if abs(audio_duration - total_duration) > 0.1:
        raise RenderPathError(
            "The dialogue WAV duration does not match the combined episode scene duration."
        )

    started = time.monotonic()
    deadline = started + timeout_seconds
    with tempfile.TemporaryDirectory(
        prefix="cartoon-studio-render-",
        dir=output.parent,
    ) as temporary:
        temporary_root = Path(temporary)
        render_project = temporary_root / "godot-project"
        render_project.mkdir()
        _write_render_project(render_project)
        scene_videos: list[Path] = []
        for index, (scene_path, duration) in enumerate(
            zip(scenes, scene_durations, strict=True),
            start=1,
        ):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RenderExecutionError("The episode render exceeded its time budget.")
            scene_video = temporary_root / f"scene-{index:02d}.avi"
            frames = duration * fps
            command = [
                str(godot),
                "--path",
                str(render_project),
                "--write-movie",
                str(scene_video),
                "--fixed-fps",
                str(fps),
                "--resolution",
                f"{width}x{height}",
                "--rendering-method",
                "gl_compatibility",
                "--disable-vsync",
                "--quit-after",
                str(frames),
                "--",
                str(scene_path),
            ]
            try:
                result = subprocess.run(
                    command,
                    cwd=render_project,
                    capture_output=True,
                    text=True,
                    timeout=remaining,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise RenderExecutionError(
                    f"Godot timed out while rendering scene {index}."
                ) from error
            if (
                result.returncode != 0
                or not scene_video.is_file()
                or scene_video.stat().st_size == 0
            ):
                detail = (result.stderr or result.stdout or "").strip()[-2500:]
                raise RenderExecutionError(
                    f"Godot could not render scene {index}. {detail}".strip()
                )
            scene_videos.append(scene_video)

        concat_file = temporary_root / "episode-scenes.txt"
        concat_file.write_text(
            "".join(f"file '{video.name}'\n" for video in scene_videos),
            encoding="utf-8",
        )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RenderExecutionError("The episode render exceeded its time budget.")
        command = [
            str(ffmpeg),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-i",
            str(audio_file),
            "-i",
            str(subtitles_file),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-map",
            "2:s:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=urd",
            "-t",
            str(total_duration),
            "-movflags",
            "+faststart",
            str(output),
        ]
        try:
            result = subprocess.run(
                command,
                cwd=temporary_root,
                capture_output=True,
                text=True,
                timeout=remaining,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise RenderExecutionError("FFmpeg timed out while creating the final MP4.") from error
        if result.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
            output.unlink(missing_ok=True)
            detail = (result.stderr or result.stdout or "").strip()[-2500:]
            raise RenderExecutionError(
                f"FFmpeg could not assemble the final MP4. {detail}".strip()
            )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            output.unlink(missing_ok=True)
            raise RenderExecutionError("The episode render exceeded its time budget.")
        try:
            _verify_rendered_mp4(ffmpeg, output, remaining, total_duration)
        except RenderExecutionError:
            output.unlink(missing_ok=True)
            raise

    return {
        "video_path": str(output),
        "duration_seconds": total_duration,
        "fps": fps,
        "width": width,
        "height": height,
        "size_bytes": output.stat().st_size,
        "rendered_at_elapsed_seconds": round(time.monotonic() - started, 2),
    }
