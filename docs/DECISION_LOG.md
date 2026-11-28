# Decision Log — Current Architecture

## D-001 — Blender is the shared asset-authoring foundation (2026-11-28)
**Decision:** Use Blender Python API and a shared reusable toolchain to author/generate all 3D asset domains: characters, clothing/hair, buildings, roads, terrain, vegetation, interiors, vehicles, furniture and props.
**Reason:** Previous procedural character outputs were below desired quality. A real DCC authoring platform provides editable geometry, rigging, materials, procedural tools and consistent reusable assets.
**Consequences:** Preserve .blend sources and recipes; export GLB/glTF; maintain common tools across domains. Blender is not required at app runtime.
**Rejected:** Blender as an optional add-on used only for character extras; separate incompatible world/prop generators.

## D-002 — Godot remains the production engine (2026-11-28)
Godot 4.7.2 handles scene assembly, animation, cameras, timeline, preview and rendering. It consumes approved Blender exports; it is not the editable modeling source of truth.

## D-003 — Browser/FastAPI remains the control plane
The existing web application orchestrates projects, Blender jobs, asset libraries, approvals, scenes and render jobs. Preserve its current APIs and persistence.

## D-004 — GLB/glTF is the asset interchange
Blender retains editable .blend files; production assets are exported as GLB/glTF with textures and manifests. Godot must import/reopen and preserve required rig/animation data.

## D-005 — No MPFB product foundation or copied GPL MPFB code
MPFB is not adopted as the product base. Evaluate other tools/assets under their exact licenses. Blender itself is GPL-3.0; external application/API use and any redistribution/bundling must receive license review.

## D-006 — Existing pure-Python GLB generator is a prototype/fallback
It may remain useful for tests or fallback, but cannot define the visual-quality ceiling or displace Blender-authored assets.

## D-007 — User owns visual acceptance
Automated checks establish structural/function correctness. The user must see actual characters/worlds to approve visual quality. Screenshot/clipping automation is diagnostic only.

## D-008 — Preserve old main and make feature line independent
The feature branch is the intended independent primary development line. Old main must remain preserved and must not receive merges. Changing default branch or renaming the feature branch requires safe repository-level handling and must not destroy old main.
