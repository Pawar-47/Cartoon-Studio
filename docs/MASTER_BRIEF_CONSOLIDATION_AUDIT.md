# Master Brief Consolidation Audit — Initial Checkpoint

**Date:** 2026-11-28  
**Repository:** `Pawar-47/Cartoon-Studio`  
**Branch:** `main`  
**Initial code-audit HEAD:** `e0e288006c13347d2bbc99ff388948c16a9e6011`
**Current code HEAD at refresh:** `4b1ed4be6beaa3048588e169ff0ca6024a364328` (world-asset persistence correction; CI #617 passed)  
**Latest observed CI:** #615 — SUCCESS on the audited HEAD  
**Binding source:** `docs/MASTER_EXECUTION_PROMPT.md` (25 parts, 1,133 lines)  
**Supporting source:** `docs/PROJECT_SPECIFICATION.md` (24 numbered sections)

## 1. Purpose and scope

This is a consolidation audit of work already present on `main` against the complete original Master Execution Prompt. It is not a declaration that future requirements are defects. The audit separates:

1. **Completed implementation slices** — functionality already present, with its actual evidence boundary.
2. **Incomplete or partially accepted implementation** — work exists but does not yet meet the brief's full acceptance requirement.
3. **Not-yet-started requirements** — future work, not a defect in completed work.
4. **Consolidation defects** — contradictions, stale records, missing traceability, incorrect status claims, adapter/UI mismatches, or implementation regressions in work already delivered.

The frozen Character Foundry feature branch is not an implementation source and is not modified. This audit uses the live `main` branch only. No feature development is authorized by this audit checkpoint.

## 2. Source and repository integrity

- The verbatim Master Brief exists at `docs/MASTER_EXECUTION_PROMPT.md` on `main`; its 25-part structure and 1,133-line length were confirmed from the live file.
- `docs/PROJECT_SPECIFICATION.md` contains 24 numbered sections and is a companion specification, not a replacement for the original brief.
- The live registry contains 171 unique atomic requirement IDs.
- The requirement traceability matrix contains the same 171 unique IDs, with no duplicate IDs detected.
- The architecture traceability matrix also contains 171 unique IDs.
- Live `main` is `e0e288006c13347d2bbc99ff388948c16a9e6011`; CI #615 succeeded on that exact commit.

## 3. Confirmed consolidation discrepancies

### CONS-001 — Registry status summary contradicts its own rows
**Severity:** High  
The registry introduction and `GOV-R004` evidence state that no requirement is VERIFIED, but the atomic rows include `PHASE-R002` with status `VERIFIED`. This is an internal contradiction. The status itself may be justified by the recorded Phase 1 installer lifecycle evidence, but the summary must be corrected and the verification scope must remain explicit.

**Correction required:** Reconcile the registry summary against all 171 row statuses; retain VERIFIED only where the cited acceptance evidence directly proves the complete atomic requirement.

### CONS-002 — Traceability matrix contains obsolete source-of-truth claims
**Severity:** High  
The current `REQUIREMENT_TRACEABILITY.md` contains a closing historical claim that the exact original prompt is not committed, which is now false because `docs/MASTER_EXECUTION_PROMPT.md` is present on main. It also carries historical HEAD/CI references (including `4171bb3`, `6823cdf`, CI #67/#68) in current-looking evidence fields. The false prompt claim and selected current-checkpoint fields are being corrected; dated historical evidence is retained where useful.

**Correction required:** Preserve historical evidence as dated history where useful, but replace current-state claims with the live source path, current hash/line count, and evidence tied to the relevant implementation commit and CI run.

### CONS-003 — Registry and traceability evidence is not synchronized to current main
**Severity:** High  
The registry and traceability matrices contain evidence from early November 25 checkpoints, including early shell-only descriptions and old main HEAD references. The application has since gained substantial Character Studio, World Builder, audio, rendering, queue, installer, asset-catalogue and Godot-worker functionality. Some rows may already have current mappings elsewhere, but their evidence fields do not consistently represent the current mainline implementation.

**Correction required:** Reconcile each of the 171 atomic rows against current source, tests, reports and workflow evidence. Do not bulk-upgrade statuses based on the presence of code.

### CONS-004 — Cross-document phase and checkpoint drift
**Severity:** High  
`BASELINE_AUDIT.md`, `MASTER_BRIEF_COMPLIANCE_AUDIT.md`, parts of `MASTER_PLAN.md`, and sections of `NEXT_STEPS.md` retain historical phase states, old HEADs, old CI numbers and pre-Godot/pre-installer descriptions. These records are useful as history but are not clearly separated from the current baseline.

**Correction required:** Keep immutable historical audit records, add dated superseding current-state sections, and ensure the live status/next-step documents use one consistent HEAD, phase table and acceptance boundary.

### CONS-005 — Phase completion language needs evidence-scoped interpretation
**Severity:** High  
The current status marks Phases 0 and 1 complete. The recorded P0.7 and P1.4 evidence supports research/architecture closure and a Windows installer lifecycle proof at their respective historical checkpoints. However, these phase labels must not be read as proof that every downstream production requirement is complete. The registry's atomic requirements and the final product acceptance criteria remain controlling.

**Correction required:** Retain phase closure only for the defined phase gate; explicitly distinguish phase-gate completion from overall product acceptance and from later regressions or new integration requirements.

### CONS-006 — Current implementation has important acceptance boundaries
**Severity:** High  
The following are real implementation slices, but must not be represented as complete end-to-end brief requirements without further acceptance:
- Character Studio: imported GLB editing, profile persistence, proportions, hairstyles, face geometry, morphs and retargeting exist; arbitrary-rig compatibility and interactive visual acceptance remain bounded.
- World Builder: persistent/editable world documents, 17 object kinds, Godot scene export and GLB preview exist; the exporter previously produced primitive blockout geometry. The new curated asset library is connected to export, but a real downloaded GLB rendering acceptance test is still required.
- Vehicle system: APIs/state/events exist; actual scene-time movement, steering, wheel rotation, braking and character enter/exit playback remain incomplete.
- Story/scene system: structured manual prompt/paste, validation, world/cast binding and editable scene generation exist; direct supported-provider generation/repair is not established.
- Animation: procedural action/camera/expression tracks exist; a reusable motion library, blending and full timeline editing/visual acceptance remain incomplete.
- Urdu audio: WAV/subtitle/mix and heuristic mouth envelopes exist; heuristic envelopes are not phoneme/viseme-accurate lip-sync. Native-speaker review and voice consistency acceptance remain open.
- Episode production: Godot scene rendering and FFmpeg MP4 assembly path plus durable SQLite job records/leases exist; no complete 5–7 minute episode has passed visual/audio acceptance, and scene-level cache/restart-resume remains open.

**Correction required:** Ensure every corresponding atomic row states the precise implementation and test boundary, not merely a feature name.

### CONS-007 — Queue documentation must distinguish durable records from supervised execution
**Severity:** Medium  
The latest status correctly states that a durable SQLite queue exists and is wired into production operations, with leases, reclaim, bounded attempts and cooperative cancellation. Some older records still say no durable render queue exists. Conversely, the current queue should not be described as a separately supervised multi-worker service or as full scene-level restart recovery.

**Correction required:** Standardize queue wording across documents and keep the distinction between durable job state, in-process execution, worker supervision, scene caching and restart recovery.

### CONS-008 — World Builder integration introduced a real adapter/UI consistency history
**Severity:** Medium  
The first-pass audit found that the browser exposed only 7 of 17 backend object kinds and the engine adapter accepted only 7. The browser palette and position/rotation controls were expanded, and the adapter allowlist was aligned to all 17 with regression coverage. These fixes are present in the current mainline history; the audit should retain the defect/fix evidence rather than treating the earlier state as current.

**Correction required:** Confirm current tests exercise the full browser/API/adapter/export chain and retain the original defect as a closed historical finding.

### CONS-009 — CI success is being used at different evidence levels
**Severity:** High  
CI #615 passing proves the checks in that workflow passed on `e0e2880`; it does not prove browser visual quality, real-asset rendered correctness, full episode output, target-PC performance or complete final acceptance.

**Correction required:** Every test/evidence reference must state exactly what the workflow ran and what it did not run. Keep visual/audio/target-PC acceptance separate.

## 4. Work already present on main — provisional inventory

The following implementation areas are confirmed by current repository paths and current project reports; their exact atomic requirement mappings and acceptance levels must be reconciled row-by-row in the next audit pass:

- FastAPI local service, browser workspaces, SQLite project persistence and versioned project documents.
- Windows CI, pinned dependencies, Godot runtime acquisition, self-contained packaging and installer lifecycle automation.
- Godot 4.7.2 worker and engine adapter; GLB import/inspection and editable scene export.
- Character import, project-scoped profiles, proportion controls, appearance recipes, imported morph controls, procedural hair/face operations, retargeting and browser preview.
- Persistent World Builder documents, templates, 17 object categories, world-scene export, GLB preview and project-scoped CC0 model catalogue with integrity checks.
- Story schema/prompt builder/validation and world/cast binding.
- Urdu audio generation, subtitles, audio mixing and heuristic mouth-envelope data.
- Editable episode scene generation, Godot AVI rendering, FFmpeg MP4 mux path and durable SQLite job records.
- License/provenance records, vendored three.js runtime and third-party notices.

This inventory is not a VERIFIED status list. Each item requires a specific source/test/evidence mapping.

## 5. Explicitly future work — not consolidation defects by itself

Unless a current implementation is found to violate an already-delivered requirement, the following remain future/incomplete requirements rather than defects simply because they are absent:
- Full production-grade world art and broad asset coverage.
- Vehicle runtime animation and character interaction playback.
- Full integrated story-provider orchestration, approval and repair.
- Reusable motion library, blending and complete timeline editor.
- Phoneme/viseme-accurate Urdu lip-sync, native-speaker quality review and character-specific voice acceptance.
- Full 5–7 minute episode acceptance with inspected visuals/audio and editable-project reopen.
- Scene-level render cache and robust restart recovery.
- Target-PC performance benchmarks and final quality-preset tuning.
- Final end-to-end release/installation acceptance after all production modules are integrated.

## 6. Consolidation sequence

1. **Evidence reconciliation:** audit all 171 atomic registry rows against live source, tests, reports and CI runs; correct stale claims and status mismatches.
2. **Traceability repair:** ensure every requirement maps to current architecture, actual source files, meaningful tests, evidence and an honest status.
3. **Implementation defect review:** inspect completed modules for missing wiring, inconsistent schemas, stale adapters, incorrect defaults, unsafe persistence/import/export behavior and regressions against the brief.
4. **Cross-module integration review:** check project/character/world/scene/animation/audio/job/render data flow for stable IDs, versioning, persistence and round-trip behavior.
5. **Correction batches:** fix confirmed defects in coherent batches, preserve current mainline work and run one CI checkpoint per substantial batch.
6. **Baseline freeze:** update the current status, master plan, next steps, test report and session checkpoint to one consistent main HEAD and acceptance boundary.

## 7. Operating constraints

- Work only on `main`; preserve the current branch history and all existing work.
- Do not reopen or merge the frozen Foundry branch.
- Do not start new feature scope until consolidation defects in the already-delivered baseline are resolved or explicitly accepted.
- Do not create repeated CI runs; group related corrections and use one checkpoint run.
- Do not mark requirements VERIFIED from code presence or lint/compile success alone.
- Preserve the exact Master Brief and its 25-part order.
- Keep future requirements pending rather than disguising them as completed or treating them as regressions.

**Audit state:** INITIAL CHECKPOINT plus targeted 2026-11-28 source corrections through CI #617. Row-by-row evidence reconciliation and source-level defect review remain in progress. The 171-ID structural match is not proof that every row is current.


## 2026-11-28 — Follow-up reconciliation checkpoint

- Re-fetched live `main`; HEAD was `8647693ae6e1e28f225b810416f32ce62ec29ddb`.
- Confirmed the latest code-bearing commit remains `e0e288006c13347d2bbc99ff388948c16a9e6011`; Windows CI #615 (run `46064317433`) passed on that exact commit. Its job ran locked dependency verification/install, pinned Godot and fixture setup, Ruff, browser JavaScript syntax, Python compilation and the test step.
- Confirmed registry and traceability each contain 171 unique IDs with matching structural coverage. Confirmed one VERIFIED registry row: `PHASE-R002`, limited to the Phase 1 installer lifecycle gate. Corrected the contradictory registry summary.
- Corrected the traceability document's false statement that the original prompt is not committed, and refreshed selected current-checkpoint metadata. The architecture crosswalk remains historical/planned and requires row-by-row source-path validation.
- Refreshed `PROJECT_STATUS.md` and `NEXT_STEPS.md` to distinguish the current docs HEAD from the latest code-bearing CI checkpoint.
- No application code was changed and no new CI run was triggered. The remaining work is the source/test/evidence reconciliation and implementation defect review described in the sequence above.


### CONS-010 — World asset selection was dropped by the API schema

**Severity:** High  
The World Builder browser downloaded a curated model, then stored both `asset_id` and `asset_path` on its in-memory object. However, `WorldObjectInput` did not declare either field. Pydantic silently discarded these extras when create/update payloads were parsed, so a selected GLB could be cached but not survive a saved world document. The exporter already expected a project-local `asset_path`, so this broke the intended catalogue-to-export connection.

**Correction committed:** `4b1ed4be6beaa3048588e169ff0ca6024a364328`. The API now accepts only the curated `asset_id`, checks that the selected asset category matches the world object kind, installs/verifies the asset in the project cache, discards any browser-supplied path, and derives the canonical project-relative `asset_path` server-side. Create/update persistence and adapter regression tests were added.

**Evidence:** Windows CI #617 passed on the correction commit. The new API tests cover create → save → reopen → update persistence, forged client path rejection by derivation, unknown IDs and category mismatches. The adapter test confirms the validated project-local path is forwarded to the worker.

**Remaining acceptance:** CI uses a test fixture for the API and a fake adapter invocation for path forwarding. It does not yet prove a real downloaded Kenney GLB imports and renders visibly in Godot. That remains a separate visual acceptance item, not a reason to disregard the persistence correction.
