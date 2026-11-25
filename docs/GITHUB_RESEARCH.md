# GitHub Open-Source Research Log
Research date: 2026-11-25. Recheck moving upstream projects before pinning a version.

## Primary candidate: Ara 3D Gen
Repository: https://github.com/olatunde85/3d-gen  
Source license: repository LICENSE says MIT.  
Stack: TypeScript, Vite, Three.js, browser-based 3D scene and canvas rendering.  
Relevant source: src/studio/actor.ts, animations.ts, catalog.ts, export.ts, film.ts, main.ts, project.ts, scene.ts, sets.ts, and src/studio/audio/*.

### Confirmed capabilities from source/docs
- Character builder and reusable character export.
- Studio film editor with cast, sets, action beats, camera shots, timeline, sound, text and project save/import.
- README/Studio guide lists 71 original sets.
- Up to 5 characters per scene.
- Procedural set geometry is generated in browser; the guide says sets are original and built in browser with no downloads.
- Browser canvas MP4 export using Mediabunny, 30 frames per second.
- Multiple scenes can be assembled into one film.
- Current source constants: MAX_SCENES = 5; each StudioProject MAX_DURATION = 60 seconds; thus current hard limit is 5 minutes. The requested 5–7 minute target requires changing scene count to at least 7 and updating validation/file-size/UI/export tests.
- Studio docs call it an early preview. It is not a finished production-grade product.
- Character assets derive from MakeHuman source data, described in scripts/ASSETS_LICENSE.txt as CC0 1.0.
- Motion clips include CMU Graphics Lab mocap data. Its terms permit commercial use but prohibit direct resale, including converted form, and require acknowledgement. Keep provenance/attribution.
- setup-assets downloads about 280 MB of MakeHuman system assets. CMU BVH downloads are only needed to rebuild baked motion data; baked data is committed.
- package.json requires Node >=20; build uses TypeScript, Vite, maps, media fetching and schema/docs generation.
- Studio has local speech generation through Supertonic 2 ONNX with F1/F2/M1/M2 voices. This is NOT suitable for Urdu: the official Supertonic 2 model card lists only English, Korean, Spanish, Portuguese and French. Official Supertonic 3 discussion also says Urdu is not supported. Do not use these voices for Urdu dialogue.
- MP4 encoding is browser capability-dependent and exports at 30fps; low-end Intel HD 5500 performance needs real testing.

### Candidate assessment
Ara is the strongest discovered candidate for a reusable character/scene/animation/film-editor foundation. It offers far more existing functionality than a scratch-built editor. However, its character assets are MakeHuman-derived human models rather than the final stylized cartoon look, it is an early preview, the current maximum film duration is 5 minutes, and its built-in speech does not support Urdu. It is therefore a high-priority integration candidate, not yet accepted as the final product without a Windows build and target-hardware proof.

Potential adoption strategy: pin upstream as a submodule or separately built upstream component, keep Cartoon Studio-specific changes in this repository as tracked patches/adapters, extend film length to 7 scenes, develop original toon-style character presets/materials, and replace/augment speech with a tested Urdu TTS adapter. Do not redistribute any asset/model whose terms are unclear.

## Other animation candidates

### Ekza Studio — https://github.com/ekza-space/ekza-studio
Browser GLB/VRM modeling, rigging, IK, keyframe animation, Dope Sheet and Graph Editor. Alpha status; README documents known gaps. package.json requires Node >=24.11 and pnpm. Main license MIT; anim-core Apache-2.0; fixtures separately licensed; brand/logo not licensed. Potential focused editor integration, but not a full episode pipeline.

### DvaitAI anim-studio — https://github.com/DvaitAI-tech/anim-studio
YAML story to Blender-rendered voiced/captioned 3D video using Python, Blender and FFmpeg. GitHub metadata reports MIT. Small prototype; Hindi-oriented speech sample and incomplete word-accurate lip-sync. Useful scene-schema and renderer-orchestration reference, not a complete base.

### AnimStudio — https://github.com/Sheggyb/AnimStudio
Browser character rigging and animation editor; GLB/FBX import, animation packs, keyframes and export. AGPL-3.0-or-later. Copyleft and third-party motion-pack terms require legal review. Reference only for now.

### Rhubarb Lip Sync NG — https://github.com/Premik/blender_rhubarb_lipsync_ng
Blender integration for Rhubarb cue capture and baking to animation actions/NLA. README says Blender 4.2+ extension. Urdu cue quality and exact release/source license still need verification.

## Urdu TTS candidates

### Supertonic 2 — https://huggingface.co/Supertone/supertonic-2
Ara's built-in local voices use this model. Official model card lists 5 languages: English, Korean, Spanish, Portuguese and French; Urdu is absent. Model is OpenRAIL-M, not plain MIT. Do not use it for Urdu speech.

### Smol Urdu TTS V1 — https://huggingface.co/ProximaAI/smol-urdu-tts-v1
135M parameters, Urdu, 24 kHz, Apache-2.0 model card. Explicitly experimental and quality may be imperfect. Potential low-resource CPU candidate, but memory, latency, output quality and voice consistency must be benchmarked.

### tiny-urdu — https://github.com/Zafar205/tiny-urdu
21 MB ONNX model, 4.5M parameters, browser/CPU inference, Roman Urdu input only, one male voice, trained on 1,000 clips from one speaker. README states a robotic tone and mispronunciations are expected. Its training dataset is the UrduTTS corpus; the dataset card states CC-BY-NC 4.0 and commercial use is out of scope. No explicit GitHub LICENSE file was found in the repository listing. Do not redistribute/use commercially until model and training-data rights are clarified. Could be evaluated only as a non-commercial research prototype if allowed.

### DeepSpeak-v1 — https://huggingface.co/mahwizzzz/deepspeak-v1
Experimental Urdu model, roughly 400M parameters, Apache-2.0 stated for model; codec weights have separate terms. Model card says training is incomplete (18k/100k steps), reference audio needed for best results, short sentences preferred. Likely too heavy for the target machine; research only.

### Dia-1.6B-Urdu — https://huggingface.co/mahwizzzz/Dia-1.6B-Urdu
Urdu fine-tune, 1.6B parameters, model card cites RTX 3090 24GB VRAM. Not suitable as a required local runtime on the target PC.

### XTTS Urdu fine-tune — https://huggingface.co/suhaibrashid17/XTTS-v2-Urdu-FT
Approximately 5.65 GB weights; model card says MIT but it is based on XTTS-v2, whose upstream model uses Coqui Public Model License. Resolve derivative/base model rights and resource requirements before use. Too large for the 8 GB target machine as a default local dependency.

## Current research conclusion (revised)
No production engine, character generator, world generator, toon renderer, Urdu TTS or lip-sync system is selected. Blender 4.5.17 LTS plus a browser-first UI is a plausible local architecture candidate, but the target PC is below Blender's published CPU minimum and has a documented legacy Intel driver risk. Bene Procgen Maps and Blender Level Architect are strong world-generation candidates but GPL-3.0 and not target-tested. Ara and Ekza remain editor candidates with incomplete/cancelled CI evidence. The next proof work must be bounded and hardware-aware. Keep the system modular, local-first, offline-capable, and preserve a manual voice-recording fallback.

## 2026-11-25 — Source-level research sweep 2

### Local 3D production engine: Blender 4.5 LTS
- Official release page lists Blender 4.5.17 LTS on 2026-11-24 and support through July 2027: https://www.blender.org/releases/4-5/
- Windows requirements for Blender 4.5 include Intel Broadwell and newer. Blender 5.0+ raises the supported Intel GPU floor to Kaby Lake, which excludes HD Graphics 5500.
- Intel's i3-5005U specification confirms Broadwell, 2 CPU cores / 4 threads, SSE4.2, AVX2, HD Graphics 5500 and OpenGL 4.3: https://www.intel.com/content/www/us/en/products/sku/84695/intel-core-i35005u-processor-3m-cache-2-00-ghz/specifications.html
- Blender's published minimum is 4 CPU cores with SSE4.2 and 8 GB RAM. The target has 2 physical cores and exactly 8 GB; it is below the CPU minimum and at the RAM minimum. HD 5500 is integrated/shared-memory graphics, so the stated dedicated 2 GB GPU requirement is not a guaranteed match.
- Blender 4.5's Windows Intel troubleshooting page warns that newer Intel drivers can crash on 3rd–5th generation iGPUs. It lists 20.19.15.4835, .4963 and .5063 as known working, and .5126, .5144, .5166 and .5171 as known failing. The exact driver on the user's PC has not been inspected.
- Candidate operating mode: browser UI + lightweight 3D preview, Blender 4.5.17 as a local background asset/scene/render process, CPU rendering and sequential work as a fallback. This is a hypothesis; startup, viewport, geometry generation, CPU rendering and RAM must be measured on the target PC.

### World/environment generation
**Bene's Procedural Maps** — https://github.com/Beneking102/bene-proggen-maps
- Inspected repository source/docs and latest main commit `f883ddb59eadcff319d3b28eee59da90d7c8c21f`; GitHub Actions run #18 succeeded on that commit.
- GPL-3.0; Blender 4.2+; modular Python/Blender generator. README describes seeded city/countryside/dungeon generation, roads, sidewalks, buildings, parks, river/bridges, terrain, props, signage, lighting and glTF export. No external model/texture files are required for its procedural geometry path.
- README describes 50 seeds across four city presets and 50 seeds across three dungeon themes. Optimization notes report roughly 4.1–4.3 seconds for a small town and 11 seconds for a metropolis on the author's machine, with high-density examples around 1.1 million vertices and thousands of props. Not a target-PC benchmark.
- Strong modular urban-world candidate. Risks: GPL-3.0 compatibility, high object/vertex counts, no persistent episode-world data contract or animated vehicle system, and no test on Blender 4.5.17 / HD 5500.

**Blender Level Architect** — https://github.com/dottyboy/BlenderLevelArchitect
- Inspected README, GPL-3.0 license, headless test launcher and repository tree. Latest inspected main commit `660e2113a2987a172f001a95d305e303b6a2aad9`; Actions run #87 succeeded.
- Blender 4.2+; README claims 1,400+ automated checks and tests on Blender 4.2.21 and 5.2.1/5.2.2. Features include seeded dungeons, rooms/corridors/stairs, castles, villages, hill cities, floor-plan-to-house generation, terrain/biomes, walkability checks and glTF/GLB export.
- Principal implementation file is approximately 1.2 MB and the headless test file approximately 386 KB. This is a substantial maintenance/integration risk despite broad features and successful upstream CI. Candidate for isolated add-on evaluation or selective reference, not an automatic merge.

### Character creation and rigging
**MPFB2** — https://github.com/makehumancommunity/mpfb2
- Active Blender add-on; latest inspected main commit `650c5c53bd6989a8ac264f31fa1d11d4a0c7bd8a`, pushed 2026-11-22. Code license file states GPL-3.0; separate asset license file states CC0 for supplied MakeHuman assets. Blender 4.2+.
- Provides procedural human generation and Blender rig/asset workflows. It creates human-like base characters, not the final Cartoon Studio toon style.

**CharacterCreator** — https://github.com/kblood/CharacterCreator
- GPL-3.0 code, MakeHuman/MPFB-derived human generation, with project notes describing generated outputs as CC0 when built only from included CC0 source assets. It includes a Three.js viewer and GLB workflow.
- Useful for studying persistent character parameters and GLB export, but human proportions/style do not satisfy the final cartoon look without substantial work. Verify provenance for every output.

### Toon/NPR rendering
- **Anime-Tools** — https://github.com/Kraxziss/Anime-Tools: README describes Blender 4.5.2 cel shading, outline and Grease Pencil/Line Art workflows. GitHub reports no SPDX license and no standalone LICENSE file was found. Research/reference only; do not copy until licensing is clarified.
- **blender-add-outline** — https://github.com/azeemba/blender-add-outline: MIT, last pushed 2023-11-30, small inverted-hull/Solidify outline add-on. Narrow technique reference, not a complete toon renderer and not yet validated on Blender 4.5.17.
- Safe candidate remains a Cartoon Studio-owned material/outline system built on Blender's documented nodes and renderer APIs after engine decision.

### Urdu lip-sync and phoneme analysis
**Parrot Lipsync** — https://github.com/blackears/parrotLipsync
- GPL-3.0; uses Allosaurus to convert audio to phonemes, then maps phonemes through an editable JSON phoneme table to mouth poses/keyframes. Requires FFmpeg. Latest inspected commit `b569ee56a427833a9f561f45faec2677fdaff55e`, pushed 2026-07-07.
- Promising because a custom Urdu phoneme-to-viseme table can be authored. Allosaurus Urdu inventory/accuracy, timing precision, CPU cost and Blender compatibility remain unverified.

**Allosaurus** — https://github.com/xinjli/allosaurus
- GPL-3.0 universal phoneme recognizer; broad multilingual coverage, latest inspected commit from 2021. Possible research component, not proof of accurate Urdu alignment. Urdu language-code availability and output quality must be tested with native Pakistani Urdu samples.

**Charley3d Blender Lip Sync** — https://github.com/Charley3d/lip-sync
- Version 1.0.6, GPL-3.0-or-later, Blender 4.4+, Vosk + Phonemizer + eSpeak, shape-key/spritesheet baking and downloadable language models. README says approximately 25/30 languages, but inspected material does not establish Urdu support. Do not infer Urdu from a generic multilingual claim.

### Persistent local render/job queue
**sqlite-workqueue** — https://github.com/SammyRyuga/sqlite-workqueue
- MIT, version 0.1.0, Python >=3.11, no runtime dependencies. Inspected queue implementation, pyproject, license and tests. Latest inspected commit `4f7cf094a77ea44f984de61b39a13594efd5f7c5`; Actions run #19 succeeded.
- Implements SQLite WAL, atomic claims, worker lease tokens, lease renewal, bounded exponential retries, idempotency keys and expired-lease recovery.
- Explicit limitations: no cancellation, result storage, periodic scheduling, schema-migration system or HTTP service; at-least-once delivery and local-host-only SQLite. Early project, not a production queue to drop in unchanged.

**Huey** — https://github.com/coleifer/huey
- MIT; supports SqliteHuey, multi-process/thread workers, retries, result storage, scheduling, priority, locks and timeouts.
- Its guide warns that tasks in progress can be lost if a consumer crashes unless interrupted tasks are explicitly re-enqueued; re-enqueue can repeat side effects. Long renders still need idempotent scene outputs and durable per-scene checkpoints.

### Windows packaging and final media
- **PyInstaller**: official docs describe Python/dependency bundling into one-folder or one-file executable. GPL-2.0 has a specific exception allowing bundled applications to use their own license, subject to dependency licenses. Prove one-folder mode before one-file mode.
- **NSIS**: primarily zlib/libpng licensed; bzip2 and LZMA modules have separate licenses.
- **Tauri 2**: MIT/Apache-2.0, Windows 10+, WebView2 and Rust toolchain; adds another runtime/build system beside Python.
- **pywebview**: BSD-3-Clause and Windows WebView2 option; runtime/packaging still requires validation.
- **FFmpeg**: default codebase LGPL-2.1-or-later; enabling GPL components such as libx264 changes the build license to GPL; nonfree builds may be unredistributable. Pin exact binary/configuration and codec rights before bundling.

### Reusable asset libraries
- **Kenney** — https://kenney.nl/support: official support page says game assets are CC0; verify the license file/page for each downloaded pack.
- **Poly Haven** — https://polyhaven.com/license: all site assets (HDRIs, textures and 3D models) are CC0.
- **Quaternius** — https://quaternius.com/faq.html and https://quaternius.com/license.html: each pack's license is specified individually. QAL v1.0 updated 2026-08-28 permits use in products but prohibits redistributing assets themselves as standalone assets. Older pack pages may explicitly state CC0. Inspect the exact pack; no blanket CC0 assumption.

### Updated Urdu TTS findings
- **Smol Urdu TTS V1** model card says Apache-2.0 and 135M parameters, but linked GitHub inference package has no LICENSE file in its tree. Code requires PyTorch, torchaudio, Transformers, Liger Kernel and separate WavTokenizer checkpoint/config; inference uses BF16. Not a proven lightweight CPU solution.
- **tiny-urdu** repository README says 1,000 training clips; its Hugging Face model card says 5,000. Treat as unresolved discrepancy. Roman Urdu only, one voice; underlying UrduTTS dataset is CC-BY-NC 4.0 and GitHub code repo has no explicit LICENSE.
- **URDUTTS** — https://github.com/KAABSHAHID/URDUTTS: dataset research reports about 89 hours / 55,450 utterances and four male speakers; dataset CC-BY-NC 4.0 while code is MIT. Non-commercial research only unless rights clarified.
- **Qwen-Audio-TTS 3.1 Flash** official Model Studio documentation explicitly lists Urdu and a male Urdu voice named Sahar. The docs do not imply Pakistani accent or offline rights. Qwen3-TTS system voices do not list Urdu. Qwen-Audio-TTS Flash is cloud-only; pricing, Pakistan access, region, terms, privacy and quality remain P0.4 tasks.
