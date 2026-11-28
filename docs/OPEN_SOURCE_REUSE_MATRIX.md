# Open-Source Reuse Matrix — Current Decisions

| Component | Role | Decision |
|---|---|---|
| Blender Python API | Shared 3D asset authoring/generation | Core platform; external authoring tool, not required app runtime |
| Godot 4.7.2 | Production scenes, animation, camera/timeline, preview/render | Retain existing pinned worker and adapter |
| GLB/glTF | Blender-to-Godot interchange | Default asset format |
| FastAPI/browser | Control plane | Retain existing app |
| FFmpeg | Final MP4/audio assembly | Retain existing pipeline foundation |
| Quaternius CC0 | Optional modular character source assets | Keep exact pack provenance and hashes |
| Kenney CC0 | Optional props/environment source assets | Keep exact pack provenance and hashes |
| MPFB | Character generation foundation | Explicitly rejected; do not use as product base or copy GPL code |
| Ara 3D Gen | Full browser studio candidate | Historical research only; not primary architecture |
| Blender add-ons | Domain-specific accelerators | Evaluate per exact code/asset license; no automatic adoption |

A candidate is not integrated merely because it appears here. Record exact commit/version, license, modifications, test result and provenance for every adopted component.
