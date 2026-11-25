# Test Report — 2026-11-25

## Current repository checkpoint
- Main HEAD: 46ac1a8e3a1523a0db52c6cc600e8cca82750bdd.
- GitHub Actions run #87: SUCCESS on that exact commit.
- Prior app CI run #67 passed Ruff, Python compileall, 12 pytest tests, Windows bootstrap ZIP packaging and artifact upload.
- Bootstrap artifact is not a self-contained installer and does not prove a clean target-PC installation.

## P0.4 target-PC harness
- Added scripts/run_target_pc_probe.ps1 and tools/godot_target_probe/.
- Static source review only. No PowerShell execution or Godot renderer launch on the user's PC has occurred.
- No actual FPS, frame-time, memory, driver, AVI or full episode render measurement exists.

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
