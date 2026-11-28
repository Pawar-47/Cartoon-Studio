# Master Brief Audit — 2026-11-28

**For the integrating AI coder.** This document is an audit of the repository at `main`
(`a88379f`, green Windows CI job `140713831551`) measured against the binding 25-part
master brief preserved at `docs/MASTER_EXECUTION_PROMPT.md`.

> **Status update (same day, later batches).** Findings **D1, D2, D3, D6 and B10 are fixed on
> `main`**: the four quality presets are stored and read by the renderer, `subtitle_mode`
> is honoured end to end (urdu / roman_urdu / english / none), English episodes and
> unsupported voice profiles are refused at validation, and `roman_urdu`/`english` subtitles
> require a per-line `subtitle_text`. **The FFmpeg half of B1 is fixed:** no GPL encoder is
> bundled or used, the video encoder is chosen from a redistribution-safe preference list at
> render time, and the installer now carries a hash-pinned LGPL FFmpeg build that
> `_find_ffmpeg` prefers. **B2 is largely fixed:** a background worker executes renders
> with per-scene progress and cooperative cancellation, and the Episode Renderer and Logs
> workspaces use the job endpoints and `/api/diagnostics`; a recorded-WAV dialogue fallback
> also works without any speech engine. **The synchronous Story-page render path is now
> closed in the UI:** the page queues the job, hands off to `/renderer` for progress and
> cancellation, and carries a subtitle-mode selector. **The scene cache and restart
> recovery are implemented:** each finished scene movie is cached under the episode by a
> SHA-256 of the scene and its render settings, reused on the next render, and excluded
> from portable packages. **A real-media render job now exists:** CI fetches the pinned
> Godot runtime and LGPL FFmpeg and renders two real scenes into a verified MP4, uploading
> it as an artifact — the first execution of that path is the next run, and its log decides
> whether B1's rendering claim holds. **That first run already proved the render chain:** the
> pinned Godot rendered both real scenes and the bundled LGPL FFmpeg muxed the MP4; the only
> failure was final verification, whose null muxer needs no subtitle encoder when the stream
> is copied (fixed). **The voice half of B1 and the remaining B3–B9 items
> stay open**, starting with `piper-tts` not being in the locked environment.

Every finding has an ID, the evidence that produced it, the brief clause it violates,
the required action, and the test that proves the action landed. Treat each finding as a
claim to re-verify against the live tree before you change anything: nothing here was
executed on a Windows host, a Godot runtime, a browser or a Piperian environment. All
statements below come from reading the code, workflows and documents at `a88379f`.

Read `docs/MASTER_EXECUTION_PROMPT.md`, `docs/MASTER_PLAN.md`,
`docs/REQUIREMENTS_REGISTRY.md` and `docs/REQUIREMENT_TRACEABILITY.md` before acting on
this document, as brief §2.6 requires.

---

## 0. Audit basis

| Item | Value |
|---|---|
| Repository | `Pawar-47/Cartoon-Studio` |
| Branch / commit audited | `main` @ `a88379f` |
| Last green CI | job `140713831551`, 1 m 48 s, all steps passed |
| Brief audited | `docs/MASTER_EXECUTION_PROMPT.md`, 1,133 lines, SHA-256 `541098ee…c35c9ddfde` |
| Files read for this audit | `app/main.py`, `app/storage.py`, `app/job_queue.py`, `app/audio.py`, `app/render.py`, `app/engine.py` (selected regions), `app/desktop.py`, `app/story.py`, `app/static/*.html`, `app/static/story.js`, `app/static/characters.*`, `pyproject.toml`, `requirements.txt`, `start.bat`, `.github/workflows/{ci,release-windows}.yml`, `installer/cartoon-studio.nsi`, `engine/godot_runtime.json`, `engine/godot_worker/worker.gd` (face/scene regions), `tests/test_render.py`, `tests/test_audio.py`, and the whole of `docs/` |
| Not available to the auditor | Windows host, Godot runtime, FFmpeg, Piper voices, a browser, a target PC |

**Method.** For each brief part, locate the code path that claims to satisfy it, read that
path, and ask one question: *can a user of the shipped Windows artifact do this today?*
Documentation claims were checked against code, not accepted from the docs.

---

## 1. Executive verdict

The repository is a **well-built foundation with a partly real production chain**, and it is
**not yet an episode-producing studio**. Three statements are simultaneously true and each
matters:

1. **Real and tested by Windows CI:** project/document storage with numbered migrations,
   portable `project.json`, story-plan schema/validation/save/reload, GLB import and
   inspection through a pinned Godot 4.7.2 worker, modular CC0 character assembly and
   export, appearance baking, hair/proportion/face geometry, retargeting with pose
   verification, world layout persistence with a versioned schema, world-scene export,
   episode-scene generation, DDL job bookkeeping, project export/import, a self-contained
   PyInstaller + NSIS installer, and a hash-locked dependency pipeline.
2. **Implemented but never exercised for real in CI:** final MP4 assembly
   (`app/render.py`) — the only test mocks both Godot and FFmpeg; Urdu speech synthesis
   (`app/audio.py`) — the only test uses a fake synthesizer and the real dependency is not
   installed anywhere.
3. **Absent:** the visual workspaces the brief demands (11 of 16), the animation library,
   lip-sync/visemes, music/SFX production, scene caching and checkpoints, in-UI progress
   and cancellation, the asset/licence library, the research agent, the AI resource
   manager, settings and diagnostics, and a published GitHub Release.

**The single most important finding (B1):** *the application that the installer delivers
cannot produce an episode.* There is no TTS dependency in the locked environment, so
`POST /story/audio` cannot succeed; and without audio there is no subtitles file, and
`POST /story/render` refuses to run. Even with audio, FFmpeg is not bundled, so the MP4
step fails on a machine that has never installed FFmpeg. This is the gap between
"pipeline code exists" and brief §23 item 18 ("complete MP4 episode assembly") — and it is
the reason Phases 6–7 cannot honestly close.

**Honesty assessment.** The documents are unusually careful about not claiming unproven
features (no requirement is marked `VERIFIED` except Phase 1, which has installer evidence).
The failures are therefore not fabrication; they are *staleness and dead ends*: schema
fields and UI controls that nothing consumes, and registry rows still describing a project
that no longer exists in that shape. Section 7 lists them precisely.

---

## 2. Compliance matrix — the 25 brief parts

Legend: **MET** = implementable by the shipped app today; **PARTIAL** = mechanism exists,
delivery or acceptance missing; **MISSING** = no implementation; **DOC-ONLY** = research or
policy document only.

| Part | Subject | Status | Evidence / gap |
|---|---|---|---|
| 1 | Role, authority, responsibility | MET (as operating behaviour) | `AGENTS.md`, `docs/MASTER_PLAN.md`, registry and per-batch commits show the lead-agent model in use |
| 2 | Full-prompt compliance protocol | PARTIAL | Registry + traceability exist (171 rows each); status vocabulary is violated (G1) and many rows are stale (G2); no automated checkpoint report per §2.4 |
| 3 | Product vision (prompt → 5–7 min MP4) | PARTIAL | Every hop exists as code; the end-to-end chain is unproven (B1) and unvalidated at 5–7 minutes |
| 4 | GitHub-first development | PARTIAL | Repo, workflows, tests, packaging present; no GitHub Release (G5); release workflow is manual-only; heavy artifacts expire in 14/30 days |
| 4.3 | Windows delivery without manual env setup | **MISSING as delivered** | Installer bundles Godot + worker but not FFmpeg and not Piper (B1, B2); `start.bat` bootstrap ships no engine at all (M1) |
| 4.4 | Builds separate from production rendering | MET | CI does build/test/package only; no GPU rendering on hosted runners |
| 5 | Extensive GitHub research before building | PARTIAL | `GITHUB_RESEARCH.md`, `REPOSITORY_EVALUATION.md`, `OPEN_SOURCE_REUSE_MATRIX.md`, `CANDIDATE_SCORECARD.md` are substantive and source-level; several later modules (lip-sync, toon shading, music) have no new research since P0.3 |
| 5.1 | Evaluate each candidate on 12 axes | PARTIAL | Strong for engines/character/TTS; not applied to the animation-library and music/SFX candidates, which are unimplemented |
| 5.2 | Reuse hierarchy | MET | Quaternius CC0 assets, Godot runtime, three.js vendored and pinned; no wholesale copying |
| 5.3 | Research deliverables | MET | All four documents exist and are kept |
| 6 | Hardware/performance and 4 quality presets | **MISSING** | Render is fixed 24 fps / 1280×720 / no sample or effect control (`app/render.py` constants); `quality_preset` is stored in every project document but read by nothing (D1). Presets are honestly marked PLANNED, but the stored field misleads |
| 7 | Application architecture | MET | FastAPI + browser + SQLite + supervised Godot worker + FFmpeg process adapter, all as frozen in P0.7 |
| 8 | Persistent cartoon world | PARTIAL | World documents, stable IDs, schema migration, templates, vehicle motion/interaction/rig endpoints, scene export; **no persistent asset registry** (contract drift, G7), interiors are one generic kind, and world locations are not linked to story `location_id`s (B6) |
| 9 | Character Studio | PARTIAL (strongest area) | Import/assembly/proportions/hair/face geometry/expressions/portrait/turnaround/export; identity across episodes is stored but **not proven across episodes**; texture painting and new blend-shape authoring absent (declared) |
| 10 | Animation engine (idle…driving, blending) | PARTIAL / largely procedural | `worker.gd` builds procedural action anchors, camera tracks and expression tracks; **no clip library, no blend graph, no transitions**. All 28 brief action families are not covered |
| 11 | Story engine (17 outputs, Urdu, RTL, Roman Urdu, editing, repair) | PARTIAL | Prompt builder + strict schema + validation + save/reload; **generation is a manual handoff**; `subtitle_mode` is dead (D2); Roman Urdu absent; "repair invalid scene data rather than failing" is not implemented (validation rejects, never repairs) |
| 12 | Multi-AI resource manager | DOC-ONLY | `docs/AI_PROVIDERS.md` has real quota/region research; **no provider adapter, no quota-aware handoff UI, no provider registry** |
| 13 | Research agent | MISSING | No workspace, no agent, no task flow; only static research documents |
| 14 | Urdu voice, audio, lip-sync | PARTIAL, and **non-functional as shipped** | Pinned `ur_PK` Piper voices are declared in `app/audio.py` but `piper-tts` is in neither `pyproject.toml` nor `requirements.lock`; no manual recording fallback; no visemes; envelope is RMS loudness (D3) |
| 15 | Complete episode production (queue, cache, checkpoints, retry, cancel, restart, monitoring) | PARTIAL | `app/job_queue.py` + `jobs`/`job_events` tables; **queue is bookkeeping inside the request thread, not a worker** (R1); no scene cache or checkpoints (R2); no memory/disk monitoring (R3); no UI cancel/progress (R4) |
| 16 | Application interface (16 workspaces, working controls, progress) | **MISSING for 11 of 16** | Present: Dashboard, Projects, Story Generator, Character Studio, World Builder. Absent: Asset Library, Animation Library, Voice Studio, Scene Editor, Timeline, standalone 3D Preview, Episode Renderer, Research Agent, AI Resource Manager, Settings, Logs & Diagnostics (nav marks three as "Planned"; the other eight are not represented) |
| 17 | Asset and licence management | PARTIAL | Third-party licences documented in `ASSET_LICENSES.md`/`THIRD_PARTY_NOTICES.md`; Quaternius catalogue carries licence metadata; **no in-app asset registry with per-asset source/author/licence/rights** (G7); user-uploaded GLBs get no provenance record; repository has no root `LICENSE` (G6) |
| 18 | Offline and cost policy | PARTIAL | No paid service is mandatory; first audio run needs the network to fetch voice models; **no offline workflow test** (R6) |
| 19 | Required documentation maintained and synchronized | PARTIAL | All documents exist; several are materially stale (section 7) |
| 20 | Phase order 0→8 | PARTIAL / out-of-order by owner direction | Phases 2–7 are being worked in parallel before Phase 2 closes; the plan records this honestly, but exit gates are not being met in order |
| 21 | Substantial batches, one coherent commit | MET | Batch commits are coherent and documented |
| 22 | Quality assurance on real output | **MISSING** | No real MP4, no inspected frames, no native-speaker listening, no measured target-PC performance. `tests/test_render.py` mocks Godot and FFmpeg; `tests/test_audio.py` uses a fake synthesizer |
| 23 | Final acceptance criteria (22 items) | Mostly not met | See section 3 |
| 24 | First actions in order | MET at the time; superseded by staleness | Phase 0/1 evidence exists and is recorded |
| 25 | Final operating rules | Followed in spirit | The honesty rules are respected; the "keep docs synchronized" rule is not (G2) |

---

## 3. Brief §23 final acceptance — item by item

| # | Criterion | Status |
|---|---|---|
| 1 | GitHub repo with complete source | MET |
| 2 | Extensive documented research and reuse | MET |
| 3 | Verified third-party licences | PARTIAL — `THIRD_PARTY_NOTICES.md` + `ASSET_LICENSES.md`; no root project licence; FFmpeg distribution licence undecided |
| 4 | Complete requirement traceability | PARTIAL — rows exist, but stale and partly non-conforming (G1, G2) |
| 5 | Working Actions build pipeline | MET |
| 6 | Successful Windows artifact | MET (installer + bootstrap + SBOM) |
| 7 | Working Windows installation | MET per CI #176 lifecycle; not re-tested since the queue/import batch |
| 8 | Browser studio interface | PARTIAL — 5 of 16 workspaces |
| 9 | Local project management | MET |
| 10 | Persistent original characters | PARTIAL — created and stored; cross-episode identity unproven |
| 11 | Persistent reusable environments | PARTIAL — worlds stored; "not a different version each episode" unproven |
| 12 | Working animation library | **NOT MET** — procedural only |
| 13 | Single-prompt story generation | **NOT MET** — manual copy/paste handoff |
| 14 | Natural Urdu dialogue | **NOT MET as shipped** — no TTS dependency installed (B1) |
| 15 | Character-specific voices or documented fallback | NOT MET — two voices declared; unusable as shipped; no recorded fallback |
| 16 | Working lip-sync or documented limitation | PARTIAL — limitation is documented (RMS envelope); no visemes, no blink, no head motion |
| 17 | Actual 3D scene rendering | PARTIAL — scene `.tscn` + MovieWriter AVI path exists; only mocked in CI |
| 18 | Complete MP4 episode assembly | **NOT MET** — no FFmpeg bundled; no real-media test |
| 19 | Scene-level caching and recovery | **NOT MET** — no cache, no checkpoints (R2) |
| 20 | Practical performance on target hardware | **NOT MET** — no measurement (correctly deferred to Phase 8) |
| 21 | No mandatory paid AI services | MET |
| 22 | Actual test evidence | PARTIAL — strong for the modules under test; none for real media, real TTS, or the installer after this batch |

---

## 4. Blocking findings

### B1 — The delivered application cannot produce an episode (Critical)

**Evidence**
- `app/audio.py:131-137` imports `piper` at call time and, on failure, raises with the text
  "Install it with: pip install piper-tts".
- `piper-tts` appears nowhere in `pyproject.toml` (only `fastapi`, `pydantic`, `uvicorn`),
  `requirements.txt`, `requirements.lock` or `uv.lock`. A repository-wide search finds the
  string only inside `app/audio.py` and the docs.
- `app/render.py:40-51` requires FFmpeg from `CARTOON_STUDIO_FFMPEG` or `PATH`, and
  `.github/workflows/release-windows.yml:63-89` copies Godot, the worker and the notices
  into the installer bundle — **not FFmpeg, not Piper**.
- `app/main.py` `render_episode` refuses to run unless an audio build and its `.srt`
  exist, so the missing TTS blocks the MP4 too.

**Why it matters:** brief §4.3 ("the user should not have to manually configure multiple
programming environments"), §15 and §23 items 14, 15, 18. The installer can build scenes
and nothing else a user can watch.

**Required action (choose and record in `DECISION_LOG.md`)**
1. *Voice:* either pin `piper-tts` + `onnxruntime` into `pyproject.toml`/lock and PyInstaller
   collection, with the two `ur_PK` ONNX voices fetched and hash-verified at install/build
   time; or ship the documented manual-recording fallback (import a WAV per dialogue line)
   as the default path and treat TTS as optional. The brief allows either, but not silence.
2. *MP4:* bundle a licence-reviewed FFmpeg build (LGPL, no GPL-only components beyond
   `libx264` if you accept GPL, or switch to an encoder whose licence permits
   redistribution) beside `engine/`, and resolve `_find_ffmpeg` against the bundled path
   first. Record the codec/patent decision that P0.7 left open.
3. *Bootstrap:* `start.bat` must fetch or explain the missing engine/FFmpeg, or the README
   must stop recommending the bootstrap for production (M1).

**Acceptance test:** a CI job (`workflow_dispatch`, Windows) that installs the built
installer into a clean temp dir, creates a project from a fixture, generates a 1-scene
fixture episode, runs audio with the real engine, renders a real MP4, and asserts
`ffprobe`-reported duration and streams — with no developer tooling on `PATH`.

---

### B2 — Job queue is bookkeeping, not execution (Critical for Part 15 semantics)

**Evidence**
- `app/job_queue.py` module docstring states it does not run work by itself; the four
  routes enqueue, claim and then execute the Godot/FFmpeg call **inside the HTTP request
  thread** (`app/main.py` production/audio/render/world-export).
- Therefore: the browser waits synchronously for up to 4 hours; closing the tab does not
  stop the work; `POST /jobs/{id}/cancel` cannot interrupt a running operation; progress is
  always 0 or 100 because nothing reports intermediate steps.

**Why it matters:** brief §15 ("persistent job queues… safe cancellation… progress
reporting"), §16 ("provide meaningful progress information"), §23 item 19.

**Required action:** a real worker (thread or child process) that claims jobs from the
queue, reports progress per scene, honours `cancel_requested` between scenes, and writes
`scene_render` checkpoints. The HTTP routes become `202 Accepted` + job id; keep a
synchronous compatibility route only if a test pins it.

**Acceptance test:** enqueue → poll `/jobs/{id}` shows monotonically increasing
`progress`; cancel mid-run ends `cancelled` with the finished scenes preserved; killing the
process and restarting resumes from the last checkpoint.

---

### B3 — No scene cache, no checkpoints, no partial-failure recovery (Critical)

**Evidence**
- `app/render.py:246-300` renders **every** scene into a fresh temp directory each call and
  assembles the MP4 from that temp tree; nothing is content-addressed, nothing survives the
  request.
- `render.json` keeps only the final MP4 path; individual scene videos are deleted with the
  temporary directory.

**Why it matters:** brief §15 ("a failure in one scene must not force the entire episode to
be rendered again"), §6 ("scene-level caching, resumable jobs"), §23 item 19.

**Required action:** render each scene to a content-addressed path derived from the scene
document hash + render settings, persist a per-scene manifest, skip cached scenes, and
rebuild only missing ones. Record cache hits in the job output.

**Acceptance test:** render, delete one scene's cached video, re-render, assert exactly one
scene was re-rendered and the final MP4 is byte-stable in duration and stream layout.

---

### B4 — 11 of 16 required workspaces do not exist (Critical for Part 16)

**Evidence:** `app/static/index.html` nav lists Dashboard, Projects, Story Generator,
Character Studio, World Builder, and marks Asset Library, Animation & Timeline, Voice Studio
as "Planned". There is no Scene Editor, no standalone 3D Preview workspace, no Episode
Renderer workspace, no Research Agent, no AI Resource Manager, no Settings and no Logs and
Diagnostics page. The render/audio/production actions live as three buttons inside the
Story page.

**Why it matters:** brief §16 lists all 16 as required; "every visible control must perform
its advertised function" is currently satisfied only because the missing ones are simply not
shown.

**Required action:** at minimum, deliver **Episode Renderer** (job list, progress, cancel,
download), **Logs and Diagnostics** (journal of jobs/events already stored in
`job_events`, install paths, engine/FFmpeg/voice health) and **Settings** (FFmpeg path,
voice path, data dir, quality preset). Then Animation & Timeline, Asset Library, Voice
Studio, Scene Editor, Research Agent, AI Resource Manager.

**Acceptance test:** browser acceptance script that visits each workspace, asserts the nav
entry is not marked "Planned", and exercises one real action per workspace.

---

### B5 — Story, scene and world vocabularies are not one system (Critical for Parts 8/11)

**Evidence**
- `app/story.py:13-85`'s `LOCATION_CATALOG` holds 70 identifiers such as `portrait`,
  `runway`, `black-box`, `cyclorama`, `photo-loft`, `night-club`, `public-restroom` — the
  Ara/Blender demo-scene vocabulary. `ScenePlan.location_id` must be one of them.
- The World Builder vocabulary is entirely different: `WorldObjectInput.kind` is
  `road|building|shop|…|indoor_room|water_body|streetlight`, and a world has objects with
  coordinates, not location IDs.
- A saved episode plan therefore cannot point at a saved world location; `world_id` links the
  episode to a world scene file, but `location_id` inside each scene is a catalogue string.
- `props` in a scene are free text; `worker.gd` does not consume `location_id` props, and
  `scene.audio` cues (music/effect/ambience) are consumed by nothing (verified: no
  `"audio"`/`music`/`ambience` handling in `worker.gd`).
- `docs/PROJECT_STATUS.md` and `docs/EXECUTION_BATCH_PLAN.md` (P4.1) already flag this as
  the required replacement of "Ara-derived catalogs".

**Why it matters:** brief §8 ("do not regenerate a completely different version of the same
location in every episode"), §11 ("every scene must identify its location… props… audio"),
§23 items 10–11.

**Required action:** introduce Cartoon Studio location IDs owned by the world document
(`world.objects[].location_id` or a `locations[]` array with kind + bounds + theme), map the
legacy catalogue as aliases once, and make `ScenePlan.location_id` reference a *world
object* so production reuses the saved layout. Do the same for `props` (world object refs)
and `audio` (asset refs), or delete those fields from the schema until they are consumed.

**Acceptance test:** save a world with three locations, build an episode whose scenes name
those three locations, produce scenes, and assert each generated scene contains the same
object set/coordinates as the saved world (no regeneration); plus a migration test that old
`location_id`s map to aliases.

---

### B6 — No animation library and no blending (Critical for Part 10)

**Evidence:** `engine/godot_worker/worker.gd` `_episode_action_pose` / `_build_episode_timeline`
generate procedural position/rotation anchors for a fixed action vocabulary; nothing loads a
clip library, nothing blends two clips, nothing retargets a library clip into an episode
scene (retargeting exists only as a separate import workflow). `ANIM-R001/R003/R005` are
honest about this, but Part 10 requires ~28 named behaviours with smooth transitions.

**Required action:** adopt a licensed clip set (Quaternius animation clips already pinned,
or UAL/UAL2 as researched) keyed by stable `action_id`, load it in the worker, cross-fade at
boundaries, and keep the procedural pose as the fallback when a clip is missing.

**Acceptance test:** for each supported `action_id`, a native proof plays the clip on a real
rig, and a transition test asserts no pose discontinuity above a threshold between
adjacent clips.

---

### B7 — No lip-sync: loudness envelope only (Critical for Part 14)

**Evidence:** `app/audio.py:178-207` builds a 50 ms RMS "openness" curve per clip;
`worker.gd` animates generated mouth nodes from it. There are no visemes, no jaw/phoneme
mapping, no blink, no head movement, no coarticulation. `VOICE-R005/R006` mark this honestly
as partial/planned.

**Required action:** Urdu G2P (eSpeak NG was researched) → compact viseme table → morph or
generated-mouth track, with a manual correction timeline (the brief mandates manual
sequencing as fallback), plus blink/gaze/head-nod tracks driven by punctuation and emphasis.

**Acceptance test:** a native proof that synthesizes a known Urdu line, produces a viseme
track, renders a short clip, and a reviewer compares mouth closures for
`/p,b,m/` words frame by frame (documented in `TEST_REPORT.md` with the clip kept as an
artifact).

---

### B8 — The brief's Part 12/13 deliverables have no runtime at all (High)

**Evidence:** `docs/AI_PROVIDERS.md` is a solid research table; there is no provider
adapter, no quota-aware switching, no prompt-export profiles beyond the single story prompt,
and no Research Agent workspace or task flow. `AI-R001…R008` and `RES-*` rows say so.

**Required action:** a provider registry (id, tier, limits, region, data policy) that the UI
can display and that gates optional features, plus a story-prompt profile per provider
(field limits, JSON strictness). Only then can Part 12 be honest as "implemented".

**Acceptance test:** a test that renders the story prompt for each registered provider and
validates the resulting JSON against `EpisodePlan`, plus a unit test that a provider over its
quota is skipped without breaking the workflow.

---

### B9 — Render and voice are unverified paths shipped to users (High)

**Evidence:** `tests/test_render.py` writes fake `Godot.exe`/`ffmpeg.exe` stubs and asserts
the command construction; `tests/test_audio.py` uses `FakeSynthesizer`. Windows CI installs
Godot (`.github/workflows/ci.yml:35-36`) but never FFmpeg and never Piper, and no test runs
the real `render_episode_video` or `PiperEngine.synthesize`.

**Required action:** add one Windows CI job that runs real media on a tiny fixture (2 scenes
of 2 s, silent TTS-friendly text, real bundled FFmpeg) and asserts the MP4 streams with
`ffprobe`; mark it `workflow_dispatch` + nightly if runtime cost matters, but it must exist.

---

### B10 — Quality presets and project settings are decorative (High)

**Evidence:** every project document stores
`settings.quality_preset = "preview"`, `frame_rate`, `resolution`
(`app/main.py:382-385`, `app/storage.py:505-508`); `render_episode` never reads them and
`render.py` hard-codes 24 fps / 1280×720 (`app/render.py:25-27`). The UI exposes no preset
selector.

**Required action:** map the four presets (Preview, Low Hardware, Balanced, High Quality) to
explicit render parameters (fps, resolution, samples/shadow/AA, scene concurrency) and read
them from the project document; add a feature-parity test asserting all four presets produce
every required stream (video + audio + subtitles) so no preset silently drops a feature.

---

## 5. Functional defects (small, concrete, fixable now)

| ID | Defect | Evidence | Fix |
|---|---|---|---|
| D1 | `quality_preset` stored, never read | `app/main.py:385`, `app/storage.py:508`; no reader anywhere | Wire into render settings, or remove the field and the promise |
| D2 | `subtitle_mode` stored, never read — Roman Urdu/English/none have no effect | `app/story.py:239`; `app/audio.py:240-252` always writes the Urdu text verbatim | Implement Roman transliteration + `none`, or delete the option |
| D3 | English episodes are offered by the UI and accepted by the schema but audio refuses them | `story.html:17` offers "English"; `app/story.py:234` allows `en`; `app/audio.py:261-264` raises `SpeechGenerationError` | Either support English TTS/recording, or make the UI/schema refuse `en` up front with a labelled limitation |
| D4 | Scene `audio` cues (music/effect/ambience) accepted and ignored | `app/story.py:199-204`; no consumer in `worker.gd`/`audio.py` | Implement music/SFX as a real mixing stage (Part 14) or remove the schema field until it exists |
| D5 | Scene `props` are free text and ignored by production | `app/story.py:216`; `worker.gd` scene build uses locations/characters only | Bind props to world objects (B5) |
| D6 | `CharacterSpec.voice_profile` is free text with no validation; an unsupported value is only rejected at audio time (`app/audio.py:305-308`), after scenes were already generated, and a dialogue line whose `character_id` is not in the cast (`narrator`) silently uses the default voice | `app/story.py:114`, `app/audio.py:278-308` | Constrain `voice_profile` to `VOICE_CATALOG` keys (plus `recorded` once that fallback exists) at validation time, and make the narrator voice explicit |
| D7 | Two different phase lists contradict each other and the code | `EXECUTION_BATCH_PLAN.md` P3.3 "NOT STARTED" (vehicles implemented), P6.1 "RESEARCH REQUIRED" (Piper implemented), P6.4 and P7.1 "NOT STARTED" (mix/subtitles and queue implemented), P7.2 "rendering… unimplemented" (`render.py` exists) | Regenerate the batch table from code + tests (section 7) |
| D8 | `PROJECT_STATUS.md` Phase 7 says "there is no durable render queue" | `docs/PROJECT_STATUS.md:89` vs `app/job_queue.py` | Correct the row |
| D9 | `PROJECT_STATUS.md` "Next implementation batch" lists finished items as open | `:94-99` — world schema migration and project export/import are done | Rewrite the next-batch list |
| D10 | `MASTER_PLAN.md` "Current baseline" describes a repository without an engine, with Ara "only a candidate" | `docs/MASTER_PLAN.md:26-36` | Replace with the P2.1/P2.2 reality and point at this audit |
| D11 | The dashboard advertises "Godot 4.7.2 · Native worker integrated" but says Episode rendering "Pending" while the app actually ships a render endpoint | `index.html` stats block | Keep the honesty, add the real status text (renderer code exists, unverified/media dependencies missing) |
| D12 | `job_events` has no UI, so the diagnostics trail a user would need is invisible | `app/job_queue.py` snapshot vs no consumer | Expose it in Logs and Diagnostics (B4) |
| D13 | Bootstrap artifact ships no engine and no FFmpeg, yet `README.md` recommends it as the way to run the app | `release-windows.yml:55` (archive list), `start.bat` (no fetch), `README.md:21-27` | Either add a fetch step to `start.bat` (`scripts/fetch_godot_runtime.py` already exists) or document that the bootstrap is UI-only |
| D14 | Uploaded character GLBs carry no provenance/licence record | `app/main.py` asset manifest builder writes source/digest/rig flags only | Add author/source/licence fields to the manifest (Part 17) |

---

## 6. Reliability and engineering issues

| ID | Issue | Evidence | Required action |
|---|---|---|---|
| R1 | Queue runs work in the request thread (see B2) | `app/main.py` route bodies | Background worker + `202` + polling |
| R2 | No scene cache/checkpoints (see B3) | `app/render.py:246-300` | Content-addressed scene renders |
| R3 | No memory/disk monitoring anywhere | no `psutil`, no `shutil.disk_usage`, no telemetry (`PROD-R009` PLANNED) | Pre-flight disk estimate per render (frames × bytes/frame), abort with a clear message; report free space in `/api/status` |
| R4 | No progress or cancel in the UI | `app/static/story.js` awaits one long fetch; `/jobs` endpoints have no consumer | Job list + poll + cancel in the Episode Renderer workspace |
| R5 | A cancelled or lost job's partial outputs are not reconciled on restart | `job_queue` reclaims the lease but nothing re-reads the cache | Add a startup reconciliation pass that marks orphaned temp dirs and resumes from checkpoints |
| R6 | No offline verification | no test disconnects the network | CI job: set `CARTOON_STUDIO_NO_NETWORK=1` (or block hosts) and run create → scenes → audio (cached models) → render |
| R7 | CI never runs the installer workflow | `release-windows.yml` is `workflow_dispatch` only; `ci.yml` runs tests only | Add an install-lifecycle job on `main` (or a nightly) so install regressions are caught automatically |
| R8 | Release artifacts expire (14/30 days) and no GitHub Release is published | `release-windows.yml:118,125,132`; no release step | Publish a versioned Release with checksums, SBOM and installer, and keep the workflow reproducible |

---

## 7. Documentation and governance drift (fix these before adding features)

### G1 — Status vocabulary is violated (brief §2.2, `PROJECT_SPECIFICATION.md:30`)

Allowed: `NOT REVIEWED, RESEARCH REQUIRED, PLANNED, IN PROGRESS, IMPLEMENTED, PARTIALLY
IMPLEMENTED, TESTED, VERIFIED, BLOCKED, DEFERRED WITH REASON, REJECTED WITH JUSTIFICATION`.

Found in `docs/REQUIREMENTS_REGISTRY.md`: bare `PARTIAL` (e.g. `CHAR-R001`, `ANIM-R004`,
`PHASE-R003`, `QA-R003`), `COMPLETE`/`ACTIVE` in `PROJECT_STATUS.md`, and `TESTED` used for
documentation rows (`DOC-R002`…`DOC-R006`) where no test exists. Replace `PARTIAL` with
`PARTIALLY IMPLEMENTED`, and use `TESTED` only with a named test.

### G2 — Registry rows that contradict the code

Rows below still describe an earlier repository. Update each with a real status and evidence
before the next batch; they are the ones a new coder will trust first.

| Row | Current text (abridged) | Reality |
|---|---|---|
| `PROD-R002` | "No implementation/test evidence… PLANNED" | `worker.gd` episode-scene generation + `app/engine.py` adapter exist and are tested |
| `PROD-R003` | "RESEARCH REQUIRED, no production assembly" | `app/render.py` mixes WAV + SRT into MP4 and verifies it (mocked in CI) |
| `PROD-R005` | (already updated) | keep |
| `PROD-R007/R008`, `REL-R002` | (already updated for the queue) | keep, but add the B2 limitation |
| `ROLE-R004` | "No self-contained installer" | P1.4 installer built and lifecycle-tested (#176) |
| `ARCH-R001` | "No service modules or full product workflows" | `app/{engine,render,audio,job_queue}.py` exist |
| `ARCH-R003` | "Godot remains provisional pending P0.6 proof" | P0.6/P0.7 froze Godot 4.7.2 as the runtime |
| `ARCH-R006` | "No migration framework, asset registry, durable queue" | migrations 1–4 and `job_queue.py` exist; the asset registry genuinely does not |
| `PHASE-R001` | "IN PROGRESS; P0.2–P0.7 remain" | Phase 0 closed (`P0_7_PHASE0_EXIT_REVIEW.md`) |
| `PHASE-R003` (`PARTIAL`) | Phase 2 exit open | Correct, but the status word must be `PARTIALLY IMPLEMENTED` |
| `QA-R001` | "No clean Windows installation proof" | CI #176 install/upgrade/uninstall/reinstall passed |
| `QA-R010` | "Prompt/schema and manual handoff only… No TTS" | `app/audio.py` implements a Piper adapter (unusable as shipped — say so, see B1) |
| `VOICE-R001/R002` | research only, no Piper | Neither row mentions the pinned `ur_PK-fasih`/`aegis_female` voices that `audio.py` declares; reconcile with `VOICE-R005` |
| `GIT-R002` | "Production engine, installer… absent" | both exist |
| `VISION-R005/R006` | "no durable render queue" | queue exists; cache/checkpoints genuinely absent |
| `DEMAND` rows referencing "Ara" as selected engine | multiple | Godot 4.7.2 is the selected runtime; Ara is rejected |

### G3 — `REQUIREMENT_TRACEABILITY.md` inherits every G2 error

It is generated in parallel with the registry and repeats the same stale claims. Update both
in the same commit, and add a consistency test (see T1).

### G4 — `NEXT_STEPS.md` and `PROJECT_STATUS.md` next-batch lists are stale

`NEXT_STEPS.md:1-5` still says main is at `321c111` and quotes "122 passed, 34 skipped" —
the head is `a88379f` and the suite changed in `c20ab8a`; the file also still opens with
"Next Steps — 2026-11-27" while completed batches are dated 2026-11-28.
`PROJECT_STATUS.md:94-99` lists as remaining both the canonical world schema migration and
project export/import, which are complete. Rewrite both from the batch order in section 9.

### G5 — No GitHub Release exists

The brief (§4.2) expects releases "where appropriate"; `release-windows.yml` produces
artifacts with 14/30-day retention and stops there. Artifacts are not a delivery channel for
a user.

### G6 — No project distribution licence

The repository has `LICENSES/` for third-party components but **no root `LICENSE`**. P0.7
records this as an owner decision. Until it is chosen, the project cannot be published or
accept copyleft bundling without ambiguity.

### G7 — Schema/contract drift

`docs/ARCHITECTURE_CONTRACTS.md:165` requires minimum indexed tables `projects, documents,
assets, render_jobs, job_events, schema_migrations`. The actual schema has `projects,
story_plans, project_documents, jobs, job_events, schema_migrations` — **no `assets` table**
and the queue table is named `jobs`, not `render_jobs`. Either amend the contract or add the
`assets` table (recommended: the brief's Part 17 needs it anyway).

### G8 — `README.md` omits half the current product

The "Current working foundation" list has no World Builder, no episode-scene generation, no
Urdu audio, no MP4 render, no job queue, no project export/import. It understates the
repository, which is less harmful than overstating it, but it misleads a new contributor.

---

## 8. What is genuinely good — keep it

State this in the registry so the next coder does not "fix" working code:

1. `app/storage.py` — numbered migrations, backup-before-migrate, WAL, foreign keys, atomic
   JSON writes, portable-document recovery. This is the most solid part of the repository.
2. `app/job_queue.py` (after `c20ab8a`) — attempts counter, lease owner/expiry, reclaim,
   event journal, bounded list page, single-writer transactions. It needs a worker (B2), not
   a rewrite.
3. `engine/godot_worker/worker.gd` — strict path/size validation, GLB round-trip
   verification, rig compatibility refusal instead of silent remapping, face-surface marker
   that survives glTF (documented in `TEST_REPORT.md`).
4. `app/engine.py` — supervised subprocess with request/response files, timeout budget,
   cancellation hooks, engine-neutral payloads.
5. CI discipline — lock check, locked sync, lint, JS syntax, compileall, real Godot fetch,
   pinned fixtures, SBOM, installer lifecycle.
6. Honesty in the requirement registry: no `VERIFIED` claim without evidence; limitations
   stated in every row. Preserve this culture; the fixes below are about accuracy, not
   trust.

---

## 9. Recommended batch order (each ends with one commit + docs)

Ordered so that each batch unblocks the next and no batch depends on an unresolved decision.

**Batch A — Make the shipped app produce a playable episode (B1).**
Decide voice strategy, pin and bundle it, bundle licence-reviewed FFmpeg, resolve
`_find_ffmpeg` to the bundle, add the real-media CI job, document the offline path. *Gate:*
clean-install MP4 from a fixture episode with no developer tooling present.

**Batch B — Real job execution, progress, cancel, diagnostics (B2, R1, R4, R5, D12).**
Background worker, per-scene progress, cooperative cancel, lease heartbeat from the worker,
Episode Renderer + Logs and Diagnostics workspaces, `/jobs` polling in the UI,
startup reconciliation. *Gate:* progress monotonicity, cancel mid-render, restart resume.

**Batch C — Scene cache and checkpoints (B3, R2, R7).**
Content-addressed scene renders, per-scene manifest, skip cached, resume missing,
cache-hit reporting. *Gate:* one-scene re-render proof.

**Batch D — One vocabulary for story, world and production (B5, D5, D6).**
Cartoon Studio location/prop IDs owned by worlds, legacy aliases, scene → world binding,
prop/audio asset refs, voice constrained to the catalogue. *Gate:* world reuse and alias
migration tests.

**Batch E — Animation library and blending (B6).**
Licensed clip set keyed by `action_id`, cross-fade, procedural fallback, per-action native
proofs. *Gate:* all supported actions play; transition continuity check.

**Batch F — Urdu lip-sync, blink and expression timing (B7, D2, D3).**
G2P → viseme table → morph/generated-mouth track, manual correction timeline, Roman Urdu and
`none` subtitle modes, English decision recorded. *Gate:* viseme clip inspection + SRT mode
tests.

**Batch G — Music, ambience and SFX (D4).**
Consume `scene.audio` cues with a real mixing stage and licensed assets; separate buses;
subtitle/mix balance check. *Gate:* audible mix containing dialogue + music + effect.

**Batch H — Asset library and provenance (G7, D14, G6).**
`assets` table, per-asset source/author/licence/rights, upload provenance capture, in-app
Asset Library workspace, root `LICENSE` chosen. *Gate:* every asset in a fixture project has
complete provenance; licence audit test.

**Batch I — Quality presets and hardware tuning (B10, Part 6).**
Read project settings, four presets with feature parity, disk/time estimates, target-PC
measurement recording. *Gate:* parity test across presets + measured numbers in
`HARDWARE_PROFILE.md`.

**Batch J — Governance and delivery (G1–G5, G8, R8).**
Registry/traceability migration to the allowed vocabulary with code-backed evidence, a
consistency test, corrected `MASTER_PLAN`/`PROJECT_STATUS`/`NEXT_STEPS`/README, published
GitHub Release with checksums and SBOM. *Gate:* consistency test green; release downloadable.

**Batch K — AI resource manager and research agent (B8).**
Provider registry with limits/region/policy, per-provider prompt profiles, quota-aware
skipping, Research Agent workspace with the brief's 10-step flow recorded as data. *Gate:*
prompt-profile tests + one recorded research task.

---

## 10. Tests to add (name them exactly so the registry can cite them)

| ID | Test | Proves |
|---|---|---|
| T1 | `test_registry_and_traceability_are_consistent` | Every registry ID has exactly one traceability row; every status is in the allowed vocabulary; no row claims "no evidence" for a module that exists in `app/` |
| T2 | `test_document_status_matches_code` | Each `PROJECT_STATUS.md` phase row maps to at least one cited test name that exists |
| T3 | `test_real_mp4_from_fixture_episode` (Windows, real Godot + bundled FFmpeg) | B1/B9 — actual MP4 with video+audio+subtitles |
| T4 | `test_real_urdu_tts_sample` (Windows, pinned voice) | B1 — real speech synthesis and WAV format contract |
| T5 | `test_job_progress_cancel_and_resume` | B2 — progress monotonic, cancel honoured, restart resumes |
| T6 | `test_scene_cache_reuses_completed_scenes` | B3 — one re-render only |
| T7 | `test_world_locations_drive_episode_scenes` | B5 — no regeneration drift |
| T8 | `test_animation_clip_library_covers_action_ids` | B6 — every `action_id` maps to a real clip or explicit fallback |
| T9 | `test_viseme_track_for_known_urdu_line` | B7 |
| T10 | `test_subtitle_modes_urdu_roman_english_none` | D2 |
| T11 | `test_audio_cues_reach_the_mix` | D4 |
| T12 | `test_quality_presets_keep_feature_parity` | B10 |
| T13 | `test_offline_workflow_after_asset_download` | R6 |
| T14 | `test_installer_bundles_engine_ffmpeg_and_voice` | B1 — inspect the built installer contents |
| T15 | `test_asset_provenance_is_required` | G7/D14 |

---

## 11. Decisions only the project owner can make

1. **Voice strategy:** bundle `piper-tts` + ONNX models (downloads ≈ 128 MiB, CPU-only) or
   ship manual recording as the default? (B1)
2. **FFmpeg licensing:** accept a GPL build with `libx264`, or switch to an encoder with a
   redistributable licence? This determines what can be bundled. (B1, G6)
3. **Project distribution licence:** choose one; nothing can be published without it. (G6)
4. **English-language scope:** support English dialogue end-to-end, or restrict to Urdu and
   remove the option? (D3)
5. **Phase order:** continue Phases 2–7 in parallel, or close Phase 2 (visual acceptance)
   before new phases? The plan records the current choice; changing it changes the batch
   order in section 9.

---

## 12. Evidence index (paths a reviewer can check)

- Voice dependency absent: `pyproject.toml:6-10`, `requirements.txt`, `requirements.lock`
  (no `piper`), `app/audio.py:131-137`.
- FFmpeg not bundled: `app/render.py:40-55`, `.github/workflows/release-windows.yml:63-89`.
- Bootstrap ships no engine: `.github/workflows/release-windows.yml:55`, `start.bat:1-28`.
- Queue executes in the request: `app/job_queue.py:16-20`, `app/main.py` production/audio/
  render/world-export route bodies.
- No scene cache: `app/render.py:246-300`.
- Presets unused: `app/main.py:382-385`, `app/storage.py:505-508`, `app/render.py:25-27`.
- `subtitle_mode` dead: `app/story.py:239` vs `app/audio.py:240-252`.
- English trap: `app/static/story.html:17`, `app/story.py:234`, `app/audio.py:261-264`.
- Ara vocabulary: `app/story.py:13-85` vs `app/main.py:189-203` (`WorldObjectInput`).
- Scene audio cues unused: `app/story.py:199-204`; no consumer in `engine/godot_worker/worker.gd`.
- No assets table: `app/storage.py` migrations 1–4 (`projects`, `story_plans`,
  `project_documents`, `jobs`, `job_events`, `schema_migrations`).
- Contract drift: `docs/ARCHITECTURE_CONTRACTS.md:165`.
- Mocked media tests: `tests/test_render.py:41-70`, `tests/test_audio.py:14-22`.
- Release is manual and artifacts expire: `.github/workflows/release-windows.yml:4,118-132`.
- Stale rows: `docs/REQUIREMENTS_REGISTRY.md` — `PROD-R002/R003`, `ROLE-R004`,
  `ARCH-R001/R003/R006`, `PHASE-R001`, `QA-R001/R010`, `VOICE-R001/R002`, `GIT-R002`.
- Stale narrative: `docs/MASTER_PLAN.md:26-36`, `docs/PROJECT_STATUS.md:89-99`,
  `docs/EXECUTION_BATCH_PLAN.md:46-81`, `docs/NEXT_STEPS.md:1-5`.
