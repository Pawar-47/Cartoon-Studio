# Session-independent development checkpoint

Updated: 2026-11-26
Repository: https://github.com/Pawar-47/Cartoon-Studio
Source of truth: `main` at `062400e58cbbf491ec92869dc140b60a9b354d7f`.
Active working branch: `work/mainline-followup`, created from that main commit.
Latest main CI #471 failed because Godot could not parse a duplicate `action_cue_count` dictionary key in the episode worker. Commit `be169c4` on the pushed working branch fixes it; the cue regression test and full pytest pass locally (136 passed, 4 skipped). Post-fix CI is pending; the workflow requires a PR targeting `main`.

## Mission and operating rules

Build the complete local-first Cartoon Studio desktop application defined by `MASTER_EXECUTION_PROMPT.md`, `MASTER_PLAN.md` and `PROJECT_SPECIFICATION.md`.

- GitHub `main` is the only source of truth.
- Preserve accepted work; do not restart completed phases or reset repositories.
- Work in substantial, coherent feature batches.
- Report implementation, automated tests, Godot execution and visual acceptance separately.
- Respond in English.
- Physical-PC testing and performance benchmarking remain Phase 8; they are not development gates.

## Current phase

Phase 2 — Character Studio is ACTIVE; P2.2 remains PARTIAL. Phase 0 and Phase 1 are complete. Partial/out-of-order world, story-binding, timeline and episode-scene code is present on main, but it does not close the Phase 2 gate or establish phase acceptance.

## Latest merged work

- PR #10: appearance recipes can be baked into a new GLB by the Godot worker; baked material and morph values are re-imported and verified, animation clips are retained, and the source GLB remains unchanged.
- PR #11: modular assembly recipes now have API-level save/reopen/reassemble regression coverage, including all source asset manifests and a bone-attached accessory.
- PR #15: compatible imported humanoid rigs expose body-proportion controls; the worker exports/re-imports a new GLB and verifies changed bones while retaining animations and preserving the source. Existing face/body morphs are grouped into corresponding controls.
- PR #17: generated hairstyles attach to the imported Head bone and are verified after export with animation clips retained.
- PR #19: the browser preview can be exported as a transparent PNG portrait.
- Main CI runs #421 and #423 passed. PR #20 turnaround-sheet export is open with passing CI #425 and remains separate from this branch.

## Implemented Character Studio capabilities

- Project-contained GLB 2.0 import, validation, SHA-256 provenance and Godot inspection.
- Browser GLB preview, imported animation selection and camera controls; default selection prefers Idle and RESET-only assets report no playable animations.
- Persistent editable character profiles.
- Rig-based torso/shoulder/arm/leg/head proportion controls for compatible imported humanoids; generated GLBs are separately stored and verified, leaving the source unchanged. Existing imported face/body morph targets are grouped and editable; this does not create new geometry or morphs.
- Seven procedural hairstyle choices generate Head-attached geometry; the worker verifies export and animation retention while preserving the original GLB. Transparent PNG portrait export is available from the browser preview.
- Non-destructive PBR material recipes and facial morph-target controls. Godot reports imported blend-shape names/defaults; signed weights from -1 to 1 persist; reset restores each model's imported defaults. A pinned CC0 RobotExpressive fixture is fetched and SHA-256 verified; CI #334 passed Godot import, morph-target and multi-clip inspection. The imported clip catalog/source selector passed CI #340. CI #341 and native-worker proof #22 passed bone-roll/non-uniform-scale retarget acceptance. Godot native-worker proof #346 passed RobotExpressive Walking-clip retarget, scene save/reopen and pose-transfer verification; CI #349 passed the source-only IK-foot hierarchy API/UI checks.
- Conservative indexed 15-bone humanoid mapping, parent-chain validation and imported rest-transform diagnostics.
- Common 3ds Max Biped, Character Creator, Unreal-style, Blender Rigify and Cesium Rigged Figure bone naming conventions are recognized. Duplicate and negative bone indices are rejected.
- Character-to-character retarget UI with source/target selectors, imported animation dropdown, strict clip-name preflight, saved Godot scene, persistent JSON record and scene download.
- Worker reopens the saved scene, verifies source animation playback and source-pose change, then compares the target pose against Godot's model-space rest-corrected retarget transform. This supports different rest-axis/bone-roll conventions; raw local source/target angles are diagnostics, not an equality requirement.
- Saved retarget records expose a separate Three.js browser preview using persisted canonical mappings. Saved animation names resolve exactly or by a unique Godot library suffix; missing or ambiguous names fail visibly rather than falling back to another clip. The saved Godot scene remains authoritative.
- Original source and target GLBs remain byte-identical.

## Imported fixture coverage

- Synthetic source/target pair: animated Mixamo-style source; separate target with different limb proportions, reordered raw skin joints and recalculated inverse-bind matrices.
- Real third-party source: `tests/fixtures/third_party/rigged_figure_ccby.glb`, Khronos glTF Sample Assets / Cesium, 2017, CC-BY-4.0. Original binary bytes are unchanged; upstream license and attribution are stored beside it.
- The third-party 19-joint rig uses names such as `torso_joint_1`, `leg_joint_L_1`, and `arm_joint_R_1`. The worker maps 15 core humanoid bones and retargets its animated source to the canonical target in Godot.
- The worker test saves and reopens the native scene, checks source animation and target pose using model-space rest correction, and confirms both original GLBs remain byte-identical.
- Godot may normalize raw GLB skin-joint ordering during import. The application uses actual bone names/indices returned by Godot inspection, never raw array positions.

## Verification

- Windows CI #285 passed DCC naming-family tests and malformed-index rejection.
- Windows CI #293 passed the full pipeline for Godot facial blend-shape inspection, the two-target GLB fixture, signed morph-weight persistence and Character Studio reporting.
- Windows CI #326 passed the full Windows pipeline on commit `696929595b2d03e64e46a568ec9d163860ae3239`, including lint, compilation, full tests, pinned Godot 4.7.2 worker, bootstrap, both self-contained builds, NSIS installers and install/upgrade/uninstall/reinstall lifecycle.
- Main CI #421 passed the generated-hairstyle worker coverage; CI #423 passed transparent portrait export coverage.
- Local integration branch full suite: 96 passed, 28 skipped; 24 pinned-Godot cases, three Node.js cases and one symlink case were unavailable locally. Ruff, compileall and whitespace checks passed.
- Earlier synthetic Mixamo source/target retarget fixture remains green and preserves both source assets.
- Dedicated browser visual acceptance has not been performed. Browser preview is not claimed to be equivalent to native Godot rendering.

## Important acceptance boundary

Two real third-party assets have passed native Godot acceptance for tested scenarios: Khronos Rigged Figure retargeting and RobotExpressive Walking/Running/Dance retargeting with its bilateral IK-foot hierarchy. This is not blanket support for arbitrary GLBs. Generated hairstyles and portrait export still need interactive visual acceptance; original face geometry also remains. Phase 2 remains ACTIVE and incomplete.

## CI execution policy

- Push/PR CI runs lint, Python compilation and the full automated test suite only; no PyInstaller or NSIS builds. Quick CI #356 also runs the Node.js unit suite for strict browser clip-name resolution.
- Full Windows application and installer validation lives in `.github/workflows/release-windows.yml` and is manually dispatched after a phase/release milestone.
- The dedicated Godot native-worker proof is now manual-only and reserved for phase milestones; routine pushes run one quick CI workflow. Full Windows application and installer validation remains manual in `.github/workflows/release-windows.yml`.
- Workflow concurrency groups prevent overlapping runs. Avoid duplicate CI runs for minor edits.

## Current retarget and browser-preview acceptance — 2026-11-25

- The target fixture generator supports local bone-roll quaternions and non-uniform per-bone scales, and recalculates inverse-bind matrices from full TRS transforms.
- Windows CI #341 passed the generated rolled/scaled target through native Godot retarget, save/reopen and model-space pose verification.
- RobotExpressive native retarget proof #346 passed; CI #349 accepted the bilateral IK-foot topology as a source-only variant. CI #351–#352 passed Walking, Running and Dance clip retargets.
- CI #356 passed deterministic sampling at 37% of the selected animation and the strict browser clip resolver. Unknown or ambiguous saved clip names no longer silently select the first GLB animation.

## Next substantial implementation batch

1. Perform browser acceptance of generated hairstyles and transparent PNG exports, then cover modular assembly, body-proportion controls and imported face/body morphs on representative models.
2. Inspect body-proportion and baked-appearance exports visually, verify animation playback and source-file immutability.
3. Compare browser retarget preview motion against the authoritative Godot scene across accepted humanoid, bone-roll and RobotExpressive fixtures.
4. Continue original face geometry authoring; generated hairstyles and imported-morph grouping do not establish original face authoring.

## Later phases

- Phase 3 — World Builder: PARTIAL / OUT-OF-ORDER; persistent/editable worlds, world-scene exports and browser previews exist, but multi-location acceptance remains.
- Phase 4 — Story and Scene Engine: PARTIAL / FROZEN; out-of-order world linking, cast binding and scene generation exist but do not complete the phase.
- Phase 5 — Animation Engine: PARTIAL / OUT-OF-ORDER; action-anchor and camera keyframes exist, but no real clip library, timeline editor or visual acceptance.
- Phase 6 — Urdu Voice and Lip-Sync: research complete; implementation not started.
- Phase 7 — Episode Generator: PARTIAL / OUT-OF-ORDER; editable scene files and GLB previews exist, but no render queue or final episode pipeline.
- Phase 8 — Optimization and Reliability: deferred, including physical-PC performance testing.

Never claim the complete application is finished while Phases 2–7 remain incomplete.


## 2026-11-25 — Body-proportion editing checkpoint

- Current GitHub main: `f9a03b9613d22c8bf99e96c5cf3d5de9997e0fd2`; quick CI #417 passed.
- Local focused tests on Windows/Python 3.12.10: `tests/test_app.py`, `tests/test_characters.py` and `tests/test_engine.py` completed with 39 passed and 5 skipped in 7.54 seconds; the skips require the pinned Godot runtime. CI #417 ran the full suite with Godot and Node configured.
- The existing downloaded folder at `Downloads/Cartoon-Studio-main` remains untouched. Work is in the separate `Downloads/Cartoon-Studio-main-current` clone on `work/p2-2-body-shape-acceptance`.
- The Character Studio page loaded in the integrated browser, but no character model was imported or rendered. Keep Phase 2 active and P2.2 partial; next validate the body controls and exported appearance on representative characters.


## 2026-11-25 — Browser retarget scene-root correction batch

- Repository head before this batch: `dcacb5aa7d72ac6cf415321c6b8e7a7132484cfe`; quick CI #357 passed.
- Found a structural risk in browser retargeting: GLTF animation tracks are resolved from the scene hierarchy, while the prior code passed only the first SkinnedMesh to Three.js. In common GLTF layouts the joint hierarchy is a sibling of that mesh, so source tracks may not reach their bones.
- The batch introduces a tested helper that attaches each imported skeleton to its GLTF scene root for retarget sampling, validates all 15 canonical mappings and duplicate assignments, and plays the generated clip through the target SkinnedMesh skeleton.
- Added a Node test using the vendored Three.js SkeletonUtils implementation, a full 15-bone rig pair, different source/target bone names, a rolled target upper arm and hip translation.
- Added a pytest wrapper so the Node suite runs in normal quick CI.
- Pending: inspect the complete diff, run quick CI once, and then perform interactive browser acceptance. No full app build or installer run is required.

## 2026-11-25 — Modular character library batch started

- Repository head at batch start: 3b4846bdd5b673311129dda6c08bcb232b5bf414; Windows CI #362 passed.
- P2.2 is being re-anchored to the master brief's original-character creation requirement. The selected starter assets are Quaternius Ultimate Modular Men/Women CC0 1.0 (21 outfit GLBs, four swappable parts and 24 clips per model; 34.92 MiB total).
- Current batch adds a pinned asset catalog, lazy-download cache with exact size/Git blob SHA-1 verification, catalog/model API endpoints, and Godot import acceptance for three representative models sharing the 62-bone rig.
- The browser builder and native four-part assembly/export are not yet complete. Next batch: Godot assembly/export; then browser controls and versioned creation-recipe persistence.


## 2026-11-25 — Body-edit browser acceptance and UI fixes

- Current local clone: `C:\Users\Hadi\Downloads\Cartoon-Studio-main-current`, branch `work/p2-2-body-shape-acceptance`, based on main `f9a03b9613d22c8bf99e96c5cf3d5de9997e0fd2`. Changes are uncommitted; the original downloaded folder remains untouched.
- Integrated-browser acceptance imported the pinned CC0 Male Adventurer, rendered its 24 animation clips, applied `torso_length=1.1`, saved the new asset/profile and reopened the profile after a page reload. The worker reported two changed bones and preserved animation and skin binding. The source copy SHA-256 matched the pinned catalog asset (`2caf3ea58a06744c44a360c941c3355b499ba5adf8edf549b98fc347c45faa28`); the edited GLB had a different hash (`a14529497467da31f4c8af3bd62d80cf141b131aa4352913cc4f55cc711116fa`).
- The Adventurer inspection reports 13/15 humanoid-name coverage and hierarchy warnings. The edit succeeded, but this asset does not establish broad retarget compatibility; keep Phase 2/P2.2 PARTIAL.
- Fixed the hidden preview placeholder CSS override and the saved-character `document` variable shadowing bug. Browser verification confirmed the placeholder hides while a GLB is loaded, saved character cards render, and profile edit/reopen restores the body value and animation list.
- A separate synthetic-fixture browser edit/save/reopen passed; do not use it as visual-quality evidence.
- Local targeted suite with pinned Godot 4.7.2: 44 passed in 39.72 seconds across `tests/test_app.py`, `tests/test_characters.py` and `tests/test_engine.py`. The pinned RobotExpressive fixture was fetched with the repository script and SHA-256 verified. Node CLI is unavailable locally; the changed module was loaded and exercised in the integrated browser.
- No commit or push was made. Remaining work: morph-capable browser acceptance, full modular assembly/download and recipe-reopen acceptance, compatibility review on hierarchy-valid rigs, retarget-preview comparison, and original face/hair geometry authoring.

## 2026-11-25 — Main feature reconciliation and verification

- Integrated upstream main `6a3406efb320a0895d4b2a7253395a107d6a394d`, including generated hairstyles (#17) and transparent PNG portraits (#19), into `work/p2-2-body-shape-acceptance`. The local saved-profile fixes are committed as `f51c7e5`; merge commit `caf2dc8` preserves the current-main integration. This branch has not yet been pushed.
- Upstream PR #20 adds a four-view turnaround sheet; its latest CI #425 passed, but the PR remains open and its changes are not in this branch.
- Full local test suite: 96 passed, 28 skipped. The skips cover unavailable pinned Godot and Node.js runtimes plus symlink support. Ruff, Python compilation and `git diff --check` passed.
- P2.2 remains PARTIAL. The new hair and portrait features have CI coverage but have not received local interactive visual acceptance; original face geometry and broader rig/visual acceptance remain open.

## 2026-11-25 — Character preview polish

- Continued on `work/character-preview-polish`, based on main `4d2a7848b7c123358b868f56eac0704a80f6c58d`; the earlier WIP stash remains preserved.
- Commit `4945beb7555c55fed2477de405e4e1a1b5b0f9a9` adds Idle-first animation selection, Idle-variant fallback, first-playable fallback and safe handling for RESET-only assets. PR #21 is open, separate from PR #20.
- Local targeted Python tests passed: 16 tests. Windows CI #429 passed Node-backed animation helper tests, JavaScript syntax checks, lint, Python compilation and the full pytest suite.
- The fresh visual browser check could not be completed in this batch. Character Studio remains PARTIAL; continue with browser acceptance and original face geometry rather than claiming completion.

## 2026-11-25 — Safe branch integration checkpoint

- Built the integration in a separate worktree based on `origin/main`, keeping the original checkout and `stash@{0}: On work/pr-20-turnaround-fix: WIP character preview polish` untouched.
- Locally merged the approved proportion-preview/composable-edit work, PR #20 turnaround export, PR #21 Idle-preview behavior and commit `1c41a8d` hairstyle-fit fix. The profile-workflow branch was inspected; its older source changes are superseded by the integrated implementations, and its stale documentation was not imported.
- The integrated-worktree run passed **122 tests with 4 environment-related skips**; the pinned Godot engine suite passed **14 tests**. Ruff and Python compilation passed locally. Three Node-backed cases and one symlink case are unavailable in this environment.
- PRs #20 and #21 were merged by the fast-forward push, and CI #432 passed. Push the final documentation sync and verify its CI, then delete only retired branches and leave the original checkout on `main`; the WIP stash remains preserved. Keep Phase 2 active and P2.2 partial; browser visual acceptance and original face geometry remain open.
