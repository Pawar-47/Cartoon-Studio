# Dependency Decisions — Blender-First

## Core decisions
| Area | Decision | Boundary |
|---|---|---|
| Backend | Existing Python 3.11+ / FastAPI / SQLite | Preserve current API and project persistence |
| Browser | Existing lightweight HTML/CSS/JS | Do not add framework without concrete benefit |
| Asset authoring | Blender Python API | Shared interactive/headless toolchain; not app runtime |
| Production engine | Godot 4.7.2 Compatibility | Scene assembly, animation, camera/timeline, preview and rendering |
| Interchange | glTF 2.0 / GLB | Blender editable source remains .blend |
| Video | FFmpeg | Final MP4/audio assembly |
| AI | Optional provider adapters/manual handoff | No mandatory API key, paid plan or quota |
| Jobs | Existing persistent queue foundation | Durable progress, cancellation, retry and recovery |

## Blender version policy
Select and pin a Blender release only after checking Python API compatibility, platform support, CI availability, add-on compatibility and actual generated output. Do not assume the user's Intel HD 5500 laptop can run all authoring workloads. Keep Blender version/capability metadata in each asset manifest.

## Licensing
Blender is GPL-3.0. Use it as an external application/toolchain; do not bundle or redistribute it without legal review. Do not use MPFB as the product foundation or copy its GPL code. Each add-on, model and asset has its own license.

## Existing components
Keep the current FastAPI, SQLite, Godot worker, Three.js preview, Quaternius/Kenney catalogues, Blender modules and FFmpeg path. Do not replace working components without evidence and migration planning.
