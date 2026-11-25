# Dependency and Licensing Decisions — P0.5

**Checkpoint:** 2026-11-25  
**Status:** architecture-level decisions; exact integration versions and transitive manifests are pinned when each dependency is adopted. No candidate is claimed as integrated or production-tested merely because it appears here.

## 1. Non-negotiable dependency policy

1. The core app must start, open/edit projects, and run local workflows without API keys, subscriptions, cloud inference, cloud rendering, online activation or a network connection after installation and asset acquisition.
2. Online AI and cloud TTS are optional adapters. Manual prompt handoff, manual recording and manual transcript/timing correction remain supported.
3. Prefer permissive, maintainable dependencies and engine-neutral data. No new dependency is adopted without an exact version/commit, source, compatibility review, complete software/model/asset license record, and a test.
4. Do not bundle a GPL/AGPL dependency, model or asset until the repository's own distribution-license/IP position has been explicitly settled. The current repository tree has no root LICENSE file. This is a release/legal decision, not a reason to stop architecture or local development.
5. Never infer a model's license from its code repository, or an asset's license from its pack vendor. Model weights, training data, fixtures, codecs and individual asset packs may have separate terms.
6. Pin all runtime dependencies for each release and publish an SBOM/third-party notices. Avoid floating latest engine or model downloads.
7. The target PC is a design constraint, not a gate: sequential work, asset reuse, low-hardware quality mode, bounded memory and optional higher-quality modes are architectural requirements. Actual frame-time/RAM/render-duration measurements are Phase 8.

## 2. Core application foundation

| Area | Decision / candidate | License / cost | Current status and boundary |
|---|---|---|---|
| Language/runtime | Python 3.11+ (existing pyproject.toml) | Python PSF license; free | Keep Python backend. CI should test supported 3.11 baseline; pin exact interpreter for release builds. |
| HTTP/API | FastAPI >=0.115,<1 and Uvicorn >=0.34,<1 (existing requirements) | FastAPI MIT; Uvicorn BSD-3-Clause | Retain existing API. Lock exact versions in a reproducible lock file during Phase 1. |
| Validation | Pydantic v2 via FastAPI dependency | MIT | Use strict, versioned request/document models. Pin through resolved dependency lock; do not maintain a second validation stack. |
| Local database | Python standard-library sqlite3 | SQLite public domain | Retain SQLite as local index and job journal. No database server or network service. Use foreign keys, WAL where supported, explicit transactions and migrations. |
| Browser UI | Existing vanilla HTML/CSS/JS | No new runtime framework dependency | Preserve dashboard/story UI. Add modular JS/CSS progressively; do not introduce a frontend build chain without measurable benefit. |
| Local service | Loopback-only FastAPI process | No cloud service | Browser talks to local service. Worker IPC remains loopback/file-based and authenticated; never expose local control API publicly by default. |

## 3. 3D engine, preview and animation

| Area | Leading candidate / decision | License / cost | Current status and proof boundary |
|---|---|---|---|
| 3D runtime | Godot 4.7.2, Compatibility renderer, native worker | MIT; include engine copyright/license and third-party notices | Selected after P0.6 hosted-runner proof. GLB import, animation, PackedScene save/reopen and a 72-frame 640x360/24 FPS MovieWriter AVI passed; no physical-PC benchmark required. See P0_6_PROOF_REPORT.md. |
| Browser viewport | Optional Godot Web export using WebAssembly/WebGL 2 and JavaScriptBridge | Godot MIT | Optional only. Must be isolated behind adapter and never be the sole production renderer. Browser threading needs cross-origin-isolation headers; threaded web export is not a baseline dependency. |
| Primary UI shell | FastAPI + existing browser UI | Existing app | Retain. Do not replace with Godot native shell or duplicate project/API logic. |
| Interchange | glTF 2.0 / GLB; VRM 1.0 as a character interchange candidate | Format/specification; each model/add-on separately licensed | Canonical project IDs remain independent of node paths, skeleton names and vendor metadata. VRM addon is not yet approved as a mandatory dependency. |
| Animation | Godot AnimationPlayer/AnimationTree as runtime primitives | Godot MIT | Prefer native primitives and Cartoon Studio-owned stable action IDs. UAL/UAL2 motion assets are candidate CC0 content only after exact pack/asset provenance is recorded. |
| World extensions | Terrain3D (MIT), Road Generator (MIT), Building Generator (MIT); Roommate (MPL-2.0) | Mixed; Roommate requires file-level MPL review | Candidate adapters, not a preselected monolithic stack. Prove each separately; avoid GPL Blender world tools as runtime dependencies. |
| Blender | Optional offline asset-authoring/conversion tool, not required in installed app | GPL-3.0 | Do not bundle or make it a runtime dependency. Use only in developer/content pipeline if needed; redistributed Blender-derived output still requires asset provenance and license review. |

Godot's official license page describes the engine as MIT and requires copyright/license notices when redistributing the engine. Official web-export docs specify WebAssembly and WebGL 2.0, and note cross-origin-isolation/header constraints for multithreaded web exports:
- https://godotengine.org/license/
- https://docs.godotengine.org/en/latest/about/complying_with_licenses.html
- https://docs.godotengine.org/en/latest/tutorials/export/exporting_for_web.html

## 4. Durable jobs, cache and recovery

| Area | Decision | License / cost | Rationale / acceptance |
|---|---|---|---|
| Queue | Use the Cartoon Studio-owned SQLite queue; isolated P0.6 prototype passed lease/retry/cancel/checkpoint tests. Do not add Huey/sqlite-workqueue unless scope expands | Python/SQLite; no extra dependency | Existing app already uses SQLite. Required semantics: one local render at a time initially, persisted state/events, per-scene checkpoints, idempotent retries, cooperative cancel and restart reconciliation. |
| Queue design | queued → preparing → rendering → assembling → completed; terminal failed / cancelled | Internal module | Claim work in a transaction with lease/heartbeat; persist every state transition; do not hold a DB transaction during rendering. |
| Cache | Content-addressed scene inputs and immutable scene outputs | Internal module | Hash canonical scene revision + engine/asset/quality versions. Cache invalidates when any render-affecting input changes. Preserve successful chunks after later failure. |
| Recovery | Startup reconciliation and stage-level retries | Internal module | A failed scene does not invalidate completed scenes. Cancellation leaves project data and completed output intact. Fault-injection tests required before reliability is marked. |
| Alternatives | Huey/SqliteHuey (MIT) and sqlite-workqueue (MIT) | Permissive candidates | Retain as fallback if owned queue scope expands beyond simple local scheduling. No current need to import either. |

## 5. Media and audio

| Area | Decision / candidate | License / cost | Current status and boundary |
|---|---|---|---|
| Scene capture | Godot MovieWriter / native frame export candidate | Godot MIT | P0.6 proof must inspect frame timing, audio output, output file limits and deterministic repeatability. No claim of production export yet. |
| Assembly | FFmpeg invoked through a narrow process adapter | FFmpeg LGPL-2.1+ by default; optional components can switch to GPL or make a build unredistributable | P0.6 verified AVI-to-MP4 assembly using FFmpeg MPEG-4 Part 2/AAC on the hosted runner. Adopt the process adapter, not that CI binary/codec. If bundled, exact build must be audited; default build must avoid --enable-gpl, --enable-nonfree, libx264 and other GPL components, and LGPL source/notice obligations must be met. |
| MP4 codec | Keep encoder selection separate from FFmpeg adapter | Codec/patent/licensing varies | Do not promise an H.264 encoder or select a redistributable codec build until the exact encoder, Windows availability and licensing are verified. |
| Audio mixing | FFmpeg filters or a small Python audio adapter, selected after proof | Depends on exact libraries/build | Keep dialogue, music and SFX as separate timeline tracks until final mix; preserve source WAV/recordings. |
| Music/SFX | Original recordings or exact verified CC0 packs | Per-asset terms | No bulk pack inclusion. Keep source, author, license, attribution and hash per asset. |

FFmpeg's official legal guidance states that the default is LGPL 2.1+, but enabling GPL components changes FFmpeg's license; it warns against assuming libx264 is part of an LGPL-only build. It also describes source, dynamic-linking and notice obligations for distributed LGPL builds:
- https://ffmpeg.org/legal.html
- https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md

## 6. Urdu, AI and speech

| Area | Candidate / decision | License / cost | Current status and boundary |
|---|---|---|---|
| Story/research AI | Optional provider adapter interface; Gemini, Groq, Cloudflare Workers AI and OpenRouter remain optional API candidates | Free-tier quotas and terms vary; no key connected | No provider is mandatory. Provider adapters expose capabilities/quota/error state; manual copy/paste handoff works without integration. |
| Free app tools | FreeMilk, ChatGPT Free, Copilot, Perplexity and similar browser apps | App-specific terms; no public API assumed | Manual user-driven handoff only. No scripted UI automation, quota bypass or unauthorized API extraction. |
| Urdu speech | Human-recorded Pakistani Urdu is the reliable baseline/fallback | No provider fee | Character voice profile and recording import are product requirements; no voice cloning without consent. |
| Cloud TTS | Qwen Audio TTS Flash Urdu voice Sahar is an optional candidate | Paid service; provider-region, privacy, accent and current price must be checked | No data is sent without explicit user approval. Not a default or mandatory dependency. |
| Local TTS/G2P | Smol Urdu TTS and eSpeak NG remain research candidates | Smol model Apache-2.0 metadata but code/runtime dependency review incomplete; eSpeak NG GPL-3.0 | Neither approved for bundling. eSpeak may be a separately installed developer tool if needed; do not make it a mandatory app dependency. |
| ASR/alignment | WhisperX + separate Urdu Wav2Vec2 aligner is a research candidate | WhisperX BSD-2-Clause; model license/weights are separate | Not installed by default. CPU/memory, boundary accuracy and Pakistani speech quality are untested. |
| Lip-sync | Engine-neutral viseme timeline + rig capability manifest and manual correction | Internal implementation | No automatic Urdu lip-sync model approved. Do not assume a generic Hindi/English model handles Urdu accurately. |

Official Qwen voice documentation lists the male Urdu Sahar voice for qwen-audio-3.1-tts-flash; this proves that a named Urdu voice exists, not Pakistani accent quality, account availability, or suitability for commercial episodes:
- https://help.aliyun.com/en/model-studio/qwen-audio-tts-voice-list

## 7. Windows packaging

| Area | Decision / candidate | License / cost | Current status |
|---|---|---|---|
| Python packaging | PyInstaller one-folder bundle as first installer path | GPL-2.0 with bundling exception; generated bundles can be distributed under app's license subject to dependency licenses | Candidate for Phase 1; verify exact release and notices. |
| Installer | NSIS for a conventional Windows installer and shortcuts | Mostly zlib/libpng with optional module-specific terms | Candidate; exact modules and licenses must be inventoried. |
| Desktop shell | Not required for first installable version; optional pywebview/Tauri only if product UX proves it necessary | Additional dependency and runtime complexity | Keep browser interface served locally. Do not add another shell merely for appearance. |
| Data location | User application data by default; preserve CARTOON_STUDIO_DATA override | Internal | Never store user projects inside install directory. |
| Release artifact | Self-contained installer or portable folder, not bootstrap ZIP | Internal release requirement | Clean Windows VM install/launch/uninstall is CI/release acceptance; user PC test is not a gate. |

PyInstaller's official license documentation explains the bundling exception. NSIS modules still need per-module review:
- https://pyinstaller.org/en/stable/license.html
- https://nsis.sourceforge.io/License

## 8. Release gates and decisions intentionally left open

- P0.6: PASSED. Godot native worker proof imported a GLB, ran animation, saved/reopened the scene and rendered/inspected AVI; see P0_6_PROOF_REPORT.md.
- P0.6: optional web viewport proof only if it provides clear product value; failure does not block native rendering.
- P0.6: FFmpeg build/codec proof with exact configure flags and a redistributable path. No GPL/nonfree build by default.
- P0.6: PASSED as a prototype. SQLite queue tests covered lease expiry, retry, completed-scene preservation, cancel and stale-worker rejection. Production queue implementation and migration tests remain Phase 1/7.
- P0.7: ready for final compliance review and architecture freeze. The optional Web viewport is deferred; final production FFmpeg codec/build remains a release-level decision.
- Phase 1: create a reproducible lock file, SBOM/third-party notices, Windows installer workflow and clean-VM smoke test.
- Phase 8: measure target-PC render time, peak RAM, disk growth, preview responsiveness, and quality-preset trade-offs. These are optimization results, not permission to start development.
- IP decision: the repository currently has no root LICENSE. Do not assume the Cartoon Studio license is MIT or proprietary. Before public redistribution of the complete app or any copyleft dependency, the project owner must choose/approve the project's own distribution license and the release must include correct notices. Architecture work continues with permissive dependencies and clear exclusions meanwhile.

## 9. Source and evidence notes

- Existing source uses FastAPI, Uvicorn, Pydantic and Python sqlite3; pyproject.toml requires Python >=3.11 and current requirements are range-based, not locked.
- Current code has no engine adapter, queue, renderer, media assembler, provider registry, asset registry, migrations or installable Windows installer.
- No model weights or third-party asset packs have been downloaded into the repository as part of this decision.
- No provider key has been connected and no user audio/text has been sent to a provider.
- Candidate versions must be checked again and pinned when the corresponding Phase 1/2/3/5/6/7 implementation batch begins.


## P2.1 — exact Godot native worker runtime

- Runtime: Godot 4.7.2-stable standard Windows x86_64 executable, Compatibility renderer, invoked with `--headless`.
- Official release archive: `Godot_v4.7.2-stable_win64.exe.zip`, 86,013,866 bytes, SHA-256 `731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`.
- CI downloads the exact official GitHub release asset, verifies SHA-256 before extraction, and bundles the executable under `_internal/engine/godot.exe`.
- Upstream MIT `LICENSE.txt` and exhaustive `COPYRIGHT.txt` from tag `4.7.2-stable` are retained in source and copied into the installer. The Godot runtime is added as a CycloneDX component with the archive hash and distribution reference.
- The Python adapter launches a one-request/one-process worker with bounded timeout, optional cancellation, structured logs and a JSON file protocol. This avoids an unauthenticated network listener and keeps the browser control plane separate.
- The worker exposes only a version/capability handshake and project-contained GLB inspection in P2.1. Character creation, rigging, animation editing and rendering remain later batches.
