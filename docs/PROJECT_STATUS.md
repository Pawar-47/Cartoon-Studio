# Project Status — 2026-11-27

## Live checkpoint — 2026-11-27 (main CI repair: generated face surface marker)

- `main` CI run [#591](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/46043255274) failed in `Test` with `EngineExecutionError: Generated face surface was not found on the head mesh after export and re-import.` in `tests/test_engine.py::test_godot_worker_bakes_cartoon_face_geometry_and_preserves_animation` and `tests/test_engine_adapter.py::test_pinned_godot_worker_builds_episode_scenes_with_world_and_character_glb`.
- **Cause:** glTF has no per-primitive name, and Godot's importer never calls `surface_set_name` (`GLTFDocument::_parse_meshes` in the pinned 4.7.2 source). Every surface of a re-imported GLB therefore has an empty name, so verification by surface name could never pass. glTF does store material names, and the importer restores them into the material `resource_name`.
- **Fix:** the generated face surface now carries the marker on its own duplicated material named `CartoonStudio_GeneratedFace`; `_replace_skin_surface_with_generated_face` also keeps the head mesh resource name, fails fast when Godot rejects the generated surface arrays, and clears the stale surface override at the new index. Verification and the face test accept the marker surface name *or* the marker material name.
- **Verified:** static review only in this batch. The next GitHub Actions run on `main` is the proof; nothing is claimed as passing before it completes.

## Live checkpoint — 2026-11-27 (P2.2 original face geometry)

- Repository: Pawar-47/Cartoon-Studio. Source of truth: `main` at `1fdae47`.
- **P2.2 original face geometry implemented.** The Godot worker now replaces the separable Skin surface on the head mesh with procedurally generated face geometry skinned to the Head bone (vertex/normal/tangent/UV/bone-weight arrays), instead of only hiding the surface with a transparent material. New `_replace_skin_surface_with_generated_face` function in `engine/godot_worker/worker.gd`; verification confirms the generated face surface survived GLB export/re-import by its marker material name (glTF stores no surface names); saved hair style/color restoration assertions added to `tests/test_characters.py`.
- **Local proof with pinned Godot 4.7.2 runtime:** **122 passed, 34 skipped, 0 failed** (`python -m pytest -q -rs`). Skips: three Node.js helper tests and one symlink-capability test. Ruff all checks passed.
- Phase 2 remains ACTIVE. P2.2 code-testable work is complete (assembly, morphs, retarget, appearance bake, saved-profile restoration, original face geometry all have test coverage). Remaining P2.2 items require manual/visual acceptance and additional rig models, not code changes alone.
- The 171-row `REQUIREMENTS_REGISTRY.md` and `REQUIREMENT_TRACEABILITY.md` were reconciled in two batches; CHAR-R003 and CHAR-R005 now document generated-face geometry replacing the Skin surface.
- Chat-independent continuation record: `docs/SESSION_CHECKPOINT.md`.

## Historical checkpoint — 2026-11-26

- Repository: Pawar-47/Cartoon-Studio
- Source-of-truth branch: `main`, at `062400e58cbbf491ec92869dc140b60a9b354d7f`. The active follow-up branch is `work/mainline-followup`, based on that commit.
- Latest main CI run [#471](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45791209337) failed because `engine/godot_worker/worker.gd` declared `"action_cue_count"` twice in the episode result dictionary; the parse error prevented the worker from loading.
- Commit `be169c4` on the pushed `work/mainline-followup` branch removes the duplicate key and tests action/camera timeline cues using pinned Godot 4.7.2. Local validation: full pytest **136 passed, 4 skipped**; targeted episode-scene integration **1 passed**. No post-fix GitHub Actions run has completed.
- Phase 0: COMPLETE.
- Phase 1: COMPLETE.
- Phase 2 — Character Studio: ACTIVE; import, preview, profiles, appearance recipes, rig-based body-proportion export, procedural Head-attached hairstyles, transparent PNG portrait export, rig diagnostics and retargeting are implemented. Preview defaults now prefer an Idle clip and safely handle RESET-only assets. CI validates this behavior; P2.2 remains PARTIAL, with broader visual acceptance and original face geometry still open.
- Out-of-order partial work is present on `main`: persistent/editable worlds, Godot world-scene export and browser previews; world-linked story plans and cast GLB binding; generated editable episode scenes and GLB previews with procedural action-anchor and camera keyframes. This does not close the Phase 2 gate or constitute phase acceptance.
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
- Original face geometry: generated face geometry replaces the separable Skin surface on the head mesh; new geometry is skinned to the Head bone with vertex/normal/tangent/UV/bone-weight arrays; replaces and survives GLB export/re-import. Previously the Skin surface was only hidden with a transparent material while overlay meshes were attached via BoneAttachment3D.
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
| Phase 2 — Character Studio | ACTIVE | Import, preview, profiles, appearance, body-proportion export, geometry-aware hairstyles, PNG portrait and four-view turnaround export are implemented; generated-face geometry now replaces the separable Skin surface on the head mesh; saved-profile hair style/color restoration verified by test; interactive visual acceptance and broad rig acceptance remain |
| Phase 3 — World Builder | ACTIVE | P3.1 complete: versioned world model with save/reopen, stable IDs, migrations; civic/commercial (school, hospital, office, police_station) and indoor/outdoor (garage, indoor_room, playground) kinds added. P3.2 complete: environmental props (furniture, water_body, streetlight) added; world template/reuse system (template_id) enables multi-location layout reuse. P3.3 complete: vehicle rig contract (VehicleRigInput), movement state (VehicleMovementInput), and interaction events (VehicleInteractionInput) endpoints added; API tests cover movement, door/enter/exit interactions, and rig registration. Multi-location reuse and phase acceptance remain open; per user direction, Phase 3 activated before P2.2 visual acceptance closure |
| Phase 4 — Story and Scene Engine | PARTIAL / FROZEN, OUT-OF-ORDER WORK PRESENT | World-linked plans and cast binding exist; the canonical schema, integrated generation, approval and complete production mapping remain incomplete |
| Phase 5 — Animation Engine | PARTIAL / OUT-OF-ORDER | Generated scenes contain procedural action-anchor and camera keyframes; no reusable clip library, animation editor, blending or visual acceptance |
| Phase 6 — Urdu Voice and Lip-Sync | PARTIAL / OUT-OF-ORDER | `app/audio.py` implements pinned Pakistani Urdu Piper voices, a mono WAV mix, SRT subtitles and RMS mouth envelopes; the envelope is heuristic, not phoneme/viseme alignment. Acceptance and visual/audio quality review remain open |
| Phase 7 — Episode Generator | PARTIAL / OUT-OF-ORDER | Editable Godot scene files, dialogue audio, subtitles, mouth envelopes and a Godot-AVI + FFmpeg MP4 path exist (`app/render.py`); there is no durable render queue, and full 5–7 minute acceptance has not been performed |
| Phase 8 — Optimization and Reliability | DEFERRED | Physical-PC benchmarks remain late-stage work; user visual acceptance for Phases 2–7 shall be performed in Phase 8 per project owner direction |

## Next implementation batch — Phase 3 World Builder

Phase 3 is now active per user direction. Work continues on:
1. Multi-location world/location reuse and canonical world schema migration
2. World-scene export quality and browser preview visual review
3. World-linked story plan production mapping (ties to Phase 4)
4. P2.2 remaining visual acceptance items proceed in parallel: interactive browser acceptance of hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on representative models

User visual acceptance for Phases 2–7 is scheduled for Phase 8 per project owner direction.

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
