# Next Steps — 2026-11-27

## Current checkpoint — 2026-11-27

Main is at `321c111` with clean working tree. P2.2 code-testable work is complete: original face geometry (generated face geometry replaces the separable Skin surface on the head mesh), saved-profile hair style/color restoration, assembly, morphs, retarget and appearance bake all have test coverage. Local proof: 122 passed, 34 skipped (all environmental), 0 failed; Ruff all checks passed. Pushed to origin `main`.

Phase 3 — World Builder is now ACTIVE per user direction. Persistent/editable worlds, Godot world-scene export and browser previews exist out of order; multi-location reuse and phase acceptance remain open. User visual acceptance for Phases 2–7 shall be performed in Phase 8 per project owner direction.

## Immediate next steps

1. Reconcile REQUIREMENTS_REGISTRY.md and REQUIREMENT_TRACEABILITY.md with current code (partially done — CHAR-R003/CHAR-R005 updated; remaining rows already reconciled in prior batch).
2. Phase 3 World Builder activation: continue multi-location world/location reuse, canonical world schema migration, world-scene export quality, browser preview visual review, and world-linked story production mapping.
3. P2.2 remaining visual acceptance proceeds in parallel: interactive browser acceptance of hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on representative models. User visual acceptance for all phases is scheduled for Phase 8.

## Candidate next engineering batch — job reliability

The highest-value cross-phase gap is the synchronous long-operation boundary. Audio generation, episode-scene production and MP4 rendering are one-shot HTTP requests with no durable queue, progress polling, resume, cancel or retry. The P0.6 SQLite lease prototype in `tools/sqlite_queue_proof.py` is deliberately isolated from `app/` and has not been productionized. A production queue batch should add migrations, bounded retries, durable event records, atomic output manifests, cancellation and recovery tests, then wire the audio/production/render endpoints to it. This should be planned against the phase gates rather than rushed into Phase 2.

## Phase 3 World Builder batches

### P3.1 — Persistent world/location schema and asset registry
- Versioned world model: save/reopen, stable IDs and migrations
- Multi-location reuse and canonical world schema migration

### P3.2 — Reusable town, streets, buildings, shops and interiors
- Modular environment kits
- World-scene export quality and browser preview visual review

### P3.3 — Vegetation, props, lighting, weather and vehicle systems
- Reusable asset/interaction kits
- Vehicle movement/interactions and world persistence tests

User visual acceptance for Phases 2–7 shall be performed in Phase 8 per project owner direction.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 2–7 remain open.
