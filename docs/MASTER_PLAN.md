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
11. Local episode production must respect the Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM and SSD target.
12. No mandatory paid APIs, subscriptions, online activation, cloud inference or cloud rendering.
13. Respect provider quotas, project terms, software/model/dataset/asset licenses and user privacy.
14. User is not responsible for running developer commands, coordinating batches or fixing implementation errors. The lead agent owns repository execution and reporting.

## Current baseline

See `docs/BASELINE_AUDIT.md`. At the audited HEAD:
- FastAPI/static dashboard, SQLite project metadata and a manual external-AI Story Generator exist.
- Story-plan schema, validation and save/load exist.
- Windows GitHub Actions validation and bootstrap ZIP packaging pass.
- No production 3D engine is integrated.
- Ara 3D Gen is only a candidate with a proof workflow; it is not selected.
- Character/world production, Urdu TTS, lip-sync, complete rendering and final installer remain unimplemented.
- Existing requirements and traceability documents need a full coverage pass.

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

P0.4 — Target-hardware and Urdu feasibility
- Verify graphics/API compatibility for Intel HD 5500 and the supported Windows environment.
- Compare browser GPU, CPU and Blender render paths.
- Estimate RAM/disk footprint from measured or source-supported evidence.
- Evaluate Urdu-script support, Pakistani pronunciation, speaker consistency, model rights and CPU viability.
- Verify current free AI-provider allowances, official integration options, terms and Pakistan availability.
- Keep manual voice and AI handoff fallbacks where direct integration is unavailable.

Deliverables: evidence-backed `HARDWARE_PROFILE.md` and `AI_PROVIDERS.md`.

P0.5 — Architecture and dependency decisions
- Select the smallest maintainable architecture that meets the full requirements.
- Define module boundaries and versioned data contracts for projects, characters, worlds, scenes, animation, audio, voices, assets and render jobs.
- Keep the story schema independent of any one 3D engine; engine adapters map stable Cartoon Studio action/location/character IDs to engine-specific formats.
- Decide how upstream code is pinned, patched, tested, licensed and upgraded.
- Define offline behavior, local data layout, job persistence, cache, failure recovery, installer and update strategy.
- Record rejected options and reasons.

Deliverables: final `ARCHITECTURE.md`, `DECISION_LOG.md` and `EXECUTION_BATCH_PLAN.md`.

**Phase 0 exit gate:** every specification requirement has registry and traceability coverage; major technical choices have source/license/compatibility evidence; target-hardware and Urdu risks are explicit; architecture and batch dependencies are frozen; no unresolved critical decision is silently assumed.

### Phase 1 — Stable application and delivery foundation

Existing work is partial; preserve and complete rather than recreate.
- Verify FastAPI project management and story-plan persistence.
- Define versioned project storage and asset/cache directories.
- Establish pinned dependency policy, reproducible CI and meaningful tests.
- Produce a reliable portable Windows bootstrap, then a self-contained installer when runtime dependencies are known.
- Verify clean installation, startup, shutdown, upgrade and data preservation on Windows.
- Keep GitHub Actions for build/test/package, not GPU episode rendering.

**Exit gate:** repeatable Windows artifact, tested local app, persistent project data and clean documented installation path.

### Phase 2 — Production engine proof and integration

Only begin after Phase 0 architecture freeze.
- Run one bounded proof for the selected engine: open, import a rigged character, load a set, animate, save/reopen and render a short clip.
- Measure target-like memory and performance; record exact runtime versions and output.
- Inspect visual output, not only build logs.
- Integrate only after the candidate passes capability, license, stability and hardware gates.
- Keep upstream pinned and all local changes reproducible in tracked patches/adapters.
- If the candidate fails, return to the comparison matrix; do not force-fit it.

**Exit gate:** accepted engine with a reproducible build, tested adapter boundary, verified notices and inspected sample render.

### Phase 3 — Character Studio

- Original reusable character definitions and visual identity.
- Character modeling/preset/import pipeline, rigs, skinning and expressions.
- Clothing, hair, accessories, personality, relationships and voice profiles.
- Persistent save/load, preview, import/export and identity consistency.
- Original cartoon style; do not ship an unmodified realistic demo as the finished style.

**Exit gate:** create, save, reopen and reuse original characters with stable appearance and working rigs.

### Phase 4 — Persistent World Builder

- Reusable towns, streets, buildings, interiors, vegetation, props and vehicles.
- Layout/material/light persistence and reusable scene templates.
- Vehicle motion and character/environment interactions.
- Consistent locations across scenes and episodes.

**Exit gate:** create and persist a multi-location cartoon world and reuse it in multiple scenes.

### Phase 5 — Story, scene and animation pipeline

- One-prompt story planning and editable approval.
- Natural Pakistani Urdu in Urdu script, optional Roman Urdu and RTL UI.
- Versioned engine-neutral scene schema with repairable validation.
- Stable action vocabulary, animation catalog adapters, timeline, camera, expressions, blocking and smooth transitions.
- Story continuity and reusable cast/location references.

**Exit gate:** an approved 5–7 minute structured episode plan maps to real scene objects, characters, locations and animation clips.

### Phase 6 — Urdu voice, facial animation and audio

- Compare and integrate a rights-cleared Urdu TTS option only after real sample evaluation.
- Character-specific persistent voices and pronunciation controls.
- Manual recording fallback.
- Dialogue timing, visemes, jaw/mouth shapes, expressions and tested Urdu lip-sync.
- Music, ambience, footsteps, vehicle and comedy effects; mix and subtitle export.

**Exit gate:** a short Urdu scene has intelligible speech, stable character voice, synchronized facial motion and balanced audio.

### Phase 7 — Complete episode production

- Prompt → story approval → assets → scene animation → dialogue/voice → lip-sync → render → mix → subtitles → MP4.
- Sequential low-memory render queue, scene caching, checkpointing, retries, safe cancellation and restart recovery.
- Preserve all editable project data and completed scenes after failure.
- Inspect a complete 5–7 minute episode for visual, narrative, audio and continuity quality.

**Exit gate:** real complete MP4 and editable project produced end-to-end without manual developer intervention.

### Phase 8 — Optimization, reliability and release

- Benchmark representative scenes on the actual target PC.
- Tune Preview, Low Hardware, Balanced and High Quality modes.
- Monitor RAM, VRAM/API limits, disk, temperature where available and render failures.
- Finalize installer, logs, diagnostics, backup/recovery, updates and release documentation.
- Run full acceptance matrix and publish verified artifacts.

**Exit gate:** reproducible installation, measured target-PC performance, recovery tests and full acceptance evidence.

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
