# P1.1 — Project Lifecycle and Portable Storage Foundation

**Date:** 2026-11-25  
**Repository:** Pawar-47/Cartoon-Studio  
**Branch:** main  
**Verified implementation commit:** 565d211ce3009c081e60d48778d3ba89acd4a4f7  
**CI:** [Run #115 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45568561903)

## Implemented

### Data location and connection safety
- Default per-user application data directory: Windows %LOCALAPPDATA%\CartoonStudio; macOS ~/Library/Application Support/CartoonStudio; Linux $XDG_DATA_HOME/CartoonStudio or ~/.local/share/CartoonStudio.
- CARTOON_STUDIO_DATA remains an explicit override.
- SQLite connections enable foreign keys and a bounded busy timeout; WAL is enabled during initialization.
- Connection context manager commits/rolls back and closes the connection.

### Numbered migrations and backups
- schema_migrations records applied versions.
- Migration 1 creates the legacy-compatible projects and story_plans tables if missing.
- Migration 2 creates project_documents and indexes.
- Before upgrading an existing legacy database, the SQLite online backup API writes a pre-migration backup under backups/.
- Future database schema versions newer than the app are rejected instead of silently downgraded.

### Portable documents and index
- Every project has a versioned project.json envelope with stable UUID, revision, timestamps, settings, metadata and references.
- Story plans are saved as versioned episode JSON under projects/<project-id>/episodes/<episode-id>.json.
- Atomic same-directory temporary writes and replace prevent partially written JSON documents.
- SQLite project_documents indexes document type, schema version, revision, relative path, SHA-256 and updated timestamp.
- Project-relative paths are resolved and checked to prevent traversal outside the project folder.
- Existing story_plans table remains for compatibility; it is synchronized with portable episode files.

### Project lifecycle APIs
- POST/GET list projects remain compatible.
- GET /api/projects/{id} opens a project and returns its record plus portable document.
- PUT /api/projects/{id} updates project name/description and increments document revision.
- PUT/GET /api/projects/{id}/story persist and reload episode JSON while keeping project references synchronized.

### Legacy and crash recovery
- Startup reconciliation reconstructs missing project.json and episode JSON from existing SQLite rows.
- If an episode JSON file exists but its legacy story_plans row is missing, startup restores the SQLite row/index from the portable file.
- Existing project UUIDs and saved plans are preserved; no reset or destructive migration.

## Verification

CI #115:
- Ruff: passed.
- Python compile: passed.
- Pytest: 21 passed, 1 warning.
- Windows bootstrap ZIP: packaged and uploaded.

The one warning is Starlette's deprecation notice for using legacy httpx with TestClient; Starlette recommends httpx2. It does not fail tests. P1.2 will resolve it through the supported test transport/dependency path, not by suppressing warnings. Upstream reference: https://www.starlette.io/testclient/

## Not yet implemented

- This does not create a self-contained installer; current Windows artifact remains a bootstrap ZIP.
- No project import/export/archive UI yet.
- No asset registry, character/world/scene schemas, renderer, production queue, provider registry or media pipeline.
- The prototype SQLite queue remains isolated under tools/; production queue belongs to later integration.
- No physical-PC performance test was run or required.
