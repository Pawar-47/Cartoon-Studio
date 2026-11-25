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
