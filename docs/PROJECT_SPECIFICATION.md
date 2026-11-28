# Authoritative Product Specification

**Revision:** Blender-first production architecture, 2026-11-28. This document supersedes earlier descriptions that treated Blender as optional or excluded it from world/prop creation.

## 1. Product
Cartoon Studio is a local-first, browser-based studio for creating original reusable 3D cartoon characters, worlds and Urdu cartoon episodes. Normal episode target is 5–7 minutes. Final output is an editable production project and an MP4.

## 2. System responsibilities
| Layer | Responsibility | Must not become |
|---|---|---|
| Browser + FastAPI | Project control, UI, prompts, asset jobs, recipes, library, approvals, scene/timeline control, job monitoring | 3D authoring or final heavy renderer |
| Blender toolchain | Author and generate all reusable 3D assets; geometry, rigs, materials, textures, procedural generation, editable sources and GLB export | Required installed-app runtime or a character-only silo |
| Godot 4.7.2 | Import GLB, assemble persistent scenes, animate, manage camera/timeline, preview and render | Source of truth for editable modeling/rigging |
| FFmpeg | Final MP4 and audio/video assembly | Story/asset database |
| SQLite + project files | Persistence, manifests, revisions, jobs, logs and assets | Cloud dependency |

## 3. Shared Blender asset platform
One shared Python API/tooling platform must expose reusable asset-generation primitives and domain tools. Shared services include Blender process discovery/launch, version/capability checks, scene lifecycle, collections, stable naming/IDs, geometry/material libraries, modifier/geometry-node helpers, rig/skin helpers, texture handling, recipe serialization, validation, export, hashing, thumbnails, provenance and structured diagnostics.

Domains include characters, clothing/hair/accessories, buildings, roads/streets, terrain, vegetation, interiors, vehicles, furniture and general props. Common style presets and asset conventions keep the world visually coherent.

Blender should support both interactive authoring and headless batch generation. Store `.blend` source and export GLB/glTF plus referenced textures and manifest. The app must be able to queue jobs, recover failures and present outputs for approval.

## 4. Character requirements
Original character templates; controllable body/face proportions; clean readable face; expressive eyes, brows and mouth; consistent hair and fitted clothing; accessories; stable IDs and versioned recipes; reusable rig; skinning; facial morphs/visemes; animation compatibility; non-destructive edits; GLB export and Godot import. Quality is evaluated by the user viewing the actual character. Do not equate generated mesh existence with acceptable visual quality.

## 5. World/environment/prop requirements
Create reusable stylized towns, neighborhoods, roads, sidewalks, crossings, houses, apartments, shops, schools, parks, offices, hospitals, interiors and set pieces. Add vegetation, trees, rocks, water, weather, lighting, vehicles and furniture. Assets must share scale, materials, topology/style, metadata and library conventions. Scenes should retain location identity across episodes.

## 6. Production requirements
Godot imports approved GLB assets, assembles scenes, handles characters, props, animation, camera and timeline. Scene data remains versioned and engine-neutral at the project level. FFmpeg assembles final video/audio. Render jobs must persist, resume, retry, cancel and report errors without losing completed outputs.

## 7. Story and Urdu
Prompt in Urdu or English. Generate editable original story plans with title, summary, cast, relationships, 5–7 minute target, scenes, dialogue, actions, expressions, locations, props, camera, lighting, music, effects, transitions and ending. Natural Pakistani Urdu in Urdu script is required. Users review and approve story/dialogue before production.

## 8. AI and external services
The core application must work without any AI provider, API key, credits, subscription or network inference. External services are optional adapters. Respect provider terms and limits; do not bypass quotas or use undocumented APIs. Manual copy/paste handoff is acceptable. Do not claim free services are unlimited.

## 9. Target hardware
Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM, SSD, Windows. Keep browser UI lightweight and bound concurrency. Blender authoring can run on a compatible workstation or CI/remote worker if the user's hardware is unsuitable; do not require Blender to launch the installed application. Hosted CI is not a GPU render farm. Actual user-PC benchmarks are late-stage work, not a development gate.

## 10. Licensing
Do not use MPFB as the product base or copy GPL code. Review Blender distribution obligations before bundling. Record separate licenses for software, add-ons, models, textures, animation, datasets and outputs. Preserve attribution and notices. No asset may be called cleared without evidence.

## 11. Existing code preservation
Retain current FastAPI/browser workspaces, SQLite/project persistence, story plans, Character Studio, World Builder, GLB importer/exporter, Godot adapter/worker, Blender toolchain, render queue and FFmpeg integration. Inspect and reuse these implementations. Do not restart or duplicate.

## 12. Acceptance
Functional tests prove API, recipe, export, import and job contracts. User visual acceptance is a separate creative quality decision. Automated screenshot/clipping checks may diagnose regressions but are not a product function and cannot substitute for the user seeing generated assets.
