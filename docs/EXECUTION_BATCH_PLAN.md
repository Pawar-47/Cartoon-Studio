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
| P0.6 | Bounded, diagnostic candidate proofs only where needed | Proof workflow, logs, sample outputs and measurements | Godot native worker: import GLB, load manifest, animate, save/reopen, short render and inspect output; FFmpeg codec/build and SQLite queue failure/cancel/restart proofs; optional Web viewport only if valuable | READY — no physical-PC benchmark prerequisite |
| P0.7 | Phase 0 compliance review and architecture freeze | MASTER_PLAN, EXECUTION_BATCH_PLAN, decision record | Every requirement traced; critical risks explicit; architecture and downstream dependencies frozen | BLOCKED BY P0.2–P0.6 |

**Phase 0 rule:** no new production-feature implementation before P0.7 exits. Preserve existing source. The existing Story Generator/schema is an early partial slice; do not expand it until Phase 4. Physical-PC performance testing is not a Phase 0 gate; P8.1 owns actual benchmarks.

## Phase 1 — GitHub and CI/CD Foundation

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P1.1 | Harden existing FastAPI app, project lifecycle, SQLite persistence and versioned local data layout | App/storage contract and tests | Create/list/save/load/restart/data-preservation integration tests | PARTIAL |
| P1.2 | Reproducible dependencies, lint/static checks and CI | Pinned/locked dependencies and CI workflow | Clean Windows runner builds/tests with reproducible logs | PARTIAL |
| P1.3 | Portable Windows package and simple launcher | Bootstrap/portable package | Clean Windows CI/VM install, launch, shutdown and diagnostics test | PARTIAL — bootstrap only; no clean-install evidence; user's PC is not the gate |
| P1.4 | Self-contained installer, upgrade and data migration | Installer and release pipeline | Install/upgrade/uninstall tests; project data survives upgrades | NOT STARTED |

**Phase 1 exit gate:** tested local app, repeatable Windows artifact, documented clean installation in a clean Windows CI/VM environment, persistent user data. Do not require installation on the user's PC to start Phase 2; target-PC performance is P8.1.

## Phase 2 — Character Studio

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P2.1 | Integrate the Phase 0-selected engine adapter as required by Character Studio | Pinned engine component, adapter, notices and reproducible patches | Build, import, adapter and license tests | BLOCKED BY PHASE 0 AND PHASE 1 |
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
