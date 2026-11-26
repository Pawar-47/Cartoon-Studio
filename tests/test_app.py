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
    assert versions == 2
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
    asset_id = str(uuid.uuid4())
    relative = f"assets/characters/{asset_id}.glb"
    asset_path = main.resolve_project_relative(main.DATA_DIR, project_id, relative)
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    asset_path.write_bytes(b"test-glb")
    asset_data = {
        "original_filename": "Ali.glb",
        "relative_path": relative,
        "rig_ready": True,
        "animation_ready": True,
    }
    asset_doc = main.make_envelope("character_asset", asset_id, asset_data, now, now)
    asset_manifest = main.resolve_project_relative(
        main.DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
    )
    digest = main.write_json_atomic(asset_manifest, asset_doc)
    with main.connect_db() as connection:
        main.upsert_document_index(
            connection, project_id, asset_doc,
            f"assets/characters/{asset_id}.json", digest,
        )

    plan = valid_episode_plan()
    plan["world_id"] = world.json()["id"]
    plan["characters"][0]["asset_id"] = asset_id
    saved = client.put(f"/api/projects/{project_id}/story", json=plan)
    assert saved.status_code == 200

    generated = client.post(f"/api/projects/{project_id}/story/production")
    assert generated.status_code == 200
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
