# Next Steps — 2026-11-27

## Current checkpoint — 2026-11-27

Main is at `1fdae47` with clean working tree. This batch implemented original face geometry authoring: the Godot worker now replaces the separable Skin surface on the head mesh with procedurally generated face geometry skinned to the Head bone (vertex/normal/tangent/UV/bone-weight arrays), instead of only hiding the surface with a transparent material. Also added saved hair style/color restoration assertions to the character profile round-trip test. Local proof: 122 passed, 34 skipped (all environmental), 0 failed; Ruff all checks passed. Pushed to origin `main`.

Phase 2 remains ACTIVE and P2.2 remains PARTIAL. Phase 6/7 code exists out of order (Urdu audio, subtitles, mouth envelopes, Godot-AVI + FFmpeg MP4), but it is not phase acceptance.

## Immediate next steps

1. Reconcile REQUIREMENTS_REGISTRY.md and REQUIREMENT_TRACEABILITY.md with current code (partially done — CHAR-R003/CHAR-R005 updated; remaining rows already reconciled in prior batch).
2. Complete P2.2 exit work: interactive visual acceptance of hairstyles, portraits, assembly, morphs and retarget preview; body-edit compatibility boundary on hierarchy-validated rigs; broad rig acceptance on representative models. These remaining items require manual/visual acceptance and additional character models, not code changes alone.
3. Only after P2.2 exit criteria are met, activate the planned Phase 3 batch. Preserve the existing out-of-order world/story/episode work without claiming phase completion.

## Candidate next engineering batch — job reliability

The highest-value cross-phase gap is the synchronous long-operation boundary. Audio generation, episode-scene production and MP4 rendering are one-shot HTTP requests with no durable queue, progress polling, resume, cancel or retry. The P0.6 SQLite lease prototype in `tools/sqlite_queue_proof.py` is deliberately isolated from `app/` and has not been productionized. A production queue batch should add migrations, bounded retries, durable event records, atomic output manifests, cancellation and recovery tests, then wire the audio/production/render endpoints to it. This should be planned against the phase gates rather than rushed into Phase 2.

## Historical next steps — 2026-11-26

## Current checkpoint

GitHub `main` is at `062400e58cbbf491ec92869dc140b60a9b354d7f`; the active work branch is `work/mainline-followup`, containing fix commit `be169c4`. Latest main CI [#471](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45791209337) failed because the Godot episode worker has a duplicate `action_cue_count` dictionary key. The pushed working-branch fix and regression test pass locally: pinned-Godot episode test 1 passed; full pytest 136 passed, 4 skipped. No post-fix CI run exists yet; this workflow runs for PRs targeting `main`, not feature-branch pushes.

Phase 2 remains ACTIVE and P2.2 remains PARTIAL. Main also contains partial/out-of-order World Builder, story binding, episode scene generation and procedural action/camera timeline code; these do not constitute phase acceptance. Preserve this work, but do not claim the Phase 2 gate is closed or bypass phase gates.

## Immediate next steps

1. Open a PR from `work/mainline-followup` to `main` to trigger Windows CI; verify it before treating the parse regression as resolved.
2. Complete P2.2 visual acceptance and remaining character-creation work. Only after its exit criteria are met should the planned Phase 3 batch become active.
3. Reassess the existing world/story/episode code against the phase requirements and acceptance evidence; keep it marked partial/out-of-order until those gates are met.

## CI policy

- Normal pushes and pull requests run lint, Python compilation and the full automated test suite with the pinned Godot worker. They do not build PyInstaller application bundles or NSIS installers.
- `.github/workflows/release-windows.yml` is manually dispatched at phase/release milestones and runs the complete Windows packaging, SBOM, installer and install/upgrade/uninstall lifecycle.
- `.github/workflows/godot-engine-proof.yml` is manual-only and reserved for phase-level native proof runs; normal pushes should trigger only quick CI.
- CI concurrency groups prevent overlapping runs within each workflow; do not launch duplicate runs for individual edits.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 2–7 remain open.

## Next P2.2 batch — interactive acceptance and original geometry

The pinned CC0 library, four-slot Godot assembly/export, browser selectors and versioned recipe manifest are implemented. PR #11 verifies API-level save/reopen/reassemble using recovered source manifests and a bone-attached accessory. PR #10 adds a separate verified appearance-bake/export path. These automated contracts do not establish browser-level visual quality.

1. Complete browser acceptance for four-part assembly, shuffle, accessories, download and recipe restoration.
2. Inspect body-proportion and baked-appearance exports on rigs that pass compatibility checks; compare matched-pose geometry, playback and source hashes.
3. Exercise imported morph sliders on a morph-capable GLB and compare browser retarget preview with the authoritative saved Godot scene.
4. Continue original face/hair geometry authoring; keep existing-rig proportion edits and imported morphs distinct from new geometry creation. Generated-face geometry now replaces the separable Skin surface on the head mesh (test verified); arbitrary face-geometry authoring beyond generated templates remains open.
5. Expand rig families only where compatibility tests and visual acceptance justify it.

Phase 2 remains ACTIVE. Do not start Phase 3 until P2.2 exit criteria are met. Physical-PC performance testing and full Windows packaging remain later-stage work, not blockers.
