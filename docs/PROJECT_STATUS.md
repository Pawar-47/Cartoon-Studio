# Project Status — 2026-11-25

## Live checkpoint

- Repository: Pawar-47/Cartoon-Studio
- Source-of-truth branch: `main`; integrated code commit: `7d396e5b9e3b07033240b9f02fb1020003a58a36`. PRs #20 and #21 are merged.
- The integration was built in an isolated worktree and pushed via fast-forward. Local validation in that worktree: full pytest **122 passed, 4 skipped**; pinned Godot engine suite **14 passed**; Ruff and Python compilation passed.
- GitHub Actions run [#432](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45703715915) passed. Initial run #431 exposed import ordering in `tests/test_characters.py`; the issue was corrected in the pushed follow-up commit.
- Phase 0: COMPLETE.
- Phase 1: COMPLETE.
- Phase 2 — Character Studio: ACTIVE; import, preview, profiles, appearance recipes, rig-based body-proportion export, procedural Head-attached hairstyles, transparent PNG portrait export, rig diagnostics and retargeting are implemented. Preview defaults now prefer an Idle clip and safely handle RESET-only assets. CI validates this behavior; P2.2 remains PARTIAL, with broader visual acceptance and original face geometry still open.
- Windows CI #326: full pipeline PASSED on `696929595b2d03e64e46a568ec9d163860ae3239`, including lint, Python compilation, full pytest, pinned Godot 4.7.2 worker, Windows bootstrap, both self-contained application builds, NSIS installers and clean install/upgrade/uninstall/reinstall lifecycle.
- Windows CI #334: quick CI PASSED on `00b4ed9f97360cba1a304054a8285fd4df1cc827`; pinned RobotExpressive download/checksum, Ruff, Python compilation and full pytest passed. The complete application and installer were intentionally not rebuilt.
- Windows CI #340: quick CI PASSED on `fba0ad5cec13a5738a2807a2af7bebf0317451cd`; animation-name catalog, explicit/default clip selection, legacy compatibility and unknown-clip rejection passed.
- Windows CI #341 and native-worker proof #22: PASSED on `57e252c922acae58831da5b966cab8edcd9b4408`; rolled-bone and non-uniform target-scale fixture coverage passed.
- Godot native-worker proof #346: PASSED on `9b1f9f3d8815ebc7f45c8b1aa90673c9a0827f85`; RobotExpressive Walking clip retargeted, scene saved/reopened, source playback and target pose transfer verified.
- Windows CI #349: PASSED on `8b1771790e6fad373b732472cbc3814dc4e0e838`; verified source-only IK-foot hierarchy handling, API preflight and UI labeling.
- Windows CI #351–#352: PASSED; RobotExpressive Walking, Running and Dance clips each retargeted through the native worker.
- Windows CI #354: PASSED; facial morph controls identify mesh and target, preserve imported defaults and reset correctly.
- Windows CI #356: PASSED on `81972eae6e5cafb4756695d385425d1d1f1a63a8`; deterministic clip-time sampling and strict browser clip-name resolution passed with Node resolver tests.
- Dedicated Godot native-worker proof #18 PASSED.
- Chat-independent continuation record: `docs/SESSION_CHECKPOINT.md`.

## Current Character Studio capabilities

- Local project-contained GLB 2.0 import, validation, provenance and Godot inspection.
- Browser GLB preview and imported animation selection.
- Persistent versioned character profiles.
- Rig-based proportion controls for compatible imported humanoids. Godot exports a new GLB, re-imports it to verify changed bone transforms and retained animation clips, and leaves the source GLB unchanged. This edits an existing rig; it does not create new mesh topology or author face/hair geometry.
- Seven procedural hairstyle choices generate geometry attached to the imported Head bone. The worker fits hair from skinned head bounds, uses face-feature geometry to infer front orientation, verifies style placement and retained animation clips, and leaves the source GLB unchanged. The user can export a transparent PNG portrait and a four-view turnaround sheet from the browser preview.
- Character preview defaults prefer an Idle clip, fall back to another playable clip, and safely handle RESET-only assets.
- Imported morph targets are grouped into face, body and other controls; sliders affect only blend shapes already present in the source GLB.
- Non-destructive material appearance recipes and facial morph-target sliders; Godot inspection reports imported blend-shape names/defaults, controls accept signed weights from -1 to 1, and reset restores each imported default. Appearance editing pauses embedded animation playback so an animation track cannot overwrite live expression-slider changes; ordinary character previews continue to play imported animations. The pinned CC0 RobotExpressive asset was successfully imported by Godot in CI with at least three facial morph targets, numeric defaults and ten or more named animation clips. A pinned CC0 third-party RobotExpressive GLB adds a real animated character with three facial-expression morph targets on its Head_4 mesh; CI fetches the upstream binary by immutable commit and verifies its SHA-256 before Godot import. A named Smile/Blink fixture continues to exercise deterministic node/mesh default precedence; persistence and range validation are covered by API tests. RobotExpressive import passed CI #334, and its Walking clip passed native retarget/save/reopen/pose-transfer proof #346. Its bilateral Blender IK-foot hierarchy is represented as a verified source-only variant; target rigs still require a standard valid hierarchy.
- Indexed 15-bone humanoid mapping, parent-chain diagnostics and per-bone rest-transform measurements; common 3ds Max Biped, Character Creator, Unreal-style, Blender Rigify and Cesium Rigged Figure bone names are recognized. Duplicate/negative hierarchy indices are rejected.
- Imported-GLB retarget workflow with source/target selection, strict preflight, source-specific clip selection, Godot scene creation, persistent history and scene download. A generated target with altered bone-roll rotations and non-uniform per-bone scale passed native Godot retarget acceptance in CI #341; inverse-bind matrices are recalculated from full TRS transforms.
- Worker verifies that the reopened source AnimationPlayer starts, seeks to a deterministic 37% point in the selected clip, advances three frames, and checks that the source pose changes and the target upper-arm pose matches Godot's model-space rest-corrected retarget transform. This avoids sampling a looped clip at its rest pose and supports different rest axes without requiring raw local rotation angles to match. Failed pose verification removes the generated scene.
- Retarget history displays source/target local pose angles as rest-axis-dependent diagnostics plus the transfer verification state.
- Saved retargets expose an in-app browser preview: Three.js retargets the selected source clip onto the saved target GLB using persisted canonical humanoid mappings. Browser retarget sampling is performed from the full GLTF scene roots (so animation tracks can reach skeleton bones that are siblings of the skinned mesh); the generated clip is played against the target SkinnedMesh skeleton. A Node-based regression suite exercises scene-root source tracks, sibling target skeletons, rest-axis roll, hip translation and invalid mappings. Clip names resolve exactly or by a unique Godot animation-library suffix; unknown or ambiguous saved names now produce an explicit error instead of silently previewing a different clip. The saved Godot scene remains authoritative; browser preview is a separate visual aid, not proof of native-scene rendering.
- Original source and target GLBs remain byte-identical.
- PR #10 adds non-destructive baked appearance export: Godot writes BaseMaterial3D color/roughness/metallic values and bound morph weights into a new GLB, re-imports it and verifies baked values while preserving animation clips and the original source asset.
- PR #11 adds API-level modular recipe round-trip coverage: restore all source asset manifests, reopen the assembled character profile and reassemble from the recovered four-part/accessory recipe. This proves persistence/replay contracts, not interactive browser acceptance.

## Distinct imported fixture coverage

The synthetic source/target fixture pair still verifies Mixamo-style animation track remapping, different limb proportions, reordered raw skin joints, scene save/reopen and byte-identical source preservation. In addition, `tests/fixtures/third_party/rigged_figure_ccby.glb` is an unchanged Khronos Cesium Rigged Figure asset (CC-BY-4.0) with a different 19-joint hierarchy and naming convention. The worker maps its 15 core humanoid bones and successfully retargets its real animation to the canonical target in Godot after scene save/reopen. Attribution and the upstream license are retained beside the fixture.

Godot may normalize raw skin-joint ordering during import. The application uses the actual bone names and indices returned by the Godot inspection worker, not raw GLB array positions. Windows CI #299 passed the full real third-party Rigged Figure inspection and retarget test. This is not blanket compatibility. RobotExpressive also passes native retarget/save/reopen/pose-transfer for Walking, Running and Dance, including its verified bilateral IK-foot source hierarchy. More rig families and browser/native visual equivalence still require acceptance. Interactive browser expression-slider/reset/save review remains outstanding.

## Phase status

| Phase | Status | Evidence / limitation |
|---|---|---|
| Phase 0 — Specification/research/architecture | COMPLETE | Baseline, requirements, research and architecture documented |
| Phase 1 — GitHub and CI/CD foundation | COMPLETE | Windows bootstrap and installer lifecycle verified |
| Phase 2 — Character Studio | ACTIVE | Import, preview, profiles, appearance, body-proportion export, geometry-aware hairstyles, PNG portrait and four-view turnaround export are implemented; visual acceptance and original face geometry remain |
| Phase 3 — World Builder | NOT STARTED | No persistent production world/location builder |
| Phase 4 — Story and Scene Engine | PARTIAL / FROZEN | Preserve existing Story Generator and saved story plan |
| Phase 5 — Animation Engine | NOT STARTED | No production timeline/action library |
| Phase 6 — Urdu Voice and Lip-Sync | RESEARCH COMPLETE; IMPLEMENTATION NOT STARTED | No production TTS/lip-sync |
| Phase 7 — Episode Generator | NOT STARTED | No complete 5–7 minute production pipeline |
| Phase 8 — Optimization and Reliability | DEFERRED | Physical-PC benchmarks remain late-stage work |

## Next implementation batch

1. Complete browser acceptance for procedural hairstyles and transparent PNG exports; verify saved-profile hair selection and output appearance.
2. Extend acceptance to modular assembly, imported morph controls and baked appearance on representative, hierarchy-validated rigs.
3. Resolve and document the body-edit compatibility boundary: the pinned Adventurer edit succeeded, but its import report still flags 13/15 humanoid names and a hierarchy needing review.
4. Compare browser retarget preview against the authoritative saved Godot scene across accepted humanoid, bone-roll and RobotExpressive fixtures.
5. Continue original face geometry authoring; generated hairstyles do not establish original face authoring or broad visual signoff.
6. Broaden third-party rig families only where direct compatibility tests and visual acceptance justify support.

## Frozen architecture and constraints

- Python 3.11+ / FastAPI / Uvicorn / Pydantic / SQLite; browser UI remains the control plane.
- Godot 4.7.2-stable Compatibility runtime behind the supervised worker.
- Engine-neutral project/character data contracts and stable Cartoon Studio IDs.
- Local-first; no mandatory paid APIs, cloud rendering or online activation.
- Physical-PC testing is deferred to Phase 8 and is not a development gate.
- GitHub main remains the sole project source of truth.

## Active P2.2 direction — modular character creator (2026-11-25)

- Published main at `7d396e5` includes the live proportion-preview/composable-edit feature, PR #20 turnaround export, PR #21 Idle-preview behavior and geometry-aware hairstyle fitting. Combined GitHub Actions run #432 passed; P2.2 remains PARTIAL.
- The pinned Quaternius Ultimate Modular Men/Women CC0 library contains 21 outfit GLBs (34.92 MiB) with four candidate slots and 24 animation clips per model. Downloads are lazy, cached and verified against the pinned source commit, byte size and Git blob SHA-1.
- Character Studio now offers head/body/legs/feet selectors, filtered by skinned mesh slot candidates. Godot performs exact shared-skeleton, hierarchy, rest-pose, rig-transform and skin-bind checks; it removes base skinned outfit meshes, attaches the selected meshes to the base skeleton, exports and re-imports the GLB, then verifies the four selected meshes and base animation names.
- A real CI integration test combines Beach head, Casual_2 body, Farmer legs and King feet on the Male Adventurer base and verifies all 24 base animation clips survive. Assembly manifests persist the base/part recipe and allow source restoration.
- PR #4 adds optional skinned or BoneAttachment3D accessories, including the Adventurer Backpack integration test. Assembly recipes persist accessory paths and bone references and restore the selected accessory list when reopening an assembled character.
- PR #6 adds one-click outfit shuffling with unique source meshes and direct GLB downloads for saved and newly assembled characters.
- PR #7 adds a Godot playback probe: after GLB export/re-import it plays the Walk clip, compares bone poses, counts skinned meshes bound to the rig and reports bone attachments. The mixed-outfit-plus-Backpack test verifies pose changes and at least four skinned meshes.
- PR #9 adds Smile/Frown/Surprise/Angry presets for imported morph targets. Presets are name-matched, do not fabricate geometry and remain disabled when no morph targets are present. Node 22 syntax checking is now part of CI.
- Phase 2 remains ACTIVE; P2.2 remains PARTIAL. Rig-based proportion changes, existing imported morphs and procedural hairstyles are implemented, but interactive visual acceptance, original face geometry authoring and cross-scene visual consistency remain open. Strict shared-rig matching is supported; automatic conversion of arbitrary incompatible rigs is not claimed.
