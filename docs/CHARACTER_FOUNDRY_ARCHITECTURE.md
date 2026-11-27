# Cartoon Character Foundry — Architecture Decision

**Status:** Approved direction; implementation starts on `feature/cartoon-character-foundry`  
**Decision date:** 2026-11-26  
**Stable baseline:** `main` at `285e8d664e4d61d57af968a5a71424cb1e6acda9`

## 1. Why the architecture is changing

The existing Character Studio is a useful imported-asset editor and modular outfit assembler. It is not yet a genuine character generator. Its Quaternius-based catalogue contains finished rigged people; proportion controls primarily change skeleton rest transforms, and facial controls depend on morph targets already present in an imported GLB. Geometry overlays and bone transforms cannot substitute for editable source topology.

This is a capability boundary, not a reason to discard the working application. Existing imported GLBs remain supported as optional assets.

## 2. Product decision

Build an original **Cartoon Character Foundry** around editable master meshes and reproducible character recipes.

- The master mesh is owned by Cartoon Studio and has controlled, documented topology.
- Face and body controls deform the actual mesh through real shape keys / morph targets (or an equivalent vertex-delta representation). A control must not claim to reshape anatomy if it only moves a bone or adds an overlay.
- A saved character stores a versioned recipe and references to generator assets. An exported GLB is a production artifact, not the editable source of truth.
- The same character identity persists across episodes and professions. Scenarios change fitted clothing, accessories, materials and props—not the underlying person.
- Hair, eyes, teeth, hands, feet and clothing may be modular assets, but must follow the master topology/rig and attachment contracts.
- One standard humanoid rig is established before expanding the character catalogue. Existing animation/retargeting work is preserved and adapted to that rig.

## 3. Generation boundary

Keep the current browser UI and FastAPI project services as the control plane, and Godot 4.7.2 as the production scene/runtime worker.

Use Blender in an isolated, optional/offline or headless **asset-generation and authoring worker** for the first master-mesh proof if it gives us reliable mesh, shape-key, rig and GLB tooling. Blender is not a mandatory day-to-day application runtime and must not become a prerequisite for opening projects or editing story/world data.

The first proof must establish whether the master mesh can be generated, morphed, rigged and exported reproducibly. Do not adopt MPFB as the product's base character or copy its GPL code into this repository. MPFB/MakeHuman are architecture references for shape-target authoring, recipe serialization and clothing refitting. Any third-party code or assets require an explicit license/provenance review before adoption.

## 4. First master character scope

Build only one original stylized adult master character initially. Do not expand the existing 21-model catalogue or create child/elderly variants until this proof passes.

The first recipe should support:
- overall height and head-to-body ratio;
- torso width/depth and shoulder width;
- arm and leg length/volume;
- jaw width, chin length, cheek fullness and face width;
- eye size/spacing, nose width/length, ear size and mouth width;
- a small set of real facial expression targets sufficient to prove the deformation system.

The initial visual style should be clearly stylized and animation-friendly, with consistent edge flow and deformation-friendly topology. Avoid photorealistic human detail. Exact art direction can be refined after the first working mesh is visible.

## 5. Clothing and deformation contract

Clothing is a separate fitted asset, not a replacement character. The first proof must include one simple garment and demonstrate that it remains attached and acceptably fitted after at least two materially different body-shape settings.

Prefer a deterministic refit approach appropriate to the mesh density: shared topology/weights where practical, surface projection or cage-based fitting where necessary. Record refit failures rather than silently exporting intersecting or detached clothing.

## 6. Canonical character recipe

The persisted recipe must be engine-neutral and versioned. It should identify:
- recipe schema version and stable character ID;
- master-template ID and generator version;
- numeric body/face parameter values;
- selected expression/morph values;
- clothing, hair and accessory asset IDs;
- rig profile ID;
- source asset/license provenance;
- generated GLB hash and generator/build metadata.

Changing a parameter must regenerate from the editable recipe/master source, not destructively edit the last exported GLB. Existing character profiles and imported-GLB workflows must continue to open.

## 7. Milestones and acceptance gates

1. **Foundation:** define master topology, parameter naming/ranges, recipe schema, rig contract and generator interface.
2. **One editable master:** create one original stylized adult mesh with real face and body deformation targets.
3. **Deformation proof:** tests and a visual artifact show multiple parameters deforming the intended vertices while preserving mesh integrity.
4. **Clothing proof:** one garment refits to at least two body configurations without detachment or severe intersections.
5. **Godot proof:** export GLB, import it with the pinned Godot worker, verify skeleton/skin/morph targets, save/reopen a scene and play a basic animation.
6. **Application integration:** save/reopen the recipe through the existing project/profile API and expose the initial controls in Character Studio.
7. **Expansion:** only after the above gates, add child/elderly and additional adult variants, broader clothing/hair libraries, Urdu visemes and production animation integration.

A phase gate requires both automated structural checks and reviewable visual outputs. Passing a parser or unit test alone is not visual acceptance.

## 8. Preserve existing application work

Do not rewrite or remove the working FastAPI/browser application, project storage, imported GLB support, profile persistence, modular outfit workflows, Godot worker, World Builder, Story Generator, Urdu speech/audio, episode scene production or MP4 renderer.

The Quaternius catalogue remains an optional imported-character/outfit source. Existing character profiles must remain readable. Migration, if needed, must be additive and backward-compatible.

The existing procedural skeletal-action implementation is retained as a capability, but new action/retarget expansion is paused until the master rig contract is stable. Later, map its action tracks to the Foundry rig.

## 9. Branch and release discipline

- `main` is the frozen stable baseline while this architecture transition is developed.
- All Foundry changes go to `feature/cartoon-character-foundry`.
- Do not merge to `main` until the first master character passes the end-to-end acceptance gates and the user approves the integration checkpoint.
- Do not create additional branches for sub-tasks.
- Work in coherent batches; run one CI workflow at a time. Do not run full packaging/build workflows for documentation-only or single-line changes.
- Never force-push or rewrite the stable baseline.

## 10. Immediate implementation order

1. Inspect the current generator/worker/test contracts on this branch.
2. Add the recipe and generator interfaces without breaking imported-character profiles.
3. Implement a minimal original stylized master mesh with a small, real vertex-deformation target set.
4. Produce a visual proof and a GLB that Godot can import and animate.
5. Add one fitted garment and verify refitting across two body shapes.

The objective is a working editable character—not another catalogue, mock UI, or long sequence of validation-only tasks.
