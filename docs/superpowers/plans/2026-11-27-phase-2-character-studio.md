# Phase 2 Character Studio Completion Plan

> **For agentic workers:** Execute this plan on `feature/cartoon-character-foundry` only. Preserve `main`; do not merge PR #23 without explicit user approval.

**Goal:** Close Phase 2 with original editable male/female cartoon characters, persistent identities, usable rigs, integrated import/preview/export workflows, and CI evidence from a real browser session.

**Architecture:** Keep the browser editor as the primary authoring surface, FastAPI as the local project/API layer, GLB 2.0 as the portable character artifact, and the pinned Godot 4.7.2 worker as the authoritative importer/exporter/rig verifier. Use Playwright in Windows CI to launch the actual app, exercise the UI and capture screenshots/artifacts.

**Tech Stack:** Python 3.11, FastAPI, Three.js 0.187, GLB 2.0, Godot 4.7.2, Node 22, Playwright Chromium, GitHub Actions.

**Spec:** `docs/PROJECT_SPECIFICATION.md` §9; `docs/MASTER_EXECUTION_PROMPT.md` Part 9; `docs/MASTER_PLAN.md` Phase 2; `docs/REQUIREMENTS_REGISTRY.md` CHAR-R001–CHAR-R006; `docs/REQUIREMENT_TRACEABILITY.md`.

## Global Constraints

- Work only on `feature/cartoon-character-foundry`; keep `main` untouched.
- Do not merge PR #23 until Phase 2 exit evidence is complete and the user approves integration.
- Preserve imported source GLBs byte-for-byte; save generated edits as new project assets.
- No mandatory paid APIs, cloud inference, or cloud rendering.
- Original characters and assets only; retain upstream asset and software license notices.
- Windows CI must use the pinned Python/Godot/Three.js versions already specified by the repository.
- One coherent implementation batch and one CI run at a time; do not push while CI is active.
- A passing unit suite is not visual acceptance. Save browser screenshots and inspect them.

## Review Focus

1. Generated faces must have visible, correctly oriented eyes, brows, nose and mouth rather than skin-coloured placeholder geometry.
2. Hair, face features and clothing must stay attached to the intended bones when morphs are applied.
3. Adult male and female templates must be recognizably distinct without breaking rig structure.
4. Saved recipes and profile metadata must survive reload/reopen without losing source asset identity.
5. WebGL/browser failures, missing Godot runtime, and unsupported rigs must fail clearly rather than silently claim acceptance.

---

### Task 1: Real browser acceptance in Windows CI

**Files:**
- Modify: `.github/workflows/ci.yml`
- Create: `scripts/character_studio_visual_acceptance.mjs`
- Create: `docs/superpowers/plans/phase-2-progress.md` (execution ledger)

**Interfaces:**
- Start the actual FastAPI app with `uv run --locked uvicorn app.main:app`.
- Use `CARTOON_STUDIO_DATA` and `CARTOON_STUDIO_GODOT_PATH` to isolate the CI project and select the pinned worker.
- Browser automation must use the existing `/characters?project=<id>` UI and project-scoped APIs.

- [ ] Install pinned Playwright without modifying the Python dependency lock.
- [ ] Install Chromium in the Windows runner.
- [ ] Launch the app and wait for `/api/health` and Godot `/api/engine/status`.
- [ ] Create a project, create male and female Foundry characters through the actual UI, verify GLB responses and browser preview, edit/reopen a saved recipe, and save screenshots.
- [ ] Upload screenshots and browser logs as a workflow artifact even on failure.
- [ ] Keep the existing single Windows CI job and its non-cancelling concurrency policy; do not create a parallel workflow.

### Task 2: Original Foundry face geometry and expression morphs

**Files:**
- Modify: `app/character_foundry.py`
- Modify: `app/main.py`
- Modify: `app/static/characters.html`
- Modify: `app/static/characters.js`
- Test: `tests/test_character_foundry.py`

**Interfaces:**
- Keep recipe schema versioned and backward-compatible with existing v1 recipes.
- Preserve existing 10 body morph keys; add explicit face/expression keys and validated face material fields.
- Export visible separate GLB primitives/materials for eye whites, irises, pupils, brows, nose and mouth, skinned to `Head`.
- Add actual morph target deltas for smile, mouth opening, eye scale/spacing and brow angle.
- Restore all face settings when editing a saved Foundry recipe.

### Task 3: Body, clothing and hair deformation integrity

**Files:**
- Modify: `app/character_foundry.py`
- Modify: `tests/test_character_foundry.py`
- Modify: `engine/godot_worker/worker.gd` only if the GLB-level fix cannot satisfy the contract.
- Test: Foundry and pinned-Godot integration coverage.

- [ ] Prove morph targets move the intended body/face vertices and preserve normalized skin weights.
- [ ] Prove clothing remains fitted for meaningful torso/shoulder/leg morph extremes.
- [ ] Prove all hairstyle variants export with the same rig and no invalid indices/normals.
- [ ] Prove female and male templates remain distinct and both use the same humanoid rig contract.

### Task 4: Character Studio integration and persistence

**Files:**
- Modify: `app/main.py`, `app/static/characters.js`, `app/static/characters.html` only as needed.
- Test: `tests/test_characters.py`, `tests/test_engine.py`, `tests/test_engine_api.py`.

- [ ] Create, edit, save, reload and reopen Foundry characters without changing stable character IDs.
- [ ] Verify source recipe, generated GLB, profile metadata, appearance settings and asset manifest remain linked.
- [ ] Verify portrait PNG and four-view turnaround exports from a real browser preview.
- [ ] Exercise the existing CC0 import/inspection, modular assembly, proportions, hairstyle, face, material and morph controls.
- [ ] Verify Godot import/re-import and animation preservation where an animated source GLB is used.
- [ ] Retain clear diagnostics for unsupported rig hierarchy or animation incompatibility.

### Task 5: Phase 2 exit review and documentation

**Files:**
- Update: `docs/REQUIREMENTS_REGISTRY.md`
- Update: `docs/REQUIREMENT_TRACEABILITY.md`
- Update: `docs/PROJECT_STATUS.md`
- Update: `docs/NEXT_STEPS.md`
- Update: `docs/TEST_REPORT.md`
- Update: `docs/P2_2_CHARACTER_STUDIO_REPORT.md`
- Update: `docs/EXECUTION_BATCH_PLAN.md`

- [ ] Reconcile CHAR-R001–CHAR-R006 against the actual code, tests, browser screenshots and Godot results.
- [ ] Mark requirements VERIFIED only when their own acceptance evidence exists; defer cross-episode story/voice runtime wiring to dependent phases where appropriate.
- [ ] Run the complete Windows CI once after the final coherent batch.
- [ ] Inspect the screenshot artifact and record any remaining visual defects.
- [ ] Close Phase 2 only if the master plan exit gate—create, save, reopen and reuse original cartoon characters with stable appearance and working rigs—is directly demonstrated.

## Phase 2 exit criteria

- Original male and female cartoon characters are editable from recipes, with visible face and hair geometry.
- Body/face morphs and clothing/hair deformation preserve the shared humanoid rig.
- Existing imported GLB workflow still works, including inspection, preview, appearance editing, portrait/turnaround export and safe source preservation.
- Character profiles, asset manifests and recipes save/reopen with stable identity.
- Godot imports/re-imports generated GLBs and verifies the rig; animation retention is proven on animated imported assets.
- Windows CI launches the real app in Chromium, completes the UI workflow, captures screenshots, and uploads evidence.
- Registry, traceability and reports reflect the evidence honestly.
