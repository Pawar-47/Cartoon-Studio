# P2.2 Character Studio — Import and Persistent Profile Report

**Date:** 2026-11-25  
**Status:** First vertical slice accepted by Windows CI #208; Character Studio phase remains active  
**Phase:** 2 — Character Studio  
**Scope:** First working vertical slice, not phase completion

## Implemented
- A dedicated browser route at `/characters`, linked from the dashboard.
- Project-scoped GLB 2.0 binary upload with a 512 MiB request limit and project-local generated storage paths.
- Container checks for GLB magic, version, declared byte length, JSON chunk and glTF asset version.
- SHA-256 provenance for every imported model.
- Actual Godot 4.7.2 worker import/inspection; records mesh, skeleton, animation-player, animation and node counts.
- Readiness flags are derived from the worker inspection. An unrigged model is not labelled rig-ready.
- Versioned character profile documents with stable IDs and create/list/get/update APIs.
- Persistent fields for name, description, face design, body proportions, height, hair, clothing, accessories, eye/mouth design, expression labels, personality, relationships, voice profile and dialogue style.
- Canonical references in project.json and portable-file recovery of character profiles after loss of the SQLite index.
- Focused tests for upload validation, import inspection contract, profile round-trip, updates, project references and recovery.

## Explicit limitations
- GLB 2.0 is the only integrated import format. VRM was researched but is not yet integrated.
- Geometry authoring is limited to generated hairstyle shapes and supported rig/morph edits; arbitrary face geometry, new rigs, texture painting and new facial blend-shape authoring are not implemented.
- Transparent PNG portrait export is available from the browser preview; user-facing visual acceptance of hairstyles and exported portraits remains outstanding.
- Voice and relationships remain profile metadata without corresponding audio/story runtime integration.
- P2.2 is not complete until the remaining character-authoring requirements and representative visual acceptance are delivered and verified.

## Verification
- New test module: `tests/test_characters.py`.
- The tests use a deterministic fake Godot adapter for API-level contract tests.
- The existing Windows CI job also runs the real pinned Godot 4.7.2 worker integration tests.
- Windows CI #208 passed on commit `41aabbb627e36f3f02f306e79e3cba33bd19dc84`: 45 tests passed; lint, compilation, runtime integrity, bootstrap smoke, both self-contained builds and the full installer lifecycle passed. The run uploaded the bootstrap, installer and SBOM artifacts.

## 2026-11-25 — Procedural hairstyles and portrait export integration

- Current main `6a3406efb320a0895d4b2a7253395a107d6a394d` includes seven procedural hairstyle choices. Godot attaches generated geometry to the imported Head bone, verifies the exported hair and retained animation clips, and leaves the source GLB unchanged.
- The browser can export the current character preview as a PNG portrait with optional transparency. Main CI #421 passed the Godot hairstyle coverage; CI #423 passed portrait-export checks. Open PR #20 adds a four-view turnaround sheet and its CI #425 check passed; the PR is not part of this main baseline.
- Local validation on the integrated branch: full pytest **96 passed, 28 skipped**; 24 skips require the pinned Godot runtime, three require Node.js and one requires symlink support. Ruff and Python compilation passed. Godot/Node-backed cases were not run locally; CI provides the runtime coverage.
- Visual acceptance of the new hairstyles and PNG output remains outstanding. The new procedural hair feature does not complete original face-geometry authoring, so P2.2 remains PARTIAL.


## Browser preview extension — 2026-11-25

- Added locally vendored three.js 0.187.0 (r187, MIT) and its GLTFLoader, OrbitControls, BufferGeometryUtils and SkeletonUtils modules.
- The browser can preview the original uploaded GLB and reopen a saved project's GLB using a project-scoped read endpoint.
- Preview controls include orbit, zoom, camera reset and embedded animation selection.
- The vendored library is pinned in `third_party/threejs-runtime.json`, its license is retained, and the CI SBOM script adds the npm component.
- This is visual presentation only. Godot remains authoritative for GLB import/inspection; no mesh editing, rig creation, material editing, facial controls or export is included.
- Browser preview requires WebGL 2. Draco/Meshopt decoders are not bundled; compressed files may be importable by Godot while unsupported by the browser viewer.
- Windows CI #212 passed on commit `843ef8d6250b1c442235119911215205fa1bfb6a`: 49 tests passed; lint, compilation, bootstrap smoke, both self-contained builds, installer compilation and the full install/upgrade/uninstall/reinstall lifecycle passed. Visual browser review remains pending.


## Material appearance editor — implementation batch (2026-11-25)

- Added a browser-side material catalogue using stable GLB scene-node paths and material-slot indices.
- Saved character cards can reopen their source GLB, inspect material slots, preview base-colour/roughness/metalness adjustments, and persist those adjustments to the character profile.
- The editor changes supported Three.js PBR material properties in the live preview. The source GLB remains unchanged.
- Added a project-scoped appearance API with validated hex colours and 0–1 roughness/metalness ranges. Saving increments the character revision and writes the recipe into the canonical character JSON document.
- Ordinary profile updates preserve the appearance recipe.
- API tests cover valid save/reopen, revision increments, preservation across profile updates, invalid values and missing character handling.
- This is non-destructive material customization, not mesh/material-slot reassignment, texture painting or GLB export. Facial blend-shape editing, rig editing and export remain future work.
- Browser preview still requires WebGL 2 and visual inspection with representative models. Windows CI acceptance is pending.


## Imported facial morph-target editor — implementation batch

- The browser viewer now discovers glTF morph targets on imported meshes and assigns stable scene-path/index/name keys.
- Saved character appearance recipes can store morph weights separately from material overrides.
- The Character Studio creates one slider per morph target found in the loaded GLB, previews weight changes immediately, and offers a reset-to-neutral action.
- The project API validates each morph weight in the 0–1 range, stores it in the versioned character JSON document and preserves it across ordinary profile updates.
- The editor reports clearly when a model contains no morph targets; it does not fabricate facial controls for models without blend shapes.
- This operates existing GLB morph targets only. It does not create new facial geometry, generate new blend shapes, provide VRM expression presets, or edit/export the source GLB.
- API tests cover persistence and range validation. Windows CI and visual review with a real blend-shape GLB are pending.


## CI-accepted appearance and facial-control batches — 2026-11-25

- Material appearance editor commit `843ef8d6250b1c442235119911215205fa1bfb6a` passed Windows CI #212 (49 tests plus lint, compilation, bootstrap, both application builds and installer lifecycle).
- Imported facial morph-target controls commit `533d59415df85be799fd4b28161aef860677a501`, followed by lint correction `e58b40d75ae10431051980246b468b736544f464`, passed Windows CI #214. All 49 tests, lint, compilation, both self-contained builds, installer compilation and clean install/upgrade/uninstall/reinstall passed.
- Remaining visual limitation: no real blend-shape cartoon GLB has yet been used for browser-level visual acceptance. API tests prove recipe persistence and range validation, not that a particular target deforms the intended face region.
- Next workflow improvement: allow saved profile metadata to be edited from the browser without reimporting or replacing the original GLB; appearance recipes must remain intact.


## Skeleton and humanoid-name inspection batch — implementation checkpoint

- The Godot worker now reports each imported Skeleton3D node and its indexed bone hierarchy (name, parent index and parent name).
- The application computes a conservative 15-bone humanoid-name coverage report, selecting the strongest individual skeleton rather than combining unrelated skeletons.
- The report explicitly never marks retargeting ready: rest pose, bone axes, scale, skin weights and real motion playback still require validation.
- This is rig inspection/preflight, not rig creation, skinning repair or retargeting. A real skinned cartoon GLB visual/animation acceptance test remains required.


## Native humanoid retargeting engine proof — 2026-11-25

- The Godot 4.7.2 proof project now constructs a canonical source/target humanoid skeleton pair with different limb proportions.
- A native `RetargetModifier3D` and `SkeletonProfileHumanoid` transfer a keyed source arm animation to the target skeleton.
- CI checks source animation playback, different rest lengths, target pose transfer and saved/reopened retarget hierarchy. This is a runtime capability proof, not yet retargeting of imported user models or a production animation library.


## Indexed humanoid profile mapping — implementation batch

- Maps the conservative core humanoid set to Godot SkeletonProfileHumanoid profile bone names.
- Each unambiguous mapping preserves imported source bone index, source name, parent index and parent name.
- Duplicate aliases (for example Hips and Pelvis) are reported as ambiguous and excluded rather than silently choosing the first candidate.
- Missing required profile bones and unrecognized source bones are reported separately; separate Skeleton3D nodes are never combined.
- Mapping is derived from Godot import inspection and does not rewrite the original GLB.
- Regression tests cover canonical profile keys, source indices/parents, duplicate aliases, unmapped bones and strongest unambiguous skeleton selection.
- This is name-based preflight, not proof of imported rest-pose, axis, skin-weight or animation compatibility. Imported-character RetargetModifier3D integration remains open.
- Windows CI for this batch is pending.



## Indexed humanoid hierarchy validation — implementation batch

- The Python rig analyzer now validates required parent/ancestor chains from Godot's indexed Skeleton3D report when the importer provides index and parent-index data.
- Checks cover the spine/head chain, both upper/lower leg and foot chains, and both upper/lower arm and hand chains. Intermediate helper bones are allowed because the validator checks ancestry rather than requiring direct parent equality.
- Invalid parent references, self-parenting, cycles and broken required chains are surfaced as structured issues.
- The Character Studio import report now shows hierarchy status and the concrete issues (or states when indexed hierarchy data is unavailable).
- This is structural validation only. A valid hierarchy does not establish compatible rest pose, axes, skin weights, scale or real animation transfer; `retargeting_ready` remains false.
- Regression coverage includes valid chains, a broken leg chain and legacy name-only importer data. Windows CI #229 is running for commit `1cac9e93adff60bd051c4029df829ebc5fc662f0`.


## Imported humanoid rig diagnostics and retarget proof — 2026-11-25

- Indexed profile mapping now retains each source bone's rest transform (local position, quaternion rotation and scale) from Godot's imported Skeleton3D.
- The report summarizes available local rest-offset lengths and labels them as local scene-unit values, not world-space limb measurements.
- Required humanoid hierarchy validation distinguishes valid, incomplete, invalid and unavailable data. A partial chain is never reported as fully valid.
- Added a deterministic 15-bone skinned humanoid GLB fixture with JOINTS_0/WEIGHTS_0 skinning, inverse bind matrices and an imported arm animation.
- Windows CI #237 passed with the real Godot 4.7.2 worker importing this fixture and checking the skeleton, animation and rest-transform payload. Windows CI #238 also passed after the native proof was expanded.
- Dedicated Godot proof #8 passed with all imported-rig checks true: 15 bones, skin binding, imported animation, finite rest transforms, different source/target arm rest lengths and transferred pose.
- Dedicated Godot proof #9 passed after making target-rest assignment explicit. Proof #10 additionally checks that the imported retarget modifier and target skeleton survive scene save/reopen.
- Scope boundary: the proof retargets an animation from the imported fixture's skeleton to a target skeleton generated from that imported hierarchy with different proportions. It does not yet implement a general user-facing retarget pipeline for two arbitrary imported GLBs.
- The imported source GLB is not rewritten. Production app integration, target-asset binding, rest-pose correction, visual acceptance on representative user models and deterministic export remain open.

## 2026-11-25 — Original character creation work resumed

The current P2.2 checkpoint is not complete: importing and retargeting existing GLBs does not meet the master brief's requirement to create original stylized characters.

The first-party modular creator will start with the Quaternius Ultimate Modular Men and Ultimate Modular Women CC0 1.0 packs. The pinned GLB conversion set contains 11 men and 10 women outfit bases, four swappable slots per model (head/body/legs/feet), and 24 animations per outfit. The 21 GLBs total 34.92 MiB. Three representative assets are the initial Godot acceptance set; their 62-bone rigs must expose matching bone-name sets.

The newer Universal Base Characters + Modular Character Outfits - Fantasy packs offer a more modern humanoid rig and 62 modular outfit parts, but the standard outfit archive is 280 MiB and the animation library is separate. They are deferred until the smaller first creator slice is proven.

The app-side library foundation exposes a catalog and lazy-download model route. Every downloaded GLB is pinned to an immutable source commit and checked for exact size and Git blob SHA-1 before caching under the user's Cartoon Studio data directory. The third-party browser creator repository is used only as a host for the CC0 model conversions; its source code is not reused because it has no declared code license.

**At the start of this batch, not yet implemented:** cross-outfit mesh assembly, material/color customization, native GLB export, creation-recipe persistence and the browser-facing modular builder. Subsequent implementation and acceptance checkpoints are recorded above.


## 2026-11-25 — Rig-based body-proportion editing

- Main commit `f9a03b9613d22c8bf99e96c5cf3d5de9997e0fd2` adds a body-shape editor for compatible imported humanoid rigs, with torso, shoulder, arm, leg and head controls.
- Applying non-neutral values asks the Godot worker to update rig transforms, export a new GLB and re-import it to verify changed bones. The source GLB is not modified; the integration test also checks animation names and playback on the exported asset.
- The project stores the edited asset as a new versioned character-asset manifest, keeping its source path and applied proportions. Imported morph targets are grouped into face, body and other slider sections; these controls use only morphs present in the GLB.
- Windows quick CI [#417](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45672883272) passed on this commit, including the pinned Godot 4.7.2 worker tests, Node syntax checks, Ruff and the full pytest suite.
- Scope boundary: this changes an existing humanoid rig or imported morph target; it does not create new mesh topology, author original face/hair geometry, generate blend shapes or convert arbitrary rigs. Local browser functional acceptance is recorded below; broad visual acceptance remains outstanding, so P2.2 remains PARTIAL.

## 2026-11-25 — Local browser acceptance follow-up

- Imported and previewed the pinned CC0 Male Adventurer through the Character Studio library. Godot reported 5 meshes, one skeleton, 24 animations, 13/15 humanoid-name coverage and hierarchy warnings; this is not evidence of general retarget compatibility.
- Applied `torso_length=1.1`. The Godot worker exported a separate GLB, reported two changed rig bones, and retained animation clips and skin binding. The source copy's SHA-256 matched the pinned library asset (`2caf3ea58a06744c44a360c941c3355b499ba5adf8edf549b98fc347c45faa28`); the edited export had a distinct SHA-256 (`a14529497467da31f4c8af3bd62d80cf141b131aa4352913cc4f55cc711116fa`).
- Saved the edited character profile, reloaded the page, reopened the profile and confirmed the 1.10 torso value, 24 animation clips and working Walk playback controls. A separate synthetic fixture also passed the same functional edit/save/reopen path; it is not suitable for visual-quality judgment.
- Browser inspection found and fixed two UI defects: the empty-preview label remained visible because the CSS `display:grid` rule overrode the `hidden` attribute, and the saved-character rendering loop shadowed the global `document`, causing `document.createElement` failures after save. The profile cards and preview placeholder now behave correctly.
- The pinned Adventurer preview showed an actual rendered character and a visible body-shape change, but its hierarchy warnings and the limited number of inspected models prevent broad visual signoff. Imported face/hair authoring and morph-capable browser acceptance remain open.

## 2026-11-25 — Geometry-aware hairstyle placement regression

- Corrected generated-hair fitting to use the skinned head mesh's bounds transformed into Head-bone rest space instead of whole-skeleton height. Face-feature surface geometry is used to infer which side is the front; rigs without an identifiable head mesh retain the existing fallback.
- Added a real Male Adventurer regression for short hair and ponytail. It confirms named face-feature surfaces determine the expected front direction; pinned Godot 4.7.2 passed export/re-import placement checks, retained all source animation names, played Walk after export, and left the source GLB byte-identical.
- `python -m pytest -o addopts= -q -rs tests\test_engine.py`: **14 passed** after fetching the pinned CC0 RobotExpressive fixture using the repository checksum-verifying script. The focused hair-fit test passed independently.
- Full local `python -m pytest -o addopts= -q -rs`: **121 passed, 4 skipped** in 101.42 seconds; only three Node.js suites and one symlink-capability test were skipped.
- A fresh browser screenshot could not be captured, so this does not establish visual quality or saved-profile behavior. Broad hairstyle acceptance, PNG review, original face geometry and the P2.2 exit criteria remain open.
