# Next Steps — Current Strategy

## Mandatory order
1. Finish and verify this complete documentation realignment.
2. Complete the repository's independent primary-branch transition safely, preserving old `main`; do not merge PR #23 into old main or force-push.
3. Inspect raw CI #630 logs and identify the actual Blender-to-Godot failure. Do not guess from prior suspected path issues.
4. Resume implementation with real Blender authoring functions. Character quality is first; shared core must support worlds and props from day one.

## First implementation batch after documentation
- Inspect current Blender modules and generation scripts.
- Consolidate reusable worker/runtime, scene lifecycle, asset identity, recipe, material, geometry, rig, export and provenance functions.
- Improve the character generator's actual geometry and face quality through Blender-native modeling operations.
- Generate an editable .blend source and GLB, then verify Godot import.
- Provide a real output for the user to inspect; do not gate progress on automated screenshot clipping.
- Build on the same primitives for a world asset and a prop rather than a parallel toolchain.

## CI policy
One run at a time. The documentation-only batch does not justify a full build or repeated CI. Wait for all active jobs before pushing. Run functional CI at a meaningful checkpoint after the next implementation batch. Do not launch packaging/installer workflows for documentation changes.

## Do not do
- Do not return to a Blender-free or Godot-only asset-creation strategy.
- Do not restart the repo or duplicate existing systems.
- Do not spend implementation cycles only writing audits, validators or screenshot tooling.
- Do not treat visual clipping scripts as a product feature.
- Do not claim CI #630 passed; it failed.
