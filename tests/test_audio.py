import array
import wave

import pytest

from app.audio import (
    DEFAULT_URDU_VOICE,
    SpeechGenerationError,
    generate_episode_audio,
)


class FakeSynthesizer:
    def synthesize(self, text, voice_id, output_path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        samples = array.array("h", [1200, -1200] * 2205)
        with wave.open(str(output_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(22050)
            output.writeframes(samples.tobytes())


def test_generates_scene_timed_urdu_dialogue_clips_and_episode_mix(tmp_path):
    plan = {
        "language": "ur",
        "characters": [
            {"id": "ali", "voice_profile": DEFAULT_URDU_VOICE},
            {"id": "bilu", "voice_profile": "ur_PK-aegis_female-medium"},
        ],
        "scenes": [
            {
                "id": "market",
                "duration_seconds": 30,
                "dialogue": [
                    {
                        "character_id": "ali",
                        "text": "السلام علیکم!",
                        "start_seconds": 2,
                        "duration_seconds": 2,
                    }
                ],
            },
            {
                "id": "street",
                "duration_seconds": 30,
                "dialogue": [
                    {
                        "character_id": "bilu",
                        "text": "وعلیکم السلام!",
                        "start_seconds": 3,
                        "duration_seconds": 2,
                    }
                ],
            },
        ],
    }
    result = generate_episode_audio(
        plan,
        tmp_path / "audio",
        tmp_path / "data",
        synthesizer=FakeSynthesizer(),
    )
    assert result["dialogue_line_count"] == 2
    assert result["voices"] == [
        "ur_PK-aegis_female-medium",
        "ur_PK-fasih-medium",
    ]
    assert result["duration_seconds"] == 60
    assert len(result["clips"]) == 2
    assert result["clips"][0]["timeline_start_seconds"] == 2
    assert result["clips"][1]["timeline_start_seconds"] == 33
    with wave.open(result["audio_path"], "rb") as mixed:
        assert mixed.getframerate() == 22050
        assert mixed.getnframes() == 60 * 22050
        assert mixed.getnchannels() == 1


def test_rejects_non_urdu_episode_before_loading_speech_runtime(tmp_path):
    with pytest.raises(SpeechGenerationError, match="Pakistani Urdu"):
        generate_episode_audio(
            {"language": "en", "scenes": [], "characters": []},
            tmp_path / "audio",
            tmp_path / "data",
            synthesizer=FakeSynthesizer(),
        )


def test_rejects_unknown_character_voice_profile(tmp_path):
    plan = {
        "language": "ur",
        "characters": [{"id": "ali", "voice_profile": "unknown-voice"}],
        "scenes": [
            {
                "id": "scene-1",
                "duration_seconds": 30,
                "dialogue": [
                    {
                        "character_id": "ali",
                        "text": "یہ ایک ٹیسٹ ہے۔",
                        "start_seconds": 1,
                        "duration_seconds": 2,
                    }
                ],
            }
        ],
    }
    with pytest.raises(SpeechGenerationError, match="unsupported voice profile"):
        generate_episode_audio(
            plan,
            tmp_path / "audio",
            tmp_path / "data",
            synthesizer=FakeSynthesizer(),
        )
