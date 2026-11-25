from __future__ import annotations

import json
import os
import shutil
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.storage import connect_db as open_database
from app.storage import (
    default_data_dir,
    make_envelope,
    project_directory,
    read_json,
    reconcile_project_files,
    resolve_project_relative,
    sync_episode_reference,
    upsert_document_index,
    write_json_atomic,
)
from app.storage import initialize_database as migrate_database
from app.story import EpisodePlan, StoryPromptRequest, build_story_prompt

ROOT = Path(__file__).resolve().parent.parent
_ENV_DATA_DIR = os.environ.get("CARTOON_STUDIO_DATA", "").strip()
DATA_DIR = Path(_ENV_DATA_DIR).expanduser() if _ENV_DATA_DIR else default_data_dir()
DB_PATH = DATA_DIR / "cartoon_studio.sqlite3"
STATIC_DIR = Path(__file__).resolve().parent / "static"
_INITIALIZED_DB_KEY: tuple[str, str] | None = None


def connect_db():
    return open_database(DATA_DIR, DB_PATH)


def initialize_database() -> None:
    global _INITIALIZED_DB_KEY
    key = (str(DATA_DIR.resolve()), str(DB_PATH.resolve()))
    if _INITIALIZED_DB_KEY == key and DB_PATH.exists():
        return
    migrate_database(DATA_DIR, DB_PATH)
    reconcile_project_files(DATA_DIR, DB_PATH)
    _INITIALIZED_DB_KEY = key


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title="Cartoon Studio",
    description="Local-first original Urdu 3D cartoon studio",
    version="0.1.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectRecord(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any]


def _project_record(row: Any) -> ProjectRecord:
    return ProjectRecord(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        metadata=json.loads(row["metadata_json"]),
    )


def _new_project_document(
    project_id: str,
    name: str,
    description: str,
    now: str,
) -> dict[str, Any]:
    return make_envelope(
        "project",
        project_id,
        {
            "name": name,
            "description": description,
            "metadata": {},
            "settings": {
                "default_language": "ur",
                "frame_rate": {"numerator": 24, "denominator": 1},
                "resolution": {"width": 1280, "height": 720},
                "quality_preset": "preview",
            },
            "references": {"characters": [], "worlds": [], "episodes": []},
        },
        now,
        now,
        1,
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "application": "Cartoon Studio",
        "version": app.version,
    }


@app.get("/api/status")
def status() -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project_count = connection.execute(
            "SELECT COUNT(*) FROM projects"
        ).fetchone()[0]
        schema_version = connection.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()[0]
    return {
        "application": "Cartoon Studio",
        "version": app.version,
        "project_count": project_count,
        "database_schema_version": schema_version,
        "storage_mode": "local",
        "production_engine": "Godot 4.7.2 Compatibility worker selected; integration pending",
        "rendering": "not available in current app build",
        "next_milestone": "project lifecycle and portable document storage",
    }


@app.post("/api/story-prompts")
def create_story_prompt(payload: StoryPromptRequest) -> dict[str, Any]:
    return {
        "prompt": build_story_prompt(payload),
        "schema": EpisodePlan.model_json_schema(),
    }


@app.post("/api/story-plans/validate", response_model=EpisodePlan)
def validate_story_plan(plan: EpisodePlan) -> EpisodePlan:
    return plan


@app.put("/api/projects/{project_id}/story")
def save_story_plan(project_id: str, plan: EpisodePlan) -> dict[str, Any]:
    initialize_database()
    now = datetime.now(UTC).isoformat()
    plan_data = plan.model_dump(mode="json")
    plan_json = json.dumps(plan_data, ensure_ascii=False)
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id, created_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        indexed = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_type = 'episode'
            ORDER BY updated_at DESC LIMIT 1
            """,
            (project_id,),
        ).fetchone()
        if indexed is None:
            episode_id = str(uuid.uuid4())
            relative_path = f"episodes/{episode_id}.json"
            revision = 1
        else:
            episode_id = indexed["document_id"]
            relative_path = indexed["relative_path"]
            revision = int(indexed["revision"]) + 1

        episode_document = make_envelope(
            "episode",
            episode_id,
            plan_data,
            project["created_at"],
            now,
            revision,
        )
        episode_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
        digest = write_json_atomic(episode_path, episode_document)
        connection.execute(
            """
            INSERT INTO story_plans(project_id, plan_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET
                plan_json = excluded.plan_json,
                updated_at = excluded.updated_at
            """,
            (project_id, plan_json, now),
        )
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (now, project_id),
        )
        upsert_document_index(
            connection, project_id, episode_document, relative_path, digest
        )
        sync_episode_reference(connection, DATA_DIR, project_id, episode_document)
    return {
        "project_id": project_id,
        "episode_id": episode_id,
        "revision": revision,
        "updated_at": now,
        "plan": plan_data,
    }


@app.get("/api/projects/{project_id}/story")
def get_story_plan(project_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        row = connection.execute(
            "SELECT plan_json, updated_at FROM story_plans WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        indexed = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_type = 'episode'
            ORDER BY updated_at DESC LIMIT 1
            """,
            (project_id,),
        ).fetchone()
    if indexed is not None:
        episode_path = resolve_project_relative(DATA_DIR, project_id, indexed["relative_path"])
        if episode_path.exists():
            document = read_json(episode_path)
            if document.get("document_type") == "episode":
                return {
                    "project_id": project_id,
                    "episode_id": document["id"],
                    "revision": document["revision"],
                    "updated_at": document["updated_at"],
                    "plan": document["data"],
                }
    if row is None:
        raise HTTPException(status_code=404, detail="No story plan saved for this project.")
    return {
        "project_id": project_id,
        "updated_at": row["updated_at"],
        "plan": json.loads(row["plan_json"]),
    }


@app.get("/story", include_in_schema=False)
def story_builder() -> FileResponse:
    return FileResponse(STATIC_DIR / "story.html")


@app.get("/api/projects", response_model=list[ProjectRecord])
def list_projects() -> list[ProjectRecord]:
    initialize_database()
    with connect_db() as connection:
        rows = connection.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        ).fetchall()
    return [_project_record(row) for row in rows]


@app.post("/api/projects", response_model=ProjectRecord, status_code=201)
def create_project(payload: ProjectCreate) -> ProjectRecord:
    initialize_database()
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Project name cannot be blank.")

    now = datetime.now(UTC).isoformat()
    project_id = str(uuid.uuid4())
    description = payload.description.strip()
    project_root = project_directory(DATA_DIR, project_id)
    project_document = _new_project_document(project_id, name, description, now)
    project_path = project_root / "project.json"
    digest = write_json_atomic(project_path, project_document)
    try:
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    id, name, description, created_at, updated_at, metadata_json
                ) VALUES (?, ?, ?, ?, ?, '{}')
                """,
                (project_id, name, description, now, now),
            )
            upsert_document_index(
                connection, project_id, project_document, "project.json", digest
            )
    except BaseException:
        shutil.rmtree(project_root, ignore_errors=True)
        raise

    return ProjectRecord(
        id=project_id,
        name=name,
        description=description,
        created_at=now,
        updated_at=now,
        metadata={},
    )


@app.get("/api/projects/{project_id}")
def open_project(project_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        row = connection.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        project_path = project_directory(DATA_DIR, project_id) / "project.json"
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Project not found.") from error
    if not project_path.exists():
        document = _new_project_document(
            project_id, row["name"], row["description"], row["created_at"]
        )
        digest = write_json_atomic(project_path, document)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, document, "project.json", digest
            )
    else:
        document = read_json(project_path)
    return {"project": _project_record(row).model_dump(mode="json"), "document": document}


@app.put("/api/projects/{project_id}", response_model=ProjectRecord)
def update_project(project_id: str, payload: ProjectUpdate) -> ProjectRecord:
    initialize_database()
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Project name cannot be blank.")
    now = datetime.now(UTC).isoformat()
    with connect_db() as connection:
        row = connection.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        project_path = project_directory(DATA_DIR, project_id) / "project.json"
        if project_path.exists():
            document = read_json(project_path)
        else:
            document = _new_project_document(
                project_id, row["name"], row["description"], row["created_at"]
            )
        document["data"]["name"] = name
        document["data"]["description"] = payload.description.strip()
        document["revision"] = int(document.get("revision", 1)) + 1
        document["updated_at"] = now
        digest = write_json_atomic(project_path, document)
        connection.execute(
            """
            UPDATE projects SET name = ?, description = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, payload.description.strip(), now, project_id),
        )
        upsert_document_index(
            connection, project_id, document, "project.json", digest
        )
        updated = connection.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    return _project_record(updated)
