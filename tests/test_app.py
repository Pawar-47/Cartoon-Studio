from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "Cartoon Studio" in response.text

def test_project_create_and_list(tmp_path, monkeypatch):
    from app import main
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    created = client.post("/api/projects", json={"name": "Test Cartoon", "description": "First local project"})
    assert created.status_code == 201
    assert created.json()["name"] == "Test Cartoon"
    listed = client.get("/api/projects")
    assert listed.status_code == 200
    assert any(item["name"] == "Test Cartoon" for item in listed.json())
