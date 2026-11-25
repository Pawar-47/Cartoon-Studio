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
- This slice does not author new 3D meshes, create/edit rigs, edit materials or blend shapes, generate a live 3D viewport/thumbnail, edit animation or export a modified GLB.
- Expressions, clothing, voice and relationships are stored as metadata; the corresponding visual/audio systems are not implemented yet.
- P2.2 is not complete until real preview and authoring/export capabilities are delivered and verified.

## Verification
- New test module: `tests/test_characters.py`.
- The tests use a deterministic fake Godot adapter for API-level contract tests.
- The existing Windows CI job also runs the real pinned Godot 4.7.2 worker integration tests.
- Windows CI #208 passed on commit `41aabbb627e36f3f02f306e79e3cba33bd19dc84`: 45 tests passed; lint, compilation, runtime integrity, bootstrap smoke, both self-contained builds and the full installer lifecycle passed. The run uploaded the bootstrap, installer and SBOM artifacts.


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
