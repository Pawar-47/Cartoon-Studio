from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main


def test_episode_render_endpoint_persists_and_serves_mp4(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "render-api.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    client = TestClient(main.app)
    project_response = client.post("/api/projects", json={"name": "Render Project"})
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]
    episode_id = "episode-render-test"
    scene_relative = f"assets/episodes/{episode_id}/scenes/scene-01.tscn"
    audio_relative = f"assets/episodes/{episode_id}/audio/dialogue_mix.wav"
    subtitles_relative = f"assets/episodes/{episode_id}/audio/subtitles.srt"
    for relative, content in (
        (scene_relative, '[gd_scene format=3]\\n'),
        (audio_relative, "wav-placeholder"),
        (subtitles_relative, "subtitle-placeholder"),
    ):
        path = main.resolve_project_relative(tmp_path, project_id, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    manifests = {
        "episode_production": {
            "data": {
                "episode_id": episode_id,
                "scenes": [{"scene_relative_path": scene_relative, "duration_seconds": 1}],
            }
        },
        "episode_audio": {
            "data": {
                "episode_id": episode_id,
                "audio_relative_path": audio_relative,
                "subtitles_relative_path": subtitles_relative,
                "clips": [],
            }
        },
    }
    monkeypatch.setattr(
        main,
        "get_story_plan",
        lambda _: {"episode_id": episode_id, "plan": {"title": "Render Test"}},
    )
    monkeypatch.setattr(
        main,
        "_latest_episode_manifest",
        lambda _project_id, document_type, _episode_id: manifests.get(document_type),
    )

    def fake_render(
        scene_paths,
        scene_durations,
        audio_path,
        subtitles_path,
        output_path,
        project_root,
        godot_executable,
        **options,
    ):
        assert len(scene_paths) == 1
        assert scene_durations == [1]
        assert audio_path.is_file() and subtitles_path.is_file()
        assert project_root == main.project_directory(tmp_path, project_id)
        assert godot_executable == tmp_path / "Godot.exe"
        # A new project uses the balanced preset: 24 fps at 1280x720 with subtitles.
        assert {
            key: value
            for key, value in options.items()
            if key not in ("progress_callback", "cancel_check")
        } == {
            "fps": 24,
            "width": 1280,
            "height": 720,
            "include_subtitles": True,
            "cache_directory": main.resolve_project_relative(
                tmp_path,
                project_id,
                f"assets/episodes/{episode_id}/render_cache",
            ),
        }
        assert callable(options["progress_callback"])
        assert callable(options["cancel_check"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"verified-mp4-test")
        return {
            "video_path": str(output_path),
            "duration_seconds": 1,
            "fps": options["fps"],
            "width": options["width"],
            "height": options["height"],
            "size_bytes": len(b"verified-mp4-test"),
            "rendered_at_elapsed_seconds": 0.01,
        }

    monkeypatch.setattr(main, "render_episode_video", fake_render)
    monkeypatch.setattr(
        main,
        "get_engine_adapter",
        lambda: SimpleNamespace(executable=tmp_path / "Godot.exe"),
    )

    rendered = client.post(f"/api/projects/{project_id}/story/render")
    assert rendered.status_code == 200, rendered.text
    payload = rendered.json()
    assert payload["duration_seconds"] == 1
    assert payload["video_url"].endswith(f"/{payload['build_id']}/mp4")

    download = client.get(payload["video_url"])
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("video/mp4")
    assert download.content == b"verified-mp4-test"
