# Session-independent development checkpoint

Updated: 2026-11-25
Repository: https://github.com/Pawar-47/Cartoon-Studio
Branch: main
Latest implementation checkpoint: `8b1771790e6fad373b732472cbc3814dc4e0e838` (CI #349 passed).

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

## Implemented Character Studio capabilities

- Project-contained GLB 2.0 import, validation, SHA-256 provenance and Godot inspection.
- Browser GLB preview, imported animation selection and camera controls.
- Persistent editable character profiles.
- Non-destructive PBR material recipes and facial morph-target controls. Godot reports imported blend-shape names/defaults; signed weights from -1 to 1 persist; reset restores each model's imported defaults. A pinned CC0 RobotExpressive fixture is fetched and SHA-256 verified; CI #334 passed Godot import, morph-target and multi-clip inspection. The imported clip catalog/source selector passed CI #340. CI #341 and native-worker proof #22 passed bone-roll/non-uniform-scale retarget acceptance. Godot native-worker proof #346 passed RobotExpressive Walking-clip retarget, scene save/reopen and pose-transfer verification; CI #349 passed the source-only IK-foot hierarchy API/UI checks.
- Conservative indexed 15-bone humanoid mapping, parent-chain validation and imported rest-transform diagnostics.
- Common 3ds Max Biped, Character Creator, Unreal-style, Blender Rigify and Cesium Rigged Figure bone naming conventions are recognized. Duplicate and negative bone indices are rejected.
- Character-to-character retarget UI with source/target selectors, imported animation dropdown, strict clip-name preflight, saved Godot scene, persistent JSON record and scene download.
- Worker reopens the saved scene, verifies source animation playback and source-pose change, then compares the target pose against Godot's model-space rest-corrected retarget transform. This supports different rest-axis/bone-roll conventions; raw local source/target angles are diagnostics, not an equality requirement.
- Saved retarget records expose a separate Three.js browser preview using persisted canonical mappings. The saved Godot scene remains authoritative.
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

Two real third-party assets have passed native Godot acceptance for tested scenarios: Khronos Rigged Figure retargeting and RobotExpressive Walking-clip retargeting with its bilateral IK-foot hierarchy. This is not blanket support for arbitrary GLBs. More rigs, humanoid multi-clip retargeting and interactive browser facial-expression acceptance remain. Phase 2 remains ACTIVE and incomplete.

## CI execution policy

- Push/PR CI runs lint, Python compilation and the full automated test suite only; no PyInstaller or NSIS builds. Windows CI #334 passed the pinned RobotExpressive fixture acquisition and Godot facial-morph inspection.
- Full Windows application and installer validation lives in `.github/workflows/release-windows.yml` and is manually dispatched after a phase/release milestone.
- The dedicated Godot native-worker proof is now manual-only and reserved for phase milestones; routine pushes run one quick CI workflow. Full Windows application and installer validation remains manual in `.github/workflows/release-windows.yml`.
- Workflow concurrency groups prevent overlapping runs. Avoid duplicate CI runs for minor edits.

## Current retarget acceptance expansion — 2026-11-25

- The target fixture generator now supports explicit local bone-roll quaternions and non-uniform per-bone scales, and recalculates inverse-bind matrices from full TRS transforms.
- A new Godot integration test builds a rolled/scaled target at test time, verifies its imported rest rotations/scales differ from the source, then checks animation transfer after scene save/reopen.
- Windows CI #341 PASSED on `57e252c922acae58831da5b966cab8edcd9b4408`; generated bone-roll/non-uniform-scale target transferred pose after native scene save/reopen.
- RobotExpressive native retarget proof #346 PASSED on `9b1f9f3d8815ebc7f45c8b1aa90673c9a0827f85`; CI #349 validated the source-only IK-foot hierarchy variant through API/UI.

## Next substantial implementation batch

1. Expose imported Godot animation names in inspection metadata and provide a source-clip dropdown in the retarget UI; validate against RobotExpressive.
2. Test browser facial sliders, reset and saved-recipe behavior against the real morph asset.
3. Retarget RobotExpressive across its named clips and add humanoid fixtures with unusual rest axes, bone roll and scale variation.
4. Compare browser retarget preview with the authoritative Godot scene across rig families.
5. Continue deterministic export and animation round-trip after broader acceptance.

## Later phases

- Phase 3 — World Builder: NOT STARTED.
- Phase 4 — Story and Scene Engine: PARTIAL / FROZEN; preserve existing Story Generator work.
- Phase 5 — Animation Engine: NOT STARTED.
- Phase 6 — Urdu Voice and Lip-Sync: research complete; implementation not started.
- Phase 7 — Episode Generator: NOT STARTED.
- Phase 8 — Optimization and Reliability: deferred, including physical-PC performance testing.

Never claim the complete application is finished while Phases 2–7 remain incomplete.
