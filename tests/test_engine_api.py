from __future__ import annotations

from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


class _FakeEngineAdapter:
    available = True

    def ping(self):
        return {
            "ok": True,
            "engine_version": "4.7.2.test",
            "protocol_version": 1,
            "capabilities": ["ping", "glb_inspect"],
            "elapsed_ms": 2,
        }

    def inspect_glb(self, source_path, allowed_root, timeout_seconds=None):
        return {
            "ok": True,
            "mesh_count": 1,
            "skeleton_count": 0,
            "animation_player_count": 0,
            "node_count": 2,
            "source_path": str(source_path),
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
    assert response.json()["available"] is True
    assert response.json()["engine_version"].startswith("4.7.2")


def test_engine_inspect_endpoint_uses_project_relative_asset_path(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    asset = tmp_path / "projects" / project_id / "assets" / "character.glb"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"fixture")
    monkeypatch.setattr(main, "get_engine_adapter", _FakeEngineAdapter)
    response = client.post(
        f"/api/projects/{project_id}/engine/inspect-glb",
        json={"relative_path": "assets/character.glb"},
    )
    assert response.status_code == 200
    assert response.json()["mesh_count"] == 1


def test_engine_inspect_endpoint_rejects_project_path_traversal(tmp_path, monkeypatch):
    project_id = _new_project(tmp_path, monkeypatch)
    response = client.post(
        f"/api/projects/{project_id}/engine/inspect-glb",
        json={"relative_path": "../../outside.glb"},
    )
    assert response.status_code == 422


def test_engine_status_endpoint_reports_missing_runtime(monkeypatch):
    class MissingEngine:
        available = False

    monkeypatch.setattr(main, "get_engine_adapter", MissingEngine)
    response = client.get("/api/engine/status")
    assert response.status_code == 200
    assert response.json()["status"] == "runtime_not_found"
