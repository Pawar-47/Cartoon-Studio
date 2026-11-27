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

## Current baseline — refreshed 2026-11-28

The complete original 25-part `MASTER_EXECUTION_PROMPT.md` is binding; the 171-row requirement registry and traceability matrix remain the atomic coverage records. The old baseline below the initial Phase 0 audit is historical and superseded by the current mainline state.

At mainline alignment commit `17d35ea4b6b87509ee2318bf26eb1078cd39351d` (Windows CI #612 SUCCESS), the repository contains:
- FastAPI/static browser application, SQLite-backed portable project documents, migrations and recovery.
- Pinned Godot 4.7.2 Compatibility worker behind a supervised adapter.
- Self-contained Windows installer build and a previously verified install/upgrade/uninstall/reinstall lifecycle.
- Character Studio with imported GLB inspection, profiles, modular Quaternius character assembly, proportions, hair/face geometry, appearance/morph editing and retargeting.
- World Builder with versioned persistent layouts, templates, 17 supported object kinds, Godot scene export and Three.js GLB preview.
- Story prompt/schema/validation and world/cast-linked editable episode-scene generation.
- Urdu speech/audio/subtitle generation, heuristic audio-envelope mouth motion and a Godot AVI + FFmpeg MP4 assembly path.
- Durable SQLite job queue with bounded attempts, leases, expiry reclaim, cancellation/progress and endpoints for production, audio, world export and render.
- Windows CI, dependency locks, SBOM and installer workflow.

Important gaps remain: World Builder geometry is procedural blockout rather than a reusable detailed environment asset library; vehicle state is not yet animated as a full runtime; story generation remains manual AI handoff; the animation editor/library and blending are incomplete; Urdu phoneme/viseme alignment and native-speaker quality acceptance are outstanding; scene-level render caching/restart-resume and full 5–7 minute episode visual/audio acceptance are not complete; target-PC benchmarks and Phase 8 acceptance remain deferred. The project root still has no selected distribution LICENSE; do not assume one.

See `docs/MAINLINE_ALIGNMENT_AUDIT.md` for the detailed gap analysis and first-pass fixes. Never interpret green CI as final product acceptance.

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


## Live checkpoint amendment — 2026-11-25

The older baseline and phase checkpoint text above records the state before the Godot worker integration. The authoritative current state is:

- Main HEAD `1f68fe8e5e87dab3115c7ed95788a7eab4176aab`; Windows CI #204 passed on that exact commit.
- P2.1 (pinned Godot 4.7.2 native worker, Python supervision adapter, handshake, GLB inspection, runtime packaging and Windows integration tests) is complete and tested.
- Phase 2 remains active. Proceed to P2.2 Character Studio foundation; do not repeat P2.1 or restart earlier phases.
- P2.2 must deliver real character import/creation, rig-readiness inspection, supported modular appearance and preview; P2.3 then expands persistent identity and character metadata.
- Keep later phases in order and preserve all existing work. PC performance testing remains Phase 8 only.


## P2.2 implementation checkpoint — 2026-11-25

A first working Character Studio vertical slice is now in the repository (pending Windows CI acceptance): project-scoped GLB 2.0 upload, strict container validation and SHA-256 inventory, Godot 4.7.2 import inspection, skeleton/animation readiness reporting, versioned character profile creation/update/list/reopen, and canonical references from project.json. Portable character documents are re-indexed when the SQLite index is rebuilt.

This is deliberately not the P2.2 exit gate. Live 3D viewport/thumbnail preview, actual rig editing/creation, mesh/material/blend-shape authoring, GLB export round-trip and rendered consistency comparisons remain open. The current importer supports GLB 2.0 only; VRM support is not yet integrated.


## P2.2 first vertical slice — accepted by Windows CI #208

Commit `41aabbb627e36f3f02f306e79e3cba33bd19dc84` passed the complete Windows pipeline on 2026-11-25. The 45-test suite passed with the pinned real Godot 4.7.2 runtime available; Ruff, Python compilation, dependency lock, SBOM, bootstrap smoke test, both self-contained builds, NSIS installers and the clean-install/upgrade/uninstall/reinstall lifecycle all passed.

The accepted slice delivers GLB 2.0 import and inspection, persistent character profiles and project recovery. It does not close Phase 2. P2.2 continues with real 3D preview, mesh/rig/appearance authoring and export round-trip before the Character Studio exit gate can be considered.


## P2.2 interactive browser preview batch — 2026-11-25

A browser-side GLB presentation preview is implemented using locally vendored three.js 0.187.0 (MIT, pinned r187 commit `7e89746a687bb88271253698fa108b1dd59825d0`). It supports orbit/zoom, camera reset and embedded animation selection. The existing Godot worker remains the native import/inspection authority. The CI run for this preview batch is pending. This does not close Phase 2; mesh/rig/material editing and export remain required.


## 2026-11-25 — Imported humanoid rig checkpoint

Phase 2 remains active. Latest implementation HEAD is aadce3ed4c8444a3130652f14cc85cdfd4db697b. Character Studio now reports indexed humanoid profile mapping, parent-chain validity and per-bone imported rest transforms. A deterministic skinned 15-bone humanoid GLB fixture includes an imported arm animation. Dedicated Godot proof #8 and #9 passed: Godot imports the fixture, confirms skin binding and animation, and retargets the imported source animation to a target skeleton generated with different rest lengths. Proof #10 adds an imported retarget save/reopen assertion and is running. Windows CI #237/#238 passed; #240/#241 are running.

This remains a bounded fixture proof, not a production retarget pipeline for arbitrary user-supplied source/target GLBs. Next deliver the user-facing non-destructive retarget workflow and verify additional real models. Phases 3–7 remain open; target-PC testing remains Phase 8.

## 2026-11-25 — P2.2 modular character creator asset-library decision

P2.2 remains active. Imported GLB inspection, appearance recipes, rig diagnostics and native retargeting are necessary foundations, but they do not yet satisfy the master brief's requirement to create original stylized characters.

The next P2.2 sub-phase is the **Modular Character Builder**:

- First implementation uses Quaternius Ultimate Modular Men and Ultimate Modular Women CC0 1.0 packs: 11 + 10 outfit bases, four swappable parts (head/body/legs/feet) and 24 animations per outfit.
- The 21 pinned GLB conversions total 34.92 MiB. Three representative models (Male Adventurer, Male Worker, Female Adventurer) are verified by Godot for a shared 62-bone rig and matching bone-name sets before assembly work proceeds.
- The newer Universal Base Characters + Modular Character Outfits - Fantasy packs remain a later expansion: their standard outfit archive is 280 MiB and animation clips come from a separate library. Their standard humanoid rig and larger 62-part wardrobe are attractive, but the smaller ready-to-use 21-GLB set is the lower-friction first slice.
- Cartoon Studio owns the assembly, customization, recipe and export code. Only the CC0 model files are used from the asset-hosting repository; no third-party character-creator source code is reused.
- Model downloads are lazy, cached in the per-user data directory and checked against the immutable source commit, exact byte size and Git blob SHA-1 before use.

**Implementation order:** (1) verified CC0 asset library and catalog API, (2) native Godot assembly/export of four selected parts with one shared skeleton and all animation clips, (3) browser builder controls and preview, (4) versioned creation-recipe save/reopen. The phase remains PARTIAL until the assembled GLB, recipe round-trip and usable creator UI pass automated acceptance.


## 2026-11-25 — P2.2 modular assembly milestone accepted

- Merged PR #3 as `b4dd8237e6369bbb74c58ef844e0fac5c9667c77`; main-branch CI run `45653650908` passed.
- The pinned Quaternius CC0 library now feeds a first-party Character Studio builder with head/body/legs/feet selectors. Slot candidate labels constrain the corresponding selector; only skinned meshes with resolvable skeletons are offered.
- The Godot worker assembles selected parts onto the base rig only when bone count/order/names, parent hierarchy, rest transforms and rig transforms match. Skin bind references are checked; incompatible rigs are rejected rather than silently remapped. Existing skinned outfit meshes on the base are removed so the selected outfit is what remains.
- The exported GLB is re-imported and checked for all four named modular meshes and the complete base animation-name set. The real integration test combines Beach head, Casual_2 body, Farmer legs and King feet on the Male Adventurer base and verifies preservation of its 24 animation clips.
- The assembled asset manifest stores the base/part recipe and supports restoring its source GLBs into the builder. The profile remains versioned and project-scoped.
- Evidence: [feature integration CI](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45653413604) and [main merge CI](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45653650908), both SUCCESS.
- Phase 2 remains ACTIVE and P2.2 remains PARTIAL. This is not arbitrary-rig retargeting, mesh sculpting, new rig authoring, texture painting or final visual acceptance. The next batch must validate the browser builder and improve real geometric customization before P2.2 can exit.


## 2026-11-25 — P2.2 accessory assembly milestone accepted

- Merged PR #4 as `f00bb3dbba55af7b6f3a02ca5b602bf773872a35`; accessory feature CI run `45654673022` passed the mixed-outfit plus accessory integration test. Main-branch CI was queued at this checkpoint.
- The modular builder now supports up to eight optional accessories in addition to head/body/legs/feet. Skinned accessories are rebound to the exact shared rig; static accessories must originate beneath a valid `BoneAttachment3D` and are attached to the matching named bone on the base skeleton.
- The Godot worker validates accessory source paths, duplicate mesh selections, skeleton/rest-pose/transform compatibility, skin bind references and attachment-bone identity. It verifies accessory meshes survive GLB export/re-import.
- The real integration test adds the Adventurer Backpack to the Beach/Casual_2/Farmer/King mixed outfit and verifies the base animation set remains intact. Assembly manifests store and restore accessory selections and attachment bones.
- This adds accessory attachment, not general-purpose hair/face sculpting, arbitrary-rig conversion or interactive visual acceptance. Phase 2 and P2.2 remain PARTIAL.


## 2026-11-25 — P2.2 semantic facial expression presets

- Added Smile, Frown, Surprise and Angry presets for imported morph targets.
- Presets only affect targets whose imported names contain supported semantic tokens; unmatched targets remain at imported default values. No facial geometry or morph targets are fabricated.
- Presets update the live preview, individual sliders and the existing versioned appearance save endpoint. Manual slider fine-tuning and reset remain available.
- Added Node unit coverage for matching, baseline restoration, unmatched-target safety and invalid preset names, wired into pytest.
- Semantic mapping is best-effort for compatible imported assets, not a universal guarantee across arbitrary GLBs.


## 2026-11-25 — P2.2 creator workflow and animation-quality gates

- PR #6 adds one-click outfit shuffling using unique source meshes and direct GLB downloads for assembled and saved characters. Feature CI `45655967987` and main CI `45656217264` passed.
- PR #7 adds a deterministic Godot animation playback probe. It imports the exported GLB, plays the selected clip, samples skeleton poses, reports changed bones, counts skinned meshes bound to the skeleton and lists valid BoneAttachment3D bones. The mixed outfit plus Backpack integration test confirms the Walk clip changes bone poses and at least four skinned meshes remain bound. Feature CI `45655936153` and main CI `45656445021` passed.
- PR #9 adds Smile, Frown, Surprise and Angry presets for imported morph targets. Presets only modify name-matched targets, preserve unmatched target values, update manual sliders/live preview and use the existing versioned appearance persistence. Node unit tests cover matching and invalid preset names; preset controls are enabled only when morph targets exist. Feature CI `45656755304` passed.
- PR #5 added Node 22 browser-JavaScript syntax validation to the main CI workflow; its feature and main CI runs `45655204627` and `45655471623` passed.
- Main CI for the expression-preset merge was run `45657010942` and was pending when this checkpoint was written.
- Phase 2 and P2.2 remain PARTIAL: automated native assembly and pose verification are now covered, but interactive browser visual acceptance, saved-profile recipe round-trip/reassemble, browser playback review and real geometric proportions/face/hair authoring remain.


## 2026-11-25 — P2.2 native appearance baking and GLB export

- Character appearance recipes now retain imported mesh/surface and blend-shape bindings alongside editable PBR and morph values.
- Added a native Godot worker operation to apply supported BaseMaterial3D color/roughness/metallic changes and blend-shape weights to a fresh imported scene, export a new GLB, re-import it, and verify the baked values.
- Added a project-scoped export endpoint that creates a new versioned asset manifest and download URL. The original source GLB and character asset reference remain unchanged.
- Added browser export controls and integration coverage using the pinned CC0 RobotExpressive facial-morph fixture.
- This batch supports named imported morph targets and BaseMaterial3D surfaces; arbitrary shader materials and ambiguous duplicate mesh names are rejected rather than guessed.
