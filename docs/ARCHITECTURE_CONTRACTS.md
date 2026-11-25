# Architecture Contracts — P0.5 Draft

**Status:** architecture contract draft; not implemented or production-verified.  
**Authority:** original master execution brief, PROJECT_SPECIFICATION.md, current FastAPI/SQLite source and P0.3/P0.4 research.  
**Version:** 1.0.0 (draft)

## 1. Contract rules
- Persistent project data is engine-neutral and versioned.
- IDs are stable Cartoon Studio identifiers; never use Godot node paths, Blender object names or third-party catalog IDs as canonical identifiers.
- Every reference must resolve or produce an explicit validation error.
- Names and display labels may change; IDs do not.
- Documents are UTF-8 JSON with schema_version, document_type, id, revision, created_at, updated_at and data.
- Binary files are stored in the project asset tree and referenced by stable asset ID plus SHA-256.
- Migrations are explicit, repeatable and preserve the source revision.

## 2. Core documents
| Document | Required identity | Main content |
|---|---|---|
| Project | project ID | settings, language, quality preset, document refs, created/updated |
| Character | character ID | identity, appearance recipe, model/rig refs, expressions, voice profile, relationships |
| World | world ID | reusable locations, environment presets and shared world assets |
| Location | location ID | layout, set pieces, props, lighting/weather presets and asset refs |
| Episode | episode ID | title, language, target duration, cast refs, ordered scene refs, subtitles, approval |
| Scene | scene ID | location, cast, props, timed camera/action/dialogue/audio tracks, transition |
| Animation clip | action ID | asset ref, rig compatibility, tags, duration, fallback |
| Asset | asset ID | relative path, kind, format, size, SHA-256, source, exact license/attribution, version |
| Render job | job ID | episode revision, preset, scene tasks, state, attempts, checkpoints, outputs and errors |

## 3. Timeline invariants
- Episode target duration is 300–420 seconds.
- All timed cues use seconds relative to their owning scene.
- Cue end time must not exceed scene duration.
- Dialogue references a character in the scene or the explicit narrator identity.
- Actions reference a character in the scene and an engine-neutral action ID.
- Camera targets resolve to a scene character or all.
- Scene order and transition are explicit.
- Scene-level rendering and assembly preserve episode ordering and total duration.
- Existing 5–7 scene Story Generator constraints remain preserved during migration; canonical schema must not inherit Ara-derived catalogs.

## 4. Engine adapter boundary
Required capabilities: report engine/version/renderer; validate scene manifest; resolve asset refs; import supported GLB assets; open/update/close preview; render one scene to a declared output format; report progress; accept cancellation; return structured errors and output metadata.

Engine-specific resource paths, node names, skeleton mappings and clip names are stored in adapter-owned manifests. They are never written into canonical episode or character documents. Engine adapters must be replaceable without rewriting story, character or world IDs.

## 5. Persistence and storage
- SQLite is the transactional index for project IDs, document revisions, asset metadata, render jobs/events and migration versions.
- JSON manifests/documents and binary media remain ordinary files in the project folder.
- Render outputs are chunked by scene and job; completed chunks are immutable inputs to assembly.
- Keep CARTOON_STUDIO_DATA as the override. Packaged default should be the user's application-data directory, not the source checkout.
- A migration ledger and backup-before-migrate behavior are required before introducing schema-changing tables.

## 6. Job lifecycle
queued → preparing → rendering → assembling → completed

Terminal alternatives: failed, cancelled. Persist every transition. One render job at a time is the initial policy. Each scene is an independently recoverable checkpoint; retries are stage-idempotent. A crash must not erase completed scene files. Cancellation is cooperative and preserves completed outputs.

## 7. Integration topology
FastAPI/browser remains the control plane. Godot is accessed only through an engine adapter. Preferred production candidate: supervised native Godot render worker. Optional viewport candidate: Godot Web export embedded in the browser, communicating through a narrow JavaScriptBridge message protocol. The Web target is not the sole renderer. Do not assume native GUI embedding or GPU headless rendering until P0.6 proof.

## 8. Provider and secret handling
Provider adapters expose capabilities, not provider-specific fields in canonical documents. Secrets stay outside Git and project data, preferably in OS-protected storage or environment configuration. If no provider is configured or quota is exhausted, manual AI handoff, manual recording and manual alignment remain supported.

## 9. Security and recovery
Bind local IPC to loopback, authenticate each worker process, validate project-relative paths, reject archive traversal/symlink escapes, use bounded request payloads, and preserve backups before migrations. Structured logs must redact secrets and private user content.

## 10. Current implementation gap
Current source implements only project metadata in SQLite, one saved story plan per project, FastAPI routes and static dashboard/story UI. It does not yet implement document envelopes, asset registry, migrations, durable render queue, engine adapter, provider adapters, scene renderer or recovery. The current story schema uses Ara-derived location/action catalogs; these are prototype validation lists only and must be migrated to stable Cartoon Studio-owned IDs in Phase 4. This document defines the target contract, not current functionality.
