# Cartoon Studio

An original, browser-first production studio for creating reusable 3D cartoon characters, worlds and Urdu cartoon episodes. The repository is the source of truth for product requirements, implementation and releases.

## Current strategy

Cartoon Studio uses a coordinated three-part production architecture:

1. **Blender — asset creation foundation.** A shared Blender Python automation/tooling platform creates and edits characters, rigs, clothing, hair, facial geometry, environments, towns, buildings, roads, vegetation, interiors, vehicles, furniture and props. Editable `.blend` sources are retained; approved assets are exported as GLB/glTF with textures and metadata.
2. **Godot 4.7.2 — production engine.** Godot assembles assets into reusable scenes, handles animation, cameras, timeline, previews and production rendering.
3. **Browser + FastAPI — studio control plane.** The web UI manages projects, story plans, asset-generation jobs, recipes, libraries, review/approval and production jobs. FFmpeg assembles final audio/video into MP4.

Blender is not a required runtime dependency of the installed application. Generated GLB assets must remain usable in Godot without Blender installed.

## Existing implementation

The repository already contains a FastAPI/browser application, project persistence, Story Generator foundations, Character Studio, World Builder foundations, a Godot worker/adapter, GLB inspection and export workflows, character recipes and generation code, a Blender toolchain/asset verification path, and FFmpeg/rendering foundations. These systems must be inspected and extended, not recreated. Consult `docs/PROJECT_STATUS.md` for the verified current checkpoint; do not infer completion from this overview.

## Product target

- Original 3D cartoon universe, not copies of protected characters or franchises.
- Urdu-first episodes, typically 5–7 minutes, with editable stories, scenes, dialogue, animation, voices, lip-sync, sound, music and final MP4.
- Reusable character identities and persistent locations across episodes.
- Characters, environments and props created through the shared Blender toolchain.
- Local-first production with no mandatory paid APIs, API keys, quotas or cloud services.
- Hardware-aware preview and render modes; physical-PC testing is not an early development gate.

## Development

Read `AGENTS.md` and the complete authoritative documents in `docs/` before implementation. Work on the feature development line, preserve the old `main`, batch changes and run one CI workflow at a time. User visual acceptance is based on seeing actual generated assets, not screenshot automation.

## Run

The existing Windows launcher/bootstrap instructions are maintained in [docs/BUILD_AND_INSTALL.md](docs/BUILD_AND_INSTALL.md). Blender is used for authoring/generation workflows, not required to launch the installed studio.
