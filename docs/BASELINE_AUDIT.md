# Repository Baseline Audit — Feature Line

## Snapshot
At documentation realignment start, `feature/cartoon-character-foundry` was `ce9530543f31b5653bed96694286e660d19b206c`; old `main` was `f6d9001b79f1cfb3108561f31c6ab6a88ebc7a23`. Default branch was still `main`. Preserve both histories; do not merge feature into old main.

## Existing systems to preserve
- FastAPI backend and browser workspaces.
- SQLite/project-scoped persistence and versioned story/character data.
- Character Studio and Foundry API/UI, character recipe persistence and procedural GLB prototype.
- Blender toolchain and Blender authoring modules.
- Blender verification path generating character, world and prop assets.
- Godot 4.7.2 worker/adapter and GLB import/inspection/round-trip.
- World Builder and curated Quaternius/Kenney asset catalogues.
- Render/job queue, episode scene foundations and FFmpeg assembly path.

## Current verification checkpoint
Latest feature CI run #630 failed. No pass is claimed. Inspect raw job logs before assigning root cause. Documentation changes must not touch application code or attempt to repair this CI failure.

## Strategy discrepancies found in older documentation
Older files described Blender as optional, character-only or excluded from the world/prop toolchain; treated Godot as the primary asset authoring path; and prescribed merging the feature branch into old main. Those statements are superseded by the current master brief.

## Audit conclusion
The repository contains substantial usable work. The required action is architectural realignment and extension, not a restart. This document is a dated checkpoint, not a claim that all existing modules are production-complete.
