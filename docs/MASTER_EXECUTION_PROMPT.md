# Master Execution Brief — Cartoon Studio (Current Authoritative Revision)

This document supersedes earlier Blender-free or Godot-only interpretations of the project brief. It is the binding product and execution direction. The detailed atomic requirements and historical evidence remain in the registry and reports; when an older document conflicts with this revision, this revision wins.

## 1. Mission
Build a functional, local-first, browser-based studio that produces original, high-quality 3D Urdu cartoon episodes, normally 5–7 minutes long, with persistent characters and a consistent reusable world. Deliver editable projects and real MP4 output, not a prompt mockup or one-off video.

All characters, stories, names, designs, voices, logos and assets must be original or properly licensed. Do not reproduce protected franchise characters, names, dialogue, branding or voice likenesses.

## 2. Product architecture
- Browser UI + FastAPI is the control plane.
- Blender is the shared authoring/generation foundation for every 3D asset domain.
- Godot 4.7.2 is the production engine for scene assembly, animation, cameras, timeline, previews and rendering.
- GLB/glTF is the interchange format between Blender and Godot.
- FFmpeg performs final MP4/audio assembly.
- SQLite and project-contained versioned manifests persist work and jobs.

## 3. Blender mandate
Develop one reusable Blender tool platform using the Blender Python API. It must support interactive and headless execution, reusable modules/operators, templates, modifiers, geometry nodes where appropriate, rigging, materials, textures, validation, export and asset manifests.

The shared platform must create:
- Characters: body/face geometry, proportions, topology, rig, skinning, facial expressions/morphs, eyes, hair, clothing, footwear, accessories and reusable variants.
- Worlds: terrain, towns, neighborhoods, streets, roads, sidewalks, intersections, buildings, shops, houses, schools, parks, interiors and set layouts.
- Natural/environmental assets: trees, vegetation, plants, grass, rocks, water, sky/lighting setups and weather elements.
- Items: vehicles, furniture, household objects, signs, tools, toys, decorations and general props.

Domain tools must share common foundations for scene setup, geometry/material libraries, naming, IDs, recipes, validation, metadata, export and provenance. Do not create an isolated character generator that cannot be reused for worlds and props.

Each generated asset should retain an editable `.blend` source and export production-ready GLB/glTF, with required textures, stable Cartoon Studio asset ID, versioned recipe, generator/tool version, dependencies, source/license provenance, hashes and preview thumbnails.

## 4. Character quality priority
The first high-quality milestone is an original stylized character with readable face and silhouette, deliberate proportions, clean topology, fitted clothing/hair, a usable rig, skin weights, facial expressions and a Godot-ready export. Improve quality through actual Blender geometry and rigging tools, not by adding decorative UI around weak primitive geometry. User reviews actual generated character outputs and decides visual acceptance.

## 5. World and prop quality
Use the same Blender toolchain to create a coherent stylized world: modular buildings, streets, roads, terrain, vegetation, interiors, vehicles, furniture and props. Maintain scale, style, material, lighting and asset-library consistency across locations and episodes. World generation is not a separate incompatible pipeline.

## 6. Godot production role
Godot consumes exported GLB assets and project manifests. It provides scene assembly, persistent sets, animation playback/blending, camera and timeline control, previews, lighting and production rendering. It must not become the authoring source of truth for editable mesh/rig creation. Preserve a clean Blender-to-GLB-to-Godot round trip.

## 7. Browser application role
The web app manages projects, prompts, asset requests, Blender jobs, generation recipes, asset library, previews, approval, scene plans, timelines and rendering. It can schedule local/headless Blender tasks or use an explicitly configured compatible worker. It must remain useful when external AI services are unavailable.

## 8. Episodes and Urdu
Accept Urdu or English prompts. Urdu is core; prioritize natural Pakistani Urdu in Urdu script, with RTL and optional Roman Urdu. Stories need cast continuity, scene durations, dialogue, actions, expressions, locations, props, camera, lighting, audio and transitions. Users can edit/approve before production. Final output is a real MP4 with dialogue, character-specific voices, lip-sync, music, effects and subtitles as available.

## 9. Cost, privacy and hardware
No mandatory paid APIs, API-key signup, usage credits, cloud rendering, online activation or service quota may block core creation/production. External AI/TTS may be optional adapters with honest quota/availability disclosure. Local-first project files and assets remain user-controlled. Design for Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM and SSD, but local-PC benchmarking is deferred to the optimization stage and is not a blocker for development. Hosted CI is for build/test/package, not an assumed free GPU render farm.

## 10. Licensing and reuse
Do not use MPFB as the product foundation and do not copy GPL MPFB code. Blender itself is GPL-3.0; use the official application/API as an external authoring tool and review distribution obligations before bundling or redistributing it. Generated outputs and source assets must each have documented provenance and rights. Do not assume a generated asset has unrestricted rights merely because a tool is open source.

## 11. Existing work and migration
Preserve all existing app code, project data, APIs, Godot worker, GLB support, character profiles, World Builder, Story Generator, render queue and FFmpeg work. Reconcile them with the Blender-first asset pipeline; do not restart or duplicate working subsystems. Existing pure-Python GLB generation may remain as a prototype/fallback, but not as the visual-quality ceiling.

## 12. Work discipline and acceptance
Deliver real functions in coherent batches. Automated tests prove contracts and regressions; they do not replace user visual review. Screenshot/clipping scripts are diagnostic tools only, not features or user acceptance. Never spend repeated batches polishing test screenshots instead of building usable Blender tools. Report exact changes, commits, tests and remaining limitations. Keep one CI run active at a time and preserve the old main branch.
