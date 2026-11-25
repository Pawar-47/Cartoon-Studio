from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LATEST_SCHEMA_VERSION = 2


def default_data_dir() -> Path:
    """Return the per-user application-data directory without adding a dependency."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "CartoonStudio"


@contextmanager
def connect_db(data_dir: Path, db_path: Path) -> Iterator[sqlite3.Connection]:
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _migration_1_legacy_project_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS story_plans (
            project_id TEXT PRIMARY KEY,
            plan_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """
    )


def _migration_2_portable_document_index(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS project_documents (
            project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            document_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            revision INTEGER NOT NULL,
            relative_path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(project_id, document_id),
            UNIQUE(project_id, relative_path)
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_project_documents_type
        ON project_documents(project_id, document_type, updated_at)
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC)"
    )


MIGRATIONS = (
    (1, "legacy_project_tables", _migration_1_legacy_project_tables),
    (2, "portable_document_index", _migration_2_portable_document_index),
)


def _existing_schema_version(db_path: Path) -> int:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return 0
    connection = sqlite3.connect(str(db_path), timeout=10)
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        if table is None:
            return 0
        row = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
        return int(row[0] or 0)
    finally:
        connection.close()


def _has_legacy_tables(db_path: Path) -> bool:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return False
    connection = sqlite3.connect(str(db_path), timeout=10)
    try:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        return "projects" in names or "story_plans" in names
    finally:
        connection.close()


def _backup_database(db_path: Path, data_dir: Path) -> Path:
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = backup_dir / f"pre-migration-{stamp}.sqlite3"
    source = sqlite3.connect(str(db_path), timeout=10)
    destination = sqlite3.connect(str(backup_path), timeout=10)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return backup_path


def initialize_database(data_dir: Path, db_path: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    current_version = _existing_schema_version(db_path)
    if current_version > LATEST_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema {current_version} is newer than this app supports "
            f"({LATEST_SCHEMA_VERSION})."
        )
    if current_version < LATEST_SCHEMA_VERSION and _has_legacy_tables(db_path):
        _backup_database(db_path, data_dir)

    with connect_db(data_dir, db_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        for version, name, migration in MIGRATIONS:
            applied = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if applied:
                continue
            connection.execute("BEGIN IMMEDIATE")
            migration(connection)
            connection.execute(
                """
                INSERT INTO schema_migrations(version, name, applied_at)
                VALUES (?, ?, ?)
                """,
                (version, name, datetime.now(UTC).isoformat()),
            )
            connection.commit()


def make_envelope(
    document_type: str,
    document_id: str,
    data: dict[str, Any],
    created_at: str,
    updated_at: str,
    revision: int = 1,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "document_type": document_type,
        "id": document_id,
        "revision": revision,
        "created_at": created_at,
        "updated_at": updated_at,
        "data": data,
    }


def write_json_atomic(path: Path, document: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, ensure_ascii=False, indent=2).encode("utf-8")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return document


def project_directory(data_dir: Path, project_id: str) -> Path:
    try:
        safe_id = str(uuid.UUID(project_id))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError("Invalid project ID.") from error
    return data_dir / "projects" / safe_id


def resolve_project_relative(data_dir: Path, project_id: str, relative_path: str) -> Path:
    root = project_directory(data_dir, project_id).resolve()
    candidate = (root / relative_path).resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError("Project document path escapes the project directory.")
    return candidate


def upsert_document_index(
    connection: sqlite3.Connection,
    project_id: str,
    document: dict[str, Any],
    relative_path: str,
    digest: str,
) -> None:
    connection.execute(
        """
        INSERT INTO project_documents(
            project_id, document_id, document_type, schema_version,
            revision, relative_path, sha256, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, document_id) DO UPDATE SET
            document_type = excluded.document_type,
            schema_version = excluded.schema_version,
            revision = excluded.revision,
            relative_path = excluded.relative_path,
            sha256 = excluded.sha256,
            updated_at = excluded.updated_at
        """,
        (
            project_id,
            document["id"],
            document["document_type"],
            document["schema_version"],
            int(document["revision"]),
            relative_path,
            digest,
            document["updated_at"],
        ),
    )


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_envelope(row: sqlite3.Row) -> dict[str, Any]:
    try:
        metadata = json.loads(row["metadata_json"])
    except (KeyError, json.JSONDecodeError):
        metadata = {}
    return make_envelope(
        "project",
        row["id"],
        {
            "name": row["name"],
            "description": row["description"],
            "metadata": metadata if isinstance(metadata, dict) else {},
            "settings": {
                "default_language": "ur",
                "frame_rate": {"numerator": 24, "denominator": 1},
                "resolution": {"width": 1280, "height": 720},
                "quality_preset": "preview",
            },
            "references": {"characters": [], "worlds": [], "episodes": []},
        },
        row["created_at"],
        row["updated_at"],
        1,
    )


def reconcile_project_files(data_dir: Path, db_path: Path) -> None:
    """Rebuild missing portable documents/index rows without discarding legacy data."""
    with connect_db(data_dir, db_path) as connection:
        projects = connection.execute("SELECT * FROM projects").fetchall()
        for project in projects:
            root = project_directory(data_dir, project["id"])
            root.mkdir(parents=True, exist_ok=True)
            project_path = root / "project.json"
            if project_path.exists():
                project_document = read_json(project_path)
                if (
                    project_document.get("document_type") != "project"
                    or project_document.get("id") != project["id"]
                    or not isinstance(project_document.get("data"), dict)
                ):
                    raise ValueError(f"Project document identity mismatch: {project_path}")
                project_data = project_document["data"]
                connection.execute(
                    """
                    UPDATE projects SET name = ?, description = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        str(project_data.get("name", project["name"])),
                        str(project_data.get("description", project["description"])),
                        project_document.get("updated_at", project["updated_at"]),
                        project["id"],
                    ),
                )
                digest = _file_digest(project_path)
            else:
                project_document = _project_envelope(project)
                digest = write_json_atomic(project_path, project_document)
            upsert_document_index(
                connection, project["id"], project_document, "project.json", digest
            )

            episode_dir = root / "episodes"
            episode_dir.mkdir(parents=True, exist_ok=True)
            story_row = connection.execute(
                "SELECT plan_json, updated_at FROM story_plans WHERE project_id = ?",
                (project["id"],),
            ).fetchone()
            indexed_episode = connection.execute(
                """
                SELECT * FROM project_documents
                WHERE project_id = ? AND document_type = 'episode'
                ORDER BY updated_at DESC LIMIT 1
                """,
                (project["id"],),
            ).fetchone()

            if indexed_episode is not None:
                episode_path = resolve_project_relative(
                    data_dir, project["id"], indexed_episode["relative_path"]
                )
                if not episode_path.exists() and story_row is not None:
                    episode_document = make_envelope(
                        "episode",
                        indexed_episode["document_id"],
                        json.loads(story_row["plan_json"]),
                        project["created_at"],
                        story_row["updated_at"],
                        int(indexed_episode["revision"]),
                    )
                    digest = write_json_atomic(episode_path, episode_document)
                    upsert_document_index(
                        connection,
                        project["id"],
                        episode_document,
                        indexed_episode["relative_path"],
                        digest,
                    )
                elif episode_path.exists():
                    episode_document = read_json(episode_path)
                    if (
                        episode_document.get("document_type") == "episode"
                        and isinstance(episode_document.get("data"), dict)
                    ):
                        connection.execute(
                            """
                            INSERT INTO story_plans(project_id, plan_json, updated_at)
                            VALUES (?, ?, ?)
                            ON CONFLICT(project_id) DO UPDATE SET
                                plan_json = excluded.plan_json,
                                updated_at = excluded.updated_at
                            """,
                            (
                                project["id"],
                                json.dumps(episode_document["data"], ensure_ascii=False),
                                episode_document["updated_at"],
                            ),
                        )
                        upsert_document_index(
                            connection,
                            project["id"],
                            episode_document,
                            indexed_episode["relative_path"],
                            _file_digest(episode_path),
                        )
                continue

            episode_files = sorted(episode_dir.glob("*.json"))
            recovered = False
            for episode_path in episode_files:
                episode_document = read_json(episode_path)
                if (
                    episode_document.get("document_type") == "episode"
                    and isinstance(episode_document.get("data"), dict)
                ):
                    relative_path = episode_path.relative_to(root).as_posix()
                    upsert_document_index(
                        connection,
                        project["id"],
                        episode_document,
                        relative_path,
                        _file_digest(episode_path),
                    )
                    connection.execute(
                        """
                        INSERT INTO story_plans(project_id, plan_json, updated_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(project_id) DO UPDATE SET
                            plan_json = excluded.plan_json,
                            updated_at = excluded.updated_at
                        """,
                        (
                            project["id"],
                            json.dumps(episode_document["data"], ensure_ascii=False),
                            episode_document["updated_at"],
                        ),
                    )
                    recovered = True
                    break

            if recovered or story_row is None:
                continue

            episode_id = str(uuid.uuid4())
            relative_path = f"episodes/{episode_id}.json"
            episode_document = make_envelope(
                "episode",
                episode_id,
                json.loads(story_row["plan_json"]),
                project["created_at"],
                story_row["updated_at"],
                1,
            )
            episode_path = resolve_project_relative(data_dir, project["id"], relative_path)
            digest = write_json_atomic(episode_path, episode_document)
            upsert_document_index(
                connection, project["id"], episode_document, relative_path, digest
            )
