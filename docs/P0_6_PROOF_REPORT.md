# P0.6 Bounded Functional Proof Report

**Date:** 2026-11-25  
**Repository:** Pawar-47/Cartoon-Studio, branch main  
**Scope:** architecture-critical functional proofs only. This report does not claim production subsystem integration.

## 1. Godot native-worker proof

| Run | Commit | Result | Evidence |
|---|---|---|---|
| Godot proof #1 | 35f0b1d54f5bbabad41c6055aab6857d6ac7e1b1 | FAILED (diagnostic) | Exposed PackedScene node ownership and project-relative MovieWriter output-path defects |
| Godot proof #2 | b05024110e76b684a5f8cee35eb57fa0428b2c11 | PASSED | [GitHub Actions run #2](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45566370409) |
| Godot proof #3 | ae9bad178c9999d5f5b7017a6409c7ee9c490786 | PASSED | [GitHub Actions run #3](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45566600241) |

Godot 4.7.2-stable official was downloaded from the pinned upstream release. The proof ran on Ubuntu 24.04 with Mesa llvmpipe and the Compatibility renderer.

All six machine-readable checks passed:
- GLB fixture imported as a PackedScene.
- Imported scene contains a MeshInstance3D.
- Animation was created and AnimationPlayer reports playback active.
- Dynamic scene serialized to PackedScene.
- Saved scene reopened with the imported GLB, animated proxy and AnimationPlayer present.
- 72 frames were recorded at 24 FPS.

MovieWriter output: 640×360, 24 FPS, 3.000 seconds, MJPEG video + PCM audio. This is a short functional export proof only.

## 2. FFmpeg MP4 assembly proof

Godot proof run #3 passed a follow-up FFmpeg conversion and FFprobe inspection:
- Container: MP4.
- Video: MPEG-4 Part 2, 640×360, 24 FPS.
- Audio: AAC.
- Duration: 3.000 seconds.

This demonstrates a working local AVI-to-MP4 assembly path. The CI host's FFmpeg build is not a distributable Cartoon Studio dependency. The production FFmpeg binary, encoder, patent position and license compliance remain separate Phase 1/7 release decisions; do not infer approval of H.264/libx264 or a GPL build from this test.

## 3. SQLite scene-queue architecture proof

Windows CI run #101 passed all 17 repository tests, including five new isolated proof tests in tests/test_sqlite_queue_proof.py:
- One scene lease at a time; ordered scene execution and assembly transition.
- Lease expiry reclaims only the interrupted scene and preserves completed scene output.
- Cancellation preserves completed outputs and prevents new scene claims.
- Cancellation requested during an active scene completes safely after the current scene and then stops.
- A stale worker cannot commit after another worker reclaims the lease.

The prototype is isolated under tools/ and is not production app code. It validates the SQLite-owned queue approach; Phase 1 must implement the production queue with migrations, bounded retry policy, durable event records, atomic output manifests and recovery tests.

## 4. Architecture decision supported by the proofs

Godot 4.7.2 Compatibility is accepted as the production 3D runtime candidate, hosted-runner functional proof passed. The production boundary remains a supervised native worker controlled by the existing FastAPI/browser application. Godot Web viewport remains optional and is not required for Phase 1. SQLite-owned queue and an FFmpeg process adapter remain the chosen local boundaries.

## 5. Explicit limitations

- No physical-PC test was performed or required. Target-PC performance, driver behavior, peak RAM, preview responsiveness and quality-preset tuning are Phase 8.
- The proof does not validate a complete 5–7 minute episode, production character rig, world generation, complex retargeted animation, Urdu voice, lip-sync, audio mixing or final visual quality.
- The proof did not test a Godot Web export or browser-embedded viewport; that path is optional and deferred.
- FFmpeg MP4 test used MPEG-4 Part 2/AAC in the hosted environment; final production codec and redistributable FFmpeg build remain unresolved.
- No engine, FFmpeg binary, TTS model, voice model or asset pack has been bundled into the application.
