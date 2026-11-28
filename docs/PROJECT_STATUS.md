# Project Status — 2026-11-28

## Live checkpoint — 2026-11-28 (real-media run found and fixed a verification defect)

- **The real-media job rendered an MP4.** Its first run (`141010017356`) had Godot render both real scenes, had the bundled LGPL FFmpeg mux them, and then failed final verification because the null muxer has no default subtitle encoder in that build.
- **Second finding, second fix:** the corrected run then measured a 1.000s timeline for a 2s episode. The proof SRT's only cue ends at exactly 1.000s, so the subtitle track ended the pass that measured the duration. `_verify_rendered_mp4` now decodes video and audio only for the duration and verifies subtitles in their own SRT decode pass.
- **Proven by that run:** Godot loads an episode scene from an absolute path outside its temporary project, renders the exact frame count, and the bundled FFmpeg picks a redistribution-safe encoder and muxes the episode.
- **Still open:** the next real-media run has to confirm the corrected verification; `piper-tts` is still outside the locked environment, and generated scenes and produced audio remain proven only by mocked tests.

## Live checkpoint — 2026-11-28 (cache size cap and a real-media render job)

- **The scene cache is bounded.** `SCENE_CACHE_LIMIT_BYTES` (8 GiB per episode) and `_enforce_scene_cache_limit` drop the oldest cached scene movies once the cache passes the limit, so repeated edits at several presets cannot fill the disk.
- **CI now renders a real episode.** A new `real-media` job in `ci.yml` fetches the pinned Godot 4.7.2 runtime and the pinned LGPL FFmpeg, runs `test_real_media_render_produces_a_playable_mp4` (two real scenes, a silent WAV, an Urdu SRT, the real binaries), and uploads the MP4 plus the FFmpeg runtime report as an artifact. The test is gated on `CARTOON_STUDIO_REAL_MEDIA=1`, so the fast job skips it.
- **This is the first execution of that path.** Nothing about it was provable here, so the first run may fail on a real-Godot detail (for example loading an episode scene from outside the temporary render project); its log will show where.
- **Tests:** the cache-limit unit test and the real-media render test.
- **Still open:** `piper-tts` is not in the locked environment, so the shipped app still cannot synthesise Urdu speech; scene generation and audio production remain proven only by mocked tests.

## Live checkpoint — 2026-11-28 (scene cache and restart recovery, Batch C, part 1)

- **A retried or restarted render reuses the scenes it already finished.** `render_episode_video` takes an optional `cache_directory`; each finished scene movie is stored under `assets/episodes/{episode_id}/render_cache/` named by a SHA-256 of the scene's bytes, the frame rate, resolution and duration, and a cache format version. A scene whose key is cached is linked into the render instead of being rendered again, so cancelling or crashing after four of seven scenes costs only the remaining three.
- **An edited scene or a changed preset re-renders only what changed.** The key covers the scene file and the render settings, so `scene-2` edited at High Quality invalidates that scene alone. `SCENE_CACHE_VERSION` invalidates every cached movie when the renderer itself changes.
- **The cache is bounded and stays inside the project.** Only the newest cached version of each scene position is kept, and a cache path outside the project is refused. `render.json` and the job result now record `cached_scene_count` and `rendered_scene_count`, so a render says how much work it skipped.
- **Packages stay small and honest.** Project export omits `render_cache` (rebuildable intermediate movies) while keeping the scenes, documents and assets that matter.
- **Tests:** cache reuse, invalidation of one edited scene, newest-only pruning, the outside-project refusal and the export omission.
- **Verified:** Windows CI passed on `b77c8a2` (job `141008060654`, 1m 54s), including the cache tests. No real Godot runtime, FFmpeg or browser was available in that batch.
- **Still open:** the cache is not size-capped across many edited scenes or many episodes, and a real-media Windows job has still not rendered an episode end to end.

## Live checkpoint — 2026-11-28 (Story page queues renders, subtitle-mode selector)

- **The Story page no longer holds an HTTP request open.** Its visible render control is `#queue-render`: `app/static/story-render-queue.js` posts to `POST /api/projects/{id}/story/render/jobs` and opens `/renderer?project=…`, where progress and cancellation already work. A refused queue request shows the server's message (no saved plan, missing scenes or missing audio) and stays on the page.
- **The synchronous render control is unreachable from the UI:** `#render-episode` is hidden and disabled, kept only for the legacy handler in `story.js`. The synchronous HTTP route remains for API compatibility.
- **Subtitle mode is selectable.** The page's Subtitles selector reflects the pasted plan's `subtitle_mode`; changing it rewrites the plan JSON, invalidates the cached validated plan and states that dialogue audio must be regenerated for the subtitle file to match.
- **Tests:** the page test asserts `#subtitle-mode`, `#queue-render` and the new script are served.
- **Verified:** Windows CI passed on `e5b2e9b` (job `141006605775`, 1m 34s), including the JavaScript syntax check and the page assertions. No browser acceptance.
- **Still open:** `piper-tts` remains outside the locked environment, so the TTS path still needs the lock regenerated and the reported install check from `/api/diagnostics`.

## Live checkpoint — 2026-11-28 (Episode Renderer and Logs workspaces)

- **Episode Renderer workspace** (`/renderer`): queue a render (`202` + poll), see each job's state and `progress/total`, cancel safely, and reach the render details. The browser no longer sits on one long request.
- **Logs and Diagnostics workspace** (`/logs`): Godot/FFmpeg/voice readiness with the chosen redistribution-safe encoder, worker state, schema version, job counts, and a selected job's event journal.
- **Recorded dialogue control** in the Story page: pick a plan line, upload the WAV and see which lines are recorded, backed by the existing per-line endpoint.
- **Navigation:** both workspaces are linked from the dashboard sidebar.
- **Correction:** the quality preset table is `QUALITY_PRESETS` again, matching its tests, after the rename mismatch that broke collection.
- **Tests:** a page test covers both workspaces, the recording panel and the dashboard links.
- **Superseded:** the Story page now queues through the job route and has a subtitle-mode selector (see the newest checkpoint); `piper-tts` still needs the lock regenerated before TTS works offline.

## Live checkpoint — 2026-11-28 (background job execution, progress and cancellation)

- **Real background worker.** `app/worker.py` runs queued operations outside the request thread: it claims, executes, reports progress, honours cancellation between scenes and records completion or failure; `app/main.py` starts it in the lifespan. A render no longer blocks the browser for hours, and closing the tab no longer leaves the work unattended.
- **Progress and cancel are real.** `GET /api/projects/{id}/jobs/{job_id}` now advances per rendered scene (each tick also extends the lease), `POST .../jobs/{job_id}/cancel` stops a running render before its next scene, and a cancelled job keeps the scenes it already rendered.
- **Queueable render.** `POST /api/projects/{id}/story/render/jobs` returns `202` with a job id and its poll/cancel URLs; the synchronous render route remains for compatibility and reports 409 when cancelled.
- **Diagnostics.** `GET /api/diagnostics` reports Godot, FFmpeg (path, chosen redistribution-safe encoder, or why it cannot run), the speech engine (installed or not, with the pinned voices), schema version, job counts and worker state.
- **Tests:** `tests/test_worker.py` plus an app test for the `202` job and diagnostics; the render API test asserts the progress/cancel callbacks.
- **Superseded:** the Episode Renderer and Logs workspaces, the recorded-line control, and the Story page's queued render and subtitle-mode selector have since landed (see newer checkpoints); `piper-tts` still needs the lock regenerated.

## Live checkpoint — 2026-11-28 (recorded Urdu dialogue fallback)

- **Owner decision applied:** voice uses both paths. A dialogue line can now be recorded and used instead of TTS: `PUT /api/projects/{id}/story/audio/lines/{scene}/{line}` stores a mono 16-bit 22,050 Hz WAV under the episode, `GET /api/projects/{id}/story/audio/recordings` lists recorded lines, and `generate_episode_audio` mixes recorded and synthesised lines, recording each clip's `source` and the counts in the audio manifest. A recorded line never calls the speech engine.
- **Format contract:** non-WAV data, empty audio, any other sample format, or a recording that runs past its scene is refused rather than resampled into the mix.
- **Tests:** three API tests and four audio tests cover storing, listing, rejecting and mixing recorded lines.
- **Still open:** `piper-tts` is not in the locked environment, so the TTS path is unavailable until the lock is regenerated by `.github/workflows/resolve-python-lock.yml` and the wheels are vendored into the installer; the Story workspace still needs a record control.

## Live checkpoint — 2026-11-28 (redistribution-safe encoding, bundled LGPL FFmpeg)

- **Owner decisions applied:** video must use a redistribution-licensed encoder, and voice uses both paths (pinned Piper TTS plus a recorded fallback).
- **Encoder policy:** `app/render.py` chooses the first available encoder from `libopenh264`, `libvpx-vp9`, `libaom-av1`, `libsvtav1`, `mpeg4`, and refuses a build whose only video encoder is GPL (`libx264`/`libx265`/`libxvid`). The chosen encoder is recorded in `render.json`.
- **Bundled runtime:** `engine/ffmpeg_runtime.json` pins BtbN's win64 LGPL FFmpeg n8.1 by URL and SHA-256; `scripts/fetch_ffmpeg.py` verifies the hash, the encoders and the licence notices; `_find_ffmpeg` prefers the bundled `engine/ffmpeg/ffmpeg.exe`, so the installed app assembles MP4s without a system FFmpeg. `release-windows.yml` fetches it, adds it to the SBOM and copies it (with notices) into both installer bundles.
- **Tests:** `tests/test_render_encoder.py` covers preference order, the native fallback, GPL-only refusal and bundled-path resolution; the render test asserts VP9 and never `libx264`.
- **Verified:** static review only; the release bundle path is `workflow_dispatch` and is proven only when that workflow is run.
- **Still open (next batch, voice half of the decision):** pin `piper-tts` into the lock via `.github/workflows/resolve-python-lock.yml`, bundle the wheels, and add the per-line recorded-WAV fallback with its endpoint and UI.

## Live checkpoint — 2026-11-28 (episode contract truthfulness: presets, subtitle modes, guards)

- **Quality presets are implemented and read at render time.** `app/quality.py` defines Preview (15 fps, 640x360), Low Hardware (24 fps, 854x480), Balanced (24 fps, 1280x720) and High Quality (30 fps, 1920x1080); new projects default to Balanced. `GET /api/quality-presets` and `GET/PUT /api/projects/{id}/settings` store the preset and derive `frame_rate`/`resolution` from it; `POST /story/render` renders at the stored preset. The Story page has a Render quality selector.
- **Subtitle modes are honoured.** `urdu` writes the dialogue text, `roman_urdu`/`english` write each line's planned `subtitle_text`, `none` writes an empty SRT and the renderer omits the subtitle stream. The audio manifest records the mode and entry count. There is no separate subtitle-mode selector in the workspace yet; the plan field decides.
- **Dead ends removed.** English dialogue is refused at validation instead of failing at audio time (the bundled voices are Pakistani Urdu only); an unsupported `voice_profile` is refused at plan validation; `roman_urdu`/`english` subtitles require `subtitle_text` per line.
- **Verified:** static review only. The next Windows CI run on `main` is the proof.
- **Still blocking:** the installed app cannot synthesise speech or assemble an MP4 — `piper-tts` and FFmpeg are not bundled. See `MASTER_BRIEF_AUDIT_2026-11-28.md` finding B1 and Batch A below.

## Live checkpoint — master-brief consolidation

- **Latest code-bearing checkpoint before this batch:** `49516e57577c74f25c33e3d481e0633fa5c2c724`; Windows CI #618 passed on that exact commit (run `46067945723`). The episode-contract batch above is newer and awaits its own CI run.
- **Latest documentation refresh:** documentation-only `[skip ci]`; it does not change application code.
- The original 25-part Master Brief is committed at `docs/MASTER_EXECUTION_PROMPT.md`; it remains the binding source.
- Registry and traceability contain 171 unique, matching requirement IDs. The registry currently has one VERIFIED requirement (`PHASE-R002`) for the defined Phase 1 installer lifecycle gate; that does not mean the product is complete.
- Current registry status counts: 7 TESTED, 18 IMPLEMENTED, 27 PLANNED, 113 PARTIALLY IMPLEMENTED, 3 RESEARCH REQUIRED, 2 IN PROGRESS and 1 VERIFIED. All 171 traceability source-path references resolve against the current repository tree; behavioral evidence reconciliation is still in progress.
- The consolidation pass is reconciling each completed implementation against source, tests and actual CI evidence. Registry statuses now use only the approved vocabulary; source evidence has been refreshed for local rendering, audio, offline paths, job telemetry and delivered UI foundations. A confirmed World Builder asset-selection persistence defect was fixed in `4b1ed4b`; CI #617 passed the save/reopen/update and adapter regressions. Registry/traceability rows still contain historical mappings and must not be treated as freshly audited merely because their IDs match.
- Confirmed completed slices include Character Studio import/assembly/appearance operations, persistent World Builder documents and 17 object kinds, a curated project-scoped CC0 GLB catalogue connected to scene export, Godot scene generation, Urdu audio/subtitles, FFmpeg MP4 assembly path and durable SQLite job records.
- Acceptance limits remain: actual downloaded GLB rendering/visual acceptance, full vehicle runtime behaviour, arbitrary-rig and character visual acceptance, integrated story-provider generation, reusable animation/blending/timeline, phoneme/viseme Urdu lip-sync, scene-level render cache/restart recovery, complete 5–7 minute episode inspection and target-PC benchmarking.
- CI #615 validates its configured locked install, lint, JavaScript syntax, Python compilation and test steps on `e0e2880`; it does not validate the later documentation-only commit or prove visual/final-product acceptance.

## Current phase table

| Phase | Status | Evidence and open acceptance |
|---|---|---|
| 0 — Specification, research, architecture | COMPLETE | Master brief preserved; 171 atomic requirements and matching traceability; research, architecture and bounded engine/queue proofs recorded |
| 1 — GitHub/CI/CD and Windows delivery | COMPLETE | Reproducible locked dependencies, CI, self-contained installer build and install/upgrade/uninstall/reinstall lifecycle proof |
| 2 — Character Studio | PARTIAL | Modular characters, import, profile persistence, proportions, hair/face geometry, morphs and retargeting implemented; interactive visual signoff and broad rig acceptance remain |
| 3 — World Builder | ACTIVE / PARTIAL | Versioned world docs, templates, scene export, GLB preview and 17 object kinds; visual quality and vehicle runtime behaviour remain |
| 4 — Story and Scene Engine | PARTIAL | Structured prompt/schema, validation, world/cast binding and editable scene generation; integrated generation, approval, repair and complete mapping remain |
| 5 — Animation Engine | PARTIAL | Procedural action/camera/expression tracks; reusable motion library, blending, timeline editor and visual acceptance remain |
| 6 — Urdu Voice and Lip-Sync | PARTIAL | Offline Urdu speech/audio mix and subtitles with urdu/roman_urdu/english/none modes and a heuristic mouth envelope; `piper-tts` is not in the locked environment, so the installed app cannot synthesise speech yet; native-speaker evaluation and phoneme/viseme alignment remain |
| 7 — Episode Generator | PARTIAL | Editable scene generation, audio, Godot/FFmpeg MP4 path rendered at the project's quality preset, a background worker with per-scene progress and cancellation, durable job records and a content-keyed scene cache that reuses finished scenes after a cancel or crash; full episode acceptance and a cache size cap remain |
| 8 — Optimization and Reliability | DEFERRED | Quality presets are implemented and the render, diagnostics and log workspaces exist; target-PC benchmarks, full visual/audio signoff and final production acceptance remain |

## Next implementation batch

1. **Batch A — make the shipped app produce an episode.** Decide and pin the voice path (bundled Piper or recorded fallback), bundle a licence-reviewed FFmpeg, resolve `_find_ffmpeg` to the bundled binary, and add a real-media Windows CI job. This is finding B1 in `MASTER_BRIEF_AUDIT_2026-11-28.md` and the only thing between the current code and a playable episode.
2. **Batch B — real job execution, progress, cancel and diagnostics.** Background worker, per-scene progress, cooperative cancel, Episode Renderer and Logs and Diagnostics workspaces.
3. **Batch C — scene cache and checkpoints**, so one failed scene never re-renders the episode.

World-scene export quality, browser preview visual review and world-linked story production mapping remain open; multi-location reuse via `template_id` is implemented and tested. User visual acceptance for Phases 2–7 is scheduled for Phase 8 per project owner direction.
