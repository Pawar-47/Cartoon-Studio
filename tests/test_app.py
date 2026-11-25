import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def valid_episode_plan():
    return {
        "title": "Market Mix-up",
        "synopsis": "Two friends misunderstand a shopkeeper and fix the confusion.",
        "language": "ur",
        "target_duration_seconds": 300,
        "characters": [{"id": "ali", "name": "Ali"}, {"id": "bilu", "name": "Bilu"}],
        "scenes": [
            {
                "id": f"scene-{number}",
                "title": f"Scene {number}",
                "location_id": "street-cafe",
                "duration_seconds": 60,
                "character_ids": ["ali", "bilu"],
                "dialogue": [
                    {
                        "character_id": "ali",
                        "text": "السلام علیکم، یہ کتنے کا ہے؟",
                        "start_seconds": 2,
                        "duration_seconds": 3,
                    }
                ],
                "actions": [
                    {
                        "character_id": "bilu",
                        "action_id": "walk",
                        "start_seconds": 5,
                        "duration_seconds": 4,
                    }
                ],
                "camera": [
                    {
                        "shot": "wide",
                        "movement": "locked",
                        "start_seconds": 0,
                        "duration_seconds": 10,
                    }
                ],
                "audio": [],
            }
            for number in range(1, 6)
        ],
    }


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_story_builder_is_served():
    response = client.get("/story")
    assert response.status_code == 200
    assert "Story Generator" in response.text


def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Cartoon Studio" in response.text


def test_project_create_and_list(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    created = client.post(
        "/api/projects",
        json={"name": "Test Cartoon", "description": "First local project"},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Test Cartoon"
    listed = client.get("/api/projects")
    assert listed.status_code == 200
    assert any(item["name"] == "Test Cartoon" for item in listed.json())


def test_story_prompt_builder_returns_schema():
    response = client.post(
        "/api/story-prompts",
        json={
            "idea": "Two friends visit a busy market and cause a funny mix-up.",
            "language": "ur",
            "target_duration_seconds": 360,
            "character_names": ["Ali", "Bilu"],
        },
    )
    assert response.status_code == 200
    assert "Pakistani Urdu" in response.json()["prompt"]
    assert "walk" in response.json()["prompt"]
    assert "street-cafe" in response.json()["prompt"]
    assert "properties" in response.json()["schema"]


def test_story_plan_validation_and_persistence(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "story-test.sqlite3")
    project = client.post("/api/projects", json={"name": "Story Project"})
    project_id = project.json()["id"]
    plan = valid_episode_plan()
    validated = client.post("/api/story-plans/validate", json=plan)
    assert validated.status_code == 200
    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200
    loaded = client.get(f"/api/projects/{project_id}/story")
    assert loaded.status_code == 200
    assert loaded.json()["plan"]["title"] == "Market Mix-up"


def test_story_plan_rejects_duration_outside_episode_window():
    plan = valid_episode_plan()
    plan["scenes"] = plan["scenes"][:4]
    response = client.post("/api/story-plans/validate", json=plan)
    assert response.status_code == 422


def test_seven_scene_episode_is_supported():
    plan = valid_episode_plan()
    plan["scenes"].append({**plan["scenes"][-1], "id": "scene-6"})
    plan["scenes"].append({**plan["scenes"][-1], "id": "scene-7"})
    plan["target_duration_seconds"] = 420
    response = client.post("/api/story-plans/validate", json=plan)
    assert response.status_code == 200
    assert len(response.json()["scenes"]) == 7


def test_story_plan_rejects_more_than_seven_scenes():
    plan = valid_episode_plan()
    for number in range(6, 9):
        plan["scenes"].append({**plan["scenes"][-1], "id": f"scene-{number}"})
    plan["target_duration_seconds"] = 420
    response = client.post("/api/story-plans/validate", json=plan)
    assert response.status_code == 422


def test_story_plan_rejects_unknown_animation_clip():
    plan = valid_episode_plan()
    plan["scenes"][0]["actions"][0]["action_id"] = "made_up_animation"
    response = client.post("/api/story-plans/validate", json=plan)
    assert response.status_code == 422


def test_story_plan_rejects_unknown_location_id():
    plan = valid_episode_plan()
    plan["scenes"][0]["location_id"] = "imaginary-market"
    response = client.post("/api/story-plans/validate", json=plan)
    assert response.status_code == 422


def test_story_plan_rejects_unknown_expression():
    plan = valid_episode_plan()
    plan["scenes"][0]["actions"][0]["expression"] = "excited"
    response = client.post("/api/story-plans/validate", json=plan)
    assert response.status_code == 422


def test_project_document_is_portable_and_versioned(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "portable.sqlite3")
    created = client.post("/api/projects", json={"name": "Portable Project"})
    project_id = created.json()["id"]

    opened = client.get(f"/api/projects/{project_id}")
    assert opened.status_code == 200
    document = opened.json()["document"]
    assert document["schema_version"] == "1.0.0"
    assert document["document_type"] == "project"
    assert document["id"] == project_id
    assert document["revision"] == 1
    assert document["data"]["settings"]["frame_rate"] == {"numerator": 24, "denominator": 1}
    assert (tmp_path / "projects" / project_id / "project.json").exists()


def test_project_update_increments_document_revision(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "update.sqlite3")
    created = client.post("/api/projects", json={"name": "Before"})
    project_id = created.json()["id"]

    updated = client.put(
        f"/api/projects/{project_id}",
        json={"name": "After", "description": "Updated description"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "After"
    opened = client.get(f"/api/projects/{project_id}")
    assert opened.json()["document"]["revision"] == 2
    assert opened.json()["document"]["data"]["description"] == "Updated description"


def test_story_plan_is_saved_as_portable_episode_document(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "episode.sqlite3")
    project = client.post("/api/projects", json={"name": "Episode Project"})
    project_id = project.json()["id"]
    plan = valid_episode_plan()

    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200
    episode_id = saved.json()["episode_id"]
    episode_path = tmp_path / "projects" / project_id / "episodes" / f"{episode_id}.json"
    assert episode_path.exists()

    document = json.loads(episode_path.read_text(encoding="utf-8"))
    assert document["document_type"] == "episode"
    assert document["revision"] == 1
    assert document["data"]["title"] == "Market Mix-up"
    project_document = json.loads((tmp_path / "projects" / project_id / "project.json").read_text(encoding="utf-8"))
    assert episode_id in project_document["data"]["references"]["episodes"]

    reopened = client.get(f"/api/projects/{project_id}/story")
    assert reopened.status_code == 200
    assert reopened.json()["episode_id"] == episode_id
    assert reopened.json()["plan"]["title"] == "Market Mix-up"

    with main.connect_db() as connection:
        connection.execute("DELETE FROM story_plans WHERE project_id = ?", (project_id,))
    main._INITIALIZED_DB_KEY = None
    main.initialize_database()
    recovered = client.get(f"/api/projects/{project_id}/story")
    assert recovered.status_code == 200
    assert recovered.json()["plan"]["title"] == "Market Mix-up"


def test_legacy_database_migrates_and_preserves_project_and_story(tmp_path, monkeypatch):
    import json
    import sqlite3
    from app import main

    db_path = tmp_path / "legacy.sqlite3"
    now = "2026-01-01T00:00:00+00:00"
    project_id = "00000000-0000-4000-8000-000000000001"
    plan = valid_episode_plan()
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE story_plans (
                project_id TEXT PRIMARY KEY, plan_json TEXT NOT NULL, updated_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id)
            )
            """
        )
        connection.execute(
            "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, "Legacy Project", "", now, now, "{}"),
        )
        connection.execute(
            "INSERT INTO story_plans VALUES (?, ?, ?)",
            (project_id, json.dumps(plan, ensure_ascii=False), now),
        )

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", db_path)
    main._INITIALIZED_DB_KEY = None
    main.initialize_database()

    with main.connect_db() as connection:
        versions = connection.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()[0]
        preserved = connection.execute(
            "SELECT name FROM projects WHERE id = ?", (project_id,)
        ).fetchone()[0]
        migrated_story = connection.execute(
            "SELECT plan_json FROM story_plans WHERE project_id = ?", (project_id,)
        ).fetchone()[0]
    assert versions == 2
    assert preserved == "Legacy Project"
    assert json.loads(migrated_story)["title"] == "Market Mix-up"
    project_file = tmp_path / "projects" / project_id / "project.json"
    assert project_file.exists()
    episode_files = list((tmp_path / "projects" / project_id / "episodes").glob("*.json"))
    assert len(episode_files) == 1
    backups = list((tmp_path / "backups").glob("pre-migration-*.sqlite3"))
    assert backups
