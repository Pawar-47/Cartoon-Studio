# Next Steps — 2026-11-28

## Live checkpoint

- Repository: `Pawar-47/Cartoon-Studio`
- Active branch: `main`
- World Builder alignment commit: `17d35ea4b6b87509ee2318bf26eb1078cd39351d`
- CI at starting checkpoint: Windows CI #612 — SUCCESS (`46062289103`)
- The Foundry branch remains frozen; do not merge or modify it.
- Binding requirements: the complete 25-part `docs/MASTER_EXECUTION_PROMPT.md` and the 171-row registry/traceability set.

## Current phase direction

Phase 3 — World Builder remains the active development phase. Existing world persistence, schema migration, templates, Godot scene export, GLB preview and vehicle API contracts are preserved. The first alignment pass closes a browser-editor omission: all 17 supported object kinds are exposed, with position and rotation editing.

## Newly confirmed adapter defect and correction\n\nThe first implementation audit also found that `app/engine.py` retained a seven-kind allowlist even after the API and Godot worker expanded to 17 kinds. This rejected valid saved worlds at export time. The adapter allowlist is now aligned with the Pydantic schema and worker; a regression test exercises all 17 kinds through the real adapter validation path.\n\n## Immediate next batch

1. Integrate verified CC0 environment models into a project-scoped reusable asset library; pin exact pack versions, checksums and license evidence, and use lazy download/cache rather than committing large asset packs.
2. Upgrade World Builder placement from primitive blockout-only geometry to reusable road, building, vegetation, furniture and vehicle assets.
3. Connect vehicle rig/movement/interaction state to actual scene-time animation and character actions.
4. Keep the existing story/episode pipeline intact; next close world-linked production mapping and scene-level caching/recovery.

## Verified foundation already present

- Versioned project/world/character/episode documents and SQLite migrations/index.
- Godot 4.7.2 Compatibility worker, scene export, character processing and episode scene generation.
- Browser Character Studio, Story Generator and World Builder.
- Durable SQLite job records, leases, bounded attempts and cancellation/progress APIs for production, audio, world export and rendering.
- Windows CI and a self-contained installer lifecycle proof; latest recorded full CI success for the implementation checkpoint is #612.
- Existing modular character asset library and verified CC0 provenance must be preserved.

## Remaining acceptance work

- World asset-library breadth and rendered visual quality.
- Character and world browser visual acceptance.
- Full Urdu pronunciation/voice review and phoneme/viseme lip-sync.
- Reusable animation library, blending and timeline editor.
- Integrated optional AI provider adapters; manual handoff remains supported.
- Scene-level render cache and restart recovery of completed scenes.
- Full 5–7 minute episode render inspected for visuals, dialogue, timing and audio.
- Target-PC benchmarks, quality presets and final install/update acceptance in Phase 8.

## Operating policy

Use main as the source of truth. Work in substantial batches, preserve all existing work, run focused tests, then one CI checkpoint. Do not start overlapping CI runs, do not rebuild the same feature, and do not call a requirement verified merely because source code exists.
