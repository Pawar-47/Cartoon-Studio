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
                "location_id": "market-street",
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
