# Cartoon Studio — Master Execution Plan

## Mission

Build an original, installable, local-first web-based production studio that turns one Urdu or English prompt into a coherent 5–7 minute original 3D cartoon episode, with persistent characters and locations, animation, Pakistani Urdu dialogue, character voices, lip-sync, sound, a real MP4 and an editable project.

This is a complete production application, not a mockup, theme, prompt generator or one-off video service.

## Non-negotiable operating rules

1. GitHub repository `Pawar-47/Cartoon-Studio` is the only project source of truth.
2. Read the complete specification and current requirement registry before planning or changing a feature.
3. Finish planning and research before selecting a production engine or implementing engine-dependent modules.
4. Do not assume Ara, Blender, Three.js or any candidate is selected until the documented evaluation gate passes.
5. Keep the product architecture engine-neutral until the engine decision is approved by evidence.
6. Preserve existing source and candidate research. No resets, destructive cleanup or wholesale replacement.
7. Implement coherent feature batches. No isolated one-line commits, speculative patches or repeated CI runs after every minor edit.
8. A batch is complete only after implementation, relevant tests, output inspection, documentation and one coherent commit.
9. Green lint/compile/unit tests do not prove production rendering or final product acceptance.
10. Do not claim functionality, compatibility, performance or test success without direct evidence.
11. Design for the stated Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM and SSD constraints. Actual target-PC testing is not a prerequisite for research, architecture, implementation or phase progression; representative measurements belong to Phase 8.
12. No mandatory paid APIs, subscriptions, online activation, cloud inference or cloud rendering.
13. Respect provider quotas, project terms, software/model/dataset/asset licenses and user privacy.
14. User is not responsible for running developer commands, coordinating batches or fixing implementation errors. The lead agent owns repository execution and reporting.

## Current baseline

See `docs/BASELINE_AUDIT.md`. The original user-approved 25-part master execution brief is the binding execution contract. The uploaded copy audited on 2026-11-25 is 1,133 lines (SHA-256 `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`). The repository's `PROJECT_SPECIFICATION.md` is a durable condensed specification, not a verbatim copy of that brief. The exact original 25-part brief is now preserved verbatim at `docs/MASTER_EXECUTION_PROMPT.md` (1,133 lines, 4,642 words; SHA-256 `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`). The GitHub-fetched file was verified to match the uploaded source text exactly. At the audited HEAD:
- FastAPI/static dashboard, SQLite project metadata and a manual external-AI Story Generator exist.
- Story-plan schema, validation and save/load exist.
- Windows GitHub Actions validation and bootstrap ZIP packaging pass.
- No production 3D engine is integrated.
- Ara 3D Gen is only a candidate with a proof workflow; it is not selected.
- Character/world production, Urdu TTS, lip-sync, complete rendering and final installer remain unimplemented.
- Existing requirements and traceability documents need a full coverage pass.
- A partial Story Generator/schema was built ahead of the specified phase order; preserve it, freeze further expansion until Phase 4, and remove its temporary Ara-derived catalog coupling before production use.

## Phase sequence and gates

### Phase 0 — Specification, research and architecture freeze

**No production feature development is allowed before this phase exits.**

P0.1 — Repository baseline and preservation
- Audit all branches, commits, workflows, source, tests, docs and current artifacts.
- Record what exists, what is genuinely tested, what is only a candidate, and what is absent.
- Preserve existing work.
- Deliverable: `BASELINE_AUDIT.md`.

P0.2 — Full requirements decomposition
- Read the entire authoritative specification and user-approved master prompt.
- Decompose every distinct requirement and sub-requirement into a uniquely identified registry entry.
- Include priority, dependencies, intended module, implementation approach, test method, evidence and honest status.
- Build a traceability row for every requirement.
- Explicitly identify cross-cutting requirements and acceptance criteria.
- Deliverables: complete `REQUIREMENTS_REGISTRY.md` and `REQUIREMENT_TRACEABILITY.md`.

P0.3 — Comparative open-source research
Research and compare complete candidates for:
- Web-based 3D studio/editor and scene/timeline systems.
- Character modeling, original cartoon styling, auto-rigging, skinning and import/export.
- Facial rigs, expressions, visemes and Urdu lip-sync.
- Motion libraries, retargeting, blending and animation authoring.
- Persistent procedural worlds, buildings, vegetation, props and vehicles.
- Blender automation and alternative CPU/WebGL rendering.
- Urdu TTS, audio generation/alignment, mixing, subtitles and FFmpeg.
- Story-to-scene schema and orchestration.
- Local-first application frameworks, job queues, crash recovery and Windows packaging.
- Multi-provider AI resource management and research workflows.

For every serious candidate inspect its source, documentation, releases, commit activity, issues, dependencies, build scripts, tests, runtime requirements and integration boundary. Record software license separately from model, dataset, motion and asset licenses. Search results alone are not evidence of compatibility.

Deliverables: updated `GITHUB_RESEARCH.md`, `REPOSITORY_EVALUATION.md`, `OPEN_SOURCE_REUSE_MATRIX.md`, `ASSET_LICENSES.md` and `RESEARCH_LOG.md`.

P0.4 — Source-based hardware, Urdu and provider feasibility
- Use official system requirements, API specifications, upstream source, driver documentation and known hardware specifications to assess compatibility and resource risks.
- Compare browser GPU, CPU, Godot Compatibility and Blender render paths on paper; label all estimates and untested assumptions.
- Record the target hardware profile, likely bottlenecks, memory/disk risks and quality-scaling strategies.
- Evaluate Urdu-script support, Pakistani pronunciation evidence, speaker consistency, model rights and CPU viability. Keep voice selection provisional until native-speaker sample evaluation in Phase 6.
- Verify current free AI-provider allowances, official integration options, terms, privacy and Pakistan availability.
- Keep manual voice and AI handoff fallbacks where direct integration is unavailable.
- Do not require a physical test on the user's PC to close P0.4 or proceed. Preserve the diagnostic harness as optional; actual representative-scene benchmarks are scheduled in Phase 8.

Deliverables: evidence-backed `HARDWARE_PROFILE.md`, `AI_PROVIDERS.md` and `URDU_VOICE_FEASIBILITY.md`, with unknowns explicitly recorded.

P0.5 — Architecture and dependency decisions
- Select the smallest maintainable architecture that meets the full requirements.
- Define module boundaries and versioned data contracts for projects, characters, worlds, scenes, animation, audio, voices, assets and render jobs.
- Keep the story schema independent of any one 3D engine; engine adapters map stable Cartoon Studio action/location/character IDs to engine-specific formats.
- Decide how upstream code is pinned, patched, tested, licensed and upgraded.
- Define offline behavior, local data layout, job persistence, cache, failure recovery, installer and update strategy.
- Record rejected options and reasons.

Deliverables: final `ARCHITECTURE.md`, `DECISION_LOG.md` and `EXECUTION_BATCH_PLAN.md`.

P0.6 — Bounded candidate proofs
- Run only small, reproducible proofs for the leading candidates where they resolve a critical architecture question.
- Ara proof run #6 (45486950450) was CANCELLED during the browser MP4 export check; it is not a pass. Type-check and partial editor checks completed, but Studio checks, production build and artifact upload were skipped.
- Diagnose the export test, make it bounded and diagnostic, and rerun only when it provides evidence needed for the Phase 0 decision. Inspect actual output and resource use; never approve a candidate from type-checking alone.
- Keep Ara unapproved unless the architecture-critical proof and licensing gates pass. A user's physical-PC benchmark is not a P0.6 approval gate; actual performance is measured in Phase 8.

P0.7 — Architecture freeze and execution baseline
- Freeze engine-neutral contracts, selected/rejected components, dependency versions, data layout, packaging and phase dependencies.
- Publish the exact batch plan and acceptance tests for each phase.

**Phase 0 exit gate:** every specification requirement has registry and traceability coverage; major technical choices have source/license/compatibility evidence; target-hardware and Urdu risks are explicit; architecture and batch dependencies are frozen; no unresolved critical decision is silently assumed. Physical target-PC benchmarks are deferred to Phase 8 and do not block this exit gate. Voice quality remains unapproved until its Phase 6 native-speaker evaluation.

### Phase 1 — GitHub and CI/CD Foundation

Preserve and complete the existing application shell; do not recreate it.
- Verify FastAPI project management, SQLite persistence, story-plan save/load and data-directory behavior.
- Establish versioned project storage, asset/cache directories and safe project migration.
- Pin/constrain dependencies and make CI reproducible across clean Windows runners.
- Build and test frontend/backend, lint, static checks and application/integration tests.
- Produce a reliable portable Windows package and then a self-contained installer when runtime dependencies are known.
- Verify clean installation, launch, browser access, shutdown, upgrade and project-data preservation on Windows.
- Keep GitHub Actions for build/test/package, not GPU episode rendering.

**Current state: COMPLETE.** P1.1–P1.3 provide the project/data foundation, reproducible CI and clean-runner bootstrap. P1.4 adds the self-contained PyInstaller/NSIS installer and passes clean install, launch, v1-to-v2 upgrade with project preservation, uninstall and reinstall in Windows CI run #175. No user-PC installation or performance test is required to close this phase.

**Exit gate:** repeatable Windows artifact, tested local app, persistent project data and a clean documented installation path, verified on a clean Windows CI/VM environment. Installation or performance testing on the user's personal PC is not a prerequisite for Phase 2.

### Phase 2 — Character Studio

- Integrate the Phase 0-selected production engine only as part of delivering the Character Studio; there is no separate numbered engine-integration phase.
- Create original stylized cartoon characters using a reusable modeling/preset/import and rigging workflow.
- Store stable identity, face/body proportions, hair, clothing, accessories, materials, expressions, personality, relationships and voice profile.
- Support rigging, skinning, preview, save/reopen, import/export and consistent reuse.
- Do not ship an unmodified realistic demo style as the finished cartoon style.

**Exit gate:** create, save, reopen and reuse original cartoon characters with stable appearance and working rigs.

### Phase 3 — World Builder

- Create persistent reusable towns, neighborhoods, streets, buildings, interiors, vegetation, props and vehicles.
- Persist layouts, materials, lighting presets, object placement and scene templates.
- Support vehicle motion and character/environment interactions.
- Keep locations recognizable across scenes and episodes.

**Exit gate:** create and persist a multi-location cartoon world and reuse it in multiple scenes.

### Phase 4 — Story and Scene Engine

- Accept one Urdu or English prompt and generate a coherent original story and structured episode plan.
- Support natural Pakistani Urdu, Urdu script, RTL and optional Roman Urdu.
- Include cast, relationships, scene breakdown, durations, dialogue, actions, expressions, environments, props, camera, lighting, music, effects, transitions and ending.
- Allow story/dialogue review, editing and approval before production.
- Maintain a versioned engine-neutral scene schema and repair invalid scene data.
- Map story locations and characters to persistent world/character IDs.

**Existing early work:** the current Story Generator and schema are retained as partial work created before the prescribed sequence. Freeze feature expansion until this phase. Before production use, replace the Ara-derived location/action/expression catalog coupling with stable Cartoon Studio identifiers and explicit engine adapters.

**Exit gate:** an approved 5–7 minute episode plan maps to real persistent characters, locations, props and scene objects.

### Phase 5 — Animation Engine

- Build the reusable action/animation library and map stable action IDs through the selected engine adapter.
- Support body actions, gestures, facial expressions, blinking, talking and character interactions.
- Add animation blending, retargeting, timing, timeline editing, blocking, camera control and smooth scene transitions.
- Inspect actual playback and rendered clips; catalog validation alone is not animation implementation.

**Exit gate:** a multi-scene episode plan plays as coherent animation using persistent characters and sets.

### Phase 6 — Urdu Voice and Lip-Sync

- Select a rights-cleared Urdu TTS option only after real sample and target-hardware evaluation.
- Support character-specific persistent voices, Pakistani pronunciation controls and manual recording fallback.
- Add dialogue timing, visemes, jaw/mouth shapes, facial expressions, blinking and head movement.
- Add music, ambience, footsteps, vehicle/comedy effects and subtitle export.

**Exit gate:** a short Urdu scene has intelligible speech, stable character voice, inspected synchronized facial motion and balanced audio.

### Phase 7 — Episode Generator

- Integrate prompt approval, persistent assets, scene animation, dialogue, voice, lip-sync, rendering, audio mix, subtitles and MP4 assembly.
- Implement a sequential low-memory render queue, scene cache, checkpoints, retries, safe cancellation and restart recovery.
- Preserve editable project data and completed scenes after failures.
- Inspect a complete 5–7 minute episode for visual, narrative, audio and continuity quality.

**Exit gate:** a real complete MP4 and editable project are produced end-to-end without manual developer intervention.

### Phase 8 — Optimization and Reliability

- Benchmark representative scenes on the actual target PC.
- Tune Preview, Low Hardware, Balanced and High Quality modes without silently removing features.
- Monitor RAM, GPU/API limits, disk and render failures.
- Finalize installer, logs, diagnostics, backup/recovery, updates and release documentation.
- Run the full acceptance matrix and publish verified artifacts.

**Exit gate:** reproducible installation, representative target-PC performance measurements, recovery tests and full acceptance evidence. Actual physical-PC benchmarking occurs here; slow performance triggers optimization and quality-preset tuning, not retroactive blocking of earlier development.

## Standard batch protocol

Every batch follows this sequence:
1. Re-read the relevant original specification sections and all linked registry dependencies.
2. State the batch objective, scope, dependencies, deliverables and acceptance tests in the repository plan.
3. Research relevant upstream sources and licenses before adopting code/assets.
4. Implement the complete coherent feature group; do not stop after a cosmetic shell or partial patch.
5. Run focused tests, integration tests and full CI when appropriate.
6. Inspect actual UI/render/media output for visual features.
7. Fix failures within the same batch.
8. Update registry, traceability, status, test report, research/decision log and next steps.
9. Review the diff as a whole; make one coherent commit for the completed batch.
10. Move to the next batch only when the acceptance gate is met.

No commit for every tiny edit. No duplicate CI runs just to test individual edits. Do not start dependent batches while a gate is unresolved.

## Interruption and resume protocol

On every resume, read the latest main HEAD, this plan, `NEXT_STEPS.md`, `PROJECT_STATUS.md`, registry, traceability, latest workflow results and the exact source/tests for the active batch. Reconcile any unfinished work before changing code. Never restart completed work or guess where execution stopped.

## Completion definition

The product is complete only when the full acceptance list in `PROJECT_SPECIFICATION.md` has direct test evidence, including a real 5–7 minute Urdu cartoon MP4, editable project, persistent original characters/world, working animation, voice/lip-sync or explicitly approved fallback, recovery, Windows installation and measured target-hardware performance.

## 2026-11-25 checkpoint — P0.4 source-feasibility closeout and P0.5 start

P0.3 source-level research and provisional candidate scoring are complete. P0.4 source-based hardware/API compatibility, Urdu model/voice feasibility and provider region/quota/privacy/cost research are documented. The physical target-PC probe remains available but optional and is deferred to Phase 8; it is not a gate for P0.5, P0.6, P0.7 or earlier implementation phases. No actual performance claim is made. Urdu voice selection remains provisional until native-speaker sample evaluation in Phase 6. Proceed with P0.5 engine-neutral architecture and dependency decisions, retaining explicit risks and reversible adapters.


## 2026-11-25 — P0.7 Phase 0 exit and architecture freeze

P0.1–P0.6 are complete. P0.7 has reconciled the original 25-part brief, all 24 numbered project-specification sections, the 171-row requirements registry, 171-row implementation traceability and the 171-row architecture crosswalk. P0.6 functional evidence is recorded in P0_6_PROOF_REPORT.md. Godot 4.7.2 Compatibility is selected as the native 3D runtime behind a supervised worker adapter; FastAPI/browser remains the control plane; SQLite remains the local index and app-owned sequential job queue; FFmpeg remains a process adapter. The optional Godot Web viewport is deferred. The final production codec/FFmpeg distribution build, project distribution license, native-speaker Urdu voice selection and exact-PC performance tuning remain explicit deferred decisions, not Phase 1 blockers. Physical-PC benchmarks belong to Phase 8.

**Phase 0 is closed. Phase 1 — GitHub and CI/CD Foundation — is now the active phase.** No production Character Studio, World Builder, Story/Scene, Animation, Urdu voice or full episode feature has been claimed complete. Existing partial Story Generator code is preserved and remains frozen until Phase 4.

## 2026-11-25 — Phase 1 completion and Phase 2 activation

P1.1–P1.4 are complete. Windows CI run #176 passed the locked dependency checks, 22 pytest tests, lint/compile, bootstrap extraction and actual launcher smoke test, self-contained PyInstaller builds for 0.1.0 and 0.1.1, NSIS installer compilation, clean install/launch, v1-to-v2 upgrade, project-data preservation, uninstall, reinstall and artifact upload. See `docs/P1_4_INSTALLER_REPORT.md`.

**Phase 1 is closed. Phase 2 — Character Studio — is active.** P2.1 integrates the selected Godot 4.7.2 Compatibility runtime as a supervised native worker behind the existing FastAPI/browser control plane. The worker must be pinned, license-noticed, bundled with the application, and validated by Windows CI before the original character creation/rigging work in P2.2. The optional Godot Web viewport remains deferred. Physical target-PC performance testing remains Phase 8 and is not a gate for P2.1.
