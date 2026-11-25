# Research Log

## 2026-11-25 — Live repository reconciliation

- Confirmed repository `Pawar-47/Cartoon-Studio`, default branch `main`, and current HEAD `40bec8c423e953a0753c62f53c8a173274ac72e1`.
- Branch search returned only `main`.
- Read all 19 requested project documents; all 19 paths were present.
- Read current FastAPI/story source, application tests, CI workflow, Ara proof workflow and Ara patch script.
- Verified Cartoon Studio CI run #52 (`45487769827`) on current HEAD: Ruff, compile, 12 pytest tests, bootstrap ZIP packaging and upload all passed.
- Verified bootstrap artifact ID `14963389016`, 74,228 bytes, SHA-256 `423371c438c3b07a5b2aa3c38f6b26768078ffb1611e96b72d3c08a2e189d0ea`.
- Inspected Ara proof run #6 (`45486950450`) jobs and full logs. It was cancelled during browser-level MP4 export. Type-check and partial film/editor tests passed; Studio checks, Vite build and artifact upload were skipped. No artifact exists.
- Ara remains an unapproved candidate; the run does not prove export, complete build, target hardware compatibility or production readiness.

## 2026-11-25 — Existing source baseline

- `app/main.py` contains FastAPI routes, SQLite project metadata, story-plan validation and persistence.
- `app/story.py` contains a strict Pydantic episode schema, 5–7 scene/300–420 second constraints, cue timing checks and Ara-derived location/action/expression ID validation.
- `tests/test_app.py` contains 12 application tests.
- `.github/workflows/ci.yml` runs on Windows and packages a bootstrap ZIP.
- `.github/workflows/ara-foundation-proof.yml` clones Ara at `4151c1124b172fdd918d23e0ef4aad727f4984c1`, applies `scripts/patch_ara_foundation.py`, then runs type, film, Studio and build checks.

## 2026-11-25 — Ara export proof diagnosis

- Run #6 completed the film model checks and several browser editor checks, then entered the browser MP4 export test.
- The workflow log ends at the browser test's wait for the rendered/downloadable film; the job conclusion is cancelled.
- The evidence does not distinguish a slow export, encoder/browser limitation, export failure hidden behind the wait, or manual cancellation. Do not invent a root cause.
- Next: inspect the exact upstream export implementation and browser harness, make the proof bounded and failure-diagnostic, then run one controlled proof only after the Phase 0 gates and proof design are ready.

## 2026-11-25 — Prior research retained

- Ara 3D Gen source at `4151c1124b172fdd918d23e0ef4aad727f4984c1` has a Studio editor, scene/film timeline, procedural sets, character import, and browser MP4 export. It is early-preview software, not approved.
- Ara's original proof patches expand the film from five to seven scenes, increase JSON size to 700 KB and compact the inspector for short desktop viewports.
- Ara's default Supertonic 2 speech does not support Urdu.
- Ekza Studio, DvaitAI anim-studio, AnimStudio and Rhubarb Lip Sync NG remain comparative candidates/references.
- Smol Urdu TTS, tiny-urdu, DeepSpeak, Dia and XTTS Urdu fine-tune have unresolved quality, resource or licensing constraints; no TTS is approved.

## Evidence policy

Every research entry must include date, source URL, exact version/commit where relevant, what was actually inspected, outcome, limitations and next action. Search results alone are not evidence. Never convert partial CI success into a production capability claim.

## 2026-11-25 — P0.3 source-level candidate sweep 2

### 3D engine and hardware
- Inspected official Blender 4.5 release/requirements and Windows Intel troubleshooting pages, plus Intel's i3-5005U specifications.
- Confirmed Blender 4.5.17 LTS is current on 2026-11-24 and supported through July 2027; Windows support includes Broadwell. Blender 5.0+ raises Intel GPU floor to Kaby Lake.
- Confirmed i3-5005U is 2C/4T, HD 5500, OpenGL 4.3, SSE4.2/AVX2. Blender's published 4-core minimum and legacy Intel driver warning create a material target-hardware risk.
- Next: inspect actual installed driver and run a bounded Blender 4.5.17 target-PC proof before any engine freeze.

### World generation
- Inspected Bene Procgen Maps README, source files, license and CI metadata. Commit `f883ddb59eadcff319d3b28eee59da90d7c8c21f`; upstream Actions #18 SUCCESS. GPL-3.0; Blender 4.2+; modular seeded city/countryside/dungeon generation.
- Inspected Blender Level Architect README, license, test launcher and tree. Commit `660e2113a2987a172f001a95d305e303b6a2aad9`; upstream Actions #87 SUCCESS. GPL-3.0; 1,400+ claimed checks; broad city/interior/floor-plan generation; monolithic 1.2 MB main file.
- Neither candidate was executed locally or on target PC. No code was copied.

### Characters, NPR and lip-sync
- Inspected MPFB2 code/asset license split and current commit `650c5c53bd6989a8ac264f31fa1d11d4a0c7bd8a`; code GPL-3.0, supplied assets CC0.
- Inspected CharacterCreator; GPL-3.0 code and CC0-output claim only for CC0 input assets. Human style requires toon conversion.
- Inspected Anime-Tools README and GitHub license metadata; no verified license file, so do not copy. Inspected MIT blender-add-outline as a narrow outline technique.
- Inspected Parrot Lipsync README/license/commit `b569ee56a427833a9f561f45faec2677fdaff55e`; GPL-3.0 and custom phoneme table over Allosaurus. Inspected Allosaurus metadata/license; GPL-3.0 and old upstream. Inspected Charley3d Lip Sync README/manifest; version 1.0.6, GPL-3.0-or-later, Blender 4.4+, Vosk/Phonemizer/eSpeak. None proves Pakistani Urdu lip-sync.

### Queue, packaging, audio and assets
- Inspected sqlite-workqueue MIT license, pyproject, queue implementation and tests; version 0.1.0, Python 3.11+, lease/retry/idempotency implementation; latest inspected commit `4f7cf094a77ea44f984de61b39a13594efd5f7c5`, Actions #19 SUCCESS. Explicit missing cancellation/results/migrations.
- Inspected Huey MIT storage/API and docs; SqliteHuey and retry/result features, but in-flight crash caveat requires idempotent stages/checkpoints.
- Inspected PyInstaller, NSIS, Tauri and FFmpeg official licensing/packaging docs. No package or FFmpeg binary selected.
- Verified Kenney CC0 per pack, Poly Haven CC0 site-wide, Quaternius per-pack licensing and QAL v1.0 restriction. No assets were downloaded or copied.

### Urdu TTS
- Inspected Smol Urdu TTS linked GitHub code: no repo LICENSE found; PyTorch/torchaudio/Transformers/Liger Kernel plus WavTokenizer files; BF16 inference path.
- Recorded 1,000-vs-5,000 clip discrepancy between tiny-urdu GitHub README and model card.
- Inspected URDUTTS repository/dataset terms: dataset CC-BY-NC 4.0, code MIT.
- Checked official Alibaba Cloud docs: qwen-audio-3.1-tts-flash lists Urdu and a male Sahar voice; Qwen3-TTS system voices do not. Region, price, Pakistan access and naturalness remain unverified.

### Research status
This is the first broad source-level sweep, not P0.3 completion. No production engine, code dependency, TTS model, lip-sync system or asset pack has been selected or copied. Next: finish comparative engine/renderer and provider research, then P0.4 target hardware, Urdu and provider feasibility.

## 2026-11-25 — P0.3 AI-provider research sweep

- Read FreeMilk Terms and Privacy Policy. Confirmed daily model allowance with changing limits, no published exact quota, third-party model processing, advertising-partner sharing, possible AI-training/data-partner licensing of Coding Sessions, email opt-out for future licensing, and prohibition on direct scripts/bots/unofficial clients/server calls. FreeMilk is a manual supported app/GitHub agent, not a programmatic provider API.
- Verified FreeMilk's current website model list (GLM 5.3 Flash, DeepSeek V4.1 Flash, GPT-6 Luna) and Pakistan App Store listing. Actual account allowance is not publicly specified.
- Read official Gemini API pricing: free tier for selected models, limited rate limits, and free-tier content may be used to improve products.
- Read Groq rate-limit/model docs: current free model-specific quotas; e.g. selected text models show 30 RPM, 1,000 RPD, 8K TPM and 200K TPD. Must check account's current limits.
- Read Cloudflare Workers AI pricing: 10,000 Neurons/day on Workers Free, daily reset 00:00 UTC; some larger models require paid plan and usage above free allowance is billed.
- Read OpenRouter pricing/rate limits: free model variants 20 RPM / 50 RPD; after $10 lifetime credit purchase cap increases to 1,000 RPD; catalog and provider capacity are dynamic.
- Verified Copilot Free's 2,000 code completions/month and limited features; it is a coding UI/agent, not a general API.
- Verified ChatGPT consumer subscriptions and API billing are separate. Claude API has trial credits for new users but usage is billed. Perplexity Free has limited Pro searches and separate API product. Mistral Free mode does not include API access. Cerebras starts with $5 free credit. GitHub Models retired July 30, 2026.
- No API keys were connected and no user project source was sent to any external provider. Pakistan-specific API access, exact account quotas, provider privacy and output quality remain P0.4 checks.

## 2026-11-25 — Godot runtime and native world stack sweep

- Inspected Godot 4.7.2-stable source, MIT license, system requirements, Compatibility renderer, GLTF/Skeleton/Animation APIs and MovieWriter documentation. Godot 4.7.2 is stable; 4.8 is beta.
- Confirmed Compatibility renderer OpenGL 3.3; HD 5500 reports OpenGL 4.3. Godot minimum CPU is x86_64/SSE4.2 and 4 GB RAM; target meets minimum, but 2 physical cores are below recommended 4. 8 GB meets recommended memory.
- MovieWriter supports non-real-time fixed-frame recording, outputs OGV/AVI or PNG+WAV; MP4 needs FFmpeg. No target test.
- Inspected Terrain3D MIT v1.1.0 docs/source; latest main commit `69699ff0e3b629230dd1a0d7e6e7dda84cca2d26`, upstream CI #96/#2685 success on commit `43734bbada0b65fb5a642cfad0d9caeccfafade8`. Compatibility renderer fully supported since v1.0/Godot4.4.
- Inspected Godot Road Generator MIT v0.9.5, Godot4.4+, upstream Actions #169 success on dev commit `648f07295a6d1cd9e0607c71196f7a2de98e6fc5`; README explicitly says not feature complete.
- Inspected Building Generator MIT v0.2.0, Godot4.7, commit `c6e662360dbd8d51fb1e62e0d9ce03190ee5fa79`; 26 variants/3 LOD and manual test scripts; no CI found.
- Inspected Roommate MPL-2.0, commit `fd9381b5e833807c83e10af50fd95fb4ca0b6bb3`; creates interior meshes/collision/scenes/navigation; its Actions #12 is docs-only.
- Inspected OpenCity MIT, Godot4.7, procedural city/traffic/pedestrians/vehicles and headless test modes; only two commits, no CI, placeholder geometry.
- Inspected Godot AI Animation Toolkit 2.0.0 MIT, commit `e8f57c27c0374a6c76fce0e4b5d35d443ba3510b`, upstream Actions #386 success; requires Godot4.7.2 and Godot AI/MCP; 103 operations for motion, rigs, IK, retargeting and AnimationTree.
- Inspected Godot Toon Shader CC0 sample; Compatibility renderer works but shadow-casting lights produce overly bright toon bands in the sample.
- Inspected Ducz CharacterCreator; no code license found, so code cannot be copied. Its Quaternius assets are separately credited CC0.
- Revised leading on-paper runtime candidate from Blender to Godot 4.7.2 Compatibility. This remains unselected until target-PC tests and integration design.

## 2026-11-25 — Animation and CC0 pack source verification

- Inspected ItsAshn/godot-motion-matching README, MIT license, source tree and test files. Godot 4.7, pure GDScript, pose/trajectory search, inertialization, foot/hand IK and headless tests; no GitHub Actions workflow and no bundled animation assets. README's ~0.1 ms/search is an unverified author claim.
- Verified official Quaternius pack pages explicitly listing CC0: Universal Base Characters (6 bases, 20 hairstyles), Modular Character Outfits - Fantasy (12 outfits/62 parts), Ultimate Modular Men (11 modular characters/24 animations), Universal Animation Library (120+ clips), UAL2 (130+ clips), Downtown City MegaKit (300+ modular pieces), Modular Streets (25 pieces), Ultimate Buildings (76), Ultimate House Interior (123), Ultimate Furniture (20), Cars (8), Public Transport (12).
- Read Quaternius FAQ and QAL v1.0. Every pack is either CC0 or QAL; QAL permits finished products but prohibits standalone asset redistribution. Only the exact CC0 pack pages above are eligible for the initial in-app redistributable asset library.
- No packs were downloaded, no code/assets were copied, and no target-PC test was run. Build an independent recipe-based character editor; do not copy Ducz.CharacterCreator because its repository code has no license.

## 2026-11-25 — Audio, final video and lip-sync pipeline research

- Inspected Godot 4.7 Movie Maker docs, Audio Playback Tracks and Audio Buses. Audio tracks display waveforms and can be scheduled on the animation timeline; buses separate dialogue/music/ambience/SFX with effects/meters.
- Verified MovieWriter CLI options for exported projects: `--write-movie`, `--fixed-fps`, `--resolution`, `--quit-after`. Non-real-time rendering keeps fixed frame pacing. Exported-project output is AVI/MJPEG (4 GB cap) or PNG+WAV; OGV is editor-build only. Audio mix rate must divide evenly by FPS; 48 kHz works for 24/30/60 FPS.
- Inspected FFmpeg official legal page. Default LGPL-2.1+; GPL codecs such as libx264/libx265 change the build license. OpenH264 is BSD and may provide an H.264 path without enabling FFmpeg GPL, but quality, bitrate and patent terms need proof.
- Inspected Kenney Music Jingles (85 CC0 stingers), Impact Sounds (130 CC0), Digital Audio (60), Interface Sounds (100), UI Audio (50), RPG Audio (50) and Voiceover Pack (90, not Urdu). Inspected OpenGameArt CC0 music-loop pages and the S3M1TR4SH catalog's provenance approach. Content ID status must be tracked separately from copyright permission.
- Allosaurus universal model `uni2005` is about 41.5 MB; CPU-capable, uses approximate CTC phone timestamps, and only English has a language-dependent model listed. Urdu inventory availability must be checked using `list_lang` on the pinned model; no Urdu-specific acoustic model has been confirmed.
- Parrot Lipsync v1.1.2 uses Allosaurus and an editable phoneme-to-viseme table, supports Blender 4.5, and is GPL-3.0. It is a Blender add-on, not a Godot plugin. If Godot is selected, implement a Godot-owned viseme timeline and use only the general data-flow idea unless the GPL component is explicitly approved.
- No audio/music assets, model weights or FFmpeg binaries were downloaded; no lip-sync or video render was run.

## 2026-11-25 — VRM face-expression and eSpeak NG Urdu support
- Inspected V-Sekai/godot-vrm root MIT license, separate MToon MIT license, README, source tree and sample license file. Latest commit `e15199f980064028bfa4fbee5e70dddb82dd55c3` updates Godot 4.7 imports; no Actions workflow. VRM0/1 import, VRM1 export, MToon, humanoid retarget and expression tracks are implemented; several node constraint/spring bone/lookAt/export limitations recorded.
- Inspected VRM 1.0 expression specification: emotion presets, five vowel visemes, blink/gaze and custom expressions with overrideMouth/overrideBlink/overrideLookAt. The spec does not prescribe facial geometry; models need blendshapes.
- Inspected eSpeak NG repo, GPL3 COPYING, README and Urdu language data. Latest commit `ee9fa7cc4704d683020526f47a9655f14c8d5f4c`, pushed 2026-11-19. Current source includes `ur`, `ur_rules` and `ur_list`; pronunciation rules credited to Him Prasad Gautam and Ejaz Shah (Pakistan).
- eSpeak NG is a compact C formant synthesizer with Windows support, WAV output and phoneme output carrying pitch/length information. README warns its voice is less natural than larger recording-based synthesizers. Record as offline Urdu G2P/placeholder TTS only, not main voice.
- No VRM sample avatar or eSpeak binary was downloaded; no Urdu synthesis or face-animation test was run.

## 2026-11-25 — WhisperX Urdu aligner and P0.3 source-research closeout
- Inspected WhisperX current main commit `8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365`, BSD-2-Clause, pyproject `3.8.7rc1` and alignment source. The source maps `ur` to `kingabzpro/wav2vec2-large-xls-r-300m-Urdu` and supports optional character-level alignment.
- Inspected Urdu model card: Apache-2.0, 300M parameters, 16 kHz mono, Common Voice 8.0 Urdu, reported WER 39.89% / CER 16.70% with 5-gram decoding; model card warns about accent, code-switching, noise, vocabulary and utterance length.
- Full WhisperX dependencies include PyTorch, torchvision, pyannote-audio, faster-whisper, CTranslate2, Transformers, NLTK and related libraries. Minimal alignment-only packaging and 8 GB CPU performance remain untested.
- Checked Sadda's multilingual phoneme model language list; Urdu is not listed, so it is not a reliable Urdu candidate. Allosaurus remains an unverified universal phone alternative.
- Concluded P0.3 source-level research coverage across engines, character/facial systems, world, animation, rendering, Urdu voice/lip-sync, audio, queues, packaging, AI providers, hardware and licensing. Added a separate provisional scorecard; no candidate is selected and no target-PC test was run.

## 2026-11-25 — P0.4 Urdu voice and provider feasibility refresh

### Urdu G2P and forced alignment
- Inspected eSpeak NG's actual Urdu rule file: https://github.com/espeak-ng/espeak-ng/blob/master/dictsource/ur_rules contains Urdu-script letter groups, vowel/consonant rules and Urdu-specific mappings. This is not evidence of Pakistani-accent voice quality; G2P output must be compared against human-reviewed pronunciation.
- Inspected eSpeak NG CLI source/manual: -v ur, -x, --ipa and --phonout expose phoneme output without requiring speech playback. eSpeak NG is GPL-3.0; bundling it in the Windows app needs a license/notice review.
- Inspected WhisperX README and upstream alignment.py. Current upstream code explicitly maps language code ur to kingabzpro/wav2vec2-large-xls-r-300m-Urdu. WhisperX README documents CPU inference with --compute_type int8 --device cpu, but the Urdu aligner is 300M parameters and the target has only 8 GB RAM. No CPU speed, memory, word timing or Pakistani-accent quality test has been run.
- WhisperX is BSD-2-Clause. Its language-specific alignment model is a separate Hugging Face artifact with its own model-card license and dataset provenance; those must be checked before redistribution.
- Decision: keep eSpeak NG as an offline G2P/diagnostic candidate, not a natural Urdu TTS voice. Keep WhisperX+Urdu wav2vec2 as a conditional alignment candidate, not an approved default. Require manual viseme/timing correction.

### Urdu TTS and cloud-region facts
- QwenCloud's official voice list identifies qwen-audio-3.1-tts-flash-sahar_ur (Sahar / سحر) as a male Urdu voice with timestamps and SSML. Its TTS HTTP API lists Singapore and China North 2 (Beijing) as supported regions. Official standard Singapore pricing is $0.23/M input tokens and $1.87/M output tokens; therefore this is not a free or local default.
- Pakistan access to a Singapore Qwen endpoint, payment/account eligibility, privacy terms, Pakistani accent quality and output timestamp usefulness remain unverified. Do not describe it as Pakistan-hosted or guaranteed accessible.
- Gemini API official supported-region list includes Pakistan. Free-tier input/output is available for selected models, but Google's pricing page explicitly says free-tier content may be used to improve products; paid-tier content is not. Current per-model quota and project eligibility still require a live account check.
- Groq's official limits page currently lists model-specific free limits including GPT-OSS 120B/20B and Qwen3.8-27B at 30 RPM, 1,000 RPD, 8K TPM and 200K TPD; organization/account limits can differ. Groq Trust Center says data centres are in US, Australia, Canada, Finland and Saudi Arabia; regional endpoints are an Enterprise arrangement.
- Cloudflare Workers AI official pricing: 10,000 Neurons/day free, $0.011 per 1,000 Neurons above free on Workers Paid, reset 00:00 UTC; some models require paid billing.
- OpenRouter official free variants: 20 RPM and 50 RPD; 1,000 RPD after at least $10 lifetime credits. Model/provider caps and third-party data handling vary.
- No API key was connected, no provider account was accessed, and no request/audio was sent to a cloud service.

### Next evidence needed
- Actual target-PC probe output and exact Intel driver.
- A short, consented native Pakistani Urdu recording plus its verbatim human-corrected transcript, ideally 30–60 seconds covering aspirated/retroflex consonants, nasalization, long/short vowels, common names and code-switching.
- Human-reviewed eSpeak Urdu IPA/phoneme output and WhisperX forced alignment timings for that sample.
- Optional Qwen Sahar sample only after the user explicitly authorizes use of an external paid service and reviews the privacy/price terms.

## P0.4 Urdu/provider feasibility batch closeout
- Documentation batch commit: 6823cdf8913fc6b645017a6b459c06062d2cc973.
- GitHub Actions run #88 completed SUCCESS on the exact commit: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45562534763.
- Updated AI provider region/quota/privacy/pricing evidence, created URDU_VOICE_FEASIBILITY.md, corrected the live status/next-step checkpoint and updated AI-R003 / VOICE-R001 / VOICE-R002 evidence. This remains source-level research only; no real Urdu audio, API key or target-PC benchmark was tested.

## 2026-11-25 — P0.4 Urdu model-card and code-level follow-up
- Inspected the actual Hugging Face model card and file tree for WhisperX's Urdu aligner, kingabzpro/wav2vec2-large-xls-r-300m-Urdu. It is Apache-2.0 metadata, 300M parameters, 1.41 GB FP32 model files, trained on Common Voice 8.0 Urdu; model-card WER/CER are 39.89%/16.70% with 5-gram decoding. This is not a strong standalone ASR transcript source. Keep it only as a forced-alignment candidate, and measure boundary accuracy separately.
- Inspected the newer kingabzpro/whisper-large-v3-turbo-urdu model card: Apache-2.0 metadata, 0.8B parameters, 3.24 GB FP32 checkpoint, self-reported Common Voice 17.0 Urdu WER 26.234% / CER 8.795%. It is a separate ASR model, not the WhisperX Urdu aligner. An 824 MB CTranslate2 int8 conversion exists, but CPU performance remains untested.
- Inspected Proxima-AI-Co/smolurdu GitHub repository tree and source files. No LICENSE file exists in the current code tree. Inference uses BF16, Liger Kernel, PyTorch/torchaudio/Transformers and separate WavTokenizer checkpoint/config; setup.py omits some runtime dependencies. The target CPU's BF16 path is unverified.
- Decision: do not approve Smol Urdu TTS for redistribution or target default. The Urdu wav2vec2 model stays conditional for forced alignment only; use a human-corrected transcript and native-speaker validation. No weights were downloaded and no audio was processed.

## 2026-11-25 — P2.2 modular character creator research

Research was redirected from retarget-only polish to the master brief's missing original-character creation workflow.

- Official Quaternius pages confirm the Ultimate Modular Men Pack (11 characters) and Ultimate Modular Women Pack (10 characters) are CC0, each with 24 animations and four interchangeable character parts.
- The pinned GLB conversions in LuanDucate/Ducz.CharacterCreator expose 21 outfit files totalling 34.92 MiB. Three representative models (Male Adventurer, Male Worker, Female Adventurer) are used for initial Godot acceptance; the model JSON reports a shared 62-joint rig and 24 animation clips.
- The host repository has no declared code license. The project will use only the Quaternius CC0 model files and independently implement the modular assembly and authoring workflow.
- The newer Universal Base Characters + Modular Character Outfits - Fantasy packs have a stronger standard-humanoid direction, but the standard outfit archive is 280 MiB and animation clips are a separate dependency; defer until the smaller first creator slice is proven.
- Configura is MIT-licensed but is a Godot editor plugin with an unstable release status; it is not a good runtime dependency for the browser-first app/headless-worker architecture. It is not vendored.
