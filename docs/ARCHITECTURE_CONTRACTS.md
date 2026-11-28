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
- Each finished scene movie is cached inside the episode (`assets/episodes/{episode_id}/render_cache/`) under a SHA-256 of the scene file, frame rate, resolution, duration and cache format version. Only the newest cached version per scene position is kept, the cache is excluded from portable packages, and a render reports how many scenes it reused.
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


## 11. Concrete document shapes

### Project document
```json
{
  "schema_version": "1.0.0",
  "document_type": "project",
  "id": "project-uuid",
  "revision": 1,
  "created_at": "2026-11-25T00:00:00Z",
  "updated_at": "2026-11-25T00:00:00Z",
  "data": {
    "name": "My Cartoon Series",
    "description": "",
    "settings": {
      "default_language": "ur",
      "frame_rate": { "numerator": 24, "denominator": 1 },
      "resolution": { "width": 1280, "height": 720 },
      "quality_preset": "balanced"
    },
    "references": {
      "characters": [],
      "worlds": [],
      "episodes": []
    }
  }
}
```

### Character document
The `data` object contains `identity` (display name, personality, relationships), `appearance` (model asset ref, rig compatibility key, body/face/outfit recipe, material overrides), `expressions` (supported expression and viseme keys), and `voice_profile_ref`. Store voice settings and voice asset refs, not API credentials. Each imported model must have a rig/face capability manifest; missing morph targets are explicit capabilities, not silently assumed.

### Episode and scene documents
Episode `data`: title, synopsis, language (`ur` only until a second voice pack is pinned), target_duration_ms (300000–420000), subtitle_mode, ordered scene_ids, character_ids, approval_state and revision notes.

`subtitle_mode` decides the SRT content and the MP4 stream: `urdu` writes each dialogue `text`, `roman_urdu` and `english` write the required per-line `subtitle_text` (validation rejects a line without it), and `none` writes an empty SRT and renders no subtitle stream. `app/quality.py` owns the four render presets; `settings.quality_preset` is the only stored choice and `frame_rate`/`resolution` are derived from it.

Scene `data`: title, duration_ms, location_id, character_ids, prop_asset_ids, environment/lighting settings, transition, and typed tracks:
- camera: shot, movement, target_id, start_ms, duration_ms;
- actions: character_id, action_id, target_id, start_ms, duration_ms, parameters;
- dialogue: character_id/narrator, text, language, emotion, delivery, audio_asset_ref, start_ms, duration_ms;
- audio: cue_type, asset_ref, start_ms, duration_ms, gain, fades and loop points;
- facial: expression/viseme keys with start_ms and duration_ms.

Canonical timing uses integer milliseconds. Engine adapters convert to frames using the project's rational frame rate. This avoids float drift while retaining a lossless conversion path for the current prototype's seconds-based schema. All cue intervals are half-open `[start_ms, start_ms + duration_ms)` and must fit inside their scene.

### Render job document
```json
{
  "schema_version": "1.0.0",
  "document_type": "render_job",
  "id": "job-uuid",
  "revision": 1,
  "created_at": "2026-11-25T00:00:00Z",
  "updated_at": "2026-11-25T00:00:00Z",
  "data": {
    "project_id": "project-uuid",
    "episode_id": "episode-uuid",
    "episode_revision": 1,
    "quality_preset": "low_hardware",
    "status": "queued",
    "stage": "preparing",
    "progress": 0.0,
    "attempt": 0,
    "cancel_requested": false,
    "scene_tasks": [],
    "output_refs": [],
    "last_error": null
  }
}
```
Allowed job states are queued, preparing, rendering, assembling, completed, failed and cancelled. State changes and stage events are persisted before progress is reported to the UI.

## 12. Portable project layout and database index

```text
<CartoonStudioData>/
  app.sqlite3
  migrations/
  projects/<project-id>/
    project.json
    characters/<character-id>.json
    worlds/<world-id>.json
    locations/<location-id>.json
    episodes/<episode-id>.json
    assets/original/
    assets/derived/
    cache/
    jobs/<job-id>/job.json
    jobs/<job-id>/scenes/<scene-id>/
    exports/
    backups/
    logs/
```

- `project.json` and its referenced documents/assets are the portable project source. Relative paths are resolved from the project root.
- `app.sqlite3` is the rebuildable global index and durable scheduler journal, not the only copy of project content.
- Minimum indexed tables: projects, documents, assets, render_jobs, job_events and schema_migrations. Keep the existing projects/story_plans tables during the first migration; add new tables and compatibility readers before retiring any old path.
- Enable SQLite foreign keys on every connection, WAL where supported, a bounded busy timeout and explicit transactions. Initial worker concurrency is one render job.
- Write JSON/media to a same-volume temporary path, validate and hash it, then atomically rename; update the SQLite index in a transaction. A startup reconciliation pass detects files written before a crash and stale index rows.
- Back up the database and affected project documents before schema migrations. Never overwrite the previous document revision during migration.
- A project package is the project directory zipped verbatim. Import takes the archive as the request body (no form parser, so no multipart dependency is added to the locked environment), rejects members that are absolute, traversing, drive-lettered or duplicated, bounds both the upload and its uncompressed total, and repoints world/episode/character documents from the exporting project id to the new one. A rejected member discards the whole import and its project row.
- A queued job records a worker lease owner and expiry; the next claim reclaims an expired lease. An in-process caller claims its job for the budget of its own operation, not the queue's short default, so long work is never reclaimed while it runs.
- Long operations run in the background worker (`app/worker.py`), not in the HTTP request: the route enqueues and returns `202` with the job id, the worker claims and executes it, reports progress between units, honours cancellation before the next unit and records completion, failure or cancellation. The synchronous route calls the same `_execute_episode_render` body, so both paths share one validation/persistence contract. `GET /api/diagnostics` reports the resolved Godot and FFmpeg paths, the chosen redistribution-safe video encoder and whether the speech engine is installed.

## 13. Versioning and compatibility
- Document schema versions use semantic major.minor.patch. Patch versions are backward-compatible metadata/validation clarifications; minor versions add optional fields; major versions require a migration.
- Application/database migrations are numbered and run once using schema_migrations. Each migration has an idempotence test and a backup/restore test.
- Existing project UUIDs and saved story plans remain readable. The Phase 4 story migration maps legacy character/scene/location/action values to canonical IDs using an explicit alias/mapping document; unmapped values are reported for repair, never dropped.
- API v1 is additive. Existing routes remain supported until callers have migrated and compatibility tests pass.

## 14. P0.5 architecture acceptance checklist
- [x] Preserve FastAPI/browser/SQLite as the current control plane.
- [x] Define stable, versioned, engine-neutral document families and timeline invariants.
- [x] Define the preferred native-worker / optional web-viewport adapter boundary without claiming it is proven.
- [x] Define portable project layout, rebuildable index, durable job journal and recovery behavior.
- [x] Define provider secret isolation and local IPC security.
- [ ] Complete per-subsystem dependency/version/license decisions.
- [ ] Map every Phase 0/1 requirement to the architecture and planned module.
- [ ] Review and reconcile all 171 registry/traceability rows against this architecture.
- [ ] Freeze the architecture and P0.6 proof plan after the dependency/licensing pass.



## 15. P0.5 architecture crosswalk and dependency decisions

The complete 171-requirement ownership map is in ARCHITECTURE_TRACEABILITY.md. Subsystem dependency choices, version policy, licenses, no-bundle decisions and P0.6 proof criteria are in DEPENDENCY_DECISIONS.md.

P0.5 decisions recorded:
- [x] Preserve FastAPI/browser/SQLite as the current control plane.
- [x] Define stable, versioned, engine-neutral document families and timeline invariants.
- [x] Define the preferred native-worker / optional web-viewport adapter boundary without claiming it is proven.
- [x] Define portable project layout, rebuildable index, durable job journal and recovery behavior.
- [x] Define provider secret isolation and local IPC security.
- [x] Record per-subsystem dependency candidates, version-pinning policy, licenses, optional/no-bundle boundaries and unresolved proof gates.
- [x] Map all 171 registry IDs to an architecture home, planned module boundary and delivery phase.
- [x] Reconcile hardware policy: exact-PC performance testing is Phase 8, not an architecture or implementation gate.
- [x] Complete P0.6 bounded engine/renderer/queue/codec proofs; see P0_6_PROOF_REPORT.md.
- [ ] P0.7 final review and freeze after P0.6 evidence.

This checklist marks architecture documentation only; it does not mark candidate software integrated, runtime behavior tested, or product requirements implemented.

## 16. P0.6 proof-backed engine decision

Godot 4.7.2-stable Compatibility is selected as the production 3D runtime candidate based on the successful hosted-runner proof in P0_6_PROOF_REPORT.md. The production adapter is a supervised native process controlled by FastAPI. The optional Web export/embedded viewport is deferred and is not a phase gate. The proof establishes basic GLB import, animation, PackedScene save/reopen, MovieWriter AVI and FFmpeg MP4 assembly; it does not establish full episode quality, target-PC performance, complex rigs or Urdu voice/lip-sync.