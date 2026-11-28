# Architecture Contracts — Blender-First

## Canonical asset identity
Every asset has a stable Cartoon Studio ID, semantic type, schema version, revision, generator/tool version, source provenance, exact license record, dependencies, hashes and relative paths. Blender object names and Godot node paths are not canonical IDs.

## Blender source/export contract
- Editable source: project-contained `.blend` file.
- Production interchange: GLB/glTF 2.0.
- Textures are external or embedded according to export profile and are explicitly listed in the manifest.
- Recipe is versioned, deterministic where feasible and sufficient to regenerate the asset.
- Export records warnings for unsupported features; never silently drop geometry, rig, materials or morph targets.
- Every successful job publishes outputs atomically; failed jobs do not overwrite the last accepted version.

## Shared tool contract
All asset domains call shared services for runtime checks, scene setup, IDs, geometry/material helpers, recipe handling, validation, export, provenance and diagnostics. Character, world and prop modules may add domain logic but may not fork these foundations.

## Godot contract
Godot imports GLB assets and canonical manifests; creates production scenes; controls animation, cameras, timeline, preview and rendering. It reports imported node/mesh/rig/animation capabilities. Blender-authored source remains editable only in Blender.

## Browser/backend contract
FastAPI queues and supervises long-running Blender/Godot/FFmpeg jobs. Job states and events persist. UI can inspect outputs, logs and provenance and approve/reject versions.

## Project persistence
SQLite indexes project, asset, recipe, revision and job records. Project-contained JSON manifests and binary files remain portable. Migrations are explicit and preserve prior data.

## User acceptance
Automated tests validate schema, geometry integrity, export/import, rig, recipe and job behavior. Visual style/quality requires user review of actual generated output.
