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
