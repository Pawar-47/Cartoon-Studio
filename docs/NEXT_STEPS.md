# Next Steps — 2026-11-28

## Current checkpoint — 2026-11-28

Main is at the batch below. Visual acceptance for Phases 2–7 remains Phase 8 per project owner direction. The blocking finding B1 in `docs/MASTER_BRIEF_AUDIT_2026-11-28.md` still holds: the installed app cannot synthesise Urdu speech or assemble an MP4 because `piper-tts` and FFmpeg are not bundled.

## Immediate next steps

1. **Batch A — make the shipped app produce an episode (B1).** Pin the voice path (bundled Piper or recorded fallback), bundle a licence-reviewed FFmpeg, resolve `_find_ffmpeg` to the bundled binary, and add a real-media Windows CI job that renders a fixture episode end to end.
2. **Batch B — real job execution.** Move production/audio/render work to a background worker with per-scene progress, cooperative cancel and the Episode Renderer, Logs and Diagnostics workspaces.
3. **Batch C — scene cache and checkpoints**, so one failed scene never re-renders the whole episode.
4. P2.2 remaining visual acceptance proceeds in parallel: interactive browser acceptance of hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on representative models.

## Completed batches

### Episode contract truthfulness — presets, subtitle modes, guards
Four quality presets in `app/quality.py`, stored in the project document and read by `POST /story/render` (Preview 15 fps/640x360, Low Hardware 24/854x480, Balanced 24/1280x720 — the new default — High Quality 30/1920x1080), with `GET /api/quality-presets` and `GET/PUT /api/projects/{id}/settings` and a Render quality selector on the Story page. `subtitle_mode` is honoured (urdu / roman_urdu / english / none, the last producing no subtitle stream). English episodes and unsupported voice profiles are now refused at validation, and `roman_urdu`/`english` subtitles require a per-line `subtitle_text`.

### Job reliability queue — IN PROGRESS
Production SQLite job queue (`app/job_queue.py`) with bounded retries counted in whole attempts (MAX_ATTEMPTS=3), durable event records, lease-based claiming with expiry-based reclaim, cancellation requests honoured at task boundaries, progress polling and persisted output; schema migrations 3 and 4 create and extend the job tables; production/audio/render/world-export endpoints wired to the queue and claiming for the budget of their own operation; `/jobs`, `/jobs/{id}`, `/jobs/{id}/cancel` API endpoints. 15 unit tests plus 2 API tests.

### Canonical world schema migration — DONE
`LATEST_WORLD_SCHEMA_VERSION = "1.0.1"` in `app/storage.py`; `WORLD_MIGRATIONS` with a 1.0.0→1.0.1 migration; `migrate_world_document()` upgrades a document and then fills the required object defaults, and every world read (list, detail) and every write (create, update, vehicle movement/interaction/rig, scene export) passes through it; 3 unit tests plus a create/update defaults test.

### World export wired to job queue — DONE
`/api/projects/{project_id}/worlds/{world_id}/export` enqueues a `world_export` job, claims it, runs `export_world_scene` and records completion only after the document is persisted; `/jobs`, `/jobs/{id}`, `/jobs/{id}/cancel` API endpoints cover world export jobs.

### Project export/import (PROD-R005) — PARTIAL
GET /api/projects/{project_id}/export returns a portable ZIP package containing project.json, character profiles, world documents and exported assets. POST /api/projects/import restores the archive as a new project: it takes the raw ZIP body (no multipart dependency), path-checks and size-limits every member, and repoints world/episode/character documents at the new project id. 4 unit tests cover the round-trip and the non-ZIP, missing-project.json and path-traversal rejections. Revising a scene inside the imported project is not yet covered by a test.

## Phase 3 World Builder batches

### P3.1 — Persistent world/location schema and asset registry — SCHEMA MIGRATION DONE
- Versioned world model: save/reopen, stable IDs and migrations
- Multi-location reuse via template_id: implemented and tested

### P3.2 — Reusable town, streets, buildings, shops and interiors
- Modular environment kits
- World-scene export quality and browser preview visual review

### P3.3 — Vegetation, props, lighting, weather and vehicle systems
- Reusable asset/interaction kits
- Vehicle movement/interactions and world persistence tests

User visual acceptance for Phases 2–7 shall be performed in Phase 8 per project owner direction.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 2–7 remain open.
