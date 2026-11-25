# Next Steps — 2026-11-25

## Live checkpoint
- Repository: Pawar-47/Cartoon-Studio
- Branch: main
- Phase 0 CLOSED; Phase 1 ACTIVE.
- P1.1 complete: portable project documents, SQLite migrations/backups, project CRUD/open/update and story-plan persistence/recovery.
- Latest verified CI: run #115 SUCCESS on 565d211ce3009c081e60d48778d3ba89acd4a4f7; 21 tests passed, Ruff/compile/Windows bootstrap package passed.
- P1.1 report: docs/P1_1_FOUNDATION_REPORT.md.
- P0.6 proofs: docs/P0_6_PROOF_REPORT.md.
- P0.7 freeze: docs/P0_7_PHASE0_EXIT_REVIEW.md.

## Hardware gate
The user's physical PC is not a prerequisite for architecture, implementation or phase progression. Keep i3-5005U / Intel HD 5500 / 8 GB / SSD as design constraints, allow slow rendering, serialize work and retain quality profiles. Actual frame-time, RAM, disk and quality-preset measurements are Phase 8 only.

## Completed
- P0.1–P0.7: specification preservation, 171-row requirements/traceability, source research, source-based feasibility, architecture/dependency decisions, Godot/FFmpeg/SQLite proofs and architecture freeze.
- P1.1: user data directory, migration framework, pre-migration backup, portable project/episode JSON, project lifecycle APIs, story-plan compatibility and file/database recovery.

## Active batch — P1.2 reproducible dependencies and CI

1. Audit pyproject.toml, requirements.txt and the exact environment resolved by CI.
2. Select a lock strategy suitable for Python 3.11 and Windows (uv lock or a fully pinned requirements lock with hashes); do not rely on floating ranges in release builds.
3. Address the Starlette TestClient/httpx deprecation using the upstream-supported httpx2 test transport or an explicitly pinned compatible stack. Do not hide/suppress the warning.
4. Make CI install from the lock and fail if the lock is stale; keep Ruff, compile, tests and Windows artifact packaging.
5. Record exact Python/framework versions and build metadata; generate dependency/license inventory for the release.
6. Run CI against the complete lock-based batch before moving to P1.3.

## Phase 1 sequence
- P1.1: COMPLETE — project lifecycle, persistence, schema and migration foundation.
- P1.2: ACTIVE — exact dependency lock, reproducible CI, lint/compile/test and build metadata.
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
