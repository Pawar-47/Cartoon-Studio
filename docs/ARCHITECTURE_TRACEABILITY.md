# Architecture Traceability — Strategy Addendum

This revision supersedes old Godot-only/Blender-optional architecture mappings. Keep existing atomic requirement IDs where applicable; add the following strategy requirements to the registry and detailed traceability.

| New ID | Requirement | Architecture owner | Acceptance evidence |
|---|---|---|---|
| BLEND-001 | Blender is the shared authoring/generation foundation for all 3D asset domains. | Blender toolchain | Same shared worker/services used by character, world and prop jobs |
| BLEND-002 | Support interactive and headless Blender automation. | Blender worker | Interactive and headless jobs execute and report capabilities |
| BLEND-003 | Preserve editable .blend source for generated assets. | Asset pipeline | Source saved, reopened and linked to asset manifest |
| BLEND-004 | Export GLB/glTF with textures and stable IDs. | Export service | Godot imports exported asset and verifies required data |
| BLEND-005 | Use versioned recipes for non-destructive regeneration. | Recipe service | Edit recipe, regenerate, compare source and new version |
| BLEND-006 | Shared tools cover characters, environments and props. | Shared authoring core | Generate one representative asset from each domain using common primitives |
| BLEND-007 | Blender is not required to launch the installed app. | Runtime packaging | Clean install/launch without Blender installed |
| GODOT-001 | Godot is production scene/animation/camera/timeline/preview/render engine. | Godot adapter | Imported assets assembled into persistent playable scene |
| WEB-001 | Browser/FastAPI orchestrates authoring and production jobs. | API/job service | UI creates, monitors, cancels and recovers generation jobs |
| ACCEPT-001 | User reviews actual visual output. | Review workflow | User sees generated asset and explicitly accepts/rejects |

Legacy 171-row mapping remains a source record but must be reconciled against the new branch and code. A planned module path is not implementation evidence. Do not mark requirements VERIFIED from code presence alone.
