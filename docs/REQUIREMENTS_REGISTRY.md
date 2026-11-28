# Requirements Registry — Blender-First Amendment

## Authority
The current binding brief is `MASTER_EXECUTION_PROMPT.md` and `PROJECT_SPECIFICATION.md`. Existing 171 atomic rows from the earlier registry are historical requirement IDs and must be reconciled, not discarded. Where their architecture assumes Blender is optional or Godot authors all assets, update the requirement mapping to this amendment.

## New atomic requirements
| ID | Priority | Requirement | Owner | Acceptance | Status |
|---|---|---|---|---|---|
| BLEND-001 | Critical | Blender is the shared authoring/generation foundation for every 3D asset domain. | Blender platform | Character, world and prop jobs use the same core services. | IN PROGRESS |
| BLEND-002 | Critical | Shared Blender core supports interactive and headless workflows. | Worker | Both modes execute a recipe and return structured results. | PLANNED |
| BLEND-003 | Critical | Generated assets retain editable .blend source. | Asset pipeline | Source reopens and is referenced by manifest. | PLANNED |
| BLEND-004 | Critical | Export GLB/glTF with textures and stable Cartoon Studio IDs. | Exporter | Godot imports output and required data survives. | IN PROGRESS |
| BLEND-005 | Critical | Assets are reproducible from versioned recipes. | Recipe service | Modify recipe and regenerate a new non-destructive version. | PLANNED |
| BLEND-006 | Critical | Shared tools support characters, worlds and props. | Shared core | Generate representative assets in all three domains with common services. | IN PROGRESS |
| BLEND-007 | High | Blender is not a required runtime dependency for the installed app. | Packaging | Clean app launch with Blender absent. | PLANNED |
| BLEND-008 | Critical | Character authoring delivers high-quality original geometry, face, rig, clothing and hair. | Character tools | User reviews actual output; structural/round-trip tests pass. | IN PROGRESS |
| BLEND-009 | High | World tools create reusable buildings, roads, terrain, vegetation and interiors. | World tools | Multi-asset location is generated and imported into Godot. | PLANNED |
| BLEND-010 | High | Prop tools create vehicles, furniture and general objects using shared platform. | Prop tools | Generated props export/import with manifests. | PLANNED |
| GODOT-001 | Critical | Godot is production engine for scene assembly, animation, camera/timeline, preview and rendering. | Godot adapter | Approved Blender assets form a persistent playable scene. | PARTIALLY IMPLEMENTED |
| WEB-001 | Critical | Browser/FastAPI controls projects, generation jobs, libraries, approvals and production. | Web app | User can submit, monitor, cancel and approve jobs. | PARTIALLY IMPLEMENTED |
| PIPE-001 | Critical | FFmpeg assembles final audio/video into MP4. | Media pipeline | Real 5–7 minute episode exports and plays. | PARTIALLY IMPLEMENTED |
| ACCEPT-001 | Critical | User visually accepts creative quality by seeing actual generated assets. | Review workflow | Actual output presented; explicit user approval recorded. | PLANNED |

## Status definitions
NOT REVIEWED, RESEARCH REQUIRED, PLANNED, IN PROGRESS, IMPLEMENTED, PARTIALLY IMPLEMENTED, TESTED, VERIFIED, BLOCKED, DEFERRED WITH REASON, REJECTED WITH JUSTIFICATION. VERIFIED requires direct acceptance evidence, not code presence.

## Registry maintenance
Retain historical IDs and original source links. Reconcile duplicates/dependencies and update exact source paths and tests in each batch. Do not invent evidence. Update this registry and REQUIREMENT_TRACEABILITY.md together.
