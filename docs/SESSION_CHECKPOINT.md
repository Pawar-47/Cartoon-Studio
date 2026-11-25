# Session-independent development checkpoint

Updated: 2026-11-25
Repository: https://github.com/Pawar-47/Cartoon-Studio
Branch: main
Latest implementation checkpoint: `d42a6e766fdae22e9a742435228cfdb4431c656b` (PR #10 baked appearance export and PR #11 modular recipe round-trip coverage merged; main quick CI run 45663866235 passed).

## Mission and operating rules

Build the complete local-first Cartoon Studio desktop application defined by `MASTER_EXECUTION_PROMPT.md`, `MASTER_PLAN.md` and `PROJECT_SPECIFICATION.md`.

- GitHub `main` is the only source of truth.
- Preserve accepted work; do not restart completed phases or reset repositories.
- Work in substantial, coherent feature batches.
- Report implementation, automated tests, Godot execution and visual acceptance separately.
- Respond in English.
- Physical-PC testing and performance benchmarking remain Phase 8; they are not development gates.

## Current phase

Phase 2 — Character Studio is ACTIVE. Phase 0 and Phase 1 are complete. Do not skip ahead to World Builder or unfreeze the partial Story Generator.

## Latest merged work

- PR #10: appearance recipes can be baked into a new GLB by the Godot worker; baked material and morph values are re-imported and verified, animation clips are retained, and the source GLB remains unchanged.
- PR #11: modular assembly recipes now have API-level save/reopen/reassemble regression coverage, including all source asset manifests and a bone-attached accessory.
- Main CI run [45663866235](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45663866235) passed on `d42a6e766fdae22e9a742435228cfdb4431c656b`.

## Implemented Character Studio capabilities

- Project-contained GLB 2.0 import, validation, SHA-256 provenance and Godot inspection.
- Browser GLB preview, imported animation selection and camera controls.
- Persistent editable character profiles.
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
- Earlier synthetic Mixamo source/target retarget fixture remains green and preserves both source assets.
- Dedicated browser visual acceptance has not been performed. Browser preview is not claimed to be equivalent to native Godot rendering.

## Important acceptance boundary

Two real third-party assets have passed native Godot acceptance for tested scenarios: Khronos Rigged Figure retargeting and RobotExpressive Walking/Running/Dance retargeting with its bilateral IK-foot hierarchy. This is not blanket support for arbitrary GLBs. More rigs and interactive browser facial-expression acceptance remain. Phase 2 remains ACTIVE and incomplete.

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

1. Perform interactive browser acceptance of the complete modular creator, including outfit selection/shuffle, accessories, assembly, preview, GLB download, profile save/reopen and recipe restoration. PR #11 now covers the API-level recipe replay contract; it does not replace visual acceptance.
2. Visually accept PR #10's baked appearance export with a real morph-capable character, checking material values, facial weights, animation preservation and source-file immutability.
3. Compare browser retarget preview motion against the authoritative Godot scene across the accepted humanoid, bone-roll and RobotExpressive fixtures.
4. Implement genuine geometric customization for proportions, face and hair; do not count text-only profile metadata as geometry editing.

## Later phases

- Phase 3 — World Builder: NOT STARTED.
- Phase 4 — Story and Scene Engine: PARTIAL / FROZEN; preserve existing Story Generator work.
- Phase 5 — Animation Engine: NOT STARTED.
- Phase 6 — Urdu Voice and Lip-Sync: research complete; implementation not started.
- Phase 7 — Episode Generator: NOT STARTED.
- Phase 8 — Optimization and Reliability: deferred, including physical-PC performance testing.

Never claim the complete application is finished while Phases 2–7 remain incomplete.


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
