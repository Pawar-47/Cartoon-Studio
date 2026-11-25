# Next Steps — 2026-11-25

## Live checkpoint

- Repository: Pawar-47/Cartoon-Studio
- Branch: main
- Phase 0: CLOSED.
- Phase 1: COMPLETE — P1.1, P1.2, P1.3 and P1.4 passed.
- Phase 2: ACTIVE — P2.1 Godot native-worker integration.
- Latest successful Windows CI: [run #176 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585584886).
- Run #176 uploaded the Windows installer, portable bootstrap and CycloneDX SBOM.
- Installer lifecycle report: `docs/P1_4_INSTALLER_REPORT.md`.
- P0.6 engine/FFmpeg/SQLite proofs: `docs/P0_6_PROOF_REPORT.md`.

## Completed

- P0.1–P0.7: specification preservation, 171-row requirements/traceability, source research, source-based feasibility, architecture/dependency decisions, Godot/FFmpeg/SQLite proofs and architecture freeze.
- P1.1: user data directory, migration framework, pre-migration backup, portable project/episode JSON, project lifecycle APIs, story-plan compatibility and file/database recovery.
- P1.2: exact uv lock, hash-locked runtime requirements, lock consistency check, Ruff, compile, 22 tests, CycloneDX SBOM and reproducible Windows CI.
- P1.3: Windows bootstrap ZIP and actual launcher smoke test on a clean Windows runner, including project persistence across restart.
- P1.4: self-contained PyInstaller application, NSIS installer, Start Menu/desktop shortcuts, clean install, first launch, v1-to-v2 upgrade, project preservation, uninstall, reinstall and project recovery. Windows CI #176 passed the full lifecycle.

## Active batch — P2.1 Godot native-worker integration

1. Pin the official Godot 4.7.2-stable Windows x86_64 binary; archive SHA-256 is `731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`.
2. Include the upstream MIT `LICENSE.txt` and exhaustive `COPYRIGHT.txt`; record the exact binary archive hash in the CycloneDX inventory.
3. Implemented the Python adapter and one-shot JSON request/response worker: executable discovery, version/capability handshake, timeout/cancellation, structured logs and project-contained GLB path validation.
4. Implemented the minimal Godot worker for handshake and GLB inspection; Windows CI is being extended to run the real pinned binary.
5. Add/execute Windows CI tests for worker startup, version reporting, GLB import, invalid paths, malformed files, timeout/cancellation and process cleanup.
6. Bundle the engine runtime with the self-contained Windows installer. The user must not need to install Godot separately.
7. Preserve the FastAPI/browser UI and the frozen Story Generator. Do not start World Builder or later phases early.

**P2.1 exit evidence:** pending clean Windows CI run for the bundled worker and the complete handshake/GLB/path/error/timeout/cancellation/cleanup suite.

## Phase 2 sequence

- P2.1: ACTIVE — Godot worker/runtime integration and adapter.
- P2.2: NOT STARTED — original toon character creation/import, modular appearance, rigging and preview.
- P2.3: NOT STARTED — persistent character identity, expressions, clothing, relationships, voice profile and cross-episode reuse.

## Deferred in the correct phase

- World Builder: Phase 3.
- Story/Scene schema normalization and full story engine: Phase 4 (preserve the existing partial Story Generator; do not expand early).
- Animation/retargeting: Phase 5.
- Pakistani Urdu TTS, voice profiles, lip-sync and audio: Phase 6.
- Full 5–7 minute MP4 pipeline and production queue integration: Phase 7.
- Target-PC benchmarks, four quality presets and optimization: Phase 8.

## Hardware policy

The user's physical PC is not a prerequisite for architecture, implementation or phase progression. Keep Intel Core i3-5005U / Intel HD 5500 / 8 GB / SSD as design constraints, allow slow rendering, serialize work and retain quality profiles. Actual frame-time, RAM, disk and quality-preset measurements remain Phase 8 only.

## Operating constraints

- GitHub main is the sole source of truth. Never reset or restart completed work.
- Work in substantial batches, not tiny edits/commits.
- Run tests and inspect evidence; distinguish implemented, tested and verified.
- No mandatory paid APIs, subscriptions, cloud rendering or online activation.
- Do not send user audio/content to an external provider without explicit approval.


## Resume correction — 2026-11-25 (supersedes the P2.1 active checklist above)

P2.1 is no longer pending. It was completed and accepted by Windows CI #204 on the latest main commit `1f68fe8e5e87dab3115c7ed95788a7eab4176aab`: [workflow run](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45590769693). All 39 pytest tests passed with the real pinned Godot runtime available; lint, compilation, Godot archive hash verification, SBOM augmentation, application packaging and the complete installer lifecycle also passed.

### Next implementation batch: P2.2 — Character Studio foundation

1. Re-scan all 171 requirements and the original character requirements CHAR-R001 through CHAR-R006 and their dependencies.
2. Complete source/license/compatibility evaluation for the character creation and import path; preserve the engine-neutral project/character identity contracts.
3. Deliver an actual character workflow, not a decorative UI: import/validate a rigged GLB or VRM, inspect humanoid skeleton and animation readiness, save a versioned character profile in the project, and preview the imported character through the bundled Godot worker.
4. Add modular appearance only where the source asset supports independently selectable meshes, materials or blend shapes; never present unsupported controls.
5. Add tests for import validation, unsafe path rejection, profile save/reopen, asset provenance and preview request/response. Run the real Godot path in Windows CI and inspect generated preview output.
6. Update registry, traceability, architecture, source-reuse evaluation, test evidence, project status and next steps in the same coherent batch.

P2.3 remains the next Character Studio batch after P2.2: persistent identity refinement, expressions, clothing variants, relationships and voice profiles. Do not start World Builder or later phases early.


## P2.2 working batch — Character Studio import and persistent profiles

Implemented in the current working commit (CI pending):
- GLB 2.0 upload with a 512 MiB bound, safe project-local storage, container validation and SHA-256 provenance.
- Godot worker inspection and evidence-based mesh/skeleton/animation readiness.
- Character profile create/list/get/update endpoints and browser Character Studio workflow.
- Versioned character identity and appearance/voice/personality metadata saved as portable project documents.
- Project-level canonical character references and recovery from portable character JSON files.
- Focused tests for import, validation, profile round-trip, updates, references and database-loss recovery.

Continue the P2.2 batch: implement a real model preview/thumbnail through Godot, then support rig/appearance authoring and export. Do not mark P2.2 complete until the full phase exit gate is satisfied. GLB is the only integrated import format at this checkpoint; VRM remains a researched candidate, not an implemented feature.


## CI-accepted checkpoint — 2026-11-25

The first P2.2 import/profile batch is accepted by Windows CI #208 on commit `41aabbb627e36f3f02f306e79e3cba33bd19dc84`. All 45 tests, lint, compilation, runtime integrity, bootstrap smoke, self-contained builds and the full installer lifecycle passed. See `docs/P2_2_CHARACTER_STUDIO_REPORT.md`.

Continue P2.2 with:
1. A real model preview path. Do not try to save viewport images from the current `--headless` worker: Godot documents that headless mode disables rendering. Evaluate a separate controlled rendering process/virtual display or a local browser renderer and test the chosen route.
2. Profile editing UI and supported appearance editing based on actual GLB mesh/material/blend-shape structure.
3. Rig/animation readiness details, then actual rig editing/retargeting and export round-trip.
4. Tests and evidence for each capability; keep the project portable and local-first.

Do not claim P2.2 complete until the phase exit gate is met. GLB is the only integrated import format; VRM remains a candidate.


## P2.2 preview batch — 2026-11-25 (CI pending)

The next P2.2 batch adds a local browser GLB preview:
- three.js 0.187.0 pinned to upstream r187 commit `7e89746a687bb88271253698fa108b1dd59825d0`, vendored locally with MIT license.
- GLTFLoader renders uploaded and saved project GLBs in an interactive canvas; OrbitControls provides orbit and zoom; embedded animation clips can be selected.
- A project-scoped asset GET endpoint serves only the generated asset UUID and validated manifest.
- CycloneDX SBOM augmentation records the vendored three.js component.

After CI acceptance, continue with character profile editing and real mesh/material/rig authoring. Keep GLB compression decoder limitations explicit; no remote CDN dependency is permitted.


## Next Character Studio batch after material recipes

1. Validate the material appearance batch in Windows CI and fix any failures.
2. Research and prove a facial-expression workflow using imported blend-shape/VRM expression channels; do not fake facial controls when the model has no compatible targets.
3. Prove humanoid rig compatibility and retargeting using a pinned Godot/VRM integration or a project-owned minimal rig adapter.
4. Add deterministic export only after appearance and rig recipes can be baked without damaging the original asset.


## Character Studio next steps after morph-target controls

1. Validate the morph-target batch in Windows CI and fix any failures.
2. Test representative cartoon GLBs with actual facial blend shapes; verify sliders affect the intended face regions and stored weights survive reload.
3. Research VRM expression presets and humanoid retargeting, then integrate only after Godot 4.7.2 compatibility and license proof.
4. Add character metadata editing and deterministic GLB export without overwriting the original source asset.


## Live resume checkpoint — 2026-11-25 (supersedes earlier active-batch summaries)

- Main head: `e58b40d75ae10431051980246b468b736544f464`.
- Windows CI #214: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45599984676). All tests, lint, compilation, both self-contained builds, installer compilation and the complete install/upgrade/uninstall/reinstall lifecycle passed.
- Completed and CI-accepted Character Studio capabilities: project-scoped GLB import and Godot inspection; local browser GLB preview; persistent character profiles; PBR material appearance recipes; imported facial morph-target sliders and saved weights.
- Next implementation batch: edit existing character identity metadata in-place without reimporting the GLB, preserve the source asset and appearance recipe, and verify the update round-trip. The profile API already supports this; the browser editor is the missing workflow.
- After profile editing: validate with representative real GLB files, improve rig/animation readiness and investigate deterministic export. Do not claim rig authoring, VRM, new blend-shape authoring or export until implemented and tested.
- PC performance testing remains Phase 8 and is not a gate.


## Current Character Studio continuation — skeleton preflight

1. Accept the profile-editor line-break correction in Windows CI #219 before starting the next dependent batch.
2. Inspect the new Skeleton3D hierarchy report on representative skinned GLBs; verify the reported bone parents and coverage against actual model structure.
3. Use the conservative 15-bone report only as a preflight. Next, build a controlled Godot 4.7.2 retarget proof with a source/target humanoid pair and inspect the resulting motion; do not claim compatibility from names alone.
4. Keep V-Sekai VRM optional until its pinned addon and MToon subrepo commits pass an isolated import/export test on the exact bundled runtime. Avoid standalone glTF export until the documented destructive-material warning is resolved.


## Native humanoid retarget proof — next validation

- Godot 4.7.2 source confirms `RetargetModifier3D` discovers direct child Skeleton3D targets and maps the bone names in its assigned SkeletonProfile. The source skeleton owns the modifier; target skeletons are direct children of that modifier.
- The proof scene now creates a `SkeletonProfileHumanoid` source/target pair with different limb lengths and animates a source bone. CI must prove the target pose changes and survives scene serialization before this is accepted.
- After the engine proof passes, adapt imported skeleton names to the canonical humanoid profile without altering the original GLB, then test on a real skinned character asset. Do not claim universal rig compatibility from the generated proof alone.
