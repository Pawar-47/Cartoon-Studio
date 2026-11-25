# Test Report — 2026-11-25

## Current repository checkpoint
- Main HEAD before this documentation batch: bbca69d5ff9933dd04233a1fd757d86c7e60e83d.
- GitHub Actions run #93: SUCCESS on the last verified implementation/documentation baseline facb0dd738e227d643d4e85d80bd5d3f620fc6e1.
- Prior app CI run #67 passed Ruff, Python compileall, 12 pytest tests, Windows bootstrap ZIP packaging and artifact upload.
- Bootstrap artifact is not a self-contained installer and does not prove a clean target-PC installation.

## P0.5 architecture and dependency documentation
- Registry and traceability were parsed from live GitHub: 171 unique requirement IDs in each; exact ID-set equality; no missing or extra IDs.
- Added a 171-row architecture crosswalk. Planned module paths are ownership targets, not implemented-code claims.
- Reviewed current source: FastAPI/Uvicorn/Pydantic/stdlib SQLite, static HTML/CSS/JS, project metadata and saved story plan. No renderer, durable queue, asset registry, migration framework, provider registry or installer is implemented.
- Reviewed current requirements: range constraints only; no fully resolved runtime lock file.
- Confirmed no root LICENSE file in the current repository tree. Copyleft adoption/bundling remains excluded until the project distribution-license decision is made.
- P0.5 is documentation-complete; P0.6 proofs have not yet run.

## Target-PC benchmark policy
- scripts/run_target_pc_probe.ps1 and tools/godot_target_probe/ remain optional diagnostics.
- No PowerShell execution or Godot renderer launch on the user's PC has occurred.
- No actual FPS, frame-time, memory, driver, AVI or full episode render measurement exists.
- This is not a gate for P0.5/P0.6/P0.7 or Phases 1–7. Representative performance and quality-preset tuning are Phase 8.

## P1.1 project lifecycle and portable storage — 2026-11-25
- Implemented app/storage.py with per-user data directory, CARTOON_STUDIO_DATA override, connection PRAGMAs, numbered schema migrations (v1 legacy tables, v2 portable document index), and online SQLite backup before legacy upgrades.
- Added atomic JSON writes, SHA-256 document indexing, safe project-relative path resolution and startup reconciliation.
- Added project open/update APIs; project creation writes a versioned project.json. Story plans write versioned episode JSON under each project while retaining the legacy story_plans row for compatibility.
- Startup recovery rebuilds missing project/episode files from legacy SQLite rows and restores SQLite story_plans/index rows from portable episode files.
- CI run #115 on 565d211ce3009c081e60d48778d3ba89acd4a4f7: Ruff passed, compile passed, 21 pytest tests passed, Windows bootstrap ZIP packaged/uploaded. One Starlette TestClient/httpx deprecation warning remains; it is a P1.2 dependency/test-client follow-up, not a functional failure.
- Current artifact remains a bootstrap ZIP, not a self-contained installer.

## P0.4 Urdu/provider research
- Source-level inspection only: eSpeak NG Urdu rules/CLI, WhisperX Urdu alignment model, Qwen Urdu voice/regions/pricing, and official provider free-tier/region docs.
- No Pakistani Urdu audio sample was processed. No voice quality, WER, forced-alignment accuracy or phoneme timing has been tested.
- No API key/account has been connected and no content has been sent to an external provider.
- See docs/URDU_VOICE_FEASIBILITY.md for a repeatable acceptance protocol.

## Existing proof limitations
- Ara proof run #6 was cancelled during browser MP4 export. No successful production MP4 export artifact exists.
- Do not mark any production engine, character, world, animation, TTS, lip-sync, installer or episode pipeline verified based on current CI.

## Verification standard
Every new test result must record exact commit/version, environment, command, exit code, elapsed time, artifacts, observed output and unresolved limitations. CI success is not a substitute for target-PC or visual/audio quality verification.

## P0.4 follow-up model audit
- Inspected WhisperX Urdu aligner model card/file size, Urdu Whisper Turbo ASR model card/file size and Smol Urdu TTS source tree. Evidence is documented in URDU_VOICE_FEASIBILITY.md and CANDIDATE_SCORECARD.md.
- This was source/model-card inspection only. No model weights were downloaded, no inference was run, and no Pakistani audio was processed.


## P0.6 bounded functional proofs — 2026-11-25

See P0_6_PROOF_REPORT.md for exact run IDs, acceptance checks and limitations.

- Godot native-worker proof run #2: SUCCESS on b05024110e76b684a5f8cee35eb57fa0428b2c11. Godot 4.7.2-stable official, Compatibility renderer, GLB imported with MeshInstance3D, animation created/playing, scene saved/reopened, 72 frames at 24 FPS; AVI is 640x360, MJPEG/PCM, 3.0 seconds. All six JSON checks true. Runner adapter was Mesa llvmpipe, not the user's GPU.
- Godot + FFmpeg proof run #3: SUCCESS on ae9bad178c9999d5f5b7017a6409c7ee9c490786. Same scene checks passed; FFmpeg converted AVI to 640x360, 24 FPS, 3.0-second MP4 with MPEG-4 Part 2 video and AAC audio. This proves container/assembly path only, not final distribution codec choice.
- SQLite queue proof: Windows CI run #101 SUCCESS on b05024110e76b684a5f8cee35eb57fa0428b2c11; 17 tests passed, including five isolated queue-prototype tests for serial claims, lease-expiry retry, completed-scene preservation, cancellation and stale-worker rejection.
- First Godot attempt #1 failed: dynamically created nodes lacked PackedScene ownership and the MovieWriter output directory was not created inside the Godot project. Both were corrected; runs #2 and #3 passed. The failed attempt is retained as diagnostic history, not hidden.
- These are bounded hosted-runner proofs, not production app integration, full episode rendering, or user-PC benchmarks. Actual target-PC measurements remain Phase 8.