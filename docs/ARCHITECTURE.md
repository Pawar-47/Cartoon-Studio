# System Architecture — Blender Authoring, Godot Production

## 1. Topology
```
Browser Studio
  | HTTP / JSON
FastAPI control plane ---- SQLite + project manifests + asset/job storage
  | job protocol
Blender Tool Worker (interactive or headless)
  | editable .blend + GLB/glTF + textures + manifest
Asset Library / Approval
  | GLB + versioned scene data
Godot 4.7.2 Production Worker
  | scene previews / render outputs
FFmpeg
  | final MP4
```

## 2. Blender shared authoring platform
Blender is the canonical 3D asset authoring environment. The platform is a reusable Python toolchain, not a single generator script. Common services: process/runtime discovery, version checks, worker execution, scene lifecycle, collections, stable naming/IDs, materials/style presets, geometry/modifier/geometry-node utilities, rig/skin utilities, texture management, recipe serialization, validation, export, thumbnail generation, hashing, provenance and structured errors.

Domain packages: characters; clothing/hair/accessories; environments/buildings; terrain/roads/streets; vegetation/nature; interiors; vehicles; furniture/props. Domain-specific tools compose shared services. No isolated character-only framework.

Outputs: editable `.blend` source; GLB/glTF; texture files; versioned recipe and asset manifest; generator/version/dependency metadata; source/license provenance; hashes; preview images. Export must be deterministic where feasible and report unsupported features rather than silently dropping them.

## 3. Godot production engine
Godot 4.7.2 consumes approved GLB assets and canonical project manifests. It assembles scenes, handles animation playback/blending, camera/timeline, lighting, previews and production rendering. Engine-specific paths and node identifiers remain in adapter manifests, not canonical project documents. The saved Godot scene is a production artifact, not the source of truth for Blender-authored mesh/rig data.

## 4. Browser and backend
FastAPI owns project APIs, job orchestration, asset metadata, recipes, approvals, story plans, scene/timeline data and worker supervision. Browser UI is the control plane and preview surface. Long tasks run as durable jobs, not request-bound synchronous work. Support progress, cancellation, retries, restart recovery and structured logs.

## 5. Interchange and persistence
- GLB/glTF 2.0 is the default interchange.
- Stable Cartoon Studio IDs are canonical; Blender object names/Godot node paths are implementation details.
- `.blend` sources and exports live in project asset storage with versioned manifests.
- SQLite indexes projects, assets, revisions, job state/events and migrations.
- Project-contained JSON manifests remain portable and recoverable.
- FFmpeg assembles approved scene renders, dialogue, music, effects and subtitles into MP4.

## 6. Blender lifecycle and optionality
The installed app must launch without Blender installed. Blender may be discovered locally, configured as a separate authoring worker, or run on a compatible generation workstation/runner. No assumption that the user's Intel HD 5500 laptop can run all Blender workloads. The app must show worker availability/capabilities and give actionable errors. Generated GLB assets are independent of Blender at production runtime.

## 7. Security and reliability
Use argument arrays, bounded timeouts, cancellation, process cleanup, isolated temporary workspaces, path containment, size limits, no shell interpolation, no secrets in logs, checksum verification and atomic output publication. Preserve previous asset versions on failed generation.

## 8. Current implementation boundary
Existing code includes Blender toolchain and generation modules, character Foundry, Blender verification script, Godot import round-trip, FastAPI APIs, browser UI and production foundations. This architecture describes target integration, not a claim that all domains or visual quality are complete. See PROJECT_STATUS.md and TEST_REPORT.md.
