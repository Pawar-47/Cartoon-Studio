# Execution Batch Plan

This file is the operational checklist beneath `MASTER_PLAN.md`. Batches are sequential. Do not start a later batch while its dependency gate is open.

## Phase 0 — planning and research

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P0.1 | Audit repository, preserve existing work, identify actual vs claimed capabilities | BASELINE_AUDIT.md | Main tree, commit history, CI and current code reviewed | COMPLETE |
| P0.2 | Decompose all 24 specification sections into atomic requirements | Registry and traceability v2 | Every requirement has ID, dependencies, module, test and evidence field | NEXT |
| P0.3 | Research candidate 3D editors, character creation, rigging, toon style and animation | Comparative research records | Multiple candidates inspected at source level; licenses and build/test evidence recorded | BLOCKED BY P0.2 |
| P0.4 | Research persistent worlds, assets, vehicles, Blender/renderer and hardware paths | Research and reuse matrix | Compatibility and target hardware risks compared | BLOCKED BY P0.2 |
| P0.5 | Research Urdu TTS, lip-sync, audio, free AI providers and offline workflow | AI_PROVIDERS, voice research, license register | Real language, quota, rights and CPU evidence | BLOCKED BY P0.2 |
| P0.6 | Compare candidates and test only bounded PoCs | Candidate decision records | Selected/rejected options have evidence, costs and limitations | BLOCKED BY P0.3–P0.5 |
| P0.7 | Freeze engine-neutral architecture and detailed implementation dependencies | ARCHITECTURE, DECISION_LOG, MASTER_PLAN | P0 exit gate satisfied; no critical unknown silently assumed | BLOCKED BY P0.2–P0.6 |

## Phase 1 — application foundation

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P1.1 | Audit and harden existing app/project persistence | App tests and storage contract | Create/list/save/load/restart tests | PARTIAL |
| P1.2 | Reproducible dependency and CI policy | CI workflow, dependency lock/constraints | Clean Windows runner build and test | PARTIAL |
| P1.3 | Portable Windows runtime package | Bootstrap/portable package | Clean Windows install and launch test | PARTIAL |
| P1.4 | Self-contained installer and update/data migration design | Installer/release pipeline | Install, upgrade, preserve projects, uninstall tests | NOT STARTED |

## Phase 2 — production engine selection/integration (requires P0)

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P2.1 | One bounded proof against the selected candidate | Reproducible proof branch/workflow | Open/import/animate/save/reopen/render, inspected output and measured resource use | CANDIDATE PROOF IN PROGRESS; NOT ACCEPTED |
| P2.2 | Production engine adapter and pinned integration | Engine module, notices, reproducible patches | Build and integration tests | BLOCKED BY P0 AND P2.1 |
| P2.3 | Render backend and scene/job contracts | Render adapter and persistent queue | Short clip render, retry/cache/restart tests | BLOCKED BY P2.2 |

## Phase 3 — Character Studio

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P3.1 | Character data contract and original visual style | Versioned character schema and design presets | Schema migration and visual style approval through tests | NOT STARTED |
| P3.2 | Character creation/import and rigging | Working create/import/rig workflow | Save/reopen and rigged animation test | NOT STARTED |
| P3.3 | Expressions, outfits, relationships and persistence | Character library | Cross-scene and cross-project identity tests | NOT STARTED |

## Phase 4 — World Builder

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P4.1 | Persistent world/location schema | Versioned world database | Save/reopen and stable IDs | NOT STARTED |
| P4.2 | Modular town, street, building and interior kits | Reusable environment assets | Multi-location scene test | NOT STARTED |
| P4.3 | Vegetation, props, vehicles and interactions | Reusable asset/animation kits | Movement and persistence test | NOT STARTED |

## Phase 5 — Story, scenes and animation

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P5.1 | Engine-neutral episode schema and story prompt pipeline | Versioned JSON schema, migration and validation | Valid/invalid/repair tests; Urdu RTL UI | PARTIAL |
| P5.2 | Character/location continuity and story approval | Story continuity service | Same cast and world reused across episodes | NOT STARTED |
| P5.3 | Action vocabulary and engine adapters | Animation catalog/adapter | Every accepted action maps to a tested clip or explicit fallback | NOT STARTED |
| P5.4 | Timeline, camera, expressions, transitions and blocking | Scene editor workflow | Playable multi-scene animation test | NOT STARTED |

## Phase 6 — voice and audio

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P6.1 | Urdu TTS benchmark and adapter | Voice adapter and benchmark report | Naturalness, pronunciation, speed, RAM and license measured | RESEARCH REQUIRED |
| P6.2 | Character voice profiles and recorded fallback | Voice library | Repeatable voice identity across lines | NOT STARTED |
| P6.3 | Urdu lip-sync and facial expression | Viseme/face adapter | Real Urdu speech-to-mouth synchronization inspection | NOT STARTED |
| P6.4 | Music, ambience, effects and subtitles | Audio mixer and subtitle exporter | Mixed scene with intelligible dialogue | NOT STARTED |

## Phase 7 — episode production

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P7.1 | Scene render orchestration, cache and recovery | Persistent job queue | Failure/retry/restart test | NOT STARTED |
| P7.2 | End-to-end scene-to-MP4 pipeline | Exporter and editable project package | Real multi-scene MP4 | NOT STARTED |
| P7.3 | Full 5–7 minute sample episode | Release candidate episode | Visual/audio/story quality review and continuity pass | NOT STARTED |

## Phase 8 — optimization and release

| Batch | Scope | Deliverables | Exit evidence | State |
|---|---|---|---|---|
| P8.1 | Target-PC performance and quality presets | Benchmark report and presets | Measured target-PC runs | NOT STARTED |
| P8.2 | Installer, backup, update and diagnostics | Windows release package | Clean install/upgrade/recovery tests | PARTIAL |
| P8.3 | Final acceptance and release | Versioned release and full test report | All specification acceptance criteria have evidence | NOT STARTED |

## Batch discipline

- One active implementation batch at a time.
- Planning/research tasks may be parallelized only when they do not depend on an unresolved architecture decision.
- A batch may contain many file changes; it should end in one coherent commit, not many tiny commits.
- A failed check is fixed within the active batch. Do not create a new feature batch to hide an unresolved failure.
- Never promote a candidate proof to production integration automatically.
- User does not need to run commands or manually trigger workflows for ordinary development.
