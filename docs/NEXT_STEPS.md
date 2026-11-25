# Next Steps — 2026-11-25

## Live checkpoint
- Repository: Pawar-47/Cartoon-Studio
- Branch: main
- Phase 0 CLOSED; Phase 1 ACTIVE.
- Latest tested implementation commit: d60def463e34575bab26b3a5da6c573b4f2bc4ee.
- Dependency-lock follow-up: 6b41eb59631f8e9757ff2fe26513be08d9623151.
- Latest verified Windows CI: [run #136 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45571086576).
- Latest dependency resolver: [run #11 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45571086600).
- P0.6 proofs: docs/P0_6_PROOF_REPORT.md.
- P1.1 foundation: docs/P1_1_FOUNDATION_REPORT.md.

## Hardware gate
The user's physical PC is not a prerequisite for architecture, implementation or phase progression. Keep Intel Core i3-5005U / Intel HD 5500 / 8 GB / SSD as design constraints, allow slow rendering, serialize work and retain quality profiles. Actual frame-time, RAM, disk and quality-preset measurements remain Phase 8 only.

## Completed
- P0.1–P0.7: specification preservation, 171-row requirements/traceability, source research, source-based feasibility, architecture/dependency decisions, Godot/FFmpeg/SQLite proofs and architecture freeze.
- P1.1: user data directory, migration framework, pre-migration backup, portable project/episode JSON, project lifecycle APIs, story-plan compatibility and file/database recovery.
- P1.2: exact uv lock, hash-locked runtime requirements, lock consistency check, Ruff, compile, 22 tests, CycloneDX SBOM and reproducible Windows CI. The legacy TestClient warning is resolved.
- P1.3: Windows bootstrap ZIP and actual launcher smoke test on a clean Windows runner. The test extracted the ZIP, ran start.bat, checked UI/static/API, created/opened a project, restarted the app and confirmed data persistence.

## Active batch — P1.4 self-contained Windows installer

1. Evaluate a redistributable packaging route that bundles Python and the app without requiring a user-installed Python/Node runtime.
2. Review installer technology and every bundled dependency's license; preserve project ownership and notices.
3. Build an installable Windows package with stable app paths, Start Menu/desktop shortcuts and optional desktop shortcut.
4. Keep user project data under %LOCALAPPDATA%\\CartoonStudio, separate from program files.
5. Test clean install, first launch, upgrade over an existing version, uninstall and reinstall; uninstall must not silently delete user projects.
6. Upload installer and diagnostics as GitHub Actions artifacts. Do not require installation on the user's PC.

## Phase 1 sequence
- P1.1: COMPLETE — project lifecycle, persistence, schema and migration foundation.
- P1.2: COMPLETE — locked dependencies and reproducible CI.
- P1.3: COMPLETE — portable Windows bootstrap, actual launcher and clean-runner persistence smoke test.
- P1.4: ACTIVE — self-contained installer, upgrade/uninstall and data migration tests.

## Deferred in correct phase
- Character Studio: Phase 2, after Phase 1 closes.
- World Builder: Phase 3.
- Story/Scene schema normalization and full story engine: Phase 4 (preserve current partial Story Generator; do not expand early).
- Animation/retargeting: Phase 5.
- Pakistani Urdu TTS, voice profiles, lip-sync and audio: Phase 6.
- Full 5–7 minute MP4 pipeline and production queue integration: Phase 7.
- Target-PC benchmarks, four quality presets and optimization: Phase 8.

## Operating constraints
- GitHub main is the sole source of truth. Never reset or restart completed work.
- Work in substantial batches, not tiny edits/commits.
- Run tests and inspect evidence; distinguish implemented, tested and verified.
- No mandatory paid APIs, subscriptions, cloud rendering or online activation.
- Do not send user audio/content to an external provider without explicit approval.
