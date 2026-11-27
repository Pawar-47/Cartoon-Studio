from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.audio import (
    SpeechEngineUnavailable,
    SpeechGenerationError,
    generate_episode_audio,
)
from app.character_builder import (
    CharacterLibraryError,
    UnknownCharacterModel,
    ensure_model_asset,
    get_character_catalog,
    get_model_spec,
)
from app.character_foundry import (
    MASTER_TEMPLATE_ID,
    default_character_recipe,
    validate_character_recipe,
    write_master_character,
)
from app.engine import (
    EngineError,
    EnginePathError,
    EngineTimeoutError,
    EngineUnavailableError,
    GodotEngineAdapter,
)
from app.render import (
    RenderDependencyUnavailable,
    RenderExecutionError,
    RenderPathError,
    render_episode_video,
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
from app.storage import (
    initialize_database as migrate_database,
)
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


class WorldObjectInput(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    kind: Literal["road", "building", "shop", "tree", "vehicle", "lamp", "park"]
    label: str = Field(min_length=1, max_length=80)
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(default=12, ge=2, le=100)
    height: float = Field(default=8, ge=2, le=60)
    rotation: float = Field(default=0, ge=0, le=360)
    color: str = Field(default="#c89b67", pattern=r"^#[0-9a-fA-F]{6}$")


class WorldPlanInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    theme: Literal["small_town", "village", "market", "park"] = "small_town"
    ground_color: str = Field(default="#789b58", pattern=r"^#[0-9a-fA-F]{6}$")
    sky: Literal["day", "sunset", "night"] = "day"
    objects: list[WorldObjectInput] = Field(default_factory=list, max_length=100)


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


class FoundryCharacterInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=1000)
    master_template_id: str = Field(default=MASTER_TEMPLATE_ID, min_length=1, max_length=128)
    parameters: dict[str, Annotated[float, Field(ge=-1, le=1)]] = Field(
        default_factory=dict, max_length=32
    )


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


class FaceFeatureInput(BaseModel):
    enabled: bool = False
    skin_color: str = Field(default="#c98768", pattern=r"^#[0-9a-fA-F]{6}$")
    eye_color: str = Field(default="#ffffff", pattern=r"^#[0-9a-fA-F]{6}$")
    iris_color: str = Field(default="#4b83b8", pattern=r"^#[0-9a-fA-F]{6}$")
    brow_color: str = Field(default="#38251c", pattern=r"^#[0-9a-fA-F]{6}$")
    mouth_color: str = Field(default="#612b2b", pattern=r"^#[0-9a-fA-F]{6}$")
    nose_color: str = Field(default="#c98768", pattern=r"^#[0-9a-fA-F]{6}$")
    face_width: float = Field(default=1.0, ge=0.8, le=1.25)
    cheek_fullness: float = Field(default=1.0, ge=0.5, le=1.5)
    jaw_width: float = Field(default=1.0, ge=0.7, le=1.3)
    chin_length: float = Field(default=1.0, ge=0.65, le=1.4)
    eye_scale: float = Field(default=1.0, ge=0.65, le=1.5)
    eye_spacing: float = Field(default=1.0, ge=0.65, le=1.35)
    smile: float = Field(default=0.35, ge=-1, le=1)
    mouth_open: float = Field(default=0.0, ge=0, le=1)
    brow_angle: float = Field(default=0.0, ge=-0.5, le=0.5)
    ear_size: float = Field(default=1.0, ge=0.6, le=1.5)
    nose_width: float = Field(default=1.0, ge=0.65, le=1.5)
    nose_height: float = Field(default=1.0, ge=0.65, le=1.5)
    mouth_width: float = Field(default=1.0, ge=0.65, le=1.5)


class CharacterAppearanceInput(BaseModel):
    materials: dict[str, MaterialAppearanceInput] = Field(default_factory=dict, max_length=256)
    face_features: FaceFeatureInput = Field(default_factory=FaceFeatureInput)
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
    for character in plan_data["characters"]:
        asset_id = character.get("asset_id")
        if not asset_id:
            continue
        selected_asset = next(
            (
                asset
                for asset in _project_character_assets(project_id)
                if asset["asset_id"] == asset_id
            ),
            None,
        )
        if selected_asset is None:
            raise HTTPException(
                status_code=422,
                detail=f"Character asset for {character['name']} is not in this project.",
            )
        if not selected_asset["rig_ready"]:
            raise HTTPException(
                status_code=422,
                detail=f"Character asset for {character['name']} is not rig-ready.",
            )
    if plan_data.get("world_id"):
        selected_world = next(
            (
                world
                for world in _project_worlds(project_id)
                if world["id"] == plan_data["world_id"]
            ),
            None,
        )
        if selected_world is None:
            raise HTTPException(
                status_code=422,
                detail="The selected world does not belong to this project.",
            )
        scene_relative_path = str(selected_world.get("scene_relative_path", ""))
        if (
            not scene_relative_path.startswith("assets/worlds/")
            or not scene_relative_path.endswith(".tscn")
        ):
            raise HTTPException(
                status_code=422,
                detail="Generate the selected world's 3D scene before saving this episode.",
            )
        scene_path = resolve_project_relative(
            DATA_DIR, project_id, scene_relative_path
        )
        if not scene_path.is_file():
            raise HTTPException(
                status_code=422,
                detail="The selected world's exported 3D scene is missing.",
            )
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


def _latest_episode_speech_tracks(
    project_id: str,
    episode_id: str,
) -> list[dict[str, Any]]:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT relative_path FROM project_documents
            WHERE project_id = ? AND document_type = 'episode_audio'
            ORDER BY updated_at DESC LIMIT 1
            """,
            (project_id,),
        ).fetchone()
    if row is None:
        return []
    manifest_path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    if not manifest_path.is_file():
        return []
    manifest = read_json(manifest_path)
    data = manifest.get("data", {})
    if data.get("episode_id") != episode_id:
        return []
    speech_tracks = []
    for clip in data.get("clips", []):
        envelope = clip.get("mouth_envelope")
        if not isinstance(envelope, list) or not envelope:
            continue
        speech_tracks.append({
            "scene_id": clip.get("scene_id", ""),
            "line_index": clip.get("line_index"),
            "duration_seconds": clip.get("duration_seconds", 0),
            "mouth_envelope": envelope,
        })
    return speech_tracks


@app.post("/api/projects/{project_id}/story/production")
def build_episode_production(project_id: str) -> dict[str, Any]:
    saved = get_story_plan(project_id)
    plan = saved["plan"]
    episode_id = saved["episode_id"]
    world_id = plan.get("world_id")
    if not world_id:
        raise HTTPException(
            status_code=422,
            detail="Select and export a 3D world before production.",
        )
    world = next(
        (item for item in _project_worlds(project_id) if item["id"] == world_id),
        None,
    )
    if world is None:
        raise HTTPException(
            status_code=422, detail="The episode's saved world is unavailable."
        )
    world_relative = str(world.get("scene_relative_path", ""))
    if not world_relative.startswith("assets/worlds/") or not world_relative.endswith(
        ".tscn"
    ):
        raise HTTPException(
            status_code=422,
            detail="Export the selected world scene before production.",
        )
    world_scene = resolve_project_relative(DATA_DIR, project_id, world_relative)
    if not world_scene.is_file():
        raise HTTPException(status_code=422, detail="The selected world scene file is missing.")
    available_assets = {
        item["asset_id"]: item for item in _project_character_assets(project_id)
    }
    character_assets = []
    for character in plan["characters"]:
        asset_id = character.get("asset_id")
        asset = available_assets.get(asset_id)
        if asset is None or not asset["rig_ready"]:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Link a rigged project GLB to character {character['name']} "
                    "before production."
                ),
            )
        character_assets.append({
            "id": character["id"],
            "name": character["name"],
            "asset_path": str(
                resolve_project_relative(DATA_DIR, project_id, asset["relative_path"])
            ),
        })
    build_id = str(uuid.uuid4())
    relative_output = f"assets/episodes/{episode_id}/builds/{build_id}/scenes"
    output_directory = resolve_project_relative(DATA_DIR, project_id, relative_output)
    speech_tracks = _latest_episode_speech_tracks(project_id, episode_id)
    episode_for_render = copy.deepcopy(plan)
    for track in speech_tracks:
        scene = next(
            (
                item
                for item in episode_for_render["scenes"]
                if item["id"] == track["scene_id"]
            ),
            None,
        )
        line_index = track["line_index"]
        if scene is None or not 1 <= line_index <= len(scene["dialogue"]):
            continue
        dialogue_line = scene["dialogue"][line_index - 1]
        dialogue_line["audio_envelope"] = track["mouth_envelope"]
        dialogue_line["audio_duration_seconds"] = track["duration_seconds"]
    try:
        result = get_engine_adapter().export_episode_scenes(
            episode_for_render,
            world_scene,
            character_assets,
            output_directory,
            allowed_root=project_directory(DATA_DIR, project_id),
        )
    except EngineUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        shutil.rmtree(output_directory.parent, ignore_errors=True)
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        shutil.rmtree(output_directory.parent, ignore_errors=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        shutil.rmtree(output_directory.parent, ignore_errors=True)
        raise HTTPException(
            status_code=502,
            detail=f"Episode scene generation failed: {error}",
        ) from error
    if not result.get("ok") or len(result.get("scenes", [])) != len(plan["scenes"]):
        shutil.rmtree(output_directory.parent, ignore_errors=True)
        raise HTTPException(status_code=502, detail="Godot did not generate every episode scene.")
    project_root = project_directory(DATA_DIR, project_id).resolve()
    scenes = []
    for item in result["scenes"]:
        scene_relative = str(
            Path(item["scene_path"]).resolve().relative_to(project_root)
        ).replace("\\", "/")
        preview_relative = str(
            Path(item["preview_path"]).resolve().relative_to(project_root)
        ).replace("\\", "/")
        scenes.append({
            "scene_id": item["scene_id"],
            "title": item["title"],
            "duration_seconds": item["duration_seconds"],
            "character_count": item["character_count"],
            "dialogue_line_count": item["dialogue_line_count"],
            "action_cue_count": item["action_cue_count"],
            "expression_cue_count": item.get("expression_cue_count", 0),
            "audio_driven_speech_cue_count": item.get(
                "audio_driven_speech_cue_count", 0
            ),
            "audio_envelope_keyframe_count": item.get(
                "audio_envelope_keyframe_count", 0
            ),
            "scene_relative_path": scene_relative,
            "preview_relative_path": preview_relative,
            "scene_reopened": item["scene_reopened"],
            "reopened_character_count": item["reopened_character_count"],
        })
    now = datetime.now(UTC).isoformat()
    data = {
        "episode_id": episode_id,
        "episode_title": plan["title"],
        "world_id": world_id,
        "character_asset_ids": [item["asset_id"] for item in plan["characters"]],
        "scene_count": len(scenes),
        "total_duration_seconds": sum(item["duration_seconds"] for item in scenes),
        "scenes": scenes,
        "generated_at": now,
    }
    relative_manifest = f"assets/episodes/{episode_id}/builds/{build_id}/production.json"
    manifest = make_envelope("episode_production", build_id, data, now, now, 1)
    digest = write_json_atomic(
        resolve_project_relative(DATA_DIR, project_id, relative_manifest), manifest
    )
    with connect_db() as connection:
        upsert_document_index(
            connection, project_id, manifest, relative_manifest, digest
        )
    return {"build_id": build_id, **data}


def _latest_episode_manifest(
    project_id: str,
    document_type: str,
    episode_id: str,
) -> dict[str, Any] | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT relative_path FROM project_documents
            WHERE project_id = ? AND document_type = ?
            ORDER BY updated_at DESC LIMIT 1
            """,
            (project_id, document_type),
        ).fetchone()
    if row is None:
        return None
    path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    if not path.is_file():
        return None
    manifest = read_json(path)
    if manifest.get("data", {}).get("episode_id") != episode_id:
        return None
    return manifest


@app.post("/api/projects/{project_id}/story/render")
def render_episode(project_id: str) -> dict[str, Any]:
    saved = get_story_plan(project_id)
    episode_id = saved["episode_id"]
    production = _latest_episode_manifest(project_id, "episode_production", episode_id)
    audio = _latest_episode_manifest(project_id, "episode_audio", episode_id)
    if production is None or audio is None:
        raise HTTPException(
            status_code=422,
            detail="Generate the episode's 3D scenes and Urdu dialogue audio before rendering.",
        )
    production_data = production["data"]
    audio_data = audio["data"]
    scenes = production_data.get("scenes", [])
    if not scenes:
        raise HTTPException(status_code=422, detail="The episode has no generated scenes.")
    if not audio_data.get("subtitles_relative_path"):
        raise HTTPException(
            status_code=422,
            detail="Regenerate Urdu dialogue audio to create the timed subtitle file.",
        )
    audio_clips = audio_data.get("clips", [])
    if any(clip.get("mouth_envelope") for clip in audio_clips):
        if not any(
            scene.get("audio_driven_speech_cue_count", 0) > 0
            for scene in scenes
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Regenerate the 3D scenes after dialogue audio so mouth movement "
                    "matches speech."
                ),
            )
    project_root = project_directory(DATA_DIR, project_id)
    scene_paths = [
        resolve_project_relative(DATA_DIR, project_id, scene["scene_relative_path"])
        for scene in scenes
    ]
    scene_durations = [int(scene["duration_seconds"]) for scene in scenes]
    audio_path = resolve_project_relative(
        DATA_DIR, project_id, audio_data["audio_relative_path"]
    )
    subtitles_path = resolve_project_relative(
        DATA_DIR, project_id, audio_data["subtitles_relative_path"]
    )
    render_id = str(uuid.uuid4())
    relative_output = f"assets/episodes/{episode_id}/renders/{render_id}"
    output_directory = resolve_project_relative(DATA_DIR, project_id, relative_output)
    output_path = output_directory / "episode.mp4"
    try:
        result = render_episode_video(
            scene_paths,
            scene_durations,
            audio_path,
            subtitles_path,
            output_path,
            project_root,
            get_engine_adapter().executable,
        )
    except RenderDependencyUnavailable as error:
        shutil.rmtree(output_directory, ignore_errors=True)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except RenderPathError as error:
        shutil.rmtree(output_directory, ignore_errors=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RenderExecutionError as error:
        shutil.rmtree(output_directory, ignore_errors=True)
        raise HTTPException(status_code=502, detail=str(error)) from error
    video_relative = str(
        Path(result["video_path"]).resolve().relative_to(project_root.resolve())
    ).replace("\\", "/")
    now = datetime.now(UTC).isoformat()
    data = {
        "episode_id": episode_id,
        "episode_title": saved["plan"]["title"],
        "video_relative_path": video_relative,
        "duration_seconds": result["duration_seconds"],
        "fps": result["fps"],
        "width": result["width"],
        "height": result["height"],
        "size_bytes": result["size_bytes"],
        "rendered_at_elapsed_seconds": result["rendered_at_elapsed_seconds"],
        "generated_at": now,
    }
    relative_manifest = f"{relative_output}/render.json"
    manifest = make_envelope("episode_render", render_id, data, now, now, 1)
    digest = write_json_atomic(
        resolve_project_relative(DATA_DIR, project_id, relative_manifest),
        manifest,
    )
    with connect_db() as connection:
        upsert_document_index(
            connection, project_id, manifest, relative_manifest, digest
        )
    return {
        "build_id": render_id,
        **data,
        "video_url": f"/api/projects/{project_id}/story/render/{render_id}/mp4",
    }


@app.get("/api/projects/{project_id}/story/render/{render_id}/mp4")
def download_episode_video(project_id: str, render_id: str) -> FileResponse:
    initialize_database()
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'episode_render'
            """,
            (project_id, render_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Episode video render not found.")
    manifest_path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="Episode video manifest is missing.")
    manifest = read_json(manifest_path)
    relative_path = str(manifest.get("data", {}).get("video_relative_path", ""))
    if not relative_path.startswith("assets/episodes/") or not relative_path.endswith(".mp4"):
        raise HTTPException(status_code=409, detail="Episode video path is invalid.")
    video_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Episode MP4 file is missing.")
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"{render_id}-episode.mp4",
    )


@app.post("/api/projects/{project_id}/story/audio")
def build_episode_audio(project_id: str) -> dict[str, Any]:
    saved = get_story_plan(project_id)
    plan = saved["plan"]
    episode_id = saved["episode_id"]
    build_id = str(uuid.uuid4())
    relative_output = f"assets/episodes/{episode_id}/audio/builds/{build_id}"
    output_directory = resolve_project_relative(DATA_DIR, project_id, relative_output)
    try:
        result = generate_episode_audio(
            plan,
            output_directory,
            DATA_DIR,
        )
    except SpeechEngineUnavailable as error:
        shutil.rmtree(output_directory, ignore_errors=True)
        raise HTTPException(status_code=503, detail=str(error)) from error
    except SpeechGenerationError as error:
        shutil.rmtree(output_directory, ignore_errors=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    project_root = project_directory(DATA_DIR, project_id).resolve()
    audio_relative = str(
        Path(result["audio_path"]).resolve().relative_to(project_root)
    ).replace("\\", "/")
    subtitles_relative = str(
        Path(result["subtitles_path"]).resolve().relative_to(project_root)
    ).replace("\\", "/")
    clips = []
    for clip in result["clips"]:
        clip_path = output_directory / clip["relative_path"]
        clips.append({**clip, "relative_path": str(
            clip_path.resolve().relative_to(project_root)
        ).replace("\\", "/")})
    now = datetime.now(UTC).isoformat()
    data = {
        "episode_id": episode_id,
        "episode_title": plan["title"],
        "duration_seconds": result["duration_seconds"],
        "sample_rate": result["sample_rate"],
        "dialogue_line_count": result["dialogue_line_count"],
        "voices": result["voices"],
        "audio_relative_path": audio_relative,
        "subtitles_relative_path": subtitles_relative,
        "clips": clips,
        "generated_at": now,
    }
    relative_manifest = f"{relative_output}/audio.json"
    manifest = make_envelope("episode_audio", build_id, data, now, now, 1)
    digest = write_json_atomic(
        resolve_project_relative(DATA_DIR, project_id, relative_manifest),
        manifest,
    )
    with connect_db() as connection:
        upsert_document_index(
            connection, project_id, manifest, relative_manifest, digest
        )
    return {
        "build_id": build_id,
        **data,
        "audio_url": f"/api/projects/{project_id}/story/audio/{build_id}/wav",
    }


@app.get("/api/projects/{project_id}/story/audio/{build_id}/subtitles")
def download_episode_subtitles(project_id: str, build_id: str) -> FileResponse:
    initialize_database()
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'episode_audio'
            """,
            (project_id, build_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Episode audio build not found.")
    manifest_path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="Episode audio manifest is missing.")
    manifest = read_json(manifest_path)
    relative_path = str(manifest.get("data", {}).get("subtitles_relative_path", ""))
    if not relative_path.startswith("assets/episodes/"):
        raise HTTPException(status_code=409, detail="Episode subtitle path is invalid.")
    subtitles_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    if not subtitles_path.is_file():
        raise HTTPException(status_code=404, detail="Episode subtitles are missing.")
    return FileResponse(
        subtitles_path,
        media_type="text/plain; charset=utf-8",
        filename="cartoon-studio-subtitles.srt",
    )


@app.get("/api/projects/{project_id}/story/audio/{build_id}/wav")
def download_episode_audio(project_id: str, build_id: str) -> FileResponse:
    initialize_database()
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'episode_audio'
            """,
            (project_id, build_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Episode audio build not found.")
    manifest_path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    if not manifest_path.is_file():
        raise HTTPException(status_code=404, detail="Episode audio manifest is missing.")
    manifest = read_json(manifest_path)
    relative_path = str(manifest.get("data", {}).get("audio_relative_path", ""))
    if not relative_path.startswith("assets/episodes/") or not relative_path.endswith(".wav"):
        raise HTTPException(status_code=409, detail="Episode audio path is invalid.")
    audio_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    if not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Episode audio file is missing.")
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=f"{build_id}-dialogue.wav",
    )


@app.get("/api/projects/{project_id}/story/production")
def get_episode_production(project_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_type = 'episode_production'
            ORDER BY updated_at DESC LIMIT 1
            """,
            (project_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No episode production has been generated.")
    path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Episode production manifest is missing.")
    manifest = read_json(path)
    return {"build_id": manifest["id"], **manifest["data"]}


@app.get("/api/projects/{project_id}/story/production/{build_id}/scenes/{scene_id}/{file_format}")
def download_episode_scene(
    project_id: str, build_id: str, scene_id: str, file_format: str
) -> FileResponse:
    if file_format not in {"tscn", "glb"}:
        raise HTTPException(status_code=404, detail="Unsupported episode scene format.")
    initialize_database()
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'episode_production'
            """,
            (project_id, build_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Episode production build not found.")
    manifest_path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
    manifest = read_json(manifest_path)
    scene = next(
        (item for item in manifest["data"]["scenes"] if item["scene_id"] == scene_id),
        None,
    )
    if scene is None:
        raise HTTPException(status_code=404, detail="Episode scene not found.")
    relative_path = (
        scene["scene_relative_path"]
        if file_format == "tscn"
        else scene["preview_relative_path"]
    )
    if not relative_path.startswith("assets/episodes/"):
        raise HTTPException(status_code=409, detail="Episode scene path is invalid.")
    scene_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    if not scene_path.is_file():
        raise HTTPException(status_code=404, detail="Episode scene file is missing.")
    media_type = "model/gltf-binary" if file_format == "glb" else "application/octet-stream"
    return FileResponse(
        scene_path,
        media_type=media_type,
        filename=f"{scene_id}.{file_format}",
    )


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




@app.get("/worlds", include_in_schema=False)
def world_builder() -> FileResponse:
    return FileResponse(STATIC_DIR / "worlds.html")


def _project_worlds(project_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        rows = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_type = 'world'
            ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    worlds = []
    for row in rows:
        path = resolve_project_relative(DATA_DIR, project_id, row["relative_path"])
        if path.is_file():
            document = read_json(path)
            worlds.append({
                "id": document["id"],
                "revision": document["revision"],
                "updated_at": document["updated_at"],
                **document["data"],
            })
    return worlds


def _project_character_assets(project_id: str) -> list[dict[str, Any]]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        rows = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_type = 'character_asset'
            ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    assets = []
    for row in rows:
        manifest_path = resolve_project_relative(
            DATA_DIR, project_id, row["relative_path"]
        )
        if not manifest_path.is_file():
            continue
        manifest = read_json(manifest_path)
        data = manifest.get("data", {})
        relative_path = str(data.get("relative_path", ""))
        if (
            manifest.get("document_type") != "character_asset"
            or manifest.get("id") != row["document_id"]
            or not relative_path.startswith("assets/characters/")
            or not relative_path.endswith(".glb")
        ):
            continue
        asset_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
        if not asset_path.is_file():
            continue
        assets.append({
            "asset_id": manifest["id"],
            "original_filename": str(data.get("original_filename", "Character GLB")),
            "relative_path": relative_path,
            "rig_ready": bool(data.get("rig_ready", False)),
            "animation_ready": bool(data.get("animation_ready", False)),
        })
    return assets


def _sync_world_reference(project_id: str, world_document: dict[str, Any]) -> None:
    project_path = project_directory(DATA_DIR, project_id) / "project.json"
    project_document = read_json(project_path)
    references = project_document.setdefault("data", {}).setdefault("references", {})
    world_ids = references.setdefault("worlds", [])
    if world_document["id"] not in world_ids:
        world_ids.append(world_document["id"])
    project_document["revision"] = int(project_document.get("revision", 1)) + 1
    project_document["updated_at"] = world_document["updated_at"]
    digest = write_json_atomic(project_path, project_document)
    with connect_db() as connection:
        upsert_document_index(
            connection, project_id, project_document, "project.json", digest
        )
        connection.execute(
            "UPDATE projects SET updated_at = ? WHERE id = ?",
            (world_document["updated_at"], project_id),
        )


@app.get("/api/projects/{project_id}/worlds")
def list_project_worlds(project_id: str) -> list[dict[str, Any]]:
    return _project_worlds(project_id)


@app.post("/api/projects/{project_id}/worlds", status_code=201)
def create_project_world(project_id: str, payload: WorldPlanInput) -> dict[str, Any]:
    initialize_database()
    now = datetime.now(UTC).isoformat()
    world_id = str(uuid.uuid4())
    data = payload.model_dump(mode="json")
    data["name"] = data["name"].strip()
    if not data["name"]:
        raise HTTPException(status_code=422, detail="World name cannot be blank.")
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id, created_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        document = make_envelope("world", world_id, data, project["created_at"], now)
        relative_path = f"worlds/{world_id}.json"
        digest = write_json_atomic(
            resolve_project_relative(DATA_DIR, project_id, relative_path), document
        )
        upsert_document_index(connection, project_id, document, relative_path, digest)
    _sync_world_reference(project_id, document)
    return {"id": world_id, "revision": 1, "updated_at": now, **data}


@app.get("/api/projects/{project_id}/worlds/{world_id}")
def get_project_world(project_id: str, world_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        indexed = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'world'
            """,
            (project_id, world_id),
        ).fetchone()
    if project is None or indexed is None:
        raise HTTPException(status_code=404, detail="World not found.")
    path = resolve_project_relative(DATA_DIR, project_id, indexed["relative_path"])
    if not path.is_file():
        raise HTTPException(status_code=404, detail="World document not found.")
    document = read_json(path)
    return {
        "id": document["id"],
        "revision": document["revision"],
        "updated_at": document["updated_at"],
        **document["data"],
    }


@app.put("/api/projects/{project_id}/worlds/{world_id}")
def update_project_world(
    project_id: str, world_id: str, payload: WorldPlanInput
) -> dict[str, Any]:
    initialize_database()
    now = datetime.now(UTC).isoformat()
    data = payload.model_dump(mode="json")
    data["name"] = data["name"].strip()
    if not data["name"]:
        raise HTTPException(status_code=422, detail="World name cannot be blank.")
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        indexed = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'world'
            """,
            (project_id, world_id),
        ).fetchone()
        if project is None or indexed is None:
            raise HTTPException(status_code=404, detail="World not found.")
        path = resolve_project_relative(DATA_DIR, project_id, indexed["relative_path"])
        document = read_json(path)
        document["data"] = data
        document["revision"] = int(document.get("revision", 1)) + 1
        document["updated_at"] = now
        digest = write_json_atomic(path, document)
        upsert_document_index(
            connection, project_id, document, indexed["relative_path"], digest
        )
    _sync_world_reference(project_id, document)
    return {
        "id": world_id,
        "revision": document["revision"],
        "updated_at": now,
        **data,
    }



@app.post("/api/projects/{project_id}/worlds/{world_id}/export")
def export_project_world(project_id: str, world_id: str) -> dict[str, Any]:
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        indexed = connection.execute(
            """
            SELECT * FROM project_documents
            WHERE project_id = ? AND document_id = ? AND document_type = 'world'
            """,
            (project_id, world_id),
        ).fetchone()
    if project is None or indexed is None:
        raise HTTPException(status_code=404, detail="World not found.")
    world_path = resolve_project_relative(DATA_DIR, project_id, indexed["relative_path"])
    if not world_path.is_file():
        raise HTTPException(status_code=404, detail="World document not found.")
    document = read_json(world_path)
    export_id = str(uuid.uuid4())
    relative_scene = f"assets/worlds/{export_id}.tscn"
    relative_preview = f"assets/worlds/{export_id}.glb"
    scene_path = resolve_project_relative(DATA_DIR, project_id, relative_scene)
    preview_path = resolve_project_relative(DATA_DIR, project_id, relative_preview)
    project_root = project_directory(DATA_DIR, project_id)
    try:
        result = get_engine_adapter().export_world_scene(
            document["data"], scene_path, allowed_root=project_root
        )
    except EngineUnavailableError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except EngineTimeoutError as error:
        scene_path.unlink(missing_ok=True)
        preview_path.unlink(missing_ok=True)
        raise HTTPException(status_code=504, detail=str(error)) from error
    except EnginePathError as error:
        scene_path.unlink(missing_ok=True)
        preview_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except EngineError as error:
        scene_path.unlink(missing_ok=True)
        preview_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=502, detail=f"World scene export failed: {error}"
        ) from error
    if (
        not result.get("ok")
        or not scene_path.is_file()
        or not preview_path.is_file()
    ):
        scene_path.unlink(missing_ok=True)
        preview_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=502,
            detail="Godot did not produce both the scene and its browser preview.",
        )
    now = datetime.now(UTC).isoformat()
    document["data"]["scene_relative_path"] = relative_scene
    document["data"]["preview_relative_path"] = relative_preview
    document["data"]["scene_exported_at"] = now
    document["data"]["scene_export"] = {
        "object_count": int(result.get("object_count", 0)),
        "theme_prop_count": int(result.get("theme_prop_count", 0)),
        "scene_reopened": bool(result.get("scene_reopened", False)),
        "lighting_preset": str(result.get("lighting_preset", document["data"].get("sky", "day"))),
    }
    document["revision"] = int(document.get("revision", 1)) + 1
    document["updated_at"] = now
    digest = write_json_atomic(world_path, document)
    with connect_db() as connection:
        upsert_document_index(connection, project_id, document, indexed["relative_path"], digest)
    _sync_world_reference(project_id, document)
    return {
        "world_id": world_id,
        "scene_relative_path": relative_scene,
        "scene_url": f"/api/projects/{project_id}/worlds/{world_id}/scene",
        "preview_url": f"/api/projects/{project_id}/worlds/{world_id}/preview",
        **document["data"]["scene_export"],
    }


@app.get("/api/projects/{project_id}/worlds/{world_id}/preview")
def preview_project_world(project_id: str, world_id: str) -> FileResponse:
    world = get_project_world(project_id, world_id)
    relative_path = str(world.get("preview_relative_path", ""))
    if not relative_path.startswith("assets/worlds/") or not relative_path.endswith(".glb"):
        raise HTTPException(status_code=404, detail="World preview has not been exported.")
    preview_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    if not preview_path.is_file():
        raise HTTPException(status_code=404, detail="World preview file is missing.")
    return FileResponse(
        preview_path,
        media_type="model/gltf-binary",
        filename=f"world-{world_id}.glb",
    )


@app.get("/api/projects/{project_id}/worlds/{world_id}/scene")
def download_project_world_scene(project_id: str, world_id: str) -> FileResponse:
    world = get_project_world(project_id, world_id)
    relative_path = str(world.get("scene_relative_path", ""))
    if not relative_path.startswith("assets/worlds/") or not relative_path.endswith(".tscn"):
        raise HTTPException(status_code=404, detail="World scene has not been exported.")
    scene_path = resolve_project_relative(DATA_DIR, project_id, relative_path)
    if not scene_path.is_file():
        raise HTTPException(status_code=404, detail="World scene file is missing.")
    return FileResponse(scene_path, media_type="text/plain", filename=f"world-{world_id}.tscn")


@app.get("/characters", include_in_schema=False)
def character_studio() -> FileResponse:
    return FileResponse(STATIC_DIR / "characters.html")



@app.put("/api/projects/{project_id}/foundry-characters/{character_id}")
def update_foundry_character(
    project_id: str, character_id: str, payload: FoundryCharacterInput
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
    previous = data.get("foundry_recipe")
    if not isinstance(previous, dict):
        raise HTTPException(
            status_code=409, detail="This character has no editable Foundry recipe."
        )
    recipe = dict(previous)
    recipe["master_template_id"] = payload.master_template_id
    recipe["parameters"] = dict(payload.parameters)
    try:
        recipe = validate_character_recipe(recipe)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    asset_id = str(uuid.uuid4())
    relative_asset = f"assets/characters/{asset_id}.glb"
    relative_recipe = f"characters/foundry/{character_id}.recipe.json"
    asset_path = resolve_project_relative(DATA_DIR, project_id, relative_asset)
    recipe_path = resolve_project_relative(DATA_DIR, project_id, relative_recipe)
    manifest_path = resolve_project_relative(
        DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
    )
    temp_asset = asset_path.with_name(f".{asset_id}.tmp.glb")
    temp_recipe = recipe_path.with_name(f".{asset_id}.tmp.json")
    try:
        write_master_character(temp_asset, recipe_path=temp_recipe, recipe=recipe)
        container = _validate_glb_container(temp_asset)
        try:
            inspection = get_engine_adapter().inspect_glb(
                temp_asset, allowed_root=project_directory(DATA_DIR, project_id)
            )
        except EngineUnavailableError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except EngineTimeoutError as error:
            raise HTTPException(status_code=504, detail=str(error)) from error
        except EngineError as error:
            raise HTTPException(
                status_code=422,
                detail=f"Godot could not import the Foundry character: {error}",
            ) from error
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        temp_asset.replace(asset_path)
        saved_recipe = json.loads(temp_recipe.read_text(encoding="utf-8"))
        saved_recipe["generated_asset"]["filename"] = asset_path.name
        recipe_path.parent.mkdir(parents=True, exist_ok=True)
        recipe_path.write_text(
            json.dumps(saved_recipe, indent=2, ensure_ascii=False) + chr(10),
            encoding="utf-8",
        )
        temp_recipe.unlink(missing_ok=True)
        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": f"{payload.name.strip()}.glb", "relative_path": relative_asset,
            "container": container, "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
            "generator": {
                "name": "Cartoon Studio Character Foundry",
                "version": saved_recipe["generator_version"],
                "template_id": saved_recipe["master_template_id"], "recipe_path": relative_recipe,
                "morph_targets": list(saved_recipe["parameters"])},
        }
        manifest = make_envelope("character_asset", asset_id, asset_data, now, now, 1)
        manifest_digest = write_json_atomic(manifest_path, manifest)
        updated_data = dict(data)
        updated_data.update(
            {"name": payload.name.strip(), "description": payload.description.strip(),
            "asset": asset_data, "foundry_recipe": saved_recipe,
            "rig_status": "ready" if asset_data["rig_ready"] else "unrigged"})
        updated = make_envelope(
            "character", character_id, updated_data, document["created_at"], now,
            int(document.get("revision", 1)) + 1)
        character_path = resolve_project_relative(
            DATA_DIR, project_id, f"characters/{character_id}.json"
        )
        character_digest = write_json_atomic(character_path, updated)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, manifest,
                f"assets/characters/{asset_id}.json", manifest_digest
            )
            upsert_document_index(
                connection, project_id, updated,
                f"characters/{character_id}.json", character_digest
            )
            sync_character_reference(connection, DATA_DIR, project_id, updated)
        return {**updated, "asset_id": asset_id,
            "asset_url": f"/api/projects/{project_id}/character-assets/{asset_id}",
            "recipe_path": relative_recipe,
        }
    except BaseException:
        temp_asset.unlink(missing_ok=True)
        temp_recipe.unlink(missing_ok=True)
        asset_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise


@app.get("/api/character-builder/catalog")
def character_builder_catalog() -> dict[str, Any]:
    return get_character_catalog()


@app.post("/api/projects/{project_id}/foundry-characters", status_code=201)
def create_foundry_character(
    project_id: str, payload: FoundryCharacterInput
) -> dict[str, Any]:
    """Generate an editable Foundry recipe and register its GLB in the project library."""
    initialize_database()
    with connect_db() as connection:
        project = connection.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    character_id = str(uuid.uuid4())
    asset_id = str(uuid.uuid4())
    recipe = default_character_recipe(character_id, payload.master_template_id)
    recipe["parameters"].update(payload.parameters)
    try:
        recipe = validate_character_recipe(recipe)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    relative_asset = f"assets/characters/{asset_id}.glb"
    relative_recipe = f"characters/foundry/{character_id}.recipe.json"
    asset_path = resolve_project_relative(DATA_DIR, project_id, relative_asset)
    recipe_path = resolve_project_relative(DATA_DIR, project_id, relative_recipe)
    manifest_path = resolve_project_relative(
        DATA_DIR, project_id, f"assets/characters/{asset_id}.json"
    )
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        write_master_character(asset_path, recipe_path=recipe_path, recipe=recipe)
        container = _validate_glb_container(asset_path)
        try:
            inspection = get_engine_adapter().inspect_glb(
                asset_path, allowed_root=project_directory(DATA_DIR, project_id)
            )
        except EngineUnavailableError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except EngineTimeoutError as error:
            raise HTTPException(status_code=504, detail=str(error)) from error
        except EngineError as error:
            raise HTTPException(
                status_code=422, detail=f"Godot could not import the Foundry character: {error}"
            ) from error

        now = datetime.now(UTC).isoformat()
        asset_data = {
            "original_filename": f"{payload.name.strip()}.glb",
            "relative_path": relative_asset,
            "container": container,
            "engine_inspection": inspection,
            "rig_analysis": analyze_rig(inspection),
            "rig_ready": int(inspection.get("skeleton_count", 0)) > 0,
            "animation_ready": int(inspection.get("animation_count", 0)) > 0,
            "generator": {
                "name": "Cartoon Studio Character Foundry",
                "version": recipe["generator_version"],
                "template_id": recipe["master_template_id"],
                "recipe_path": relative_recipe,
                "morph_targets": list(recipe["parameters"]),
            },
        }
        manifest = make_envelope(
            "character_asset", asset_id, asset_data, now, now, 1
        )
        digest = write_json_atomic(manifest_path, manifest)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, manifest,
                f"assets/characters/{asset_id}.json", digest
            )

        data = {
            "name": payload.name.strip(),
            "description": payload.description.strip(),
            "face_design": "Original editable Cartoon Studio Foundry master character.",
            "body_proportions": {},
            "height_cm": None,
            "hair": "",
            "clothing": ["Foundry casual outfit"] if recipe["clothing_asset_ids"] else [],
            "accessories": [],
            "eye_design": "Stylized cartoon eyes",
            "mouth_design": "Stylized cartoon mouth",
            "expressions": [],
            "personality": "",
            "relationships": [],
            "voice_profile": "",
            "dialogue_style": "",
            "asset": asset_data,
            "appearance_recipe": {
                "materials": {},
                "morph_targets": {},
                "morph_bindings": {},
                "face_features": FaceFeatureInput().model_dump(mode="json"),
            },
            "rig_status": "ready" if asset_data["rig_ready"] else "unrigged",
            "foundry_recipe": recipe,
        }
        document = make_envelope("character", character_id, data, now, now, 1)
        character_relative = f"characters/{character_id}.json"
        character_path = resolve_project_relative(
            DATA_DIR, project_id, character_relative
        )
        character_digest = write_json_atomic(character_path, document)
        with connect_db() as connection:
            upsert_document_index(
                connection, project_id, document, character_relative, character_digest
            )
            sync_character_reference(connection, DATA_DIR, project_id, document)
        return {
            **document,
            "asset_id": asset_id,
            "asset_url": f"/api/projects/{project_id}/character-assets/{asset_id}",
            "recipe_path": relative_recipe,
        }
    except BaseException:
        asset_path.unlink(missing_ok=True)
        recipe_path.unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)
        raise


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


@app.get("/api/projects/{project_id}/character-assets")
def list_project_character_assets(project_id: str) -> list[dict[str, Any]]:
    return _project_character_assets(project_id)


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
    data["appearance_recipe"] = {
        "materials": {},
        "morph_targets": {},
        "morph_bindings": {},
        "face_features": FaceFeatureInput().model_dump(mode="json"),
    }
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
        "face_features": appearance["face_features"],
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
    face_features = appearance.get("face_features", {})
    if not materials and not morph_targets and not face_features.get("enabled", False):
        raise HTTPException(status_code=422, detail="There are no appearance edits to export.")
    asset_id = str(uuid.uuid4())
    relative_path = f"assets/characters/{asset_id}.glb"
    destination = resolve_project_relative(DATA_DIR, project_id, relative_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        inspection = get_engine_adapter().export_character_appearance(
            source_path,
            materials,
            morph_targets,
            destination,
            allowed_root=project_root,
            face_features=face_features,
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
            "applied_face_feature_count": inspection.get("applied_face_feature_count", 0),
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
