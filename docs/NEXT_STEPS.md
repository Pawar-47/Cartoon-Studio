# Next Steps — 2026-11-27

## Current checkpoint — 2026-11-27

Main is at `321c111` with clean working tree. P2.2 code-testable work is complete: original face geometry (generated face geometry replaces the separable Skin surface on the head mesh), saved-profile hair style/color restoration, assembly, morphs, retarget and appearance bake all have test coverage. Local proof: 122 passed, 34 skipped (all environmental), 0 failed; Ruff all checks passed. Pushed to origin `main`.

Phase 3 — World Builder is now ACTIVE per user direction. Persistent/editable worlds, Godot world-scene export and browser previews exist out of order; multi-location reuse and phase acceptance remain open. User visual acceptance for Phases 2–7 shall be performed in Phase 8 per project owner direction.

## Immediate next steps

1. Phase 3 World Builder activation: world schema migration complete (`migrate_world_document`, `LATEST_WORLD_SCHEMA_VERSION`, `WORLD_MIGRATIONS` in `app/storage.py`; auto-migration on `get_project_world` read). Multi-location reuse already works via `template_id`. Remaining: world-scene export quality, browser preview visual review, world-linked story production mapping (ties to Phase 4).
2. P2.2 remaining visual acceptance proceeds in parallel: interactive browser acceptance of hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on representative models. User visual acceptance for all phases is scheduled for Phase 8.

## Completed batches

### Job reliability queue — IN PROGRESS
Production SQLite job queue (`app/job_queue.py`) with bounded retries counted in whole attempts (MAX_ATTEMPTS=3), durable event records, lease-based claiming with expiry-based reclaim, cancellation requests honoured at task boundaries, progress polling and persisted output; schema migrations 3 and 4 create and extend the job tables; production/audio/render/world-export endpoints wired to the queue and claiming for the budget of their own operation; `/jobs`, `/jobs/{id}`, `/jobs/{id}/cancel` API endpoints. 14 unit tests plus 2 API tests.

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
