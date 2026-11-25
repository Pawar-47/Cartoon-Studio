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
