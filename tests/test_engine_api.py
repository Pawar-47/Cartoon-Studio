from __future__ import annotations

from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


class _FakeEngineAdapter:
    def handshake(self):
        return {
            "status": "ok",
            "protocol_version": 1,
            "engine": {"name": "Godot Engine", "version": "4.7.2.test"},
            "capabilities": ["handshake", "glb.inspect"],
        }

    def inspect_glb(self, project_root, relative_path):
        return {
            "status": "ok",
            "asset": {"file_name": relative_path.rsplit("/", 1)[-1]},
            "metrics": {"mesh_count": 1, "skeleton_count": 0, "animation_count": 0},
        }


def _new_project(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "engine-api.sqlite3")
    monkeypatch.setattr(main, "_INITIALIZED_DB_KEY", None)
    response = client.post("/api/projects", json={"name": "Engine API Test"})
    assert response.status_code == 201
    return response.json()["id"]


def test_engine_status_endpoint_reports_worker(monkeypatch):
    monkeypatch.setattr(main, "get_engine_adapter", _FakeEngineAdapter)
    response = client.get("/api/engine/status")
    assert response.status_code == 200
    assert response.json()["engine"]["version"].startswith("4.7.2")


def test_engine_inspect_endpoint_uses_project_relative_asset_path(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    asset = tmp_path / "projects" / project_id / "assets" / "character.glb"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"fixture")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeEngineAdapter)
    response = client.post(
        "/api/engine/inspect-glb",
        json={"project_id": project_id, "asset_path": "assets/character.glb"},
    )
    assert response.status_code == 200
    assert response.json()["asset"]["file_name"] == "character.glb"
    assert response.json()["metrics"]["mesh_count"] == 1


def test_engine_inspect_endpoint_rejects_project_path_traversal(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    response = client.post(
        "/api/engine/inspect-glb",
        json={"project_id": project_id, "asset_path": "../../outside.glb"},
    )
    assert response.status_code == 422


def test_engine_status_endpoint_reports_missing_runtime(monkeypatch):
    from app.engine import EngineUnavailableError

    class MissingEngine:
        def handshake(self):
            raise EngineUnavailableError("Godot runtime missing.")

    monkeypatch.setattr(main, "get_engine_adapter", MissingEngine)
    response = client.get("/api/engine/status")
    assert response.status_code == 503
