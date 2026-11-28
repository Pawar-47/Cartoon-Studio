import io
import json
import uuid

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


def test_status_endpoint_reports_current_character_studio_milestone(
    tmp_path, monkeypatch
):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "status.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)

    response = client.get("/api/status")
    assert response.status_code == 200
    milestone = response.json()["next_milestone"].lower()
    assert "visual acceptance" in milestone
    assert "face/hair geometry authoring" in milestone



def test_world_builder_is_served():
    response = client.get("/worlds")
    assert response.status_code == 200
    assert "World Builder" in response.text


def test_world_layout_create_edit_and_portable_reopen(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "worlds.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Town Project"})
    project_id = project.json()["id"]
    payload = {
        "name": "Sunny Town",
        "theme": "small_town",
        "ground_color": "#789b58",
        "sky": "day",
        "objects": [
            {
                "id": "road-main",
                "kind": "road",
                "label": "Main Road",
                "x": 50,
                "y": 50,
                "width": 70,
                "height": 10,
                "rotation": 0,
                "color": "#55585c",
            },
            {
                "id": "shop-1",
                "kind": "shop",
                "label": "Corner Shop",
                "x": 25,
                "y": 25,
                "width": 14,
                "height": 12,
                "rotation": 0,
                "color": "#d9a15b",
            },
        ],
    }
    created = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert created.status_code == 201
    world_id = created.json()["id"]
    world_path = tmp_path / "projects" / project_id / "worlds" / f"{world_id}.json"
    document = json.loads(world_path.read_text(encoding="utf-8"))
    assert document["document_type"] == "world"
    assert document["data"]["objects"][0]["kind"] == "road"
    project_doc = json.loads(
        (tmp_path / "projects" / project_id / "project.json").read_text(encoding="utf-8")
    )
    assert world_id in project_doc["data"]["references"]["worlds"]

    changed = {**payload, "name": "Sunny Town v2", "sky": "sunset"}
    updated = client.put(
        f"/api/projects/{project_id}/worlds/{world_id}", json=changed
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["name"] == "Sunny Town v2"
    assert reopened.json()["sky"] == "sunset"
    assert len(client.get(f"/api/projects/{project_id}/worlds").json()) == 1



def test_world_asset_selection_survives_save_reopen_and_update(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-assets.sqlite3")
    main._INITIALIZED_DB_KEY = None

    def fake_install(project_root, asset_id):
        assert asset_id == "road-straight"
        relative_path = "assets/world-library/road-straight.glb"
        target = project_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"glTF-test-fixture")
        return {
            "id": asset_id,
            "name": "Road Straight",
            "relative_path": relative_path,
            "cached": False,
            "license": "CC0-1.0",
        }

    monkeypatch.setattr(main, "install_world_asset", fake_install)
    project = client.post("/api/projects", json={"name": "Asset World"})
    assert project.status_code == 201
    project_id = project.json()["id"]
    payload = {
        "name": "Asset Town",
        "objects": [{
            "id": "road-1",
            "kind": "road",
            "label": "Main Road",
            "x": 50,
            "y": 50,
            "width": 60,
            "height": 10,
            "asset_id": "road-straight",
            "asset_path": "../../outside.glb",
        }],
    }

    created = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert created.status_code == 201
    world_id = created.json()["id"]
    expected_path = "assets/world-library/road-straight.glb"
    assert created.json()["objects"][0]["asset_id"] == "road-straight"
    assert created.json()["objects"][0]["asset_path"] == expected_path

    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["objects"][0]["asset_path"] == expected_path

    updated = client.put(
        f"/api/projects/{project_id}/worlds/{world_id}", json=payload
    )
    assert updated.status_code == 200
    assert updated.json()["objects"][0]["asset_id"] == "road-straight"
    assert updated.json()["objects"][0]["asset_path"] == expected_path

    saved = json.loads(
        (tmp_path / "projects" / project_id / "worlds" / f"{world_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert saved["data"]["objects"][0]["asset_path"] == expected_path


def test_world_asset_selection_rejects_unknown_and_mismatched_assets(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-assets-invalid.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Invalid Asset World"})
    project_id = project.json()["id"]
    payload = {
        "name": "Invalid Asset Town",
        "objects": [{
            "id": "road-1", "kind": "road", "label": "Road",
            "x": 50, "y": 50, "asset_id": "car-sedan",
        }],
    }
    mismatched = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert mismatched.status_code == 422
    payload["objects"][0]["asset_id"] = "not-in-catalogue"
    unknown = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert unknown.status_code == 422


def test_world_layout_recovers_from_portable_documents_without_old_database(
    tmp_path, monkeypatch
):
    from app import main

    data_dir = tmp_path / "data"
    monkeypatch.setattr(main, "DATA_DIR", data_dir)
    monkeypatch.setattr(main, "DB_PATH", data_dir / "original.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Recovered Town"})
    project_id = project.json()["id"]
    created = client.post(
        f"/api/projects/{project_id}/worlds",
        json={"name": "Old Town", "objects": []},
    )
    assert created.status_code == 201
    world_id = created.json()["id"]

    monkeypatch.setattr(main, "DB_PATH", data_dir / "rebuilt.sqlite3")
    main._INITIALIZED_DB_KEY = None
    recovered = client.get(f"/api/projects/{project_id}/worlds")
    assert recovered.status_code == 200
    assert [world["id"] for world in recovered.json()] == [world_id]
    project_document = json.loads(
        (data_dir / "projects" / project_id / "project.json").read_text(
            encoding="utf-8"
        )
    )
    assert world_id in project_document["data"]["references"]["worlds"]


def test_world_layout_rejects_out_of_bounds_objects_and_unknown_kinds(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-validation.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Validation Project"})
    project_id = project.json()["id"]
    invalid = {
        "name": "Broken Map",
        "objects": [{
            "id": "bad",
            "kind": "spaceship",
            "label": "Unknown",
            "x": 101,
            "y": 50,
        }],
    }
    response = client.post(f"/api/projects/{project_id}/worlds", json=invalid)
    assert response.status_code == 422


def test_world_layout_accepts_civic_and_indoor_object_kinds(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-civic.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Civic Project"})
    project_id = project.json()["id"]
    payload = {
        "name": "Town Center",
        "theme": "small_town",
        "ground_color": "#789b58",
        "sky": "day",
        "objects": [
            {"id": "school-1", "kind": "school", "label": "Elementary School",
             "x": 10, "y": 10, "width": 18, "height": 22, "rotation": 0,
             "color": "#8a9ba8"},
            {"id": "hospital-1", "kind": "hospital", "label": "Clinic",
             "x": 40, "y": 30, "width": 20, "height": 26, "rotation": 0,
             "color": "#e8dcc8"},
            {"id": "office-1", "kind": "office", "label": "Town Hall",
             "x": 70, "y": 50, "width": 16, "height": 20, "rotation": 0,
             "color": "#c8b8a8"},
            {"id": "police-1", "kind": "police_station", "label": "Precinct",
             "x": 85, "y": 15, "width": 14, "height": 18, "rotation": 0,
             "color": "#5a6a7a"},
            {"id": "garage-1", "kind": "garage", "label": "Repair Garage",
             "x": 20, "y": 70, "width": 16, "height": 14, "rotation": 0,
             "color": "#6a5a5a"},
            {"id": "room-1", "kind": "indoor_room", "label": "Back Room",
             "x": 50, "y": 80, "width": 12, "height": 10, "rotation": 0,
             "color": "#e8dcc8"},
            {"id": "play-1", "kind": "playground", "label": "Kids Park",
             "x": 80, "y": 85, "width": 14, "height": 12, "rotation": 0,
             "color": "#7aa85b"},
        ],
    }
    created = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert created.status_code == 201
    world_id = created.json()["id"]
    world_path = tmp_path / "projects" / project_id / "worlds" / f"{world_id}.json"
    document = json.loads(world_path.read_text(encoding="utf-8"))
    assert document["document_type"] == "world"
    kinds = {obj["kind"] for obj in document["data"]["objects"]}
    expected = {"school", "hospital", "office", "police_station", "garage",
                "indoor_room", "playground"}
    assert kinds == expected
    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["revision"] == 1
    assert len(client.get(f"/api/projects/{project_id}/worlds").json()) == 1


def test_world_layout_accepts_environmental_object_kinds(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-environment.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Environment Project"})
    project_id = project.json()["id"]
    payload = {
        "name": "Park Area",
        "theme": "park",
        "ground_color": "#789b58",
        "sky": "day",
        "objects": [
            {"id": "bench-1", "kind": "furniture", "label": "Park Bench",
             "x": 30, "y": 30, "width": 4, "height": 2, "rotation": 0,
             "color": "#5a4a3a"},
            {"id": "pond-1", "kind": "water_body", "label": "Duck Pond",
             "x": 60, "y": 50, "width": 12, "height": 10, "rotation": 0,
             "color": "#5b9bd5"},
            {"id": "light-1", "kind": "streetlight", "label": "Main Street Light",
             "x": 20, "y": 20, "width": 2, "height": 5, "rotation": 0,
             "color": "#444b50"},
        ],
    }
    created = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert created.status_code == 201
    world_id = created.json()["id"]
    world_path = tmp_path / "projects" / project_id / "worlds" / f"{world_id}.json"
    document = json.loads(world_path.read_text(encoding="utf-8"))
    assert document["document_type"] == "world"
    kinds = {obj["kind"] for obj in document["data"]["objects"]}
    assert kinds == {"furniture", "water_body", "streetlight"}
    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["revision"] == 1


def test_world_template_instantiate_from_saved_world(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-template.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Template Project"})
    project_id = project.json()["id"]

    # Create a template world
    template_payload = {
        "name": "Town Square Template",
        "theme": "market",
        "ground_color": "#789b58",
        "sky": "day",
        "objects": [
            {"id": "road-1", "kind": "road", "label": "Main Road",
             "x": 50, "y": 50, "width": 80, "height": 12, "rotation": 0,
             "color": "#4b4d50"},
            {"id": "shop-1", "kind": "shop", "label": "Bakery",
             "x": 30, "y": 40, "width": 18, "height": 16, "rotation": 0,
             "color": "#d9a46b"},
        ],
    }
    template_created = client.post(
        f"/api/projects/{project_id}/worlds", json=template_payload
    )
    assert template_created.status_code == 201
    template_id = template_created.json()["id"]

    # Instantiate a new world from the template
    instance_payload = {
        "name": "Town Square Copy",
        "template_id": template_id,
        "sky": "sunset",
    }
    instance_created = client.post(
        f"/api/projects/{project_id}/worlds", json=instance_payload
    )
    assert instance_created.status_code == 201
    instance_id = instance_created.json()["id"]
    assert instance_id != template_id
    instance_data = instance_created.json()
    assert instance_data["theme"] == "market"
    assert instance_data["sky"] == "sunset"
    assert len(instance_data["objects"]) == 2
    instance_kinds = {obj["kind"] for obj in instance_data["objects"]}
    assert instance_kinds == {"road", "shop"}

    # Both worlds exist independently
    all_worlds = client.get(f"/api/projects/{project_id}/worlds")
    assert len(all_worlds.json()) == 2


def test_world_template_instantiate_rejects_missing_template(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-template-missing.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Missing Template Project"})
    project_id = project.json()["id"]
    payload = {
        "name": "Bad Copy",
        "template_id": "nonexistent-template-id",
    }
    response = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert response.status_code == 404


def test_world_migration_is_noop_at_latest_version():
    from app.storage import LATEST_WORLD_SCHEMA_VERSION, migrate_world_document
    document = {
        "schema_version": LATEST_WORLD_SCHEMA_VERSION,
        "document_type": "world",
        "id": "world-1",
        "revision": 1,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "data": {"name": "Test World", "objects": [{"location_kind": "park"}]},
    }
    migrated = migrate_world_document(document)
    assert migrated["schema_version"] == LATEST_WORLD_SCHEMA_VERSION
    assert migrated["data"]["objects"][0]["location_kind"] == "park"


def test_world_migrates_from_1_0_0_to_1_0_1():
    from app.storage import LATEST_WORLD_SCHEMA_VERSION, migrate_world_document
    document = {
        "schema_version": "1.0.0",
        "document_type": "world",
        "id": "world-1",
        "revision": 1,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "data": {
            "name": "Old World",
            "theme": "small_town",
            "objects": [{"id": "obj-1", "kind": "tree"}],
        },
    }
    migrated = migrate_world_document(document)
    assert migrated["schema_version"] == LATEST_WORLD_SCHEMA_VERSION
    assert migrated["data"]["objects"][0]["location_kind"] == "generic"


def test_world_migration_rejects_unknown_version():
    from app.storage import migrate_world_document
    document = {
        "schema_version": "9.9.9",
        "document_type": "world",
        "id": "world-1",
        "revision": 1,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "data": {"name": "Future World"},
    }
    try:
        migrate_world_document(document)
    except ValueError as error:
        assert "no migration path found" in str(error)
    else:
        raise AssertionError("Expected ValueError for unknown schema version")


def test_story_schema_rejects_english_episodes():
    from pydantic import ValidationError

    from app.story import EpisodePlan

    plan = valid_episode_plan()
    plan["language"] = "en"
    try:
        EpisodePlan.model_validate(plan)
    except ValidationError as error:
        assert "language" in str(error).lower()
    else:
        raise AssertionError("The Urdu-only voice pack must reject an English episode")


def test_story_schema_rejects_unsupported_voice_profile():
    from pydantic import ValidationError

    from app.story import EpisodePlan

    plan = valid_episode_plan()
    plan["characters"][0]["voice_profile"] = "some-hindi-voice"
    try:
        EpisodePlan.model_validate(plan)
    except ValidationError as error:
        assert "voice_profile" in str(error)
    else:
        raise AssertionError("An unsupported voice profile must fail validation")


def test_story_schema_accepts_a_supported_voice_profile():
    from app.audio import VOICE_CATALOG
    from app.story import EpisodePlan

    plan = valid_episode_plan()
    plan["characters"][0]["voice_profile"] = next(iter(VOICE_CATALOG))
    EpisodePlan.model_validate(plan)


def test_roman_urdu_subtitles_require_planned_subtitle_text():
    from pydantic import ValidationError

    from app.story import EpisodePlan

    plan = valid_episode_plan()
    plan["subtitle_mode"] = "roman_urdu"
    try:
        EpisodePlan.model_validate(plan)
    except ValidationError as error:
        assert "subtitle_text" in str(error)
    else:
        raise AssertionError("Roman Urdu subtitles must require subtitle_text")

    for scene in plan["scenes"]:
        for line in scene["dialogue"]:
            line["subtitle_text"] = "Roman subtitle"
    EpisodePlan.model_validate(plan)


def test_world_schema_version_stored_on_create(tmp_path, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-schema.sqlite3")
    main._INITIALIZED_DB_KEY = None
    main.initialize_database()
    project = client.post("/api/projects", json={"name": "Schema Project"})
    project_id = project.json()["id"]
    payload = {"name": "Schema World"}
    created = client.post(f"/api/projects/{project_id}/worlds", json=payload)
    assert created.status_code == 201
    world_path = tmp_path / "projects" / project_id / "worlds" / f"{created.json()['id']}.json"
    document = json.loads(world_path.read_text(encoding="utf-8"))
    assert document["schema_version"] == "1.0.1"


def test_world_create_with_minimal_fields_fills_defaults(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-minimal.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Minimal Project"})
    project_id = project.json()["id"]
    created = client.post(
        f"/api/projects/{project_id}/worlds", json={"name": "Minimal Town"}
    )
    assert created.status_code == 201
    world_id = created.json()["id"]
    assert created.json()["theme"] == "small_town"
    assert created.json()["ground_color"] == "#789b58"
    assert created.json()["sky"] == "day"
    assert created.json()["objects"] == []
    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["theme"] == "small_town"
    assert reopened.json()["ground_color"] == "#789b58"
    assert reopened.json()["sky"] == "day"
    assert reopened.json()["objects"] == []


def test_vehicle_movement_steering_acceleration_braking(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-vehicle.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Vehicle Project"})
    project_id = project.json()["id"]

    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Street Scene",
            "objects": [
                {
                    "id": "car-1",
                    "kind": "vehicle",
                    "label": "Sedan",
                    "x": 50,
                    "y": 50,
                    "width": 12,
                    "height": 8,
                    "rotation": 0,
                    "color": "#477fa8",
                }
            ],
        },
    )
    assert world.status_code == 201
    world_id = world.json()["id"]

    movement = {
        "vehicle_id": "car-1",
        "steering_angle": 15.0,
        "wheel_rotation": 30.0,
        "acceleration": 0.8,
        "braking": 0.0,
        "turn_direction": "right",
        "parking_state": "moving",
    }
    response = client.post(
        f"/api/projects/{project_id}/worlds/{world_id}/vehicles/car-1/movement",
        json=movement,
    )
    assert response.status_code == 200
    data = response.json()
    movement_data = next(
        obj.get("movement", {})
        for obj in data.get("objects", [])
        if obj.get("id") == "car-1"
    )
    assert movement_data["steering_angle"] == 15.0
    assert movement_data["acceleration"] == 0.8
    assert movement_data["turn_direction"] == "right"
    assert movement_data["parking_state"] == "moving"

    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["revision"] == 2


def test_vehicle_interaction_door_and_enter(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-vehicle-interact.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Vehicle Interaction Project"})
    project_id = project.json()["id"]

    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Bus Stop",
            "objects": [
                {
                    "id": "bus-1",
                    "kind": "vehicle",
                    "label": "City Bus",
                    "x": 30,
                    "y": 40,
                    "width": 20,
                    "height": 14,
                    "rotation": 0,
                    "color": "#d9a46b",
                }
            ],
        },
    )
    assert world.status_code == 201
    world_id = world.json()["id"]

    open_door = {
        "vehicle_id": "bus-1",
        "action": "open_door",
        "door_index": 0,
        "character_id": None,
    }
    response = client.post(
        f"/api/projects/{project_id}/worlds/{world_id}/vehicles/bus-1/interaction",
        json=open_door,
    )
    assert response.status_code == 200
    data = response.json()
    interactions = next(
        obj.get("interactions", [])
        for obj in data.get("objects", [])
        if obj.get("id") == "bus-1"
    )
    assert len(interactions) == 1
    assert interactions[0]["action"] == "open_door"
    assert interactions[0]["door_index"] == 0

    enter = {
        "vehicle_id": "bus-1",
        "action": "enter",
        "door_index": 0,
        "character_id": "char-hero",
    }
    response = client.post(
        f"/api/projects/{project_id}/worlds/{world_id}/vehicles/bus-1/interaction",
        json=enter,
    )
    assert response.status_code == 200
    data = response.json()
    interactions = next(
        obj.get("interactions", [])
        for obj in data.get("objects", [])
        if obj.get("id") == "bus-1"
    )
    assert len(interactions) == 2
    assert interactions[1]["action"] == "enter"
    assert interactions[1]["character_id"] == "char-hero"


def test_vehicle_rig_registration(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-vehicle-rig.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Vehicle Rig Project"})
    project_id = project.json()["id"]

    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Fleet Yard",
            "objects": [
                {
                    "id": "truck-1",
                    "kind": "vehicle",
                    "label": "Delivery Truck",
                    "x": 10,
                    "y": 20,
                    "width": 16,
                    "height": 14,
                    "rotation": 0,
                    "color": "#6a5a5a",
                }
            ],
        },
    )
    assert world.status_code == 201
    world_id = world.json()["id"]

    rig = {
        "vehicle_id": "truck-1",
        "vehicle_class": "truck",
        "rig_type": "four_wheel_drive",
    }
    response = client.post(
        f"/api/projects/{project_id}/worlds/{world_id}/vehicles/truck-1/rig",
        json=rig,
    )
    assert response.status_code == 200
    data = response.json()
    rig_data = next(
        obj.get("rig", {})
        for obj in data.get("objects", [])
        if obj.get("id") == "truck-1"
    )
    assert rig_data["vehicle_class"] == "truck"
    assert rig_data["rig_type"] == "four_wheel_drive"

    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["revision"] == 2


def test_vehicle_movement_rejects_non_vehicle_object(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-vehicle-bad.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Bad Vehicle Project"})
    project_id = project.json()["id"]

    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "No Vehicle",
            "objects": [
                {
                    "id": "tree-1",
                    "kind": "tree",
                    "label": "Oak",
                    "x": 50,
                    "y": 50,
                    "width": 10,
                    "height": 12,
                    "rotation": 0,
                    "color": "#4c9850",
                }
            ],
        },
    )
    assert world.status_code == 201
    world_id = world.json()["id"]

    movement = {
        "vehicle_id": "tree-1",
        "steering_angle": 15.0,
    }
    response = client.post(
        f"/api/projects/{project_id}/worlds/{world_id}/vehicles/tree-1/movement",
        json=movement,
    )
    assert response.status_code == 422


def test_vehicle_endpoints_reject_missing_vehicle(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-vehicle-missing.sqlite3")
    main._INITIALIZED_DB_KEY = None
    project = client.post("/api/projects", json={"name": "Missing Vehicle Project"})
    project_id = project.json()["id"]

    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={"name": "No Vehicle Here"},
    )
    assert world.status_code == 201
    world_id = world.json()["id"]

    movement = {
        "vehicle_id": "ghost-1",
        "steering_angle": 15.0,
    }
    response = client.post(
        f"/api/projects/{project_id}/worlds/{world_id}/vehicles/ghost-1/movement",
        json=movement,
    )
    assert response.status_code == 404


def test_story_builder_is_served():
    response = client.get("/story")
    assert response.status_code == 200
    assert "Story Generator" in response.text


def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Cartoon Studio" in response.text
    assert "World Builder foundation" in response.text
    assert "curated CC0 assets and Godot scene export" in response.text
    assert "Pipeline partial" in response.text
    assert "full 5–7 minute acceptance remains" in response.text


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


def test_project_export_returns_zip_package(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "export.sqlite3")
    created = client.post("/api/projects", json={"name": "Exportable Project"})
    project_id = created.json()["id"]

    exported = client.get(f"/api/projects/{project_id}/export")
    assert exported.status_code == 200
    assert exported.headers["content-type"] == "application/zip"
    assert f'filename="project-{project_id}.zip"' in exported.headers.get(
        "content-disposition", ""
    )

    import zipfile

    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        names = archive.namelist()
        assert "project.json" in names
        project_doc = json.loads(archive.read("project.json"))
        assert project_doc["document_type"] == "project"
        assert project_doc["id"] == project_id
        assert project_doc["data"]["name"] == "Exportable Project"


def test_project_import_round_trip(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "import.sqlite3")
    created = client.post(
        "/api/projects", json={"name": "Original", "description": "Original desc"}
    )
    project_id = created.json()["id"]

    # Add a world to the project
    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={"name": "Imported Town", "theme": "small_town"},
    )
    assert world.status_code == 201
    world_id = world.json()["id"]

    # Export the project
    exported = client.get(f"/api/projects/{project_id}/export")
    assert exported.status_code == 200

    # Import into a fresh data directory
    import_tmp = tmp_path / "imported"
    import_tmp.mkdir()
    monkeypatch.setattr(main, "DATA_DIR", import_tmp)
    monkeypatch.setattr(main, "DB_PATH", import_tmp / "imported.sqlite3")

    imported = client.post(
        "/api/projects/import",
        content=exported.content,
        headers={"Content-Type": "application/zip"},
    )
    assert imported.status_code == 201
    new_project_id = imported.json()["id"]
    assert new_project_id != project_id
    assert imported.json()["name"] == "Original"
    assert imported.json()["description"] == "Original desc"

    # Verify the imported project has the world, and that the world document was
    # repointed at the imported project rather than the exporting one.
    imported_worlds = client.get(f"/api/projects/{new_project_id}/worlds")
    assert imported_worlds.status_code == 200
    world_ids = [w["id"] for w in imported_worlds.json()]
    assert world_id in world_ids
    imported_world = client.get(f"/api/projects/{new_project_id}/worlds/{world_id}")
    assert imported_world.status_code == 200
    imported_world_path = (
        import_tmp / "projects" / new_project_id / "worlds" / f"{world_id}.json"
    )
    assert project_id not in imported_world_path.read_text(encoding="utf-8")


def test_project_import_rejects_non_zip(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "badimport.sqlite3")

    response = client.post(
        "/api/projects/import",
        content=b"not a zip file",
        headers={"Content-Type": "application/zip"},
    )
    assert response.status_code == 422


def test_project_import_rejects_missing_project_json(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "badimport2.sqlite3")

    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "hello")
    buffer.seek(0)

    response = client.post(
        "/api/projects/import",
        content=buffer.read(),
        headers={"Content-Type": "application/zip"},
    )
    assert response.status_code == 422
    assert "project.json" in response.json()["detail"]


def test_project_import_rejects_path_traversal(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "badimport3.sqlite3")
    created = client.post("/api/projects", json={"name": "Traversal Project"})
    project_id = created.json()["id"]
    project_root = tmp_path / "projects" / project_id
    project_document = json.loads(
        (project_root / "project.json").read_text(encoding="utf-8")
    )

    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("project.json", json.dumps(project_document))
        archive.writestr("../escaped.txt", "should never be written")
    buffer.seek(0)

    response = client.post(
        "/api/projects/import",
        content=buffer.read(),
        headers={"Content-Type": "application/zip"},
    )
    assert response.status_code == 422
    assert "unsafe path" in response.json()["detail"]
    assert not (tmp_path / "projects" / "escaped.txt").exists()


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
    project_document_path = tmp_path / "projects" / project_id / "project.json"
    project_document = json.loads(project_document_path.read_text(encoding="utf-8"))
    assert episode_id in project_document["data"]["references"]["episodes"]

    second_save = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert second_save.status_code == 200
    assert second_save.json()["episode_id"] == episode_id
    assert second_save.json()["revision"] == 2
    project_document_path = tmp_path / "projects" / project_id / "project.json"
    project_document = json.loads(project_document_path.read_text(encoding="utf-8"))
    assert project_document["revision"] == 3

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
    assert versions == 4
    assert preserved == "Legacy Project"
    assert json.loads(migrated_story)["title"] == "Market Mix-up"
    project_file = tmp_path / "projects" / project_id / "project.json"
    assert project_file.exists()
    episode_files = list((tmp_path / "projects" / project_id / "episodes").glob("*.json"))
    assert len(episode_files) == 1
    backups = list((tmp_path / "backups").glob("pre-migration-*.sqlite3"))
    assert backups


def test_database_index_rebuilds_from_portable_project_and_episode_files(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    db_path = tmp_path / "cartoon_studio.sqlite3"
    monkeypatch.setattr(main, "DB_PATH", db_path)

    created = client.post("/api/projects", json={"name": "Recoverable Project"})
    assert created.status_code == 201
    project_id = created.json()["id"]
    saved = client.put(f"/api/projects/{project_id}/story", json=valid_episode_plan())
    assert saved.status_code == 200
    episode_id = saved.json()["episode_id"]

    assert (tmp_path / "projects" / project_id / "project.json").exists()
    assert (tmp_path / "projects" / project_id / "episodes" / f"{episode_id}.json").exists()

    # Portable files are the recovery source; remove only the rebuildable SQLite index.
    for suffix in ("-wal", "-shm"):
        (tmp_path / f"cartoon_studio.sqlite3{suffix}").unlink(missing_ok=True)
    db_path.unlink()
    main._INITIALIZED_DB_KEY = None
    main.initialize_database()

    opened = client.get(f"/api/projects/{project_id}")
    recovered_story = client.get(f"/api/projects/{project_id}/story")
    assert opened.status_code == 200
    assert opened.json()["project"]["name"] == "Recoverable Project"
    assert recovered_story.status_code == 200
    assert recovered_story.json()["episode_id"] == episode_id
    assert recovered_story.json()["plan"]["title"] == "Market Mix-up"

    with main.connect_db() as connection:
        assert connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM project_documents").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM story_plans").fetchone()[0] == 1


def test_world_job_endpoints_report_and_cancel_queued_work(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "jobs.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    monkeypatch.setattr(main, "_JOB_QUEUE", None)
    monkeypatch.setattr(main, "_JOB_QUEUE_KEY", None)
    project = client.post("/api/projects", json={"name": "Job Project"})
    project_id = project.json()["id"]
    other_project = client.post("/api/projects", json={"name": "Other Jobs"})

    queue = main.get_job_queue()
    job_id = queue.enqueue(project_id, "episode_production", total_units=1)

    listed = client.get(f"/api/projects/{project_id}/jobs")
    assert listed.status_code == 200
    assert [job["job_id"] for job in listed.json()["jobs"]] == [job_id]

    opened = client.get(f"/api/projects/{project_id}/jobs/{job_id}")
    assert opened.status_code == 200
    assert opened.json()["state"] == "queued"
    assert opened.json()["events"][0]["event_type"] == "job_queued"

    # A job is not visible through another project.
    assert client.get(
        f"/api/projects/{other_project.json()['id']}/jobs/{job_id}"
    ).status_code == 404

    cancelled = client.post(f"/api/projects/{project_id}/jobs/{job_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"
    assert cancelled.json()["cancel_requested"] is True

    # Cancelling an already-cancelled job is a no-op that still reports the truth.
    again = client.post(f"/api/projects/{project_id}/jobs/{job_id}/cancel")
    assert again.status_code == 200
    assert again.json()["state"] == "cancelled"

    assert client.get(
        f"/api/projects/{project_id}/jobs/00000000-0000-0000-0000-000000000000"
    ).status_code == 404


def test_job_list_rejects_unknown_project(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "jobs-missing.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    missing = "0" * 36
    assert client.get(f"/api/projects/{missing}/jobs").status_code == 404


def test_world_object_defaults_survive_create_and_update(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "world-defaults.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "World Defaults"})
    project_id = project.json()["id"]
    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Defaults Town",
            "objects": [
                {"id": "obj-1", "kind": "tree", "label": "Tree", "x": 4, "y": 6},
            ],
        },
    )
    assert world.status_code == 201
    # A freshly created world carries the same object defaults as a migrated one.
    assert world.json()["objects"][0]["location_kind"] == "generic"

    world_id = world.json()["id"]
    updated = client.put(
        f"/api/projects/{project_id}/worlds/{world_id}",
        json={
            "name": "Defaults Town Updated",
            "objects": [
                {"id": "obj-1", "kind": "tree", "label": "Tree", "x": 5, "y": 7},
            ],
        },
    )
    assert updated.status_code == 200
    reopened = client.get(f"/api/projects/{project_id}/worlds/{world_id}")
    assert reopened.status_code == 200
    assert reopened.json()["objects"][0]["location_kind"] == "generic"
    document = json.loads(
        (tmp_path / "projects" / project_id / "worlds" / f"{world_id}.json").read_text(
            encoding="utf-8"
        )
    )
    assert document["schema_version"] == "1.0.1"
    assert document["data"]["objects"][0]["location_kind"] == "generic"


def test_episode_can_be_bound_to_an_exported_world_in_its_project(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "episode-world.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "World Episode"})
    project_id = project.json()["id"]
    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Market Town",
            "theme": "market",
            "ground_color": "#789b58",
            "sky": "day",
            "objects": [],
        },
    )
    assert world.status_code == 201

    class FakeWorldExporter:
        def export_world_scene(self, world_data, output_path, allowed_root, **kwargs):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '[gd_scene format=3]\\n[node name="CartoonWorld" type="Node3D"]\\n',
                encoding="utf-8",
            )
            output_path.with_suffix(".glb").write_bytes(b"glTF-preview")
            return {
                "ok": True,
                "object_count": 0,
                "scene_reopened": True,
                "lighting_preset": "day",
            }

    monkeypatch.setattr(main, "get_engine_adapter", FakeWorldExporter)
    exported = client.post(
        f"/api/projects/{project_id}/worlds/{world.json()['id']}/export"
    )
    assert exported.status_code == 200

    plan = valid_episode_plan()
    plan["world_id"] = world.json()["id"]
    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200
    assert saved.json()["plan"]["world_id"] == world.json()["id"]
    reopened = client.get(f"/api/projects/{project_id}/story")
    assert reopened.json()["plan"]["world_id"] == world.json()["id"]


def test_episode_rejects_unexported_or_foreign_world_reference(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "episode-world-invalid.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "Episode Project"})
    other_project = client.post("/api/projects", json={"name": "Other Project"})
    project_id = project.json()["id"]
    foreign_world = client.post(
        f"/api/projects/{other_project.json()['id']}/worlds",
        json={
            "name": "Foreign Town",
            "theme": "small_town",
            "ground_color": "#789b58",
            "sky": "day",
            "objects": [],
        },
    )
    plan = valid_episode_plan()
    plan["world_id"] = foreign_world.json()["id"]
    rejected = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert rejected.status_code == 422

    local_world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Unexported Town",
            "theme": "small_town",
            "ground_color": "#789b58",
            "sky": "day",
            "objects": [],
        },
    )
    plan["world_id"] = local_world.json()["id"]
    rejected = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert rejected.status_code == 422



def test_episode_character_assets_are_project_scoped_and_require_a_rig(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "character-binding.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "Character Binding"})
    project_id = project.json()["id"]
    other = client.post("/api/projects", json={"name": "Other Character Project"})

    def register_asset(owner_id, rig_ready):
        now = "2026-11-26T00:00:00+00:00"
        asset_id = str(uuid.uuid4())
        relative = f"assets/characters/{asset_id}.glb"
        asset_path = main.resolve_project_relative(main.DATA_DIR, owner_id, relative)
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_bytes(b"test-glb")
        data = {
            "original_filename": "Ali.glb",
            "relative_path": relative,
            "rig_ready": rig_ready,
            "animation_ready": False,
        }
        manifest = main.make_envelope("character_asset", asset_id, data, now, now)
        manifest_path = main.resolve_project_relative(
            main.DATA_DIR, owner_id, f"assets/characters/{asset_id}.json"
        )
        digest = main.write_json_atomic(manifest_path, manifest)
        with main.connect_db() as connection:
            main.upsert_document_index(
                connection, owner_id, manifest,
                f"assets/characters/{asset_id}.json", digest,
            )
        return asset_id

    rigged_asset = register_asset(project_id, True)
    static_asset = register_asset(project_id, False)
    foreign_asset = register_asset(other.json()["id"], True)

    listed = client.get(f"/api/projects/{project_id}/character-assets")
    assert listed.status_code == 200
    assert {item["asset_id"] for item in listed.json()} == {
        rigged_asset, static_asset
    }

    plan = valid_episode_plan()
    plan["characters"][0]["asset_id"] = rigged_asset
    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200
    assert saved.json()["plan"]["characters"][0]["asset_id"] == rigged_asset

    plan["characters"][0]["asset_id"] = static_asset
    rejected_static = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert rejected_static.status_code == 422

    plan["characters"][0]["asset_id"] = foreign_asset
    rejected_foreign = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert rejected_foreign.status_code == 422


def test_episode_production_endpoint_persists_scene_build_manifest(tmp_path, monkeypatch):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "episode-production.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    project = client.post("/api/projects", json={"name": "Production Project"})
    project_id = project.json()["id"]
    world = client.post(
        f"/api/projects/{project_id}/worlds",
        json={
            "name": "Town",
            "theme": "small_town",
            "ground_color": "#789b58",
            "sky": "day",
            "objects": [],
        },
    )

    class FakeWorldExporter:
        def export_world_scene(self, world_data, output_path, allowed_root, **kwargs):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                '[gd_scene format=3]\\n[node name="CartoonWorld" type="Node3D"]\\n',
                encoding="utf-8",
            )
            output_path.with_suffix(".glb").write_bytes(b"glTF-preview")
            return {"ok": True, "object_count": 0, "scene_reopened": True}

        def export_episode_scenes(
            self, episode, world_scene_path, character_assets, output_directory,
            allowed_root, **kwargs
        ):
            output_directory.mkdir(parents=True, exist_ok=True)
            scenes = []
            for scene in episode["scenes"]:
                tscn = output_directory / f"{scene['id']}.tscn"
                glb = output_directory / f"{scene['id']}.glb"
                tscn.write_text('[gd_scene format=3]\\n', encoding="utf-8")
                glb.write_bytes(b"glTF-preview")
                scenes.append({
                    "scene_id": scene["id"],
                    "title": scene["title"],
                    "duration_seconds": scene["duration_seconds"],
                    "character_count": len(scene["character_ids"]),
                    "dialogue_line_count": len(scene["dialogue"]),
                    "action_cue_count": len(scene["actions"]),
                    "scene_path": str(tscn),
                    "preview_path": str(glb),
                    "scene_reopened": True,
                    "reopened_character_count": len(scene["character_ids"]),
                })
            return {"ok": True, "scene_count": len(scenes), "scenes": scenes}

    monkeypatch.setattr(main, "get_engine_adapter", FakeWorldExporter)
    world_export = client.post(
        f"/api/projects/{project_id}/worlds/{world.json()['id']}/export"
    )
    assert world_export.status_code == 200

    now = "2026-11-26T00:00:00+00:00"

    def register_asset(filename):
        asset_id = str(uuid.uuid4())
        relative = f"assets/characters/{asset_id}.glb"
        asset_path = main.resolve_project_relative(main.DATA_DIR, project_id, relative)
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_bytes(b"test-glb")
        asset_data = {
            "original_filename": filename,
            "relative_path": relative,
            "rig_ready": True,
            "animation_ready": True,
        }
        asset_doc = main.make_envelope(
            "character_asset", asset_id, asset_data, now, now
        )
        asset_manifest = main.resolve_project_relative(
            main.DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
        )
        digest = main.write_json_atomic(asset_manifest, asset_doc)
        with main.connect_db() as connection:
            main.upsert_document_index(
                connection, project_id, asset_doc,
                f"assets/characters/{asset_id}.json", digest,
            )
        return asset_id

    ali_asset_id = register_asset("Ali.glb")
    bilu_asset_id = register_asset("Bilu.glb")
    plan = valid_episode_plan()
    plan["world_id"] = world.json()["id"]
    plan["characters"][0]["asset_id"] = ali_asset_id
    plan["characters"][1]["asset_id"] = bilu_asset_id
    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200

    generated = client.post(f"/api/projects/{project_id}/story/production")
    assert generated.status_code == 200, generated.text
    assert generated.json()["scene_count"] == 5
    assert generated.json()["total_duration_seconds"] == 300
    reopened = client.get(f"/api/projects/{project_id}/story/production")
    assert reopened.status_code == 200
    assert reopened.json()["build_id"] == generated.json()["build_id"]
    scene_id = generated.json()["scenes"][0]["scene_id"]
    download = client.get(
        f"/api/projects/{project_id}/story/production/"
        f"{generated.json()['build_id']}/scenes/{scene_id}/glb"
    )
    assert download.status_code == 200



def test_episode_audio_endpoint_saves_and_serves_the_dialogue_mix(
    tmp_path, monkeypatch
):
    from app import main

    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "audio.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)

    project_response = client.post(
        "/api/projects", json={"name": "Urdu Audio Project"}
    )
    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    plan = valid_episode_plan()
    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200

    def fake_audio_builder(episode, output_directory, data_dir):
        output_directory.mkdir(parents=True, exist_ok=True)
        audio_path = output_directory / "dialogue_mix.wav"
        audio_path.write_bytes(b"RIFF-cartoon-studio-test")
        subtitles_path = output_directory / "subtitles.srt"
        subtitles_path.write_text(
            "1\n00:00:02,000 --> 00:00:03,000\nالسلام علیکم!\n",
            encoding="utf-8",
        )
        clip_path = output_directory / "clips" / "scene-01-line-01.wav"
        clip_path.parent.mkdir(parents=True, exist_ok=True)
        clip_path.write_bytes(b"RIFF-test-clip")
        return {
            "audio_path": str(audio_path),
            "subtitles_path": str(subtitles_path),
            "sample_rate": 22050,
            "duration_seconds": 300,
            "dialogue_line_count": 5,
            "subtitle_mode": "urdu",
            "subtitle_entry_count": 1,
            "voices": ["ur_PK-fasih-medium"],
            "clips": [
                {
                    "scene_id": "scene-1",
                    "character_id": "ali",
                    "text": "السلام علیکم، یہ کتنے کا ہے؟",
                    "voice_id": "ur_PK-fasih-medium",
                    "start_seconds": 2.0,
                    "timeline_start_seconds": 2.0,
                    "duration_seconds": 1.0,
                    "relative_path": "clips/scene-01-line-01.wav",
                }
            ],
        }

    monkeypatch.setattr(main, "generate_episode_audio", fake_audio_builder)
    generated = client.post(f"/api/projects/{project_id}/story/audio")
    assert generated.status_code == 200
    payload = generated.json()
    assert payload["dialogue_line_count"] == 5
    assert payload["subtitle_mode"] == "urdu"
    assert payload["audio_relative_path"].endswith("/dialogue_mix.wav")
    assert payload["clips"][0]["relative_path"].endswith(
        "/clips/scene-01-line-01.wav"
    )

    downloaded = client.get(payload["audio_url"])
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("audio/wav")
    assert downloaded.content == b"RIFF-cartoon-studio-test"
    subtitles = client.get(
        f"/api/projects/{project_id}/story/audio/{payload['build_id']}/subtitles"
    )
    assert subtitles.status_code == 200
    assert "السلام علیکم!" in subtitles.text
    assert "text/plain" in subtitles.headers["content-type"]


def test_world_builder_exposes_every_supported_world_object_kind():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    html = (root / "app" / "static" / "worlds.html").read_text(encoding="utf-8")
    javascript = (root / "app" / "static" / "worlds.js").read_text(encoding="utf-8")
    supported_kinds = {
        "road", "building", "shop", "school", "hospital", "office",
        "police_station", "tree", "vehicle", "lamp", "park", "garage",
        "indoor_room", "playground", "furniture", "water_body", "streetlight",
    }
    for kind in supported_kinds:
        assert f'data-kind="{kind}"' in html
        assert f'{kind}:' in javascript
    for control in ("object-x", "object-y", "object-rotation"):
        assert f'id="{control}"' in html
        assert f'"{control}"' in javascript
