# Next Steps — 2026-11-28

## Live checkpoint

- Repository: `Pawar-47/Cartoon-Studio`; active branch `main`.
- Newest batch: redistribution-safe video encoding with a bundled LGPL FFmpeg (Batch A, FFmpeg half) — awaits its own CI run.
- Owner decisions on record: no GPL video encoder; voice uses both a pinned Piper TTS path and a recorded-WAV fallback.
- Binding source: `docs/MASTER_EXECUTION_PROMPT.md`, all 25 parts. Do not create or switch development branches.

## Current objective

Finish Batch A's voice half, then Batch B and Batch C. The FFmpeg half is implemented;
the installed app can assemble an MP4 with the bundled LGPL FFmpeg and a
redistribution-safe encoder, but it still cannot synthesise Urdu speech because
`piper-tts` is not in the locked environment.

## Immediate next steps

1. **Finish the TTS half of Batch A.** Add `piper-tts` and `onnxruntime` to the locked
   environment through `.github/workflows/resolve-python-lock.yml`, vendor the wheels into the
   installer, and bundle the two pinned `ur_PK` voices so speech synthesis works offline.
   The recorded fallback (per-line WAV upload, validation, mixing) is already implemented.
2. **Record control in the Story workspace**, so the recorded fallback is reachable without
   the API: pick a dialogue line, record, review the stored WAV, and show whether the line is
   recorded or synthesised before generation.
3. **Batch B — real job execution.** Background worker, per-scene progress, cooperative
   cancel, and the Episode Renderer, Logs and Diagnostics workspaces.
4. **Batch C — scene cache and checkpoints**, so one failed scene never re-renders the
   whole episode.
5. P2.2 remaining visual acceptance proceeds in parallel: interactive browser acceptance of
   hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on
   representative models.

## Recent completed batches

### Recorded Urdu dialogue fallback (Batch A, voice half)
`PUT /api/projects/{id}/story/audio/lines/{scene_id}/{line_index}` stores a mono 16-bit
22,050 Hz WAV for one dialogue line (20 MiB limit, scene-boundary check); `GET .../audio/recordings`
lists recorded lines; `generate_episode_audio(..., recordings=...)` mixes recorded and
synthesised lines and reports `recorded_line_count`/`tts_line_count` in the audio manifest.
A recorded line works with no speech engine installed.

## Recent completed batches

### Redistribution-safe encoding and bundled LGPL FFmpeg
No GPL encoder is bundled or used. `app/render.py` selects `libopenh264`, `libvpx-vp9`,
`libaom-av1`, `libsvtav1` or native `mpeg4` from the build's encoder list and refuses a
GPL-only build; the chosen encoder is recorded in `render.json`. `engine/ffmpeg_runtime.json`
pins BtbN's win64 LGPL FFmpeg n8.1 by URL and SHA-256; `scripts/fetch_ffmpeg.py` verifies
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
