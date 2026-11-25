# Next Steps — 2026-11-25

## Live checkpoint
- Repository: Pawar-47/Cartoon-Studio
- Branch: main
- Phase 0 is CLOSED; Phase 1 is ACTIVE.
- Latest verified CI before the P0.7 documentation batch: run #102 SUCCESS on ae9bad178c9999d5f5b7017a6409c7ee9c490786.
- Godot native-worker proof #3: SUCCESS on the same commit.
- SQLite queue proof: run #101 SUCCESS; 17 total tests passed.
- Full proof record: docs/P0_6_PROOF_REPORT.md.
- Phase 0 freeze record: docs/P0_7_PHASE0_EXIT_REVIEW.md.

## Hardware gate
The user's physical PC is not a prerequisite for architecture, implementation or phase progression. Keep i3-5005U / Intel HD 5500 / 8 GB / SSD as design constraints, allow slow rendering, serialize work and retain quality profiles. Actual frame-time, RAM, disk and quality-preset measurements are Phase 8 only.

## Completed
- P0.1–P0.7: specification preservation, 171-row requirements/traceability, source research, source-based feasibility, architecture/dependency decisions, Godot/FFmpeg/SQLite proofs and architecture freeze.
- Godot 4.7.2 Compatibility selected as native 3D runtime behind a supervised worker adapter.
- FastAPI/browser remains primary UI/control plane; SQLite is local index and queue; FFmpeg process adapter is the media boundary.
- Optional Godot Web viewport is deferred; it does not block native rendering.

## Active batch — P1.1 app and project foundation
1. Re-audit current app routes, database schema, story-plan persistence and data-path handling against the frozen architecture.
2. Implement project lifecycle and versioned portable project/document storage while preserving existing project UUIDs and story plans.
3. Add numbered SQLite migrations, backup-before-migrate and startup reconciliation.
4. Add integration tests for create/list/open/save/load/restart and data preservation.
5. Keep CARTOON_STUDIO_DATA override; use user application data as packaged default.
6. Commit the complete coherent batch and run CI once.

## Phase 1 sequence
- P1.1: app/project lifecycle, persistence, schema and migration foundation.
- P1.2: exact dependency lock, reproducible CI, lint/compile/test and build metadata.
- P1.3: portable Windows package and launcher; validate on clean Windows CI/VM.
- P1.4: self-contained installer, upgrade/uninstall and project-data migration tests.

## Deferred in correct phase
- Character Studio: Phase 2.
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
