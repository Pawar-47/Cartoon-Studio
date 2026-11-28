# Execution Batch Plan — Blender-First

## Batch 0 — Documentation and repository realignment
Rewrite governing briefs, architecture, requirements, research decisions, status, reports and agent instructions to the Blender-first strategy. Preserve historical evidence but mark it historical. No application code changes. Verify diff and commit once.

## Batch 1 — Shared Blender tool foundation
- Runtime discovery/version/capability check.
- Interactive and headless worker lifecycle.
- Stable asset IDs, naming, collections and project-relative workspaces.
- Reusable scene, geometry, modifier/geometry-node, material/style and texture utilities.
- Versioned recipes and asset manifests.
- GLB export, .blend source retention, texture packaging, hashes, thumbnails and provenance.
- Structured errors, cancellation and recovery.
**Acceptance:** generate a character, a world component and a prop using the same shared services.

## Batch 2 — Character quality milestone
- Original stylized master character, expressive face, clean topology and controlled proportions.
- Fitted clothes/hair/accessories.
- Reusable rig, skin weights and facial morphs/visemes.
- Non-destructive recipe regeneration.
- Godot import/save/reopen and animation checks.
- Present actual generated outputs for user review.
**Acceptance:** user can inspect a real character and judge quality; automated tests only verify structure/function.

## Batch 3 — World and item authoring
- Reusable building, street/road, terrain, vegetation, interior, vehicle, furniture and prop tools.
- Consistent scale/style/material conventions.
- Export/import and persistent placement in Godot.
**Acceptance:** build a coherent reusable location from multiple Blender-generated assets.

## Batch 4 — Browser orchestration and asset library
Durable job queue, progress, cancel/retry/recovery, recipes, versioning, review/approval, provenance and scene linking.

## Batch 5 — Episode production
Story approval, Urdu dialogue, scene planning, animation/timeline, camera, voice/lip-sync, sound, rendering and FFmpeg MP4 assembly.

## Batch 6 — Reliability and release
Functional CI, packaging milestones, license/SBOM, backup/recovery, target-PC benchmarking and quality presets.

## Discipline
One coherent feature batch at a time. No multiple CI runs. No full builds for documentation-only edits. Preserve all prior code/data. Do not replace real product work with repeated audits, screenshot scripts or validators.
