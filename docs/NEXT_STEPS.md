# Next Steps — 2026-11-28

## Live checkpoint

- Repository: `Pawar-47/Cartoon-Studio`; active branch `main`.
- Newest batch: **Batch E — licensed clip library with baked cross-fades.** A manifest maps action IDs to named glTF clips from an owner-installed CC0 pack; `worker.gd` samples clip bone tracks into the episode timeline with 0.25 s fade-in/out, falling back to procedural poses when no pack is installed. Awaits its own CI run.
- Last green CI: `f4e776f`, both jobs (`test` 1m 57s, job `141054471473`; `real-media` 40s, job `141054471164`) — the pinned Godot staged five scenes across two saved world locations and the bundled LGPL FFmpeg produced a verified MP4.
- Owner decisions on record: no GPL video encoder; voice uses both a pinned Piper TTS path and a recorded-WAV fallback.
- Binding source: `docs/MASTER_EXECUTION_PROMPT.md`, all 25 parts. Do not create or switch development branches.

## Current objective

Close the two production gaps the brief still names for a watchable episode: the animation
library (Part 10) and Urdu lip-sync (Part 14), then pin the voice pack. The persistent universe
now has one vocabulary: a saved world location is a real place that episodes stage scenes in.

## Immediate next steps

1. **Batch F — Urdu lip-sync.** Replace the loudness envelope with a G2P → viseme track plus blink/gaze, and keep the manual correction path the brief requires.
2. **Voice pack.** Pin `piper-tts` and `onnxruntime` through
   `.github/workflows/resolve-python-lock.yml`, vendor the wheels and the two `ur_PK` voices into
   the installer, and prove a real synthesis with `test_real_urdu_tts_sample`.
3. **Props and audio cues (audit D4/D5).** Bind scene `props` to world objects and consume
   `scene.audio` cues with a real mixing stage, or remove the fields until they are consumed.
4. **Settings workspace and asset registry.** The brief's Part 16 still lacks a Settings page
   and an in-app asset/licence registry (audit G7), and Part 12/13 have no runtime (audit B8).

## Recent completed batches

### Batch E — licensed clip library with baked cross-fades

### Batch D — one vocabulary for story, world and production
A world document (schema 1.0.2) carries `locations: [{id, label}]` and each object carries
`location_id` (empty = shared scenery). The API and `GodotEngineAdapter.export_world_scene` refuse
an object whose location is undeclared, and duplicate or malformed location IDs.
`ScenePlan.location_id` accepts a catalog backdrop or `world:<location-id>`; `PUT /story` refuses
an unknown location and a world reference without a world, naming the valid ones; production
refuses a retired location. `worker.gd` keeps only the scene's location plus shared scenery,
places the cast at that location's centre and aims the episode camera at it, reporting
`location_id`/`location_object_count`/`removed_object_count`. `POST /api/story-prompts` takes
`world_locations` and lists them for the model; the World Builder has a Saved Locations panel and
a per-object location selector.

### FFmpeg pinned to a dated release
`engine/ffmpeg_runtime.json` pointed at FFmpeg-Builds' moving `latest` tag, so the archive hash failed as soon as upstream published a new build. It now pins the dated release `autobuild-2026-11-28-13-45`, the exact `ffmpeg-n8.1.3-1004-g8524289d26-win64-lgpl-8.1.zip` asset and its SHA-256 from that release's `checksums.sha256`; `tests/test_ffmpeg_runtime_manifest.py` refuses a non-dated URL, a non-hex hash or a GPL encoder in the allowed list.

### Scene-cache size cap and a real-media render job (Batch C, part 2)
`SCENE_CACHE_LIMIT_BYTES` (8 GiB per episode) plus `_enforce_scene_cache_limit` drop the
oldest cached scene movies once an episode's cache passes the limit. A new `real-media` job
in `ci.yml` fetches the pinned Godot runtime and LGPL FFmpeg and runs
`test_real_media_render_produces_a_playable_mp4`, which renders two real scenes with a
silent WAV and an Urdu SRT through `render_episode_video` and uploads the MP4 and the
FFmpeg runtime report as an artifact.

### Scene cache and restart recovery (Batch C, part 1)
`render_episode_video` takes a `cache_directory`; each finished scene movie is stored as
`scene-NN-<sha256>.avi` keyed by the scene file, frame rate, resolution, duration and
`SCENE_CACHE_VERSION`, and reused through a hard link (or copy) on the next render. An
edited scene or a changed preset invalidates only itself, only the newest version per scene
position is kept, a cache path outside the project is refused, `render.json` records
`cached_scene_count`/`rendered_scene_count`, and portable packages omit `render_cache`.

### Story page queued render and subtitle-mode selector
The Story page's visible render control queues `POST /api/projects/{id}/story/render/jobs`
and hands off to `/renderer?project=…` for progress and cancellation; the synchronous
`#render-episode` button is hidden and disabled, kept only for the legacy `story.js`
handler. A Subtitles selector (`urdu`, `roman_urdu`, `english`, `none`) rewrites the pasted
plan's `subtitle_mode` and invalidates the cached validated plan, and states that dialogue
audio must be regenerated for the subtitle file to match.

### Episode Renderer and Logs workspaces, recorded-line control (Batch C, UI)
`/renderer` queues renders through the `202` job route, shows `progress/total`, cancels
safely and links to the render details; `/logs` shows Godot/FFmpeg/voice diagnostics,
worker state, schema and job counts plus a selected job's event journal; the Story page
gains a recorded-line panel backed by the per-line upload endpoint. Dashboard navigation
lists both workspaces. The `QUALITY_PRESETS` naming mismatch that broke test collection is
fixed.

### Background job execution, progress and cancellation (Batch B)
`app/worker.py` runs queued operations in one background thread with progress, cancellation
between scenes and failure recording; `JobQueue` gains `report_progress`, `cancel_requested`
and `mark_cancelled`; `app/render.py` accepts `progress_callback`/`cancel_check`; the render
route body is shared by the synchronous route and the worker handler; `POST
/api/projects/{id}/story/render/jobs` returns `202` with poll/cancel URLs; `GET
/api/diagnostics` reports Godot, FFmpeg, voice, schema, job counts and worker state.

### Recorded Urdu dialogue fallback (Batch A, voice half)
`PUT /api/projects/{id}/story/audio/lines/{scene_id}/{line_index}` stores a mono 16-bit
22,050 Hz WAV for one dialogue line (20 MiB limit, scene-boundary check); `GET .../audio/recordings`
lists recorded lines; `generate_episode_audio(..., recordings=...)` mixes recorded and
synthesised lines and reports `recorded_line_count`/`tts_line_count` in the audio manifest.
A recorded line works with no speech engine installed.

### Redistribution-safe encoding and bundled LGPL FFmpeg
No GPL encoder is bundled or used. `app/render.py` selects `libopenh264`, `libvpx-vp9`,
`libaom-av1`, `libsvtav1` or native `mpeg4` from the build's encoder list and refuses a
GPL-only build; the chosen encoder is recorded in `render.json`. `engine/ffmpeg_runtime.json`
pins a dated win64 LGPL FFmpeg n8.1 release by URL and SHA-256; `scripts/fetch_ffmpeg.py` verifies
the hash, encoders and licence notices; `_find_ffmpeg` prefers the bundled
`engine/ffmpeg/ffmpeg.exe`; the release workflow fetches it, adds it to the SBOM and copies
it with its notices into both installer bundles.

### Episode contract truthfulness — presets, subtitle modes, guards
Four quality presets in `app/quality.py`, stored in the project document and read by
`POST /story/render` (Preview 15 fps/640x360, Low Hardware 24/854x480, Balanced 24/1280x720
— the default — High Quality 30/1920x1080), with `GET /api/quality-presets`,
`GET/PUT /api/projects/{id}/settings` and a Render quality selector on the Story page.
`subtitle_mode` is honoured end to end (urdu / roman_urdu / english / none). English
episodes and unsupported voice profiles are refused at validation.
