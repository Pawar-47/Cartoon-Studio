# Execution Batch Plan

This is the operational checklist beneath `MASTER_PLAN.md` and the user's original 25-part master execution brief. The numbered phases below intentionally match the original brief exactly. Batches are sequential; do not start a dependent batch while its gate is open.

## Phase 0 — Complete specification and GitHub research

P0.2 checkpoint: atomic registry and traceability were expanded on 2026-11-25. The exact 25-part master brief is preserved verbatim at `docs/MASTER_EXECUTION_PROMPT.md` (1,133 lines, 4,642 words; SHA-256 `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`).

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P0.1 | Repository baseline, preservation, code/tests/workflows/artifacts audit | BASELINE_AUDIT.md | Main branch, commit history, current source, docs, CI and candidate proof inspected | COMPLETE |
| P0.2 | Atomic decomposition of all 25 master-brief parts and all 24 PROJECT_SPECIFICATION sections | Atomic registry and one-to-one traceability | 171 atomic rows and 171 traceability rows; 75 legacy IDs preserved | COMPLETE — atomic registry/traceability complete; verbatim prompt stored at docs/MASTER_EXECUTION_PROMPT.md |
| P0.3 | Comparative source-level GitHub research across all major subsystems | Research matrix, license records and candidate scorecard | Source-level research and provisional weighted scorecard published | COMPLETE |
| P0.4 | Source-based hardware, Urdu and provider feasibility | HARDWARE_PROFILE, AI_PROVIDERS, URDU_VOICE_FEASIBILITY; optional target-PC probe retained | Official compatibility/resource evidence; Urdu G2P/alignment/TTS and model/license assessment; Pakistan API availability, quotas, privacy and cost; explicit unknowns | COMPLETE — source-level feasibility documented. Physical-PC benchmarks move to P8.1; native-speaker voice evaluation remains a Phase 6 prerequisite |
| P0.5 | Engine-neutral architecture and dependency decisions | ARCHITECTURE, ARCHITECTURE_CONTRACTS, ARCHITECTURE_TRACEABILITY, DEPENDENCY_DECISIONS, DECISION_LOG | Canonical document contracts; service/adapter boundaries; 171-ID architecture crosswalk; core/engine/queue/media/voice/AI/packaging dependency and license decisions; offline, privacy, persistence, cache/recovery and release boundaries | DOCUMENTATION COMPLETE — proceed to bounded P0.6 proofs; exact-PC benchmark is Phase 8 only |
| P0.6 | Bounded, diagnostic candidate proofs only where needed | Proof workflow, logs, sample outputs and measurements | Godot 4.7.2 Compatibility: GLB import, animation, save/reopen, 72-frame MovieWriter AVI; FFmpeg MP4/AAC assembly; SQLite lease/retry/cancel/checkpoint proof | COMPLETE — hosted-runner functional proofs pass; no physical-PC benchmark required |
| P0.7 | Phase 0 compliance review and architecture freeze | P0_7_PHASE0_EXIT_REVIEW, MASTER_PLAN, EXECUTION_BATCH_PLAN, decision record | Reconcile 171 requirements/crosswalk; record proof evidence and remaining IP/voice/codec risks; freeze Godot native-worker architecture and Phase 1 dependency baseline | COMPLETE — Phase 0 closed; Phase 1 active |

**Phase 0 rule:** no new production-feature implementation before P0.7 exits. Preserve existing source. The existing Story Generator/schema is an early partial slice; do not expand it until Phase 4. Physical-PC performance testing is not a Phase 0 gate; P8.1 owns actual benchmarks.

## Phase 1 — GitHub and CI/CD Foundation

**Phase 1 is COMPLETE.** P1.1–P1.3 passed their Windows CI acceptance tests. P1.4 passed clean install, launch, v1-to-v2 upgrade with project preservation, uninstall, reinstall and final data-retention checks in [CI run #175](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585234644) on commit `24f1617cff4d592e981908c7ceea641225c05ac0`. Phase 2 is now ready; do not treat user-PC performance testing as a gate.

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P1.1 | Harden existing FastAPI app, project lifecycle, SQLite persistence and versioned local data layout | app/storage.py, project APIs, portable project/episode JSON, numbered migrations and integration tests | Create/list/open/update/save/load/restart, legacy DB backup/migration, portable-file recovery and data-preservation tests | COMPLETE — CI #115 passed 21 tests; the later P1.2 dependency update removed the legacy TestClient warning |
| P1.2 | Reproducible dependencies, lint/static checks and CI | pyproject.toml, uv.lock, hash-locked requirements.lock, CI and CycloneDX SBOM | Clean Windows runner installs exact lock, checks lock freshness, lints, compiles, tests and packages | COMPLETE — CI #125 and lock workflow #11 passed; Python 3.11 Windows runner; no TestClient deprecation warning |
| P1.3 | Portable Windows package and simple launcher | Hash-locked bootstrap ZIP, start.bat, configurable port/data path and clean-runner smoke test | Extract into a clean temporary directory, run actual launcher, exercise UI/API, create/open a project, restart and confirm persistence | COMPLETE — Windows CI #136 passed actual start.bat launch, HTTP/static/API checks and project persistence after restart; no user-PC test required |
| P1.4 | Self-contained installer, upgrade and data migration | PyInstaller self-contained bundle, NSIS installer, per-user shortcuts and lifecycle smoke test | Clean install/launch, v1-to-v2 upgrade with project preservation, uninstall, reinstall and data retention | COMPLETE — Windows CI #175 passed the complete lifecycle; installer, bootstrap and SBOM artifacts uploaded |

**Phase 1 exit gate: PASSED.** P1.1–P1.4 deliver the tested local app, repeatable Windows artifacts, self-contained installer, clean install/upgrade/uninstall/reinstall validation and persistent user data. User-PC installation and target-PC performance are not prerequisites for Phase 2; performance is P8.1.

## Phase 2 — Character Studio

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P2.1 | Integrate the Phase 0-selected engine adapter as required by Character Studio | Pinned Godot component, adapter, notices and reproducible character workflow | Build, import, adapter, license and character save/reopen tests | READY — Phase 0 and Phase 1 exit gates passed; start with source/license audit |
| P2.2 | Original toon character creation/import, rigging and skinning | Character create/import/rig workflow | Create/import, preview, save/reopen and animate test | NOT STARTED |
| P2.3 | Character identity, expressions, clothing, relationships and persistence | Persistent character library | Cross-scene and cross-episode identity tests | NOT STARTED |

## Phase 3 — World Builder

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P3.1 | Persistent world/location schema and asset registry | Versioned world model | Save/reopen, stable IDs and migrations | NOT STARTED |
| P3.2 | Reusable town, streets, buildings, shops and interiors | Modular environment kits | Multi-location scene and visual inspection | NOT STARTED |
| P3.3 | Vegetation, props, lighting, weather and vehicle systems | Reusable asset/interaction kits | Vehicle movement/interactions and world persistence tests | NOT STARTED |

## Phase 4 — Story and Scene Engine

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P4.1 | Engine-neutral versioned episode/scene schema; normalize existing early schema | Schema, migrations, validation and repair | Valid/invalid/repair tests; no engine-specific IDs in canonical data | PARTIAL — current Ara-derived catalogs need replacement |
| P4.2 | Single-prompt story generation, Urdu dialogue, continuity and approval | Story provider adapters and editor workflow | Story edit/approve test in Urdu and English; persistent cast/location continuity | PARTIAL — manual external-AI handoff only |
| P4.3 | Complete scene breakdown and production mapping | Scene planner | Every scene maps to persistent characters, world, props, camera, lighting and audio | NOT STARTED |

## Phase 5 — Animation Engine

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P5.1 | Stable action/expression vocabulary and engine adapters | Animation catalog and adapters | Every accepted action maps to a real tested clip or explicit fallback | NOT STARTED — current IDs are validation-only |
| P5.2 | Timeline, camera, blocking, blending, retargeting and transitions | Animation/timeline editor | Playable multi-scene animation test and inspected clip | NOT STARTED |
| P5.3 | Character interactions and facial/body animation | Reusable animation library | Motion quality and interaction tests | NOT STARTED |

## Phase 6 — Urdu Voice and Lip-Sync

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P6.1 | Urdu TTS benchmark and pluggable adapter | Voice adapter and report | Naturalness, Pakistani pronunciation, speed, RAM, license and sample evaluation | RESEARCH REQUIRED |
| P6.2 | Character voice profiles and recorded fallback | Persistent voice library | Stable repeatable character voices | NOT STARTED |
| P6.3 | Urdu lip-sync, visemes and facial expression | Face/viseme adapter | Real Urdu speech-to-mouth synchronization inspection | NOT STARTED |
| P6.4 | Music, ambience, effects, mixing and subtitles | Audio mixer/subtitle exporter | Intelligible balanced Urdu scene with exported subtitles | NOT STARTED |

## Phase 7 — Episode Generator

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P7.1 | Persistent render queue, sequential rendering, cache and recovery | Render orchestrator | Failure/retry/cancel/restart/cache-hit tests | NOT STARTED |
| P7.2 | Scene-to-MP4 pipeline and editable project packaging | Renderer/media assembler | Real multi-scene MP4 with editable source project | NOT STARTED |
| P7.3 | Complete 5–7 minute Urdu episode | Sample episode and QA report | Full visual/audio/story/continuity review | NOT STARTED |

## Phase 8 — Optimization and Reliability

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P8.1 | Target-PC benchmarks and quality presets | Benchmark report and presets | Representative scenes measured on i3-5005U/HD 5500/8 GB; tune Preview, Low Hardware, Balanced and High Quality without silently removing features | NOT STARTED — optimization stage, not an upstream gate |
| P8.2 | Installer, backup, updates, diagnostics and recovery | Final Windows release package | Clean install/upgrade/recovery tests | PARTIAL — bootstrap only |
| P8.3 | Full acceptance and release | Versioned release and complete test report | Every final acceptance criterion has direct evidence | NOT STARTED |

## Batch discipline

- One active batch at a time.
- Research may be parallelized only when it does not depend on an unresolved architecture decision.
- Each batch can change many files but ends with one coherent commit.
- Update registry, traceability, status, test report, research/decision log and next steps together.
- Run CI once after the complete batch, not after every documentation or code edit.
- Fix failures in the same active batch.
- Never promote a candidate proof to production integration automatically.
- The user does not need to run developer commands or coordinate ordinary batches.
