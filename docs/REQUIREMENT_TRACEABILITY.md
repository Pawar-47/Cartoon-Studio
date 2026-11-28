# Requirement Traceability — Blender-First

| ID | Requirement | Code/architecture owner | Test/evidence required | Current state |
|---|---|---|---|---|
| BLEND-001 | Blender is shared authoring platform for all asset domains | app/blender_toolchain.py and Blender authoring modules | Character/world/prop jobs call same shared foundation | IN PROGRESS |
| BLEND-002 | Interactive and headless Blender workflows | Blender worker | Both execution modes tested | PLANNED |
| BLEND-003 | Retain editable .blend source | Asset storage/manifest | Reopen source and verify asset manifest | PLANNED |
| BLEND-004 | Export GLB/glTF with textures and metadata | Blender exporter | Godot import/round-trip test | IN PROGRESS |
| BLEND-005 | Versioned non-destructive recipes | Asset recipe service | Save/edit/reopen/regenerate test | PLANNED |
| BLEND-006 | Common platform used by character, world and prop tools | Shared geometry/material/scene/export modules | Three-domain integration test | IN PROGRESS |
| BLEND-007 | Blender not required at installed-app runtime | Installer/bootstrap | Clean launch without Blender executable | PLANNED |
| BLEND-008 | High-quality character generation | Character Foundry | Rig/mesh tests plus user visual review | IN PROGRESS |
| BLEND-009 | World/environment authoring | World tools | Generate location, export, Godot assembly | PLANNED |
| BLEND-010 | Prop/vehicle/furniture authoring | Prop tools | Generate and import representative items | PLANNED |
| GODOT-001 | Godot production pipeline | app engine adapter / engine/godot_worker | Scene save/reopen, animation and render tests | PARTIALLY IMPLEMENTED |
| WEB-001 | Browser/FastAPI orchestration | app/main.py and browser workspaces | Durable job lifecycle and approval tests | PARTIALLY IMPLEMENTED |
| PIPE-001 | Final MP4 production | FFmpeg pipeline | Real episode file playback/duration/audio test | PARTIALLY IMPLEMENTED |
| ACCEPT-001 | User visual acceptance | Review/approval UX | User sees real output and accepts/rejects | PLANNED |

Historical 171-row crosswalk remains a legacy source map and must be reconciled row-by-row with this amendment. Never mark requirements complete based solely on planned file paths.
