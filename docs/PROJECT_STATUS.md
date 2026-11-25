# Project Status — 2026-11-25

## Live GitHub checkpoint

- P0.2 atomic requirements and traceability batch is pushed to `main` as the current checkpoint; CI run #70 is in progress.

- Repository: `Pawar-47/Cartoon-Studio`
- Branch: `main`
- Starting HEAD for this batch: `4171bb320a10c3d7cfec561f706f7e10ebd3bacd`
- Latest completed CI before this batch: run #68 — SUCCESS on that exact HEAD.
- Previous application CI run #67: Ruff, Python compileall, 12 pytest tests and Windows bootstrap ZIP upload passed.
- Current artifact is bootstrap-only; it is not a self-contained installer.

## Master-brief compliance

The original 25-part prompt was reread in full (1,133 lines, 4,642 words; SHA-256 `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`). P0.2 now has 171 atomic requirements with mandatory metadata and a corresponding traceability row for each. The exact prompt file is not yet in GitHub; its verbatim preservation remains open.

## Implemented and tested foundation

- FastAPI backend, static dashboard and Story Generator workspace.
- SQLite project metadata and partial story-plan schema/validation.
- CI pipeline and Windows bootstrap ZIP.
- CI run #68 passed on the pre-P0.2 alignment HEAD.

## Partial work that must be preserved

- Existing Story Generator and schema are early, out-of-sequence work. Preserve it; freeze feature expansion until Phase 4.
- Existing Ara-derived action/location/expression IDs are provisional validator catalogs only. Do not treat them as stable engine-neutral IDs or playback proof.
- Ara proof run #6 was cancelled during MP4 export; no production engine is approved.

## Not implemented or not verified

No production Character Studio, persistent World Builder, canonical animation playback/library, direct multi-provider AI orchestration, research agent, verified Pakistani Urdu TTS, lip-sync, audio mixer, full 3D renderer, MP4 episode pipeline, scene cache/recovery, self-contained installer or target-PC benchmark has been demonstrated. No complete Windows installation has been verified. No requirement is marked VERIFIED.

## Correct phase sequence

0. Complete specification and GitHub research.
1. GitHub and CI/CD foundation.
2. Character Studio.
3. World Builder.
4. Story and Scene Engine.
5. Animation Engine.
6. Urdu Voice and Lip-Sync.
7. Episode Generator.
8. Optimization and Reliability.

## Immediate priority

P0.3 — continue the comparative source-level research sweep. P0.4 hardware/Urdu/provider feasibility follows P0.3. P0.5 architecture freeze follows P0.3–P0.4. Do not begin production feature implementation before P0.7 exits. Do not start Phase 2 until Phase 1 installation gate passes.

## P0.3 research checkpoint

- P0.2 is complete: 171 atomic requirements, 171 traceability rows and 75 legacy aliases. Final CI run #71 passed on the P0.2 commit.
- P0.3 source-level sweeps inspected Blender/Godot compatibility, Godot-native world plugins, procedural Blender world generators, character-generation candidates, NPR/outline approaches, Urdu lip-sync candidates, SQLite queues, Windows packaging, FFmpeg licensing and individually verified CC0 asset packs.
- No engine or code dependency is selected. No candidate code or assets were copied.
- Major risk discovered: target i3-5005U is 2C/4T, below Blender's published 4-core minimum; HD 5500 has a documented legacy driver crash issue. P0.4 must test exact driver and actual hardware.
- Current candidate set: Godot 4.7.2 Compatibility as leading on-paper runtime; Terrain3D/Road Generator/Building Generator/Roommate as Godot-native environment candidates; Blender 4.5 and its world/character add-ons as optional authoring research; Ara/Ekza as browser-editor candidates; Parrot/Allosaurus as Urdu lip-sync research only.
- Urdu TTS: no local model approved. Qwen-Audio-TTS 3.1 Flash officially lists Urdu but is cloud-only and requires P0.4 review of Pakistan availability, pricing, terms, privacy and quality.

## AI provider research checkpoint
- FreeMilk is confirmed as a manual coding agent with GitHub integration and a daily allowance, but not a programmatic API. Its terms prohibit scripts/direct server calls; its privacy policy allows third-party model processing and possible AI-training/data-partner licensing of coding sessions unless the user opts out for future sessions.
- Current official API candidates with free usage: GroqCloud, Cloudflare Workers AI, Gemini Developer API and OpenRouter. Each has quotas and privacy/region caveats.
- GitHub Models is retired; Copilot Free is limited to 2,000 completions/month and is not a backend API. ChatGPT, Claude and Perplexity consumer free plans do not provide a general free API.
- No provider is integrated or approved. No API keys have been connected.

## Godot runtime research checkpoint
- Godot 4.7.2 Compatibility renderer is now the strongest on-paper runtime candidate for the target i3-5005U/HD 5500/8 GB machine: OpenGL 3.3 compatibility, minimum SSE4.2 CPU and 4 GB RAM. The target meets minimum requirements but is below recommended 4-core CPU.
- Native Godot candidates: Terrain3D (MIT; Compatibility renderer supported), Road Generator (MIT; incomplete), Building Generator (MIT; 26 low-poly variants), Roommate (MPL-2.0), OpenCity (MIT prototype), and Godot AI Animation Toolkit (MIT, optional authoring tool).
- Blender 4.5 remains optional asset-authoring research, not the target runtime leader.
- No target-PC test or integration has been performed; no engine/plugin is selected.

## Animation and asset research checkpoint
- Godot's built-in BoneMap/SkeletonProfileHumanoid retargeting plus Quaternius Universal Animation Library and UAL2 provide a potential CC0 starting point of 250+ humanoid clips.
- Quaternius Universal Base Characters and Modular Character Outfits provide CC0 modular bodies/clothing; Downtown City, Modular Streets, buildings, interiors, furniture, cars and public transport packs provide CC0 environment assets.
- These packs are not yet downloaded or imported. Exact pack license files must be preserved; QAL packs are excluded from the in-app asset library.
- Godot Motion Matching is an optional MIT future candidate with no upstream CI; use simple AnimationTree + UAL first.

## Audio and episode-render research checkpoint
- Godot Audio Playback Tracks and Audio Buses can handle dialogue, music, ambience and SFX on a single timeline.
- Godot MovieWriter supports non-real-time fixed-FPS rendering; exported projects output AVI/MJPEG (4 GB cap) or PNG+WAV. OGV is editor-build only. FFmpeg is required for MP4.
- FFmpeg default LGPL build is compatible with a more permissive distribution path; avoid GPL libx264/libx265 unless the project license decision allows it. OpenH264 BSD is a possible H.264 encoder candidate, not tested.
- Kenney CC0 packs cover SFX and short jingles; OpenGameArt CC0 loops are available but need per-track license and YouTube Content ID checks.
- Urdu lip-sync remains unproven. WhisperX maps Urdu to a word/character aligner model; eSpeak NG provides Urdu G2P; Allosaurus is an unverified phone-level alternative. No Pakistani sample, timing quality or target-PC performance has been tested. Manual correction remains required.

## Face-expression and Urdu phoneme research checkpoint
- VRM 1.0 provides a humanoid expression contract: five vowel visemes, emotion presets, blink/gaze and custom expressions. The MIT Godot VRM add-on imports/exports VRM and includes an MIT MToon shader; several features still need proof.
- eSpeak NG includes Urdu `ur` language rules and can output phoneme/pitch/length data locally. It is compact but formant TTS is robotic; retain it only as offline G2P/placeholder voice, not the main production voice.
- Allosaurus remains an unverified audio-to-phone candidate; actual Urdu timing must be measured on native recordings. Manual viseme editing remains required.
- No VRM avatars, eSpeak binary or voice models have been downloaded or integrated.

## Current checkpoint — 2026-11-25

- **P0.1 baseline audit:** completed in the prior checkpoint.
- **P0.2 atomic requirement registry and traceability:** completed; the exact original brief is now preserved at `docs/MASTER_EXECUTION_PROMPT.md`.
- **P0.3 source-level research and candidate scorecard:** complete. See `docs/CANDIDATE_SCORECARD.md`. Godot 4.7.2 Compatibility is the leading on-paper runtime candidate, not a frozen selection.
- **P0.4 target-hardware, Urdu and provider feasibility:** ready to start. No target-PC tests, Pakistani Urdu voice tests or account-specific provider quota checks have been run yet.
- P0.3 closeout commit: `5bcbf8775014c4b25699a9bdcb5e633c5fa00811`; GitHub Actions run #84 SUCCESS. Latest main HEAD at this checkpoint is the same commit.
- **P0.5 architecture freeze:** blocked by P0.4. **P0.6 bounded proofs:** blocked by P0.5. **P0.7 plan freeze:** blocked by P0.2–P0.6.
- Existing FastAPI/SQLite/browser shell and Story Generator remain preserved; no production feature expansion before P0.7.
