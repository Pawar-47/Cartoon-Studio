from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.character_builder import (
    CharacterLibraryError,
    UnknownCharacterModel,
    ensure_model_asset,
    get_character_catalog,
    get_model_spec,
)
from app.engine import (
    EngineError,
    EnginePathError,
    EngineTimeoutError,
    EngineUnavailableError,
    GodotEngineAdapter,
)
from app.rig_analysis import analyze_rig
from app.storage import connect_db as open_database
from app.storage import (
    default_data_dir,
    make_envelope,
    project_directory,
    read_json,
    reconcile_project_files,
    resolve_project_relative,
    sync_character_reference,
    sync_episode_reference,
    upsert_document_index,
    write_json_atomic,
)
from app.storage import initialize_database as migrate_database
from app.story import EpisodePlan, StoryPromptRequest, build_story_prompt
from app.version import APP_VERSION

ROOT = Path(__file__).resolve().parent.parent
_ENV_DATA_DIR = os.environ.get("CARTOON_STUDIO_DATA", "").strip()
DATA_DIR = Path(_ENV_DATA_DIR).expanduser() if _ENV_DATA_DIR else default_data_dir()
DB_PATH = DATA_DIR / "cartoon_studio.sqlite3"
STATIC_DIR = Path(__file__).resolve().parent / "static"
_INITIALIZED_DB_KEY: tuple[str, str] | None = None


def connect_db():
    return open_database(DATA_DIR, DB_PATH)


def get_engine_adapter() -> GodotEngineAdapter:
    return GodotEngineAdapter(data_dir=DATA_DIR)


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
    version=APP_VERSION,
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)


class GlbInspectRequest(BaseModel):
    relative_path: str = Field(min_length=1, max_length=512)


class CharacterHairInput(BaseModel):
    style: str = Field(pattern="^(short|bob|long|ponytail|spiky|curly|mohawk)$")
    color: str = Field(default="#2b1b13", pattern=r"^#[0-9a-fA-F]{6}$")


class CharacterProportionsInput(BaseModel):
    torso_length: float = Field(default=1.0, ge=0.75, le=1.25)
    shoulder_width: float = Field(default=1.0, ge=0.75, le=1.25)
    arm_length: float = Field(default=1.0, ge=0.75, le=1.25)
    leg_length: float = Field(default=1.0, ge=0.75, le=1.25)
    head_size: float = Field(default=1.0, ge=0.75, le=1.25)


class ModularPartInput(BaseModel):
    slot: str = Field(min_length=1, max_length=12)
    relative_path: str = Field(min_length=1, max_length=512)
    mesh_path: str = Field(min_length=1, max_length=1024)


class ModularAccessoryInput(BaseModel):
    relative_path: str = Field(min_length=1, max_length=512)
    mesh_path: str = Field(min_length=1, max_length=1024)
    attachment_bone: str = Field(default="", max_length=128)


class ModularAssemblyInput(BaseModel):
    base_relative_path: str = Field(min_length=1, max_length=512)
    parts: list[ModularPartInput] = Field(min_length=4, max_length=4)
    accessories: list[ModularAccessoryInput] = Field(default_factory=list, max_length=8)


class CharacterRetargetInput(BaseModel):
    source_character_id: str = Field(min_length=1, max_length=64)
    target_character_id: str = Field(min_length=1, max_length=64)
    animation_name: str = Field(default="", max_length=120)



class CharacterProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=1000)
    face_design: str = Field(default="", max_length=500)
    body_proportions: dict[str, float] = Field(default_factory=dict)
    height_cm: float | None = Field(default=None, gt=0, le=300)
    hair: str = Field(default="", max_length=200)
    clothing: list[str] = Field(default_factory=list, max_length=30)
    accessories: list[str] = Field(default_factory=list, max_length=30)
    eye_design: str = Field(default="", max_length=200)
    mouth_design: str = Field(default="", max_length=200)
    expressions: list[str] = Field(default_factory=list, max_length=30)
    personality: str = Field(default="", max_length=1000)
    relationships: list[str] = Field(default_factory=list, max_length=30)
    voice_profile: str = Field(default="", max_length=500)
    dialogue_style: str = Field(default="", max_length=500)
    asset_path: str = Field(min_length=1, max_length=512)


class MaterialAppearanceInput(BaseModel):
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    roughness: float | None = Field(default=None, ge=0, le=1)
    metalness: float | None = Field(default=None, ge=0, le=1)
    mesh_name: str | None = Field(default=None, max_length=256)
    surface_index: int | None = Field(default=None, ge=0, le=255)
    material_name: str | None = Field(default=None, max_length=256)


class MorphBindingInput(BaseModel):
    mesh_name: str = Field(min_length=1, max_length=256)
    target_index: int = Field(ge=0, le=1023)
    target_name: str = Field(min_length=1, max_length=256)


class CharacterAppearanceInput(BaseModel):
    materials: dict[str, MaterialAppearanceInput] = Field(default_factory=dict, max_length=256)
    morph_targets: dict[str, Annotated[float, Field(ge=-1, le=1)]] = Field(
        default_factory=dict, max_length=512
    )
    morph_bindings: dict[str, MorphBindingInput] = Field(default_factory=dict, max_length=512)


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



MAX_CHARACTER_ASSET_BYTES = 512 * 1024 * 1024


def _validate_glb_container(path: Path) -> dict[str, Any]:
    size = path.stat().st_size
    if size < 20 or size > MAX_CHARACTER_ASSET_BYTES:
        raise ValueError("GLB file size is outside the supported range.")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        header = handle.read(12)
        if len(header) != 12:
            raise ValueError("GLB header is incomplete.")
        magic = header[:4]
        version = int.from_bytes(header[4:8], "little")
        declared_length = int.from_bytes(header[8:12], "little")
        if magic != b"glTF" or version != 2 or declared_length != size:
            raise ValueError("File is not a valid GLB 2.0 container.")
        chunk_header = handle.read(8)
        if len(chunk_header) != 8:
            raise ValueError("GLB JSON chunk is missing.")
        chunk_length = int.from_bytes(chunk_header[:4], "little")
        chunk_type = int.from_bytes(chunk_header[4:8], "little")
        if chunk_type != 0x4E4F534A or chunk_length > size - 20:
            raise ValueError("GLB JSON chunk is invalid.")
        raw_json = handle.read(chunk_length)
        if len(raw_json) != chunk_length:
            raise ValueError("GLB JSON chunk is truncated.")
        try:
            document = json.loads(raw_json.decode("utf-8").rstrip("\x00 \t\r\n"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("GLB JSON document is invalid.") from error
        if not isinstance(document, dict) or not isinstance(document.get("asset"), dict):
            raise ValueError("GLB asset metadata is missing.")
        if str(document["asset"].get("version", "")) != "2.0":
            raise ValueError("Only glTF 2.0 binary assets are supported.")
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    meshes = document.get("meshes", [])
    nodes = document.get("nodes", [])
    skins = document.get("skins", [])
    animations = document.get("animations", [])
    if not all(isinstance(value, list) for value in (meshes, nodes, skins, animations)):
        raise ValueError("GLB mesh, node, skin and animation collections must be arrays.")
    return {
        "format": "glTF Binary 2.0",
        "size_bytes": size,
        "sha256": digest.hexdigest(),
        "mesh_count": len(meshes),
        "node_count": len(nodes),
        "skin_count": len(skins),
        "animation_count": len(animations),
    }


def _character_document(data_dir: Path, project_id: str, character_id: str) -> dict[str, Any]:
    relative_path = f"characters/{character_id}.json"
    path = resolve_project_relative(data_dir, project_id, relative_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Character not found.")
    document = read_json(path)
    if (
        document.get("document_type") != "character"
        or document.get("id") != character_id
        or not isinstance(document.get("data"), dict)
    ):
        raise HTTPException(status_code=409, detail="Character document identity is invalid.")
    return document


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


@app.get("/api/engine/status")
def engine_status() -> dict[str, Any]:
    adapter = get_engine_adapter()
    if not adapter.available:
        return {
            "available": False,
            "status": "runtime_not_found",
            "expected_version": "4.7.2-stable",
        }
    try:
        result = adapter.ping()
    except EngineError as error:
        return {
            "available": False,
            "status": "worker_error",
            "expected_version": "4.7.2-stable",
            "detail": str(error),
        }
    return {
        "available": True,
        "status": "ready",
        "engine_version": result.get("engine_version", "unknown"),
        "protocol_version": result.get("protocol_version"),
        "capabilities": result.get("capabilities", []),
        "elapsed_ms": result.get("elapsed_ms"),
    }


@app.post("/api/projects/{project_id}/engine/inspect-glb")
def inspect_project_glb(
    project_id: str,
    payload: GlbInspectRequest,
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        project_root = project_directory(DATA_DIR, project_id)
        source_path = resolve_project_relative(
            DATA_DIR, project_id, payload.relative_path
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if source_path.suffix.lower() != ".glb":
        raise HTTPException(status_code=422, detail="Only .glb files can be inspected.")
    if not source_path.is_file():
        raise HTTPException(status_code=404, detail="GLB file not found in this project.")
    try:
        return get_engine_adapter().inspect_glb(
            source_path,
            allowed_root=project_root,
        )
    except EngineUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EngineError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error



@app.post("/api/projects/{project_id}/modular-assemblies", status_code=201)
def create_modular_assembly(
    project_id: str,
    payload: ModularAssemblyInput,
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    slots = [part.slot for part in payload.parts]
    if set(slots) != {"head", "body", "legs", "feet"} or len(set(slots)) != 4:
        raise HTTPException(
            status_code=422,
            detail="Choose exactly one mesh for each slot: head, body, legs and feet.",
        )
    try:
        project_root = project_directory(DATA_DIR, project_id)
        base_path = resolve_project_relative(
            DATA_DIR, project_id, payload.base_relative_path
        )
        parts = [
            {
                "slot": part.slot,
                "source_path": str(
                    resolve_project_relative(DATA_DIR, project_id, part.relative_path)
                ),
                "mesh_path": part.mesh_path,
            }
            for part in payload.parts
        ]
        accessories = [
            {
                "source_path": str(
                    resolve_project_relative(DATA_DIR, project_id, accessory.relative_path)
                ),
                "mesh_path": accessory.mesh_path,
                "attachment_bone": accessory.attachment_bone,
            }
            for accessory in payload.accessories
        ]
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if base_path.suffix.lower() != ".glb" or not base_path.is_file():
        raise HTTPException(status_code=404, detail="Base character GLB was not found.")
    if any(not Path(part["source_path"]).is_file() for part in parts):
        raise HTTPException(status_code=404, detail="One or more modular part GLBs were not found.")
    if any(not Path(item["source_path"]).is_file() for item in accessories):
        raise HTTPException(status_code=404, detail="One or more accessory GLBs were not found.")
    asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{asset_id}.glb"
    destination = resolve_project_relative(DATA_DIR, project_id, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        assembly = get_engine_adapter().assemble_modular_character(
            base_path,
            parts,
            destination,
            allowed_root=project_root,
            accessories=accessories,
        )
        container = _validate_glb_container(destination)
        inspection = assembly
        if not assembly.get("assembly_verified") or not assembly.get("animation_preserved"):
            raise HTTPException(
                status_code=422,
                detail="Godot did not verify the assembled character and animation preservation.",
            )
        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": "modular-character.glb",
            "relative_path": relative_path,
            "container": container,
            "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
            "assembly": {
                "base_relative_path": payload.base_relative_path,
                "parts": [
                    {
                        "slot": part.slot,
                        "relative_path": part.relative_path,
                        "mesh_path": part.mesh_path,
                    }
                    for part in payload.parts
                ],
                "added_parts": assembly.get("added_parts", []),
                "base_meshes_removed": assembly.get(
                    "base_meshes_removed", []
                ),
                "accessories": [
                    {
                        "relative_path": accessory.relative_path,
                        "mesh_path": accessory.mesh_path,
                        "attachment_bone": accessory.attachment_bone,
                    }
                    for accessory in payload.accessories
                ],
                "added_accessories": assembly.get("added_accessories", []),
                "animation_preserved": True,
                "verified": True,
            },
        }
        manifest = make_envelope("character_asset", asset_id, asset_data, now, now, 1)
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
        )
        digest = write_json_atomic(manifest_path, manifest)
        with connect_db() as connection:
            upsert_document_index(
                connection,
                project_id,
                manifest,
                f"assets/characters/{asset_id}.json",
                digest,
            )
        return {"asset_id": asset_id, **asset_data}
    except EngineUnavailableError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Modular assembly failed: {error}") from error
    except ValueError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid assembled GLB: {error}") from error
    except BaseException:
        destination.unlink(missing_ok=True)
        raise



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
        "production_engine": (
            "Godot 4.7.2 Compatibility worker available"
            if get_engine_adapter().available
            else "Godot 4.7.2 Compatibility selected; worker runtime unavailable"
        ),
        "rendering": (
            "GLB inspection worker available"
            if get_engine_adapter().available
            else "not available in current app build"
        ),
        "next_milestone": "Character Studio visual acceptance and face/hair geometry authoring",
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



@app.get("/characters", include_in_schema=False)
def character_studio() -> FileResponse:
    return FileResponse(STATIC_DIR / "characters.html")


@app.get("/api/character-builder/catalog")
def character_builder_catalog() -> dict[str, Any]:
    return get_character_catalog()


@app.get("/api/character-builder/models/{pack}/{outfit}")
def character_builder_model(pack: str, outfit: str) -> FileResponse:
    try:
        spec = get_model_spec(pack, outfit)
    except UnknownCharacterModel as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    try:
        model_path = ensure_model_asset(DATA_DIR / "character-library", pack, outfit)
    except CharacterLibraryError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return FileResponse(
        model_path,
        media_type="model/gltf-binary",
        filename=model_path.name,
        headers={
            "ETag": f'"{spec.git_blob_sha1}"',
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@app.post("/api/projects/{project_id}/character-assets", status_code=201)
async def upload_character_asset(project_id: str, request: Request) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id, created_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    filename = request.headers.get("x-asset-filename", "character.glb").strip()
    if (
        not filename
        or len(filename) > 120
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
        or not filename.lower().endswith(".glb")
    ):
        raise HTTPException(status_code=422, detail="Choose a valid .glb filename.")
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_CHARACTER_ASSET_BYTES:
                raise HTTPException(status_code=413, detail="GLB exceeds the 512 MiB limit.")
        except ValueError as error:
            raise HTTPException(status_code=400, detail="Invalid Content-Length header.") from error

    asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{asset_id}.glb"
    try:
        destination = resolve_project_relative(DATA_DIR, project_id, relative_path)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{asset_id}.upload")
    total = 0
    try:
        with temporary.open("wb") as handle:
            async for chunk in request.stream():
                total += len(chunk)
                if total > MAX_CHARACTER_ASSET_BYTES:
                    raise HTTPException(status_code=413, detail="GLB exceeds the 512 MiB limit.")
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        if total == 0:
            raise HTTPException(status_code=422, detail="Uploaded GLB is empty.")
        temporary.replace(destination)
        try:
            container = _validate_glb_container(destination)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        try:
            inspection = get_engine_adapter().inspect_glb(
                destination,
                allowed_root=project_directory(DATA_DIR, project_id),
            )
        except EngineUnavailableError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except EngineTimeoutError as error:
            raise HTTPException(status_code=504, detail=str(error)) from error
        except EngineError as error:
            raise HTTPException(
                status_code=422,
                detail=f"Godot could not import this GLB: {error}",
            ) from error

        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": filename,
            "relative_path": relative_path,
            "container": container,
            "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
        }
        manifest = make_envelope("character_asset", asset_id, asset_data, now, now, 1)
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
        )
        digest = write_json_atomic(manifest_path, manifest)
        with connect_db() as connection:
            upsert_document_index(
                connection,
                project_id,
                manifest,
                f"assets/characters/{asset_id}.json",
                digest,
            )
        return {"asset_id": asset_id, **asset_data}
    except BaseException:
        temporary.unlink(missing_ok=True)
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)


@app.get("/api/projects/{project_id}/character-assets/{asset_id}")
def get_character_asset(project_id: str, asset_id: str) -> FileResponse:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        safe_asset_id = str(uuid.UUID(asset_id))
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{safe_asset_id}.json"
        )
        asset_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{safe_asset_id}.glb"
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid character asset ID.") from error
    if not manifest_path.is_file() or not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Character asset not found.")
    manifest = read_json(manifest_path)
    if manifest.get("document_type") != "character_asset" or manifest.get("id") != safe_asset_id:
        raise HTTPException(status_code=409, detail="Character asset manifest is invalid.")
    return FileResponse(
        asset_path,
        media_type="model/gltf-binary",
        filename=manifest["data"].get("original_filename", "character.glb"),
    )


@app.get("/api/projects/{project_id}/character-assets/{asset_id}/manifest")
def get_character_asset_manifest(project_id: str, asset_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        safe_asset_id = str(uuid.UUID(asset_id))
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{safe_asset_id}.json"
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid character asset ID.") from error
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="Character asset manifest not found.")
    manifest = read_json(manifest_path)
    if (
        manifest.get("document_type") != "character_asset"
        or manifest.get("id") != safe_asset_id
        or not isinstance(manifest.get("data"), dict)
    ):
        raise HTTPException(status_code=409, detail="Character asset manifest is invalid.")
    return {"asset_id": safe_asset_id, **manifest["data"]}



@app.post("/api/projects/{project_id}/character-assets/{asset_id}/proportions", status_code=201)
def customize_character_asset_proportions(
    project_id: str, asset_id: str, payload: CharacterProportionsInput
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        safe_asset_id = str(uuid.UUID(asset_id))
        source_manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{safe_asset_id}.json"
        )
        source_manifest = read_json(source_manifest_path)
        source_data = source_manifest.get("data", {})
        current_relative_path = str(source_data.get("relative_path", ""))
        current_geometry_edit = source_data.get("geometry_edit") or {}
        history = list(source_data.get("geometry_edit_history") or [])
        for prior_edit in (
            source_data.get("previous_geometry_edit"),
            current_geometry_edit,
        ):
            if isinstance(prior_edit, dict) and prior_edit:
                if not history or history[-1] != prior_edit:
                    history.append(prior_edit)
        last_body_edit = next(
            (
                item for item in reversed(history)
                if item.get("type") == "humanoid_body_proportions"
            ),
            {},
        )
        if current_geometry_edit.get("type") == "humanoid_body_proportions":
            source_relative_path = str(
                current_geometry_edit.get("source_relative_path") or current_relative_path
            )
            source_proportions = current_geometry_edit.get("source_proportions") or {}
        elif last_body_edit:
            source_relative_path = current_relative_path
            source_proportions = last_body_edit.get("proportions") or {}
        else:
            source_relative_path = current_relative_path
            source_proportions = {}
        rig_analysis = source_data.get("rig_analysis") or {}
        bone_mapping = rig_analysis.get("bone_mapping", {})
        if (
            rig_analysis.get("status") != "humanoid_names_complete"
            or not isinstance(bone_mapping, dict)
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Body-proportion editing requires a complete, unambiguous "
                    "humanoid bone mapping."
                ),
            )
        project_root = project_directory(DATA_DIR, project_id)
        source_path = resolve_project_relative(DATA_DIR, project_id, source_relative_path)
    except (ValueError, OSError) as error:
        raise HTTPException(
            status_code=422,
            detail="The source character asset is invalid.",
        ) from error
    if (
        source_manifest.get("document_type") != "character_asset"
        or source_manifest.get("id") != safe_asset_id
        or not source_path.is_file()
        or source_path.suffix.lower() != ".glb"
    ):
        raise HTTPException(status_code=404, detail="The source character GLB was not found.")
    proportions = payload.model_dump(mode="json")
    if all(abs(value - 1.0) < 0.0001 for value in proportions.values()):
        raise HTTPException(
            status_code=422,
            detail="Change at least one body proportion before applying.",
        )
    worker_proportions: dict[str, float] = {}
    for name, value in proportions.items():
        baseline = source_proportions.get(name, 1.0)
        if (
            isinstance(baseline, bool)
            or not isinstance(baseline, (int, float))
            or not 0.75 <= float(baseline) <= 1.25
        ):
            raise HTTPException(
                status_code=422,
                detail="The saved source body-proportion baseline is invalid.",
            )
        worker_proportions[name] = float(value) / float(baseline)
    new_asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{new_asset_id}.glb"
    destination = resolve_project_relative(DATA_DIR, project_id, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        inspection = get_engine_adapter().customize_character_proportions(
            source_path,
            worker_proportions,
            destination,
            allowed_root=project_root,
            bone_mapping=bone_mapping,
        )
        if not inspection.get("proportions_verified"):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Godot did not verify the edited bone transforms after GLB export "
                    "and re-import."
                ),
            )
        container = _validate_glb_container(destination)
        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": "proportioned-character.glb",
            "relative_path": relative_path,
            "container": container,
            "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
            "geometry_edit": {
                "type": "humanoid_body_proportions",
                "source_relative_path": source_relative_path,
                "source_proportions": source_proportions,
                "proportions": proportions,
                "changed_bones": inspection.get("changed_bones", []),
                "verified": True,
            },
            "geometry_edit_history": history[-20:],
        }
        if source_data.get("assembly"):
            asset_data["assembly"] = source_data["assembly"]
        if current_geometry_edit:
            asset_data["previous_geometry_edit"] = current_geometry_edit
        manifest = make_envelope("character_asset", new_asset_id, asset_data, now, now, 1)
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{new_asset_id}.json"
        )
        digest = write_json_atomic(manifest_path, manifest)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, manifest,
                f"assets/characters/{new_asset_id}.json", digest
            )
        return {"asset_id": new_asset_id, **asset_data}
    except EngineUnavailableError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail=f"Body-proportion editing failed: {error}",
        ) from error
    except ValueError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid proportioned GLB: {error}") from error
    except BaseException:
        destination.unlink(missing_ok=True)
        raise



@app.post("/api/projects/{project_id}/character-assets/{asset_id}/hair", status_code=201)
def add_character_asset_hair(
    project_id: str, asset_id: str, payload: CharacterHairInput
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        safe_asset_id = str(uuid.UUID(asset_id))
        source_manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{safe_asset_id}.json"
        )
        source_manifest = read_json(source_manifest_path)
        source_data = source_manifest.get("data", {})
        source_relative_path = str(source_data.get("relative_path", ""))
        project_root = project_directory(DATA_DIR, project_id)
        source_path = resolve_project_relative(DATA_DIR, project_id, source_relative_path)
    except (ValueError, OSError) as error:
        raise HTTPException(
            status_code=422, detail="The source character asset is invalid."
        ) from error
    if (
        source_manifest.get("document_type") != "character_asset"
        or source_manifest.get("id") != safe_asset_id
        or not source_path.is_file()
        or source_path.suffix.lower() != ".glb"
    ):
        raise HTTPException(status_code=404, detail="The source character GLB was not found.")
    new_asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{new_asset_id}.glb"
    destination = resolve_project_relative(DATA_DIR, project_id, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        inspection = get_engine_adapter().add_character_hair(
            source_path, payload.style, payload.color, destination, allowed_root=project_root
        )
        if not inspection.get("hair_verified"):
            raise HTTPException(
                status_code=422,
                detail="Godot could not verify the hairstyle attachment after GLB export.",
            )
        container = _validate_glb_container(destination)
        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": f"{payload.style}-hairstyle-character.glb",
            "relative_path": relative_path,
            "container": container,
            "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
            "geometry_edit": {
                "type": "procedural_hair",
                "style": payload.style,
                "color": payload.color,
                "attachment_bone": inspection.get("hair_attachment_bone", ""),
                "mesh_count": inspection.get("hair_mesh_count", 0),
                "verified": True,
            },
        }
        if source_data.get("assembly"):
            asset_data["assembly"] = source_data["assembly"]
        history = list(source_data.get("geometry_edit_history") or [])
        for prior_edit in (
            source_data.get("previous_geometry_edit"),
            source_data.get("geometry_edit"),
        ):
            if isinstance(prior_edit, dict) and prior_edit:
                if not history or history[-1] != prior_edit:
                    history.append(prior_edit)
        asset_data["geometry_edit_history"] = history[-20:]
        if source_data.get("geometry_edit"):
            asset_data["previous_geometry_edit"] = source_data["geometry_edit"]
        manifest = make_envelope("character_asset", new_asset_id, asset_data, now, now, 1)
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{new_asset_id}.json"
        )
        digest = write_json_atomic(manifest_path, manifest)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, manifest,
                f"assets/characters/{new_asset_id}.json", digest
            )
        return {"asset_id": new_asset_id, **asset_data}
    except EngineUnavailableError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422, detail=f"Hairstyle generation failed: {error}"
        ) from error
    except ValueError as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid hairstyle GLB: {error}") from error
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


@app.post("/api/projects/{project_id}/retargets", status_code=201)
def create_character_retarget(
    project_id: str, payload: CharacterRetargetInput
) -> dict[str, Any]:
    initialize_database()
    if payload.source_character_id == payload.target_character_id:
        raise HTTPException(status_code=422, detail="Choose two different characters.")
    with connect_db() as connection:
        exists = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    source = _character_document(DATA_DIR, project_id, payload.source_character_id)
    target = _character_document(DATA_DIR, project_id, payload.target_character_id)
    source_data, target_data = source["data"], target["data"]
    source_asset = source_data.get("asset", {})
    target_asset = target_data.get("asset", {})
    for label, asset in (("source", source_asset), ("target", target_asset)):
        rig = asset.get("rig_analysis", {})
        hierarchy = rig.get("hierarchy_validation", {})
        inspection = asset.get("engine_inspection", {})
        if int(inspection.get("skeleton_count", 0) or 0) != 1:
            raise HTTPException(
                status_code=422,
                detail=f"The {label} character must contain exactly one skeleton.",
            )
        if rig.get("status") != "humanoid_names_complete":
            raise HTTPException(
                status_code=422,
                detail=(
                    f"The {label} character needs an unambiguous "
                    "15-bone humanoid mapping."
                ),
            )
        allowed_hierarchy_statuses = {"valid"}
        if label == "source":
            allowed_hierarchy_statuses.add("valid_with_ik_foot_hierarchy")
        if hierarchy.get("status") not in allowed_hierarchy_statuses:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"The {label} character's humanoid parent hierarchy "
                    "is not validated: "
                    + str(hierarchy.get("note", "review the rig diagnostics"))
                ),
            )

    source_inspection = source_asset.get("engine_inspection", {})
    target_inspection = target_asset.get("engine_inspection", {})
    target_container = target_asset.get("container", {})
    available_animations = source_inspection.get("animation_names")
    if int(source_inspection.get("animation_count", 0) or 0) < 1 or (
        isinstance(available_animations, list) and not available_animations
    ):
        raise HTTPException(
            status_code=422,
            detail="The source character has no playable imported animation clips.",
        )
    requested_animation = payload.animation_name.strip()
    if (
        requested_animation
        and isinstance(available_animations, list)
        and requested_animation not in available_animations
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "The selected animation is not present in the "
                "source character's imported clips."
            ),
        )
    target_skin_count = target_container.get(
        "skin_count", target_inspection.get("skin_count", 0)
    )
    if int(target_skin_count or 0) < 1:
        raise HTTPException(
            status_code=422, detail="The target character has no skinned mesh."
        )

    project_root = project_directory(DATA_DIR, project_id)
    try:
        source_path = resolve_project_relative(
            DATA_DIR, project_id, str(source_asset.get("relative_path", ""))
        )
        target_path = resolve_project_relative(
            DATA_DIR, project_id, str(target_asset.get("relative_path", ""))
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422, detail="A character asset path is invalid."
        ) from error
    if not source_path.is_file() or not target_path.is_file():
        raise HTTPException(
            status_code=404, detail="A source or target GLB file is missing."
        )
    if source_path == target_path:
        raise HTTPException(
            status_code=422,
            detail="Source and target must use different imported GLB assets.",
        )

    retarget_id = str(uuid.uuid4())
    scene_relative = f"retargets/{retarget_id}.tscn"
    scene_path = resolve_project_relative(DATA_DIR, project_id, scene_relative)
    try:
        result = get_engine_adapter().retarget_glb_pair(
            source_path,
            target_path,
            scene_path,
            allowed_root=project_root,
            source_profile_mapping=source_asset["rig_analysis"][
                "godot_profile_mapping"
            ],
            target_profile_mapping=target_asset["rig_analysis"][
                "godot_profile_mapping"
            ],
            animation_name=payload.animation_name.strip(),
        )
    except EngineUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        scene_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=502, detail=f"Godot retargeting failed: {error}"
        ) from error

    now = datetime.now(UTC).isoformat()
    data = {
        "source_character_id": source["id"],
        "source_character_name": source_data.get("name", ""),
        "target_character_id": target["id"],
        "target_character_name": target_data.get("name", ""),
        "source_asset_path": source_asset["relative_path"],
        "target_asset_path": target_asset["relative_path"],
        "animation_name": result.get(
            "animation_name", payload.animation_name.strip()
        ),
        "scene_relative_path": scene_relative,
        "mapped_bone_count": result.get("mapped_bone_count", 0),
        "target_skinned_mesh_count": result.get("target_skinned_mesh_count", 0),
        "scene_reopened": bool(result.get("scene_reopened", False)),
        "pose_transferred": bool(result.get("pose_transferred", False)),
        "source_animation_playing": bool(result.get("source_animation_playing", False)),
        "source_pose_angle_degrees": result.get("source_pose_angle_degrees"),
        "target_pose_angle_degrees": result.get("target_pose_angle_degrees"),
        "source_glb_preserved": True,
        "target_glb_preserved": True,
    }
    document = make_envelope("character_retarget", retarget_id, data, now, now, 1)
    config_relative = f"retargets/{retarget_id}.json"
    config_path = resolve_project_relative(DATA_DIR, project_id, config_relative)
    digest = write_json_atomic(config_path, document)
    with connect_db() as connection:
        upsert_document_index(connection, project_id, document, config_relative, digest)
    return document


@app.get("/api/projects/{project_id}/retargets")
def list_character_retargets(project_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with connect_db() as connection:
        exists = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        rows = connection.execute(
            """
            SELECT relative_path FROM project_documents
            WHERE project_id = ? AND document_type = 'character_retarget'
            ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    documents = []
    for row in rows:
        path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
        if path.is_file():
            document = read_json(path)
            if document.get("document_type") == "character_retarget":
                documents.append(document)
    return documents


@app.get(
    "/api/projects/{project_id}/retargets/{retarget_id}/scene",
    response_class=FileResponse,
)
def download_character_retarget_scene(
    project_id: str, retarget_id: str
) -> FileResponse:
    initialize_database()
    with connect_db() as connection:
        exists = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        safe_id = str(uuid.UUID(retarget_id))
        config_path = resolve_project_relative(
            DATA_DIR, project_id, f"retargets/{safe_id}.json"
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid retarget ID.") from error
    if not config_path.is_file():
        raise HTTPException(status_code=404, detail="Retarget record not found.")
    document = read_json(config_path)
    if (
        document.get("document_type") != "character_retarget"
        or document.get("id") != safe_id
    ):
        raise HTTPException(status_code=409, detail="Retarget record is invalid.")
    scene_relative = str(document.get("data", {}).get("scene_relative_path", ""))
    if not scene_relative.startswith("retargets/") or not scene_relative.endswith(
        ".tscn"
    ):
        raise HTTPException(status_code=409, detail="Retarget scene path is invalid.")
    scene_path = resolve_project_relative(DATA_DIR, project_id, scene_relative)
    if not scene_path.is_file():
        raise HTTPException(status_code=404, detail="Retarget scene file is missing.")
    return FileResponse(
        scene_path,
        media_type="text/plain",
        filename=f"retarget-{safe_id}.tscn",
    )



@app.get("/api/projects/{project_id}/retargets/{retarget_id}/preview")
def get_character_retarget_preview(project_id: str, retarget_id: str) -> dict[str, Any]:
    """Return project-local GLBs and canonical bone maps for the browser preview."""
    initialize_database()
    with connect_db() as connection:
        exists = connection.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        safe_id = str(uuid.UUID(retarget_id))
        config_path = resolve_project_relative(DATA_DIR, project_id, f"retargets/{safe_id}.json")
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid retarget ID.") from error
    if not config_path.is_file():
        raise HTTPException(status_code=404, detail="Retarget record not found.")
    document = read_json(config_path)
    if document.get("document_type") != "character_retarget" or document.get("id") != safe_id:
        raise HTTPException(status_code=409, detail="Retarget record is invalid.")
    data = document.get("data", {})
    source = _character_document(DATA_DIR, project_id, str(data.get("source_character_id", "")))
    target = _character_document(DATA_DIR, project_id, str(data.get("target_character_id", "")))

    def preview_asset(character: dict[str, Any]) -> tuple[str, dict[str, str]]:
        asset = character.get("data", {}).get("asset", {})
        relative_path = str(asset.get("relative_path", ""))
        try:
            asset_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
            asset_id = str(uuid.UUID(Path(relative_path).stem))
        except ValueError as error:
            raise HTTPException(
                status_code=409,
                detail="A retarget character asset path is invalid.",
            ) from error
        if not relative_path.startswith("assets/characters/") or not asset_path.is_file():
            raise HTTPException(status_code=404, detail="A retarget character GLB is missing.")
        raw_mapping = asset.get("rig_analysis", {}).get("godot_profile_mapping", {})
        if not isinstance(raw_mapping, dict):
            raise HTTPException(status_code=409, detail="A retarget humanoid mapping is invalid.")
        mapping: dict[str, str] = {}
        for profile_name, entry in raw_mapping.items():
            if isinstance(entry, dict) and isinstance(entry.get("source_name"), str):
                mapping[str(profile_name)] = entry["source_name"]
        return f"/api/projects/{project_id}/character-assets/{asset_id}", mapping

    source_url, source_mapping = preview_asset(source)
    target_url, target_mapping = preview_asset(target)
    return {
        "source_asset_url": source_url,
        "target_asset_url": target_url,
        "source_mapping": source_mapping,
        "target_mapping": target_mapping,
        "animation_name": str(data.get("animation_name", "")),
        "preview_kind": "threejs_browser_retarget",
        "authoritative_scene": f"/api/projects/{project_id}/retargets/{safe_id}/scene",
    }


@app.get("/api/projects/{project_id}/characters")
def list_characters(project_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with connect_db() as connection:
        exists = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        rows = connection.execute(
            """
            SELECT relative_path FROM project_documents
            WHERE project_id = ? AND document_type = 'character'
            ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    characters = []
    for row in rows:
        path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
        if path.is_file():
            document = read_json(path)
            if document.get("document_type") == "character":
                characters.append(document)
    return characters


@app.post("/api/projects/{project_id}/characters", status_code=201)
def create_character(
    project_id: str, payload: CharacterProfileInput
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id, created_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        asset_path = resolve_project_relative(DATA_DIR, project_id, payload.asset_path)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if not asset_path.is_file() or asset_path.suffix.lower() != ".glb":
        raise HTTPException(status_code=422, detail="Import a validated GLB asset first.")
    asset_id = asset_path.stem
    try:
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
        )
        manifest = read_json(manifest_path)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(
            status_code=422, detail="GLB asset has not passed import inspection."
        ) from error
    if (
        manifest.get("document_type") != "character_asset"
        or manifest.get("data", {}).get("relative_path") != payload.asset_path
    ):
        raise HTTPException(
            status_code=422,
            detail="Character asset manifest does not match the imported file.",
        )

    now = datetime.now(UTC).isoformat()
    character_id = str(uuid.uuid4())
    data = payload.model_dump(exclude={"asset_path"}, mode="json")
    data["name"] = payload.name.strip()
    data["description"] = payload.description.strip()
    data["asset"] = manifest["data"]
    data["appearance_recipe"] = {"materials": {}, "morph_targets": {}, "morph_bindings": {}}
    data["rig_status"] = (
        "ready" if manifest["data"].get("rig_ready") else "unrigged"
    )
    document = make_envelope(
        "character", character_id, data, now, now, 1
    )
    relative_path = f"characters/{character_id}.json"
    path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    digest = write_json_atomic(path, document)
    with connect_db() as connection:
        upsert_document_index(connection, project_id, document, relative_path, digest)
        sync_character_reference(connection, DATA_DIR, project_id, document)
    return document


@app.get("/api/projects/{project_id}/characters/{character_id}")
def get_character(project_id: str, character_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        exists = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    try:
        return _character_document(DATA_DIR, project_id, character_id)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.put("/api/projects/{project_id}/characters/{character_id}")
def update_character(
    project_id: str, character_id: str, payload: CharacterProfileInput
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    existing = _character_document(DATA_DIR, project_id, character_id)
    if payload.asset_path != existing.get("data", {}).get("asset", {}).get("relative_path"):
        raise HTTPException(
            status_code=422,
            detail="Changing a character's source asset requires a new import.",
        )
    now = datetime.now(UTC).isoformat()
    data = payload.model_dump(exclude={"asset_path"}, mode="json")
    data["name"] = payload.name.strip()
    data["description"] = payload.description.strip()
    data["asset"] = existing["data"]["asset"]
    data["appearance_recipe"] = existing["data"].get(
        "appearance_recipe", {"materials": {}, "morph_targets": {}, "morph_bindings": {}}
    )
    data["rig_status"] = existing["data"].get("rig_status", "unrigged")
    document = make_envelope(
        "character",
        character_id,
        data,
        existing["created_at"],
        now,
        int(existing.get("revision", 1)) + 1,
    )
    relative_path = f"characters/{character_id}.json"
    path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    digest = write_json_atomic(path, document)
    with connect_db() as connection:
        upsert_document_index(connection, project_id, document, relative_path, digest)
        sync_character_reference(connection, DATA_DIR, project_id, document)
    return document


@app.put("/api/projects/{project_id}/characters/{character_id}/appearance")
def update_character_appearance(
    project_id: str, character_id: str, payload: CharacterAppearanceInput
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        exists = connection.execute(
            "SELECT 1 FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    document = _character_document(DATA_DIR, project_id, character_id)
    appearance = payload.model_dump(mode="json", exclude_none=True)
    materials = appearance["materials"]
    morph_targets = appearance["morph_targets"]
    morph_bindings = appearance["morph_bindings"]
    if any(
        not key.strip() or len(key) > 512
        for key in [*materials, *morph_targets, *morph_bindings]
    ):
        raise HTTPException(
            status_code=422,
            detail="Material identifiers must be 1–512 characters.",
        )
    now = datetime.now(UTC).isoformat()
    data = dict(document["data"])
    data["appearance_recipe"] = {
        "materials": materials,
        "morph_targets": morph_targets,
        "morph_bindings": morph_bindings,
    }
    updated = make_envelope(
        "character",
        character_id,
        data,
        document["created_at"],
        now,
        int(document.get("revision", 1)) + 1,
    )
    relative_path = f"characters/{character_id}.json"
    path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    digest = write_json_atomic(path, updated)
    with connect_db() as connection:
        upsert_document_index(connection, project_id, updated, relative_path, digest)
        sync_character_reference(connection, DATA_DIR, project_id, updated)
    return updated

@app.post("/api/projects/{project_id}/characters/{character_id}/export", status_code=201)
def export_character_appearance(
    project_id: str, character_id: str, payload: CharacterAppearanceInput
) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    document = _character_document(DATA_DIR, project_id, character_id)
    data = document.get("data", {})
    source_relative_path = str(data.get("asset", {}).get("relative_path", ""))
    try:
        project_root = project_directory(DATA_DIR, project_id)
        source_path = resolve_project_relative(DATA_DIR, project_id, source_relative_path)
    except ValueError as error:
        raise HTTPException(
            status_code=422, detail="Character source asset path is invalid."
        ) from error
    if not source_path.is_file() or source_path.suffix.lower() != ".glb":
        raise HTTPException(status_code=404, detail="Character source GLB was not found.")
    appearance = payload.model_dump(mode="json", exclude_none=True)
    materials: list[dict[str, Any]] = []
    for key, values in appearance["materials"].items():
        if not values.get("mesh_name") or values.get("surface_index") is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Material edits need imported mesh/surface bindings. "
                    "Reopen and resave the editor."
                ),
            )
        if not any(
            values.get(field) is not None
            for field in ("color", "roughness", "metalness")
        ):
            raise HTTPException(
                status_code=422, detail="A material edit must change a PBR value."
            )
        materials.append({"key": key, **values})
    morph_targets: list[dict[str, Any]] = []
    for key, value in appearance["morph_targets"].items():
        binding = appearance["morph_bindings"].get(key)
        if binding is None:
            raise HTTPException(
                status_code=422,
                detail="Morph edits must include their imported mesh/target bindings.",
            )
        morph_targets.append({"key": key, **binding, "value": value})
    if not materials and not morph_targets:
        raise HTTPException(status_code=422, detail="There are no appearance edits to export.")
    asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{asset_id}.glb"
    destination = resolve_project_relative(DATA_DIR, project_id, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        inspection = get_engine_adapter().export_character_appearance(
            source_path, materials, morph_targets, destination, allowed_root=project_root
        )
        if not inspection.get("appearance_verified"):
            raise HTTPException(
                status_code=422,
                detail="Godot did not verify the customized GLB after export and re-import.",
            )
        container = _validate_glb_container(destination)
        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": "customized-character.glb",
            "relative_path": relative_path,
            "container": container,
            "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
            "source_character_id": character_id,
            "source_relative_path": source_relative_path,
            "appearance_recipe": appearance,
            "appearance_export_verified": True,
        }
        manifest = make_envelope("character_asset", asset_id, asset_data, now, now, 1)
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
        )
        digest = write_json_atomic(manifest_path, manifest)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, manifest,
                f"assets/characters/{asset_id}.json", digest
            )
        return {
            "asset_id": asset_id,
            "relative_path": relative_path,
            "download_url": f"/api/projects/{project_id}/character-assets/{asset_id}",
            "original_filename": asset_data["original_filename"],
            "appearance_verified": True,
            "applied_material_count": inspection.get("applied_material_count", 0),
            "applied_morph_count": inspection.get("applied_morph_count", 0),
        }
    except EngineUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except Exception:
        destination.unlink(missing_ok=True)
        raise


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
