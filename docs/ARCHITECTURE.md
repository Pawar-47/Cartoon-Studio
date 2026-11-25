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

Do not lock a production 3D engine until source review and architecture-critical P0.6 proofs are complete. Physical target-PC benchmarking is not an architecture gate and is scheduled for Phase 8. Do not use browser rendering for final episodes unless a later proof establishes a production-quality export path. GitHub Actions builds/tests/packages; local production rendering is separate.

## Initial API
GET /api/health  
GET /api/status  
GET /api/projects  
POST /api/projects


## Current schema caveat — corrective action required

The current `app/story.py` validates `location_id`, `action_id` and expression values against hard-coded catalogs copied/derived from the unapproved Ara candidate. These identifiers are currently useful only for validating the early Story Generator prototype. They are not approved Cartoon Studio canonical IDs and must not become the permanent project format. During Phase 0 architecture freeze, define stable engine-neutral Cartoon Studio identifiers and explicit engine adapters. During Phase 4, migrate the existing schema and tests to those contracts. Preserve the existing story data and UI; do not discard or rewrite the foundation wholesale.

## P0.3 research findings — not yet frozen

A plausible candidate architecture is a browser-first FastAPI UI, a local engine adapter, a background renderer and a durable SQLite stage/job store. Blender 4.5.17 LTS is under evaluation as a local production engine, while Three.js-based editors (Ara/Ekza) remain browser-editor candidates. This is not a decision: the target i3-5005U is below Blender's published CPU minimum and HD 5500 has a documented Intel driver risk. These source-based risks inform the design but do not block architecture or implementation; benchmark the completed representative workflow in Phase 8.

Bene Procgen Maps and Blender Level Architect are world-generation candidates; MPFB2/CharacterCreator are character-generation candidates; Parrot/Allosaurus and Charley3d are lip-sync research candidates. Their GPL obligations and target compatibility must be reviewed before integration. FFmpeg must be pinned to a known license/configuration; the default LGPL build differs from builds enabling GPL codecs.

Do not mix engine-specific identifiers into canonical project data. Use stable Cartoon Studio IDs, versioned asset/scene contracts and adapters only after P0.5. Keep provider/TTS optional, local-first and replaceable. No engine or queue is selected at this checkpoint.

## P0.3 Godot candidate architecture — not yet frozen

Godot 4.7.2 Compatibility renderer is now the leading source-based runtime candidate for the target i3-5005U/HD 5500/8 GB machine. No physical-PC benchmark is required before architecture freeze. A Godot-native environment stack is under review: Terrain3D for terrain/foliage, Road Generator for roads/lanes, Building Generator for low-poly structures, Roommate for interiors, and a Cartoon Studio-owned toon shader. Imported GLB assets and an original modular character editor may avoid making Blender a mandatory runtime dependency.

The existing FastAPI/SQLite project/story backend and browser UI must be preserved. P0.5 must compare three integration paths: (1) Godot as the native app/editor shell with FastAPI as local service, (2) Godot as a local renderer sidecar controlled by the browser UI, or (3) Godot Web export embedded as a browser viewport. Each has IPC, memory, windowing and performance trade-offs.

Blender 4.5.17 remains an optional asset-authoring candidate, not the current target-runtime leader. Godot plugins are candidates only; their individual licenses, versions, renderer support, scene sizes and target-PC performance must be verified. No engine is selected at this checkpoint.

## Character and asset strategy candidate — not frozen

A low-hardware Godot Character Studio can be evaluated using a recipe-based model: one stable humanoid skeleton, swappable CC0 head/body/outfit/accessory GLBs, material recoloring, a JSON character definition and GLB export. Quaternius Universal Base Characters, Modular Character Outfits and UAL/UAL2 provide a starting point for bodies, clothing and 250+ animations. Cartoon Studio must create its own persistent IDs, face-expression/viseme controls, Pakistani clothing variants and character consistency layer; no unlicensed character-builder code is copied.

A Godot-native world proof can combine Terrain3D, Road Generator, Building Generator and Roommate with exact CC0 Quaternius city/street/building/interior/vehicle packs. Use LODs and asset instancing; test draw calls, object count, texture memory and scene load time on the HD 5500. No asset is imported into the production repository before engine freeze and per-pack license manifest.

## Episode audio and video output candidate

Use Godot's built-in AnimationPlayer audio tracks and Audio Buses to arrange dialogue, ambience, music and SFX. Store each track as a versioned asset reference with start/end, gain, fade, loop and source/license metadata. Keep dialogue separate from music/SFX for later mix and ducking.

Use Godot Movie Maker mode with fixed FPS and non-real-time rendering. Render scene chunks independently so a crash does not force a full-episode rerender. For exported builds, begin with AVI/MJPEG chunks below 4 GB or PNG+WAV chunks; OGV is editor-build only. Assemble/normalize/mix with a pinned FFmpeg build and export MP4. A custom GDExtension MovieWriter that pipes frames to FFmpeg is a later optimization, not a Phase 0 assumption.

FFmpeg must be built without GPL/nonfree components unless the project license decision explicitly permits them. OpenH264 (BSD) is a possible H.264 encoder, subject to quality/bitrate tests and patent review. Record codec, encoder version, configure flags and licenses in the build manifest.

For audio assets, maintain a local catalog with stable IDs, source, exact pack license, author, attribution, duration, loop points and Content ID status. Kenney CC0 packs cover SFX/stingers but not a complete soundtrack; OpenGameArt CC0 tracks require per-track checks. Preserve manual music import and original soundtrack options.

## Humanoid face, emotion and Urdu lip-sync candidate

Use VRM 1.0 or a compatible Cartoon Studio expression schema for humanoid character assets. Standard presets cover emotions (happy, angry, sad, relaxed, surprised), five vowel visemes (aa, ih, ou, ee, oh), blink and gaze; custom expressions and overrides prevent lip-sync from fighting emotion/blink. Every character must provide its own valid morph targets; the schema does not create facial geometry.

Candidate pipeline:
1. Text: normalize Urdu script and obtain phonemes using eSpeak NG `ur` rules for offline G2P; retain the original Urdu text.
2. Voice: prefer human recording or an approved natural Urdu TTS provider; eSpeak NG is only an offline placeholder/emergency voice.
3. Timing: use actual audio-to-phone/forced-alignment evidence (Allosaurus is a candidate, not proven); never apply eSpeak text durations blindly to a different voice recording.
4. Mapping: map Urdu phones to a compact viseme set plus custom mouth shapes, then animate VRM/Cartoon Studio expression weights.
5. Editing: expose a manual timeline for viseme correction, emotion layering, blinks and gaze.

Godot VRM/MToon is a candidate import/export and shading path. Keep non-humanoid characters on GLB/custom rigs. Do not bundle VRM sample avatars; preserve each external avatar's license metadata.

## Revised Urdu voice and lip-sync candidate pipeline

- **Text/G2P:** eSpeak NG `ur` rules provide local Urdu phoneme conversion. Its formant voice is only a placeholder; keep human recording and optional natural TTS.
- **Audio alignment:** WhisperX's current source maps Urdu to an Apache-2.0 300M Wav2Vec2 Urdu model and can return word/character timings. It is not phoneme-level; full WhisperX is heavy, so investigate a minimal align-only implementation.
- **Viseme conversion:** map aligned Urdu characters/words through eSpeak G2P into a compact Urdu phoneme/viseme table, then drive VRM/Cartoon Studio expression weights. This is an experimental approximation; actual coarticulation and timing must be manually correctable.
- **Alternative phone recognition:** Allosaurus universal model may provide phone labels with approximate timestamps; verify Urdu inventory and quality before use.
- **Fallbacks:** manual voice recording, word/character alignment, and manual mouth-keyframe correction. Do not claim automatic lip-sync quality until a native Pakistani Urdu sample is reviewed.


## Hardware-aware architecture policy — 2026-11-25

- Use the published hardware profile to constrain memory use, background concurrency, asset density and renderer/API selection from the start.
- Do not block architecture, implementation or phase completion on the user's physical PC. Source-based compatibility and bounded architecture proofs suffice for earlier decisions when unknowns are explicit.
- Keep Preview, Low Hardware, Balanced and High Quality modes. Quality changes may reduce resolution, samples, effects, concurrency or render speed, but must not silently remove required features.
- Design for sequential/chunked rendering, asset reuse, scene caching, resumable jobs and memory/disk monitoring.
- Run representative-scene benchmarks and tune modes in Phase 8 / P8.1. Until then, publish no FPS or episode render-time promises.


## P0.5 architecture direction — draft for review and P0.6 proof

### Control plane and rendering boundary
Preserve the existing FastAPI + browser UI as the application control plane. FastAPI owns project lifecycle, validation, local persistence, job scheduling, provider adapters and status reporting. The browser remains the main workflow UI. 3D functionality is isolated behind a versioned engine adapter; engine-specific files and IDs never become canonical project data.

**Preferred integration pattern:** a hybrid Godot adapter. An optional Godot Web export may provide an embedded interactive viewport in the browser using WebAssembly/WebGL 2 and a narrow JavaScriptBridge contract. A pinned native Godot build is the candidate scene-import/render worker, supervised by the local backend with versioned file inputs/outputs and bounded local IPC. Both targets consume the same engine-neutral manifests. Exact worker lifecycle, viewport transport and MovieWriter behavior remain subject to P0.6; do not assume headless mode provides GPU rendering or native viewport embedding works automatically.

### Integration-path comparison
| Path | Benefits | Costs / constraints | Current decision |
|---|---|---|---|
| Godot replaces the UI as a native application shell | Direct native rendering and one executable experience | Rebuilds existing browser workflow; duplicates project/API logic; risks discarding working FastAPI/SQLite foundation | Reject as primary path |
| Native Godot sidecar controlled by FastAPI/browser | Preserves current UI/backend; native engine can own scene import and local rendering; clean adapter boundary | Process supervision, IPC, packaging and viewport/window integration need proof | Preferred production-render boundary |
| Godot Web export embedded as viewport | Browser-integrated interactive 3D; JavaScriptBridge can exchange data with host page | WebAssembly/WebGL 2, browser memory/threading/header constraints and browser lifecycle/filesystem limits | Optional viewport target, not sole production renderer |

Godot Web export requires WebAssembly and WebGL 2; JavaScriptBridge is available in Web exports. Threaded web builds have cross-origin-isolation/header constraints. The Godot Web editor is preliminary and is not our product editor. Native command-line export/import supports reproducible build operations but does not prove GPU rendering behavior. References: https://docs.godotengine.org/en/4.7/tutorials/export/exporting_for_web.html ; https://docs.godotengine.org/en/4.7/classes/class_javascriptbridge.html ; https://docs.godotengine.org/en/4.7/tutorials/editor/using_the_web_editor.html ; https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html

### Service boundaries
1. Application/API: FastAPI routes, validation, project commands and status.
2. Project repository: SQLite index plus versioned JSON documents and file assets.
3. Character: identity, appearance recipe, rig/face/expression refs and persistent voice profile.
4. World: locations, reusable sets, props, environment and placement data.
5. Story/scene: prompt requests, canonical episode/scene documents, continuity and approval.
6. Asset registry: stable IDs, file hashes, origin, license, attribution, format and version.
7. Engine adapter: maps canonical IDs to engine resources; validate/import/preview/render/cancel/status.
8. Animation: stable action/clip IDs, rig compatibility, timing, transitions and manual overrides.
9. Voice/audio: recorded/provider speech, alignment, visemes, tracks, mixing and subtitles.
10. Job orchestrator: durable queue, bounded render workload, checkpoints, retries, cancellation and recovery.
11. Media assembler: pinned FFmpeg adapter for scene chunks, audio, subtitles and final MP4.
12. Provider adapters: story/research/TTS/alignment capabilities; secrets never enter project docs.

### Canonical envelope and entities
Persistent documents use UTF-8 JSON, explicit schema version, stable opaque IDs and UTC timestamps. Envelope fields: schema_version, document_type, id, revision, created_at, updated_at, data. IDs are Cartoon Studio-owned; labels may change, IDs do not. Canonical entities are Project, Character, World, Location, Episode, Scene, AnimationClip, AudioCue, Asset and RenderJob. Required fields and invariants are specified in ARCHITECTURE_CONTRACTS.md.

### Storage, recovery, API and security
SQLite is the transactional index for project IDs, document revisions, asset metadata, jobs/events and migration versions. Portable JSON documents and binary media remain ordinary project files; large media is not stored as SQLite blobs. Use a migration ledger, backups before migrations, one render job at a time initially, scene-level checkpoints, idempotent stage retries and startup reconciliation. Keep CARTOON_STUDIO_DATA; packaged default moves to user application data in Phase 1. Preserve existing endpoints while introducing /api/v1. Engine IPC binds to loopback with per-process random authentication. Validate project-relative paths/archive extraction; keep provider secrets outside project files, SQLite metadata and Git.

### Honest implementation boundary
This is a target architecture, not a claim about current code. Current implementation remains project metadata + one saved story plan per project, FastAPI routes and static UI. Asset registry, migrations, render queue, engine/provider adapters, scene renderer and recovery are not implemented. Existing Ara-derived catalogs are prototype validation only and will be replaced with stable Cartoon Studio IDs in Phase 4.


## P0.5 dependency decisions and implementation boundaries

The dependency-level choices and unresolved adoption gates are maintained in DEPENDENCY_DECISIONS.md. The complete requirement-to-module ownership crosswalk is maintained in ARCHITECTURE_TRACEABILITY.md.

Architecture direction is now concrete:
- Retain Python 3.11+, FastAPI/Uvicorn, Pydantic, stdlib SQLite and the existing vanilla browser UI; lock exact versions for releases in Phase 1.
- Treat Godot 4.7.2 Compatibility as the leading native worker candidate, subject to P0.6 functional proofs. A Web export is optional and cannot be the sole production renderer.
- Start with an application-owned SQLite job queue rather than adding an external task framework; preserve per-scene checkpoints and idempotent retry semantics.
- Use an FFmpeg process adapter, but do not bundle a binary or freeze an MP4 encoder until exact build flags, codec availability and licensing are checked.
- Keep AI/TTS optional, manual Pakistani Urdu recording supported, and model/asset adoption individually licensed.
- Actual PC performance measurements are Phase 8 only and do not gate any earlier phase.

## P0.6 result — Godot native worker selected

Godot 4.7.2-stable with the Compatibility renderer is selected as the production 3D runtime, behind the native worker adapter controlled by FastAPI. The bounded proof imported a self-generated GLB, created/played an AnimationPlayer track, saved/reopened the PackedScene, and recorded a 3-second 640×360/24 FPS MJPEG AVI. FFmpeg then assembled a 640×360/24 FPS MP4 with MPEG-4 Part 2 video and AAC audio. Exact CI evidence and limitations are in P0_6_PROOF_REPORT.md.

The optional Godot Web viewport is deferred; it is not a prerequisite for the browser control plane or production rendering. The browser remains the primary UI. A separate native preview window or a future browser viewport can be implemented behind the same engine-neutral adapter without changing project documents. Target-PC performance remains Phase 8.

## P2.2 Character Studio import/profile implementation — 2026-11-25

The first production slice keeps the project format engine-neutral and uses the existing Godot worker only as a supervised importer/inspector.

- Browser route: `/characters`; project selection scopes every operation.
- Upload: raw binary GLB 2.0 request body, maximum 512 MiB, generated UUID storage name under `projects/<id>/assets/characters/`, original filename retained only as metadata.
- Validation: GLB magic, version, declared total length, first JSON chunk, glTF asset version and array shape are checked before Godot import. SHA-256 is recorded for provenance.
- Inspection: the pinned Godot worker reports mesh, Skeleton3D, AnimationPlayer, animation and node counts. Rig-ready and animation-ready flags are based on those reports.
- Identity: each character is a versioned `characters/<uuid>.json` document with stable ID, canonical imported asset reference and fields for face/body, height, hair, clothing, accessories, eyes/mouth, expression labels, personality, relationships, voice profile and dialogue style.
- Project integration: `project.json.data.references.characters` stores stable character IDs. The SQLite document index can be reconstructed from the portable character JSON files.
- No imported character assets are bundled with the application; uploaded user assets remain local to their project.

Limitations are explicit: this slice does not create or edit meshes, rig a skeleton, edit materials/blend shapes, provide a live 3D viewport/thumbnail, export modified GLB, or import VRM. Those are still required work for the full Character Studio phase.


## P2.2 browser-side GLB preview — 2026-11-25

The Character Studio preview uses a pinned local copy of three.js 0.187.0 (upstream tag r187, commit `7e89746a687bb88271253698fa108b1dd59825d0`, MIT). The browser loads GLB data through the vendored GLTFLoader and presents a lit orbitable preview with embedded animation selection. OrbitControls supports pointer/touch orbit and zoom.

- All viewer modules are served locally from `app/static/vendor/three/`; no CDN or runtime network request is required.
- The three.js version, source commit, file inventory and MIT license are recorded in `third_party/threejs-runtime.json`, `LICENSES/three.js/LICENSE` and the CycloneDX SBOM.
- Imported assets are fetched only from the selected local project via the new project-scoped asset endpoint.
- Godot remains the authoritative import/inspection worker. Three.js is the browser presentation layer, not a replacement for the engine or a claim of rig editing.
- Browser preview requires WebGL 2. Compressed GLB extensions requiring external Draco/Meshopt decoders are not bundled in this slice; such assets may import in Godot but fail browser preview with an explicit status.
- Preview does not modify the source GLB. Mesh editing, material editing, rig editing, expression editing and export remain separate work.
