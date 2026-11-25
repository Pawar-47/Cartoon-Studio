# Next Steps — 2026-11-25

## Current checkpoint

Main is `d42a6e766fdae22e9a742435228cfdb4431c656b`. PR #10 (verified baked appearance GLB export) and PR #11 (modular recipe save/reopen/reassembly regression coverage) are merged. Main quick CI run [45663866235 PASSED](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45663866235). Phase 2 Character Studio remains active; no interactive browser acceptance or geometric customization is being claimed from these API/worker tests.

## Active batch — Phase 2 Character Studio

The first user-facing non-destructive imported-GLB retarget workflow and saved browser preview are implemented. Facial morph-target metadata is now reported by the Godot worker; named and unnamed morph fixtures are covered, and the appearance API has save/reopen/range-validation regression tests. The appearance editor now pauses embedded animation playback to prevent morph animation tracks from fighting expression sliders; ordinary previews still auto-play. Windows CI #326 passed the complete full-build pipeline on `696929595b2d03e64e46a568ec9d163860ae3239`. Windows CI #334 passed the quick validation pipeline, including the pinned third-party RobotExpressive download and Godot facial morph/animation inspection. Windows CI #299 passed the complete pipeline, including a real third-party Khronos Rigged Figure retargeted onto the canonical target after scene save/reopen. It includes source/target selectors, preflight validation, a saved Godot scene, a persistent project record, scene download, and a runtime check that the reopened source animation transfers its pose to the target skeleton.

Saved retarget records now also have a browser preview action. The preview endpoint resolves the project's original source/target GLBs and canonical humanoid mappings; the browser uses the locally vendored Three.js SkeletonUtils retarget pass to animate the target GLB. This is a visual aid, not the authoritative saved-scene renderer. The Godot scene remains the authoritative native artifact.

## Verification

- Windows CI #334 passed: fixture acquisition/checksum, Ruff, Python compilation and full pytest including Godot 4.7.2 facial morph import and multi-clip inspection. This quick CI intentionally did not build the complete Windows app or installer.
- Windows CI #340 passed: clip catalog, selected/default clip persistence, legacy metadata compatibility and unknown-clip rejection.
- Windows CI #341 and native-worker proof #22 passed: synthetic bone-roll/non-uniform-scale target compatibility. Native-worker proof #346 passed RobotExpressive Walking retarget; CI #349 passed source-only IK-foot hierarchy API/UI support.
- Windows CI #351–#352 passed RobotExpressive Walking, Running and Dance retargets. CI #354 passed facial morph UI/default-reset checks. CI #356 passed deterministic clip sampling and strict browser animation-name resolution with Node unit tests.
- The full packaging/installer workflow is now isolated in `.github/workflows/release-windows.yml` and is manually dispatched at phase/release milestones.
- Windows CI #326 passed the complete Windows build and installer lifecycle after the appearance-editor playback isolation change.
- Windows CI #303 passed on commit `0bfce71625d6e3084b4ceda9b64a9825cca95101`: Ruff lint, Python compilation, full pytest including pinned Godot 4.7.2 tests, third-party GLB inspection/retarget, morph-target inspection, bootstrap smoke, both self-contained builds, NSIS installer and full install/upgrade/uninstall/reinstall lifecycle.
- Windows CI #293 passed the complete pipeline for Godot facial blend-shape inspection, imported default values, signed morph weights and Character Studio reporting.
- Windows CI #285 passed four DCC naming families and malformed hierarchy rejection.
- Earlier Windows CI #279 passed on commit 56c61487089097108b6baa862f9ac9125568b9a5: lint, Python compilation, full pytest suite including the pinned Godot 4.7.2 worker scenario, Windows bootstrap packaging/smoke test, both self-contained application builds, NSIS installer compilation, clean install, upgrade, uninstall, reinstall and artifact uploads.
- CI #279 artifacts: Windows installer (103,861,406 bytes), bootstrap (819,154 bytes), dependency SBOM (32,632 bytes).
- The worker test covers a Mixamo-named animated source and a distinct differently proportioned target; it checks source animation playback, pose transfer after scene save/reopen and byte-identical source asset preservation.
- Browser retarget preview now resolves saved clip names exactly or by a unique Godot library suffix; unknown/ambiguous names fail rather than silently previewing a different animation. Node tests cover this contract. Browser visual fidelity still requires interactive acceptance.

## Next substantial batch

The browser retarget path now samples source animation from the full GLTF scene root and plays generated tracks through the target SkinnedMesh skeleton. This handles common GLTF layouts where the mesh and its joint hierarchy are siblings rather than parent/child nodes. The new Node suite exercises the vendored Three.js retarget implementation against a 15-bone pair with different bone names and a rolled target arm, including hip translation and mapping rejection. This batch still needs quick CI and interactive browser acceptance.

1. Compare browser retarget preview motion against the authoritative Godot scene across the accepted humanoid, bone-roll and RobotExpressive fixtures.
2. Add more third-party humanoid rig families with varied rest axes and hierarchy layouts.
3. Perform interactive browser acceptance of RobotExpressive facial sliders, reset-to-imported-defaults and save/reopen.
4. Continue deterministic export and animation round-trip after broader compatibility acceptance.

## Deferred to their specified phases

- World Builder: Phase 3.
- Full Story/Scene Engine: Phase 4; preserve the existing partial Story Generator and keep its expansion frozen until then.
- Production animation library and timeline: Phase 5.
- Pakistani Urdu voice/TTS/lip-sync: Phase 6.
- Full episode rendering, audio mix and MP4: Phase 7.
- Target-PC benchmarks and optimization: Phase 8.

## CI policy

- Normal pushes and pull requests run lint, Python compilation and the full automated test suite with the pinned Godot worker. They do not build PyInstaller application bundles or NSIS installers.
- `.github/workflows/release-windows.yml` is manually dispatched at phase/release milestones and runs the complete Windows packaging, SBOM, installer and install/upgrade/uninstall lifecycle.
- `.github/workflows/godot-engine-proof.yml` is manual-only and reserved for phase-level native proof runs; normal pushes should trigger only quick CI.
- CI concurrency groups prevent overlapping runs within each workflow; do not launch duplicate runs for individual edits.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 2–7 remain open.

## Next P2.2 batch — interactive acceptance and original geometry

The pinned CC0 library, four-slot Godot assembly/export, browser selectors and versioned recipe manifest are implemented. PR #11 now verifies API-level save/reopen/reassemble using recovered source manifests and a bone-attached accessory. PR #10 adds a separate verified appearance-bake/export path. These automated contracts do not establish browser-level visual quality.

1. Exercise the browser creator end-to-end: library preview/import, choose head/body/legs/feet, shuffle, add/remove accessories, assemble, download, preview expressions, save the profile, reload the project and restore the recipe.
2. Inspect baked appearance export with a real morph-capable character. Compare material and morph values before/after export, verify animation clips remain usable and confirm the original source GLB is byte-identical.
3. Add browser-facing playback acceptance for assembled GLBs and compare browser retarget preview with the authoritative saved Godot scene.
4. Implement real geometric customization for proportions, face and hair using compatible mesh, morph-target or rig operations. Keep metadata-only fields clearly distinguished from geometry changes.
5. Expand rig families only where compatibility tests and visual acceptance justify it.

Phase 2 remains ACTIVE. Do not start Phase 3 until P2.2 exit criteria are met. Physical-PC performance testing and full Windows packaging remain later-stage work, not blockers.


## 2026-11-25 — Modular recipe persistence regression coverage (completed)

PR #11 merged the deterministic API-level round-trip test for modular character recipes. It exercises assembly with four parts plus a bone-attached accessory, persists the resulting asset manifest, verifies every source manifest can be reopened, saves and reopens a character profile referencing the assembled asset, and submits a second assembly using only the recovered recipe. The fake engine isolates persistence/replay contracts; the separate pinned-Godot integration test remains responsible for real skeleton compatibility and animation playback.

This closes the API-level persistence regression item only. Interactive browser acceptance and geometric customization remain open.
