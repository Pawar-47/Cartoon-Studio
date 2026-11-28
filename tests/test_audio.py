import array
import wave
from pathlib import Path

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
    subtitles = Path(result["subtitles_path"]).read_text(encoding="utf-8")
    assert "00:00:02,000 --> 00:00:02,200" in subtitles
    assert "السلام علیکم!" in subtitles
    assert "00:00:33,000 --> 00:00:33,200" in subtitles


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

@pytest.mark.parametrize("start_seconds", [1.0, 0.9])
def test_rejects_dialogue_that_runs_past_its_scene_boundary(tmp_path, start_seconds):
    plan = {
        "language": "ur",
        "characters": [{"id": "ali", "voice_profile": DEFAULT_URDU_VOICE}],
        "scenes": [
            {
                "id": "short-scene",
                "duration_seconds": 1,
                "dialogue": [
                    {
                        "character_id": "ali",
                        "text": "یہ ایک ٹیسٹ ہے۔",
                        "start_seconds": start_seconds,
                        "duration_seconds": 0.1,
                    }
                ],
            }
        ],
    }
    with pytest.raises(SpeechGenerationError, match="outside its duration|scene boundary"):
        generate_episode_audio(
            plan,
            tmp_path / "audio",
            tmp_path / "data",
            synthesizer=FakeSynthesizer(),
        )


def _subtitle_plan(subtitle_mode, subtitle_text="", text="السلام علیکم!"):
    return {
        "language": "ur",
        "subtitle_mode": subtitle_mode,
        "characters": [{"id": "ali", "voice_profile": DEFAULT_URDU_VOICE}],
        "scenes": [
            {
                "id": "market",
                "duration_seconds": 30,
                "dialogue": [
                    {
                        "character_id": "ali",
                        "text": text,
                        "subtitle_text": subtitle_text,
                        "start_seconds": 2,
                        "duration_seconds": 2,
                    }
                ],
            }
        ],
    }


def test_subtitle_mode_urdu_writes_the_dialogue_text(tmp_path):
    result = generate_episode_audio(
        _subtitle_plan("urdu"),
        tmp_path / "audio",
        tmp_path / "data",
        synthesizer=FakeSynthesizer(),
    )
    assert result["subtitle_mode"] == "urdu"
    assert result["subtitle_entry_count"] == 1
    assert "السلام علیکم!" in Path(result["subtitles_path"]).read_text(encoding="utf-8")


def test_subtitle_mode_roman_urdu_writes_the_planned_subtitle_text(tmp_path):
    result = generate_episode_audio(
        _subtitle_plan("roman_urdu", subtitle_text="Assalam-o-Alaikum!"),
        tmp_path / "audio",
        tmp_path / "data",
        synthesizer=FakeSynthesizer(),
    )
    assert result["subtitle_mode"] == "roman_urdu"
    assert result["subtitle_entry_count"] == 1
    subtitles = Path(result["subtitles_path"]).read_text(encoding="utf-8")
    assert "Assalam-o-Alaikum!" in subtitles
    assert "السلام علیکم!" not in subtitles


def test_subtitle_mode_none_writes_no_entries(tmp_path):
    result = generate_episode_audio(
        _subtitle_plan("none"),
        tmp_path / "audio",
        tmp_path / "data",
        synthesizer=FakeSynthesizer(),
    )
    assert result["subtitle_mode"] == "none"
    assert result["subtitle_entry_count"] == 0
    # The file still exists so the render step keeps a stable input list.
    assert Path(result["subtitles_path"]).read_text(encoding="utf-8") == ""


def test_roman_urdu_rejects_a_line_without_subtitle_text(tmp_path):
    with pytest.raises(SpeechGenerationError, match="no subtitle_text"):
        generate_episode_audio(
            _subtitle_plan("roman_urdu"),
            tmp_path / "audio",
            tmp_path / "data",
            synthesizer=FakeSynthesizer(),
        )


def test_rejects_unknown_subtitle_mode(tmp_path):
    with pytest.raises(SpeechGenerationError, match="Unsupported subtitle_mode"):
        generate_episode_audio(
            _subtitle_plan("klingon"),
            tmp_path / "audio",
            tmp_path / "data",
            synthesizer=FakeSynthesizer(),
        )
