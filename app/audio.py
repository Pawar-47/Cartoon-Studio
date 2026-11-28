from __future__ import annotations

import array
import hashlib
import io
import math
import os
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path


class SpeechEngineUnavailable(RuntimeError):
    pass


class SpeechGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class VoiceModel:
    voice_id: str
    label: str
    model_file: str
    config_file: str
    revision: str
    model_md5: str
    config_md5: str
    model_size: int
    config_size: int


VOICE_CATALOG = {
    "ur_PK-fasih-medium": VoiceModel(
        voice_id="ur_PK-fasih-medium",
        label="Fasih · Pakistani Urdu · Male",
        model_file="ur/ur_PK/fasih/medium/ur_PK-fasih-medium.onnx",
        config_file="ur/ur_PK/fasih/medium/ur_PK-fasih-medium.onnx.json",
        revision="b4e358ffcb232591bf73a540e70f7de528e4174a",
        model_md5="f32ec2c6ebcc6bd1752cab0b932859c7",
        config_md5="0cc49a3a9f342ea849b62766e9017f7a",
        model_size=64832023,
        config_size=3237,
    ),
    "ur_PK-aegis_female-medium": VoiceModel(
        voice_id="ur_PK-aegis_female-medium",
        label="Aegis · Pakistani Urdu · Female",
        model_file="ur/ur_PK/aegis_female/medium/ur_PK-aegis_female-medium.onnx",
        config_file="ur/ur_PK/aegis_female/medium/ur_PK-aegis_female-medium.onnx.json",
        revision="025220c2b026011dda1a68435f2f3f5a495bf823",
        model_md5="81f9f9772025785f548e1aa0de3361b7",
        config_md5="6ee1b0405998a314c51c6744b714becd",
        model_size=63515589,
        config_size=5236,
    ),
}
DEFAULT_URDU_VOICE = "ur_PK-fasih-medium"
SAMPLE_RATE = 22050
MAX_DIALOGUE_LINES = 420
MAX_MODEL_BYTES = 100 * 1024 * 1024


def _md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_verified(url: str, destination: Path, expected_size: int, expected_md5: str) -> None:
    if destination.is_file() and destination.stat().st_size == expected_size:
        if _md5(destination) == expected_md5:
            return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".download")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Cartoon-Studio-offline-speech/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open("wb") as out:
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_MODEL_BYTES:
                    raise SpeechGenerationError(
                        "The selected Urdu voice model exceeded its size limit."
                    )
                out.write(chunk)
    except (OSError, urllib.error.URLError) as error:
        temporary.unlink(missing_ok=True)
        raise SpeechGenerationError(
            "Could not download the Urdu voice model. Check the internet connection and retry."
        ) from error
    if temporary.stat().st_size != expected_size or _md5(temporary) != expected_md5:
        temporary.unlink(missing_ok=True)
        raise SpeechGenerationError("The downloaded Urdu voice model failed its integrity check.")
    os.replace(temporary, destination)


def ensure_voice_files(data_dir: Path, voice_id: str) -> Path:
    spec = VOICE_CATALOG.get(voice_id)
    if spec is None:
        raise SpeechGenerationError(f"Unsupported Urdu voice: {voice_id}")
    model_path = Path(data_dir) / "models" / "piper" / voice_id / Path(spec.model_file).name
    config_path = Path(str(model_path) + ".json")
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/" + spec.revision + "/"
    _download_verified(
        base_url + spec.model_file,
        model_path,
        spec.model_size,
        spec.model_md5,
    )
    _download_verified(
        base_url + spec.config_file,
        config_path,
        spec.config_size,
        spec.config_md5,
    )
    return model_path


class PiperEngine:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self._voices: dict[str, object] = {}

    def synthesize(self, text: str, voice_id: str, output_path: Path) -> None:
        try:
            from piper import PiperVoice
        except ImportError as error:
            raise SpeechEngineUnavailable(
                'Urdu speech support is not installed. Install it with: pip install piper-tts.'
            ) from error
        voice = self._voices.get(voice_id)
        if voice is None:
            model_path = ensure_voice_files(self.data_dir, voice_id)
            try:
                voice = PiperVoice.load(str(model_path))
            except Exception as error:
                raise SpeechGenerationError(f"Could not load Urdu voice {voice_id}.") from error
            self._voices[voice_id] = voice
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with wave.open(str(output_path), "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)
        except Exception as error:
            output_path.unlink(missing_ok=True)
            raise SpeechGenerationError(
                "Piper could not synthesize one of the dialogue lines."
            ) from error


def validate_recorded_audio(data: bytes) -> float:
    """Validate an uploaded recorded WAV and return its duration in seconds.

    A recording replaces one dialogue line, so it must match the mix contract:
    mono 16-bit PCM at 22,050 Hz. Anything else is refused instead of being
    silently resampled or mixed at the wrong rate.
    """
    if not data:
        raise SpeechGenerationError("The recorded audio is empty.")
    try:
        with wave.open(io.BytesIO(data), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            sample_rate = source.getframerate()
            frames = source.getnframes()
            raw = source.readframes(frames)
    except (OSError, EOFError, wave.Error) as error:
        raise SpeechGenerationError(
            "The recorded audio is not a readable WAV file."
        ) from error
    if channels != 1 or sample_width != 2 or sample_rate != SAMPLE_RATE:
        raise SpeechGenerationError(
            "A recorded dialogue line must be mono 16-bit PCM at 22,050 Hz; "
            f"this file is {channels} channel(s), {sample_width * 8}-bit at "
            f"{sample_rate} Hz."
        )
    if not raw:
        raise SpeechGenerationError("The recorded audio contains no samples.")
    return len(raw) / (sample_width * channels) / sample_rate


def _read_pcm(path: Path) -> tuple[int, array.array]:
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            sample_rate = source.getframerate()
            frames = source.getnframes()
            raw = source.readframes(frames)
    except (OSError, wave.Error) as error:
        raise SpeechGenerationError("The speech engine produced an invalid WAV file.") from error
    if channels != 1 or sample_width != 2 or sample_rate != SAMPLE_RATE:
        raise SpeechGenerationError("Urdu voice output must be mono 16-bit PCM at 22,050 Hz.")
    samples = array.array("h")
    samples.frombytes(raw)
    if os.sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        raise SpeechGenerationError("The speech engine produced an empty audio clip.")
    return sample_rate, samples


def _build_mouth_envelope(samples: array.array, window_ms: int = 50) -> list[dict]:
    window_frames = max(1, round(SAMPLE_RATE * window_ms / 1000))
    levels = []
    for start in range(0, len(samples), window_frames):
        window = samples[start : start + window_frames]
        if not window:
            continue
        mean_square = sum(sample * sample for sample in window) / len(window)
        levels.append(math.sqrt(mean_square) / 32768.0)
    if not levels:
        return []
    peak = max(levels)
    threshold = max(0.006, peak * 0.12)
    dynamic_range = max(peak - threshold, 0.001)
    envelope = []
    for index, level in enumerate(levels):
        openness = max(0.0, min(1.0, (level - threshold) / dynamic_range))
        if openness < 0.10:
            openness = 0.0
        envelope.append({
            "time": round(index * window_frames / SAMPLE_RATE, 3),
            "openness": round(openness, 3),
        })
    duration = len(samples) / SAMPLE_RATE
    if envelope and envelope[-1]["time"] < duration:
        envelope.append({
            "time": round(duration, 3),
            "openness": envelope[-1]["openness"],
        })
    return envelope


def _write_episode_mix(path: Path, duration_seconds: int, clips: list[dict]) -> None:
    total_frames = duration_seconds * SAMPLE_RATE
    mixed = array.array("h", [0]) * total_frames
    for clip in clips:
        _, samples = _read_pcm(Path(clip["path"]))
        start_frame = round(float(clip["timeline_start_seconds"]) * SAMPLE_RATE)
        if start_frame >= total_frames:
            continue
        available = min(len(samples), total_frames - start_frame)
        for index in range(available):
            value = mixed[start_frame + index] + round(samples[index] * 0.82)
            mixed[start_frame + index] = max(-32768, min(32767, value))
    if os.sys.byteorder != "little":
        mixed.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(mixed.tobytes())


def _srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{millis:03d}"


SUBTITLE_MODES = ("urdu", "roman_urdu", "english", "none")


def _subtitle_line_text(clip: dict, subtitle_mode: str) -> str:
    """Return the text this episode's subtitle mode should show for one clip."""
    if subtitle_mode == "urdu":
        return str(clip["text"])
    return str(clip.get("subtitle_text") or "")


def _write_subtitles(path: Path, clips: list[dict], subtitle_mode: str = "urdu") -> None:
    """Write the episode SRT for the requested subtitle mode.

    ``none`` writes an empty file so the render step still has a subtitle input,
    and the mode recorded in the manifest says the stream carries no text.
    """
    if subtitle_mode == "none":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
        return
    entries = []
    for index, clip in enumerate(clips, start=1):
        start = float(clip["timeline_start_seconds"])
        end = start + float(clip["duration_seconds"])
        text = _subtitle_line_text(clip, subtitle_mode)
        text = text.replace("\r", " ").replace("\n", " ").strip()
        if not text or end <= start:
            continue
        entries.append(
            f"{index}\n{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{text}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(entries) + ("\n" if entries else ""), encoding="utf-8")


def generate_episode_audio(
    plan: dict,
    output_directory: Path,
    data_dir: Path,
    synthesizer: object | None = None,
    recordings: dict[tuple[str, int], Path] | None = None,
) -> dict:
    """Produce the episode dialogue mix, subtitles and mouth envelopes.

    ``recordings`` maps ``(scene_id, line_index)`` to a WAV that replaces the
    synthetic line. A recorded line works without any speech engine installed,
    so a recording can be used when Piper is unavailable or when the owner
    prefers a human voice.
    """
    if plan.get("language", "ur") != "ur":
        raise SpeechGenerationError(
            "The current offline speech pack supports Pakistani Urdu episodes only."
        )
    subtitle_mode = str(plan.get("subtitle_mode", "urdu"))
    if subtitle_mode not in SUBTITLE_MODES:
        raise SpeechGenerationError(
            f"Unsupported subtitle_mode {subtitle_mode!r}; use one of: "
            + ", ".join(SUBTITLE_MODES)
            + "."
        )
    recorded = dict(recordings or {})
    scenes = plan.get("scenes", [])
    total_duration = sum(
        int(scene.get("duration_seconds", 0)) for scene in scenes
    )
    dialogue_count = sum(len(scene.get("dialogue", [])) for scene in scenes)
    if not 1 <= dialogue_count <= MAX_DIALOGUE_LINES:
        raise SpeechGenerationError(
            f"Episode audio requires between 1 and {MAX_DIALOGUE_LINES} dialogue lines."
        )
    engine = synthesizer or PiperEngine(data_dir)
    output_directory = Path(output_directory)
    clips_directory = output_directory / "clips"
    clips_directory.mkdir(parents=True, exist_ok=True)
    voice_by_character = {
        character["id"]: character.get("voice_profile") or DEFAULT_URDU_VOICE
        for character in plan.get("characters", [])
    }
    clips: list[dict] = []
    scene_offset = 0.0
    for scene_index, scene in enumerate(scenes, start=1):
        scene_duration = int(scene.get("duration_seconds", 0))
        scene_id = scene.get("id", scene_index)
        if scene_duration <= 0:
            raise SpeechGenerationError(
                f"Scene {scene_id} has an invalid duration."
            )
        for line_index, line in enumerate(scene.get("dialogue", []), start=1):
            text = str(line.get("text", "")).strip()
            if not text:
                raise SpeechGenerationError("A dialogue line is empty.")
            try:
                local_start = float(line.get("start_seconds", 0))
            except (TypeError, ValueError) as error:
                raise SpeechGenerationError("A dialogue line has an invalid start time.") from error
            if not math.isfinite(local_start) or local_start < 0 or local_start >= scene_duration:
                raise SpeechGenerationError(
                    f"Dialogue in scene {scene.get('id', scene_index)} starts outside its duration."
                )
            character_id = str(line.get("character_id", "narrator"))
            voice_id = voice_by_character.get(character_id, DEFAULT_URDU_VOICE)
            if voice_id not in VOICE_CATALOG:
                raise SpeechGenerationError(
                    f"Character {character_id} has an unsupported voice profile: {voice_id}"
                )
            clip_path = clips_directory / f"scene-{scene_index:02d}-line-{line_index:02d}.wav"
            recording = recorded.get((str(scene["id"]), line_index))
            if recording is not None:
                source = Path(recording)
                if not source.is_file():
                    raise SpeechGenerationError(
                        f"The recorded line {scene_id}:{line_index} is missing."
                    )
                clip_path.write_bytes(source.read_bytes())
                line_source = "recorded"
            else:
                engine.synthesize(text, voice_id, clip_path)
                line_source = "tts"
            _, samples = _read_pcm(clip_path)
            actual_duration = len(samples) / SAMPLE_RATE
            remaining_scene_time = scene_duration - local_start
            if actual_duration > remaining_scene_time + (1 / SAMPLE_RATE):
                clip_path.unlink(missing_ok=True)
                raise SpeechGenerationError(
                    f"Dialogue in scene {scene_id} runs past the scene boundary. "
                    "Shorten the line or move it earlier before generating audio."
                )
            timeline_start = scene_offset + local_start
            subtitle_text = ""
            if subtitle_mode in ("roman_urdu", "english"):
                subtitle_text = str(line.get("subtitle_text", "")).strip()
                if not subtitle_text:
                    clip_path.unlink(missing_ok=True)
                    raise SpeechGenerationError(
                        f"Dialogue {line_index} in scene {scene_id} has no "
                        f"subtitle_text for subtitle_mode {subtitle_mode!r}."
                    )
            clips.append({
                "scene_id": scene["id"],
                "line_index": line_index,
                "character_id": character_id,
                "text": text,
                "subtitle_text": subtitle_text,
                "voice_id": voice_id,
                "source": line_source,
                "start_seconds": float(line.get("start_seconds", 0)),
                "timeline_start_seconds": timeline_start,
                "duration_seconds": round(actual_duration, 3),
                "mouth_envelope": _build_mouth_envelope(samples),
                "relative_path": clip_path.relative_to(output_directory).as_posix(),
                "path": str(clip_path),
            })
        scene_offset += scene_duration
    mix_path = output_directory / "dialogue_mix.wav"
    _write_episode_mix(mix_path, total_duration, clips)
    subtitles_path = output_directory / "subtitles.srt"
    _write_subtitles(subtitles_path, clips, subtitle_mode)
    subtitle_entry_count = 0 if subtitle_mode == "none" else sum(
        1 for clip in clips if _subtitle_line_text(clip, subtitle_mode).strip()
    )
    for clip in clips:
        clip.pop("path", None)
    return {
        "audio_path": str(mix_path),
        "subtitles_path": str(subtitles_path),
        "sample_rate": SAMPLE_RATE,
        "duration_seconds": total_duration,
        "dialogue_line_count": len(clips),
        "subtitle_mode": subtitle_mode,
        "subtitle_entry_count": subtitle_entry_count,
        "recorded_line_count": sum(1 for clip in clips if clip["source"] == "recorded"),
        "tts_line_count": sum(1 for clip in clips if clip["source"] == "tts"),
        "voices": sorted({clip["voice_id"] for clip in clips}),
        "clips": clips,
    }
