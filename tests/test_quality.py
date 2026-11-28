from fastapi.testclient import TestClient

from app import main
from app.quality import (
    DEFAULT_QUALITY_PRESET,
    QUALITY_PRESETS,
    quality_summary,
    resolve_quality_profile,
)

client = TestClient(main.app)


def test_every_preset_is_valid_and_distinct() -> None:
    assert list(QUALITY_PRESETS) == [
        "preview",
        "low_hardware",
        "balanced",
        "high_quality",
    ]
    sizes = {(profile.fps, profile.width, profile.height) for profile in QUALITY_PRESETS.values()}
    assert len(sizes) == len(QUALITY_PRESETS)
    for profile in QUALITY_PRESETS.values():
        assert profile.fps in {12, 15, 20, 24, 25, 30}
        assert profile.width >= 640 and profile.height >= 360
        assert profile.width % 2 == 0 and profile.height % 2 == 0


def test_unknown_preset_falls_back_to_the_default() -> None:
    assert DEFAULT_QUALITY_PRESET == "balanced"
    assert resolve_quality_profile("preview").fps == 15
    fallback = resolve_quality_profile("cinematic-ultra")
    assert fallback.name == DEFAULT_QUALITY_PRESET
    assert resolve_quality_profile(None).name == DEFAULT_QUALITY_PRESET


def test_quality_summary_marks_one_default() -> None:
    summary = quality_summary()
    assert [item["name"] for item in summary] == list(QUALITY_PRESETS)
    assert [item["name"] for item in summary if item["default"]] == [DEFAULT_QUALITY_PRESET]


def test_project_settings_default_to_balanced(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "settings.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "Preset Project"})
    project_id = project.json()["id"]

    settings = client.get(f"/api/projects/{project_id}/settings")
    assert settings.status_code == 200
    body = settings.json()
    assert body["settings"]["quality_preset"] == "balanced"
    assert body["quality"]["fps"] == 24
    assert body["quality"]["width"] == 1280
    assert body["quality"]["height"] == 720
    # The stored frame rate and resolution are the preset's, not a second truth.
    assert body["settings"]["frame_rate"] == {"numerator": 24, "denominator": 1}
    assert body["settings"]["resolution"] == {"width": 1280, "height": 720}


def test_changing_the_preset_updates_the_project_document(tmp_path, monkeypatch):
    import json

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "settings-update.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "Preview Project"})
    project_id = project.json()["id"]

    updated = client.put(
        f"/api/projects/{project_id}/settings", json={"quality_preset": "preview"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["quality"] == {
        "name": "preview",
        "label": "Preview",
        "fps": 15,
        "width": 640,
        "height": 360,
        "note": "Fastest draft on the target laptop: 15 fps at 640x360.",
    }
    document = json.loads(
        (tmp_path / "projects" / project_id / "project.json").read_text(encoding="utf-8")
    )
    assert document["data"]["settings"]["quality_preset"] == "preview"
    assert document["data"]["settings"]["frame_rate"] == {"numerator": 15, "denominator": 1}
    assert document["data"]["settings"]["resolution"] == {"width": 640, "height": 360}
    assert document["revision"] == 2

    assert client.put(
        f"/api/projects/{project_id}/settings", json={"quality_preset": "ultra"}
    ).status_code == 422


def test_project_settings_reject_unknown_project(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "settings-missing.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    missing = "0" * 36
    assert client.get(f"/api/projects/{missing}/settings").status_code == 404
    assert client.put(
        f"/api/projects/{missing}/settings", json={"quality_preset": "balanced"}
    ).status_code == 404
