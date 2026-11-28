# Master Plan — Blender-First Cartoon Studio

## Strategic baseline
The feature development line is the active working line. The old `main` branch remains preserved and is not a merge target. Branch promotion/default-branch changes are a separate owner-approved repository operation; no destructive rename, deletion or force-push is implied by this plan.

Blender is the shared asset authoring/generation foundation for characters, worlds, buildings, roads, vegetation, interiors, vehicles, furniture and props. Godot 4.7.2 is the production engine. Browser/FastAPI is the control plane. GLB/glTF is the interchange format. FFmpeg assembles MP4.

## Architecture principles
1. One shared Blender toolchain, with reusable core services and domain modules.
2. Character quality first, but world and prop requirements are included in the shared foundation from day one.
3. Keep editable `.blend` sources and deterministic, versioned recipes; export stable GLB assets and metadata.
4. Godot consumes assets and handles production scenes, animation, camera, timeline, preview and rendering.
5. Blender is not a runtime prerequisite for installed Cartoon Studio.
6. Preserve all existing project/app/engine functionality and integrate incrementally.
7. Core work remains local-first and independent of paid AI/API quotas.
8. User visual review—not screenshot automation—decides creative acceptance.

## Delivery sequence
### Track A — Governance and architecture realignment
- Rewrite all briefs, plans, architecture, requirements, research decisions, status and historical reports to this strategy.
- Identify stale claims and mark historical evidence versus current direction.
- Preserve atomic requirement IDs where possible; add Blender-specific requirements and crosswalk them.
- Do not change application code in the documentation-only realignment commit.

### Track B — Blender shared tool foundation
- Blender executable discovery/version capability and worker lifecycle.
- Headless and interactive job execution; structured request/response and cancellation.
- Shared scene/collection, naming, asset-ID, recipe and metadata conventions.
- Material/style library, geometry helpers, reusable modifiers/geometry-node patterns.
- Export GLB, retain .blend, package textures, hash and provenance.
- Deterministic fixtures and diagnostics.

### Track C — Character Foundry quality
- Original master character with deliberate silhouette, proportions, clean topology and expressive face.
- Reusable rig and skinning; facial morphs/visemes; hair/clothing/accessories.
- Non-destructive recipe editing and regeneration.
- User-visible generated output and review loop.
- Godot round-trip import, animation and scene persistence.

### Track D — Shared world and item tools
- Reuse Track B primitives to generate buildings, roads, terrain, vegetation, interiors, vehicles, furniture and props.
- Modular kits, style consistency, scale, placement, metadata and recipe reuse.
- Godot scene assembly and persistent world identity.

### Track E — Studio workflow integration
- Browser job orchestration, progress, cancel/retry/recovery.
- Asset library, versions, approvals, provenance and scene linking.
- Story-to-scene mapping, timeline/camera, animation and audio.
- Urdu TTS/lip-sync adapters where legally and technically viable.
- FFmpeg final MP4 and editable project packaging.

### Track F — reliability, packaging and performance
- CI functional checks; full packaging only at milestones.
- Release artifacts and notices.
- Physical-PC benchmarks, quality presets and optimization late in development.

## Existing implementation to preserve
FastAPI/browser UI, SQLite/project documents, Story Generator, Character Studio, World Builder, pure-Python GLB prototype, Blender toolchain/modules, Godot 4.7.2 adapter/worker, asset catalogues, recipes, render queue and FFmpeg path. The exact verified state is in PROJECT_STATUS.md.

## Work discipline
One coherent batch at a time, no duplicate CI, no full builds for docs-only edits, no extra branches, no blind merges, no restart. Each feature batch should deliver a real usable capability rather than only more audits or validation scripts.
