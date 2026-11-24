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
