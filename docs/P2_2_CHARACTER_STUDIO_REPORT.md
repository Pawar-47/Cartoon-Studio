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
- Windows CI acceptance is pending.
