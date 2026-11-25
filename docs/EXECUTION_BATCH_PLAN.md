# Execution Batch Plan

This is the operational checklist beneath `MASTER_PLAN.md` and the user's original 25-part master execution brief. The numbered phases below intentionally match the original brief exactly. Batches are sequential; do not start a dependent batch while its gate is open.

## Phase 0 — Complete specification and GitHub research

P0.2 checkpoint: atomic registry and traceability were expanded on 2026-11-25. Exact master brief SHA-256: `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`. The verbatim source-file commit remains an explicit open item; the hash is not a substitute for storing the original.

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P0.1 | Repository baseline, preservation, code/tests/workflows/artifacts audit | BASELINE_AUDIT.md | Main branch, commit history, current source, docs, CI and candidate proof inspected | COMPLETE |
| P0.2 | Atomic decomposition of all 25 master-brief parts and all 24 PROJECT_SPECIFICATION sections | Atomic registry and one-to-one traceability | 171 atomic rows and 171 traceability rows; 75 legacy IDs preserved | COMPLETE — final CI #71 SUCCESS |
| P0.3 | Comparative source-level GitHub research across 3D editors, character generation/rigging, toon styling, worlds, animation, renderers, TTS/lip-sync, audio, queue/recovery, packaging and AI providers | GITHUB_RESEARCH, REPOSITORY_EVALUATION, OPEN_SOURCE_REUSE_MATRIX, ASSET_LICENSES, RESEARCH_LOG | Godot runtime/world stack, CC0 character/animation/environment/audio packs, provider APIs and MovieWriter/FFmpeg pipeline mapped; Urdu lip-sync and remaining subsystem comparisons still open | IN PROGRESS — sweeps 1–5 recorded |
| P0.4 | Target hardware, Urdu and provider feasibility | HARDWARE_PROFILE, AI_PROVIDERS, voice research | Intel HD 5500/Windows path, CPU/RAM/disk, Pakistani Urdu samples, model rights, free quotas and Pakistan availability evidenced | BLOCKED BY P0.3 |
| P0.5 | Engine-neutral architecture and dependency decisions | ARCHITECTURE, DECISION_LOG | Versioned contracts, adapters, data layout, offline mode, queue/cache/recovery, packaging and rejected options documented | BLOCKED BY P0.3–P0.4 |
| P0.6 | Bounded, diagnostic candidate proofs only where needed | Proof workflow, logs, sample outputs and measurements | Open/import/animate/save/reopen/render and inspect output; Ara run #6 is CANCELLED and not accepted | BLOCKED BY P0.5 — proof only after candidate shortlist |
| P0.7 | Phase 0 compliance review and architecture freeze | MASTER_PLAN, EXECUTION_BATCH_PLAN, decision record | Every requirement traced; critical risks explicit; architecture and downstream dependencies frozen | BLOCKED BY P0.2–P0.6 |

**Phase 0 rule:** no new production-feature implementation before P0.7 exits. Preserve existing source. The existing Story Generator/schema is an early partial slice; do not expand it until Phase 4.

## Phase 1 — GitHub and CI/CD Foundation

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P1.1 | Harden existing FastAPI app, project lifecycle, SQLite persistence and versioned local data layout | App/storage contract and tests | Create/list/save/load/restart/data-preservation integration tests | PARTIAL |
| P1.2 | Reproducible dependencies, lint/static checks and CI | Pinned/locked dependencies and CI workflow | Clean Windows runner builds/tests with reproducible logs | PARTIAL |
| P1.3 | Portable Windows package and simple launcher | Bootstrap/portable package | Clean Windows install, launch, shutdown and diagnostics test | PARTIAL — bootstrap only; no target-PC install evidence |
| P1.4 | Self-contained installer, upgrade and data migration | Installer and release pipeline | Install/upgrade/uninstall tests; project data survives upgrades | NOT STARTED |

**Phase 1 exit gate:** tested local app, repeatable Windows artifact, documented clean installation, persistent user data. Do not start Phase 2 until it passes.

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
| P8.1 | Target-PC benchmarks and quality presets | Benchmark report and presets | Actual i3-5005U/HD 5500/8 GB runs | NOT STARTED |
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
