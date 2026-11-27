# Next Steps — 2026-11-27

## Current checkpoint — 2026-11-27

Main is at `321c111` with clean working tree. P2.2 code-testable work is complete: original face geometry (generated face geometry replaces the separable Skin surface on the head mesh), saved-profile hair style/color restoration, assembly, morphs, retarget and appearance bake all have test coverage. Local proof: 122 passed, 34 skipped (all environmental), 0 failed; Ruff all checks passed. Pushed to origin `main`.

Phase 3 — World Builder is now ACTIVE per user direction. Persistent/editable worlds, Godot world-scene export and browser previews exist out of order; multi-location reuse and phase acceptance remain open. User visual acceptance for Phases 2–7 shall be performed in Phase 8 per project owner direction.

## Immediate next steps

1. Phase 3 World Builder activation: world schema migration complete (`migrate_world_document`, `LATEST_WORLD_SCHEMA_VERSION`, `WORLD_MIGRATIONS` in `app/storage.py`; auto-migration on `get_project_world` read). Multi-location reuse already works via `template_id`. Remaining: world-scene export quality, browser preview visual review, world-linked story production mapping (ties to Phase 4).
2. P2.2 remaining visual acceptance proceeds in parallel: interactive browser acceptance of hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on representative models. User visual acceptance for all phases is scheduled for Phase 8.

## Completed batches

### Job reliability queue — DONE
Production SQLite job queue (`app/job_queue.py`) with bounded retries (MAX_ATTEMPTS=3), durable event records, lease-based claiming, cancellation, progress polling, atomic output manifests; schema migration v3 added job tables; production/audio/render endpoints wired to queue; `/jobs`, `/jobs/{id}`, `/jobs/{id}/cancel` API endpoints added; 11 unit tests. CI green.

### Canonical world schema migration — DONE
`LATEST_WORLD_SCHEMA_VERSION = "1.0.1"` in `app/storage.py`; `WORLD_MIGRATIONS` with example 1.0.0→1.0.1 migration; `migrate_world_document()` auto-upgrades world documents on `get_project_world` read; world documents created with latest schema version; 3 unit tests.

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
