from __future__ import annotations

import array
import hashlib
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


def generate_episode_audio(
    plan: dict,
    output_directory: Path,
    data_dir: Path,
    synthesizer: object | None = None,
) -> dict:
    if plan.get("language", "ur") != "ur":
        raise SpeechGenerationError(
            "The current offline speech pack supports Pakistani Urdu episodes only."
        )
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
        for line_index, line in enumerate(scene.get("dialogue", []), start=1):
            text = str(line.get("text", "")).strip()
            if not text:
                raise SpeechGenerationError("A dialogue line is empty.")
            character_id = str(line.get("character_id", "narrator"))
            voice_id = voice_by_character.get(character_id, DEFAULT_URDU_VOICE)
            if voice_id not in VOICE_CATALOG:
                raise SpeechGenerationError(
                    f"Character {character_id} has an unsupported voice profile: {voice_id}"
                )
            clip_path = clips_directory / f"scene-{scene_index:02d}-line-{line_index:02d}.wav"
            engine.synthesize(text, voice_id, clip_path)
            _, samples = _read_pcm(clip_path)
            actual_duration = len(samples) / SAMPLE_RATE
            timeline_start = scene_offset + float(line.get("start_seconds", 0))
            clips.append({
                "scene_id": scene["id"],
                "character_id": character_id,
                "text": text,
                "voice_id": voice_id,
                "start_seconds": float(line.get("start_seconds", 0)),
                "timeline_start_seconds": timeline_start,
                "duration_seconds": round(actual_duration, 3),
                "relative_path": clip_path.relative_to(output_directory).as_posix(),
                "path": str(clip_path),
            })
        scene_offset += int(scene["duration_seconds"])
    mix_path = output_directory / "dialogue_mix.wav"
    _write_episode_mix(mix_path, total_duration, clips)
    for clip in clips:
        clip.pop("path", None)
    return {
        "audio_path": str(mix_path),
        "sample_rate": SAMPLE_RATE,
        "duration_seconds": total_duration,
        "dialogue_line_count": len(clips),
        "voices": sorted({clip["voice_id"] for clip in clips}),
        "clips": clips,
    }
