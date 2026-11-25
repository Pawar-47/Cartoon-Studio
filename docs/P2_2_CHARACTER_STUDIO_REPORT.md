# P2.2 Character Studio — Import and Persistent Profile Report

**Date:** 2026-11-25  
**Status:** Implementation committed; Windows CI acceptance pending  
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
- The combined CI result is pending at the time this report is authored.
