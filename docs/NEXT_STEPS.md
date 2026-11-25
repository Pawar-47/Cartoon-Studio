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

1. Pin the official Godot 4.7.2-stable Windows x86_64 binary and verify its published SHA-256 digest.
2. Include the Godot MIT copyright/license notice and record the binary in the dependency/SBOM inventory.
3. Implement the Python engine adapter: executable discovery, version/capability handshake, request/response protocol, timeouts, cancellation, structured logs and path safety.
4. Implement a minimal Godot worker that validates requests, imports/inspects a GLB fixture and returns structured JSON.
5. Add Windows CI tests for worker startup, version reporting, GLB import, invalid paths, failures and process cleanup.
6. Bundle the engine runtime with the self-contained Windows installer. The user must not need to install Godot separately.
7. Preserve the FastAPI/browser UI and the frozen Story Generator. Do not start World Builder or later phases early.

**P2.1 exit evidence:** clean Windows CI launches the bundled Godot worker, confirms the pinned engine version, imports the GLB fixture, returns a valid response, rejects unsafe paths and cleans up correctly.

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
