from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
import wave
from collections.abc import Callable
from pathlib import Path


class RenderDependencyUnavailable(RuntimeError):
    pass


class RenderPathError(RuntimeError):
    pass


class RenderExecutionError(RuntimeError):
    pass


class RenderCancelled(RenderExecutionError):
    """Raised when the owner cancelled the render between scenes."""


RENDER_FPS = 24
RENDER_WIDTH = 1280
RENDER_HEIGHT = 720
RENDER_TIMEOUT_SECONDS = 14_400
# The four quality presets in app/quality.py render at 15, 24 and 30 fps.
SUPPORTED_FPS = frozenset({12, 15, 20, 24, 25, 30})
MIN_RENDER_WIDTH = 640
MIN_RENDER_HEIGHT = 360
BUNDLED_FFMPEG_NAME = "ffmpeg.exe"
# Bump when a cached scene video is no longer valid for the current renderer.
SCENE_CACHE_VERSION = 1

# Video encoders this application may redistribute, in preference order.
#
# libx264, libx265 and libxvid are deliberately absent: they are GPL-only, and
# bundling them would put GPL obligations on the whole installer. The first
# available encoder below is used, so the same code works with the bundled LGPL
# FFmpeg build and with a system FFmpeg that has more encoders.
VIDEO_ENCODER_PREFERENCE = (
    # BSD, Cisco OpenH264; MP4/H.264 with the CSP patent grant for its binary.
    "libopenh264",
    # BSD; VP9 in MP4, the fallback when OpenH264 is not in the build.
    "libvpx-vp9",
    # BSD; AV1 in MP4.
    "libaom-av1",
    "libsvtav1",
    # Native FFmpeg MPEG-4 Part 2 (LGPL), kept as the last resort.
    "mpeg4",
)
VIDEO_ENCODER_OPTIONS = {
    "libopenh264": ["-b:v", "2500k", "-pix_fmt", "yuv420p"],
    "libvpx-vp9": ["-crf", "34", "-b:v", "0", "-pix_fmt", "yuv420p"],
    "libaom-av1": ["-crf", "38", "-b:v", "0", "-pix_fmt", "yuv420p"],
    "libsvtav1": ["-crf", "40", "-preset", "10", "-pix_fmt", "yuv420p"],
    "mpeg4": ["-q:v", "5", "-pix_fmt", "yuv420p"],
}
GPL_ONLY_VIDEO_ENCODERS = frozenset({"libx264", "libx265", "libxvid"})
VIDEO_ENCODER_KIND = {
    "libopenh264": "H.264 (OpenH264, BSD binary)",
    "libvpx-vp9": "VP9 (BSD)",
    "libaom-av1": "AV1 (BSD)",
    "libsvtav1": "AV1 (BSD)",
    "mpeg4": "MPEG-4 Part 2 (FFmpeg native)",
}


def _project_file(path: Path, root: Path, suffix: str) -> Path:
    resolved = Path(path).resolve(strict=True)
    if resolved == root or root not in resolved.parents:
        raise RenderPathError("Render inputs must remain inside the episode project.")
    if not resolved.is_file() or resolved.suffix.lower() != suffix:
        raise RenderPathError(f"Episode render requires an existing {suffix} file.")
    return resolved


def _bundled_ffmpeg() -> Path | None:
    """Return the FFmpeg that ships beside the application, when it is installed."""
    bundle_root = Path(__file__).resolve().parent.parent
    candidates = (
        bundle_root / "engine" / "ffmpeg" / BUNDLED_FFMPEG_NAME,
        bundle_root / "third_party" / "ffmpeg" / BUNDLED_FFMPEG_NAME,
        bundle_root / "build" / "ffmpeg" / BUNDLED_FFMPEG_NAME,
    )
    return next((path for path in candidates if path.is_file()), None)


def _find_ffmpeg(explicit_path: str | Path | None = None) -> Path:
    """Resolve FFmpeg: explicit path, then the bundled build, then environment/PATH."""
    if explicit_path:
        candidate: str | Path | None = explicit_path
    else:
        candidate = _bundled_ffmpeg()
    if candidate is None:
        candidate = os.environ.get("CARTOON_STUDIO_FFMPEG", "").strip()
    if not candidate:
        candidate = shutil.which("ffmpeg")
    if not candidate:
        raise RenderDependencyUnavailable(
            "FFmpeg was not found and the bundled engine/ffmpeg/ffmpeg.exe is missing. "
            "Install the Cartoon Studio installer build, or set CARTOON_STUDIO_FFMPEG to "
            "an LGPL FFmpeg executable."
        )
    executable = Path(candidate).expanduser().resolve(strict=False)
    if not executable.is_file():
        raise RenderDependencyUnavailable("The configured FFmpeg executable does not exist.")
    return executable


def _available_encoders(executable: Path) -> list[str]:
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
    if result.returncode != 0:
        raise RenderDependencyUnavailable(
            "FFmpeg could not list its encoders, so the MP4 output cannot be verified."
        )
    listing = result.stdout + "\n" + result.stderr
    names: list[str] = []
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        flags = parts[0]
        # Encoder rows look like " V..... libx264 ..." or " A....D aac ...":
        # one or two letters for the media type and capabilities, then dots.
        if not 5 <= len(flags) <= 6 or flags[0] not in "VASD":
            continue
        if not all(character == "." or character.isalpha() for character in flags[1:]):
            continue
        if parts[1].startswith("="):
            continue
        names.append(parts[1])
    return names


def choose_video_encoder(executable: Path) -> str:
    """Return the first redistribution-safe video encoder the build supports.

    The video encoder is chosen from the build's own encoder list so the same
    code works with the bundled LGPL FFmpeg and with a fuller system build. A
    build whose only video encoders are GPL is refused rather than used.
    """
    available = _available_encoders(executable)
    for encoder in ("aac", "mov_text"):
        if encoder not in available:
            raise RenderDependencyUnavailable(
                "The configured FFmpeg build cannot create the required MP4. "
                f"Missing encoder: {encoder}. Install a build with AAC and mov_text."
            )
    for encoder in VIDEO_ENCODER_PREFERENCE:
        if encoder in available:
            return encoder
    gpl = sorted(set(available) & GPL_ONLY_VIDEO_ENCODERS)
    if gpl:
        raise RenderDependencyUnavailable(
            "The configured FFmpeg build offers only GPL video encoders "
            f"({', '.join(gpl)}). Cartoon Studio bundles an LGPL FFmpeg with "
            "OpenH264 or VP9; replace the system FFmpeg with that build."
        )
    raise RenderDependencyUnavailable(
        "The configured FFmpeg build has no redistribution-safe video encoder. "
        "Install a build with libopenh264, libvpx-vp9 or the native mpeg4 encoder."
    )


def _verify_rendered_mp4(
    executable: Path,
    video_path: Path,
    timeout: float,
    expected_duration: float,
    include_subtitles: bool = True,
) -> None:
    maps = ["-map", "0:v:0", "-map", "0:a:0"]
    if include_subtitles:
        maps += ["-map", "0:s:0"]
    try:
        result = subprocess.run(
            [
                str(executable),
                "-v",
                "error",
                "-i",
                str(video_path),
                *maps,
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
        streams = "video/audio/subtitle" if include_subtitles else "video/audio"
        raise RenderExecutionError(
            f"The final MP4 failed its {streams} decode check. {detail}".strip()
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


def ffmpeg_status() -> dict[str, object]:
    """Return the resolved FFmpeg, its chosen encoder, or why it cannot run."""
    try:
        executable = _find_ffmpeg()
    except RenderDependencyUnavailable as error:
        return {"available": False, "executable": None, "error": str(error)}
    try:
        encoder = choose_video_encoder(executable)
    except RenderDependencyUnavailable as error:
        return {
            "available": False,
            "executable": str(executable),
            "error": str(error),
        }
    return {
        "available": True,
        "executable": str(executable),
        "video_encoder": encoder,
        "video_codec": VIDEO_ENCODER_KIND[encoder],
    }


def _scene_cache_key(
    scene_path: Path,
    fps: int,
    width: int,
    height: int,
    duration: int,
) -> str:
    """Fingerprint a scene and the render settings its cached video belongs to.

    The key covers the scene file's bytes, the exact frame rate, resolution and
    duration, and a cache format version, so an edited scene, a changed quality
    preset or a new cache format never reuses a stale video.
    """
    digest = hashlib.sha256()
    digest.update(f"cartoon-studio-scene-cache-v{SCENE_CACHE_VERSION}\0".encode())
    digest.update(f"{fps}x{width}x{height}:{duration}\0".encode())
    with scene_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def _place_scene(source: Path, destination: Path) -> None:
    """Put an identical scene video at the destination without rewriting it.

    The cache and the temporary render directory sit on the same project volume,
    so a hard link reuses the movie instead of copying it; a filesystem that
    refuses the link falls back to a copy, and the destination only appears once
    it is complete.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    partial.unlink(missing_ok=True)
    try:
        os.link(source, partial)
    except OSError:
        shutil.copyfile(source, partial)
    partial.replace(destination)


def _prune_scene_cache(cache_root: Path, index: int, keep: Path) -> None:
    """Drop cached versions of a scene that the current file replaced.

    Scene videos are large, so only the newest version of each scene position is
    kept. A render already reading an older version keeps working through its own
    link, so pruning never breaks work in progress.
    """
    for stale in cache_root.glob(f"scene-{index:02d}-*.avi"):
        if stale.name != keep.name:
            stale.unlink(missing_ok=True)


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
    include_subtitles: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
    cache_directory: Path | None = None,
) -> dict:
    """Render the episode scene by scene and assemble the MP4.

    ``progress_callback`` receives ``(scenes_done, scene_count)`` after each
    scene so a background job can report real progress, and ``cancel_check`` is
    consulted before each scene and before assembly so a cancelled job stops
    without rendering the remaining scenes. Both are optional; a synchronous
    caller gets exactly the previous behaviour.

    ``cache_directory`` keeps every finished scene video keyed by the scene's
    bytes and its render settings, so a retried or restarted render reuses the
    scenes it already finished instead of rendering the whole episode again.
    """
    def cancelled() -> bool:
        return bool(cancel_check and cancel_check())
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
    if (
        fps not in SUPPORTED_FPS
        or width < MIN_RENDER_WIDTH
        or height < MIN_RENDER_HEIGHT
        or width % 2
        or height % 2
    ):
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
    video_encoder = choose_video_encoder(ffmpeg)
    output = Path(output_path).resolve(strict=False)
    if output == root or root not in output.parents or output.suffix.lower() != ".mp4":
        raise RenderPathError("The final MP4 must be saved inside the episode project.")
    if output.exists():
        raise RenderPathError("Refusing to overwrite an existing episode MP4.")
    output.parent.mkdir(parents=True, exist_ok=True)
    cache_root: Path | None = None
    if cache_directory is not None:
        candidate_cache = Path(cache_directory).resolve(strict=False)
        if candidate_cache == root or root not in candidate_cache.parents:
            raise RenderPathError(
                "The scene cache must stay inside the episode project."
            )
        candidate_cache.mkdir(parents=True, exist_ok=True)
        cache_root = candidate_cache

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
        cached_scenes = 0
        rendered_scenes = 0
        for index, (scene_path, duration) in enumerate(
            zip(scenes, scene_durations, strict=True),
            start=1,
        ):
            if cancelled():
                raise RenderCancelled(
                    f"The episode render was cancelled before scene {index}."
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RenderExecutionError("The episode render exceeded its time budget.")
            scene_video = temporary_root / f"scene-{index:02d}.avi"
            frames = duration * fps
            cache_key = ""
            if cache_root is not None:
                cache_key = _scene_cache_key(scene_path, fps, width, height, duration)
                cached_video = cache_root / f"scene-{index:02d}-{cache_key}.avi"
                if cached_video.is_file() and cached_video.stat().st_size > 0:
                    _place_scene(cached_video, scene_video)
                    scene_videos.append(scene_video)
                    cached_scenes += 1
                    if progress_callback is not None:
                        progress_callback(index, len(scenes))
                    continue
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
            render_log = result.stdout + "\n" + result.stderr
            expected_frame_report = f"{frames} frames at {fps} FPS"
            if (
                result.returncode != 0
                or not scene_video.is_file()
                or scene_video.stat().st_size == 0
                or expected_frame_report not in render_log
            ):
                detail = render_log.strip()[-2500:]
                raise RenderExecutionError(
                    f"Godot did not render scene {index} at its exact frame count "
                    f"({expected_frame_report}). {detail}".strip()
                )
            if cache_root is not None:
                cached_scene = cache_root / f"scene-{index:02d}-{cache_key}.avi"
                _place_scene(scene_video, cached_scene)
                _prune_scene_cache(cache_root, index, cached_scene)
            rendered_scenes += 1
            scene_videos.append(scene_video)
            if progress_callback is not None:
                progress_callback(index, len(scenes))

        if cancelled():
            raise RenderCancelled("The episode render was cancelled before assembly.")
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
        ]
        if include_subtitles:
            command += ["-i", str(subtitles_file)]
        command += ["-map", "0:v:0", "-map", "1:a:0"]
        if include_subtitles:
            command += ["-map", "2:s:0"]
        command += [
            "-c:v",
            video_encoder,
            *VIDEO_ENCODER_OPTIONS[video_encoder],
            "-c:a",
            "aac",
            "-b:a",
            "160k",
        ]
        if include_subtitles:
            command += [
                "-c:s",
                "mov_text",
                "-metadata:s:s:0",
                "language=urd",
            ]
        command += [
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
            _verify_rendered_mp4(
                ffmpeg, output, remaining, total_duration, include_subtitles
            )
        except RenderExecutionError:
            output.unlink(missing_ok=True)
            raise

    return {
        "video_path": str(output),
        "duration_seconds": total_duration,
        "fps": fps,
        "width": width,
        "height": height,
        "has_subtitles": include_subtitles,
        "cached_scene_count": cached_scenes,
        "rendered_scene_count": rendered_scenes,
        "video_encoder": video_encoder,
        "video_codec": VIDEO_ENCODER_KIND[video_encoder],
        "size_bytes": output.stat().st_size,
        "rendered_at_elapsed_seconds": round(time.monotonic() - started, 2),
    }
