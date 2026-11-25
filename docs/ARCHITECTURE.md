# Architecture — Initial Baseline

## Working foundation
- Browser UI: static HTML/CSS/JavaScript served by FastAPI.
- Local API: FastAPI.
- Project metadata: SQLite.
- Data path: configurable with CARTOON_STUDIO_DATA.
- CI: GitHub Actions Windows runner.
- First artifact: bootstrap ZIP, not a standalone installer.

## Target modules (research-dependent)
1. Project/workspace service — persistent metadata, versioned project documents and assets.
2. Story service — provider-neutral prompt processing and structured scene schema.
3. Character service — reusable definitions, model references, rig metadata, expressions and voice profiles.
4. World service — persistent sets, locations, props and layouts.
5. Asset registry — source, license, checksum, format, version and local cache.
6. Animation service — clip catalog, rig compatibility, retargeting, blending and timeline.
7. Voice service — pluggable Urdu TTS and recorded-voice fallback.
8. Lip-sync service — cue/viseme adapter and face-rig mapping.
9. Render orchestrator — scene jobs, Blender adapter, progress, retries, cache and recovery.
10. Media assembly — FFmpeg adapter for audio, captions and MP4.
11. AI provider adapters — official APIs where permitted; manual handoff otherwise.
12. Research agent — evidence-backed search and evaluation.

Do not lock the 3D engine until source review and hardware proofs are complete. Do not use browser rendering for final episodes. GitHub Actions builds/tests/packages; local production rendering is separate.

## Initial API
GET /api/health  
GET /api/status  
GET /api/projects  
POST /api/projects


## Current schema caveat — corrective action required

The current `app/story.py` validates `location_id`, `action_id` and expression values against hard-coded catalogs copied/derived from the unapproved Ara candidate. These identifiers are currently useful only for validating the early Story Generator prototype. They are not approved Cartoon Studio canonical IDs and must not become the permanent project format. During Phase 0 architecture freeze, define stable engine-neutral Cartoon Studio identifiers and explicit engine adapters. During Phase 4, migrate the existing schema and tests to those contracts. Preserve the existing story data and UI; do not discard or rewrite the foundation wholesale.

## P0.3 research findings — not yet frozen

A plausible candidate architecture is a browser-first FastAPI UI, a local engine adapter, a background renderer and a durable SQLite stage/job store. Blender 4.5.17 LTS is under evaluation as a local production engine, while Three.js-based editors (Ara/Ekza) remain browser-editor candidates. This is not a decision: the target i3-5005U is below Blender's published CPU minimum and HD 5500 has a documented Intel driver risk.

Bene Procgen Maps and Blender Level Architect are world-generation candidates; MPFB2/CharacterCreator are character-generation candidates; Parrot/Allosaurus and Charley3d are lip-sync research candidates. Their GPL obligations and target compatibility must be reviewed before integration. FFmpeg must be pinned to a known license/configuration; the default LGPL build differs from builds enabling GPL codecs.

Do not mix engine-specific identifiers into canonical project data. Use stable Cartoon Studio IDs, versioned asset/scene contracts and adapters only after P0.5. Keep provider/TTS optional, local-first and replaceable. No engine or queue is selected at this checkpoint.

## P0.3 Godot candidate architecture — not yet frozen

Godot 4.7.2 Compatibility renderer is now the leading on-paper runtime candidate for the target i3-5005U/HD 5500/8 GB machine. A Godot-native environment stack is under review: Terrain3D for terrain/foliage, Road Generator for roads/lanes, Building Generator for low-poly structures, Roommate for interiors, and a Cartoon Studio-owned toon shader. Imported GLB assets and an original modular character editor may avoid making Blender a mandatory runtime dependency.

The existing FastAPI/SQLite project/story backend and browser UI must be preserved. P0.5 must compare three integration paths: (1) Godot as the native app/editor shell with FastAPI as local service, (2) Godot as a local renderer sidecar controlled by the browser UI, or (3) Godot Web export embedded as a browser viewport. Each has IPC, memory, windowing and performance trade-offs.

Blender 4.5.17 remains an optional asset-authoring candidate, not the current target-runtime leader. Godot plugins are candidates only; their individual licenses, versions, renderer support, scene sizes and target-PC performance must be verified. No engine is selected at this checkpoint.
