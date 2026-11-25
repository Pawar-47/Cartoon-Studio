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
No production engine, character generator, world generator, toon renderer, Urdu TTS or lip-sync system is selected. Godot 4.7.2 is now the strongest on-paper runtime candidate for the target PC because its Compatibility renderer uses OpenGL 3.3 and its minimum CPU/RAM requirements fit the target better than Blender; it still needs a real target-PC proof. Blender 4.5.17 remains a possible optional asset-authoring path but the target is below its published CPU minimum and has a documented Intel driver risk. Godot-native candidates (Terrain3D, Road Generator, Building Generator, Roommate and OpenCity) now form the primary environment shortlist. Ara and Ekza remain browser-editor candidates with incomplete/cancelled CI evidence. No candidate is selected; keep the system modular, local-first, offline-capable, and preserve a manual voice-recording fallback.

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

## 2026-11-25 — AI provider/API research sweep

Official source checks:
- FreeMilk Terms and Privacy: https://www.freemilk.ai/terms and https://www.freemilk.ai/privacy-policy
- Gemini API pricing/free tier: https://ai.google.dev/gemini-api/docs/pricing
- Groq rate limits/models: https://console.groq.com/docs/rate-limits and https://console.groq.com/docs/models
- Cloudflare Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- OpenRouter free models/rate limits: https://openrouter.ai/collections/free-models/ and https://openrouter.ai/pricing
- Copilot Free: https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/usage-limits
- ChatGPT/API billing separation: https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform
- Claude API pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Perplexity plan comparison: https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you
- Mistral free/API limits: https://docs.mistral.ai/admin/billing-usage/usage-limits
- Cerebras pricing: https://www.cerebras.ai/pricing
- GitHub Models retirement: https://docs.github.com/en/github-models

Initial conclusions:
- FreeMilk's daily coding-agent allowance is useful for manual GitHub work, but exact quota is not public, the terms prohibit direct scripted access, and coding sessions may be licensed to data partners for AI training unless the user opts out for future sessions.
- Groq, Cloudflare Workers AI, Gemini and OpenRouter are the main official API candidates with some free usage; each has different quotas, privacy and regional constraints.
- Copilot Free, ChatGPT Free, Claude Free, Perplexity Standard and FreeMilk are manual agent/UI workflows, not interchangeable free API endpoints.
- GitHub Models was retired on 2026-07-30; remove it from any provider plan.
- No provider is selected. P0.4 must check Pakistan access, actual account limits, official terms, data handling, model suitability and current prices.

## 2026-11-25 — Godot runtime and Godot-native subsystem sweep

### Godot engine: target-hardware fit
- Inspected Godot source repository, MIT license, 4.7.2-stable tag, system requirements, Compatibility renderer documentation, animation/GLTF/material APIs and MovieWriter class.
- Godot 4.7.2 is stable; 4.8 is still beta in the current release stream. Pin 4.7.2 for evaluation, not a beta.
- Compatibility renderer uses OpenGL 3.3. Intel HD 5500 reports OpenGL 4.3, so it meets the API floor on paper. Godot's minimum CPU requirement is x86_64/SSE4.2 and 4 GB RAM; recommended is 4 physical cores and 8 GB. The i3-5005U meets the minimum CPU instruction set and RAM recommendation but has only 2 physical cores, below recommended.
- Godot 4.7 Compatibility renderer has feature/performance limitations versus Forward+: use low light counts, baked lighting and a custom toon shader. The renderer is a better hardware fit than Blender 4.5 on paper, not yet tested on the target PC.
- Godot provides GLTF import, Skeleton3D, AnimationPlayer/AnimationTree, retargeting, path following, audio tracks and built-in toon diffuse/specular material modes. It does not provide a full character sculpting/auto-rig studio; that must be built or supplied by imported GLB assets.
- Godot MovieWriter supports non-real-time recording with fixed frame pacing. Its built-in outputs are OGV, AVI or PNG sequence plus WAV, not MP4; FFmpeg is still required for final MP4 assembly. Non-real-time recording is promising for slow hardware because rendering need not sustain real-time FPS, but 5–7 minute output speed remains unmeasured.

### Godot-native world and environment candidates

**Terrain3D** — https://github.com/TokisanGames/Terrain3D
- MIT; inspected latest main commit `69699ff0e3b629230dd1a0d7e6e7dda84cca2d26`, pushed 2026-11-21. Upstream Actions #96 and #2685 passed on commit `43734bbada0b65fb5a642cfad0d9caeccfafade8`.
- C++ GDExtension for Godot 4; current v1.1.0 asset listing says Godot 4.3–4.8 builds. Supports clipmap LOD terrain, up to 10 LOD levels, foliage instancing, sculpting, holes, texture painting, heightmap import and large non-contiguous regions.
- Its platform documentation explicitly says Compatibility/OpenGL ES 3 is fully supported since Terrain3D 1.0 and Godot 4.4. This is important for HD 5500; still benchmark the C++ extension and GPU cost.

**Godot Road Generator** — https://github.com/TheDuckCow/godot-road-generator
- MIT; main release 0.9.5, Godot 4.4+; current development occurs on dev branch. Upstream Actions #169 succeeded on dev commit `648f07295a6d1cd9e0607c71196f7a2de98e6fc5`.
- Cross-section-based roads, reusable RoadContainers, intersections, snapping/gizmos, terrain flattening integration with Terrain3D, AI lanes and traffic agents. README explicitly says the project is not feature complete. Strong road/traffic proof candidate, not a frozen dependency.

**Building Generator** — https://github.com/Oli4k/building-generator
- MIT; Godot 4.7; latest inspected commit `c6e662360dbd8d51fb1e62e0d9ce03190ee5fa79`, pushed 2026-11-06. No upstream Actions workflow found.
- Procedural houses, shops, offices, churches, chalets, hangars, warehouses and stations. Version 0.2.0 catalog has 26 variants, three LODs, shared materials/textures and low triangle counts (most house/shop/station/church LOD0 examples 312–990 triangles). Includes manual test scripts for build, catalog, ground, normals, seed and render preview.
- Good low-poly building candidate; limited catalog, no automated CI evidence and no target benchmark.

**Roommate** — https://github.com/hoork/roommate
- MPL-2.0; latest inspected commit `fd9381b5e833807c83e10af50fd95fb4ca0b6bb3`, pushed 2026-11-13. Godot 4 plugin.
- Editor plugin generates meshes, collision, scenes and navigation from block-based room layouts; declarative style rules and custom block types. README says it runs no background tasks after generation. Actions #12 is a documentation workflow, not evidence of runtime tests.
- Good indoor/room/prop placement candidate; MPL-2.0 file-level obligations and no runtime test evidence need review.

**OpenCity** — https://github.com/webgl-games/opencity
- MIT code; Godot 4.7; only two commits inspected and no CI workflow found. Its CREDITS file identifies the player mannequin as Quaternius CC0.
- Procedural city, roads/sidewalks/towers, traffic, pedestrians, enterable cars/truck and helicopter. It includes headless test modes for boot screenshot, walking, driving, boost and flying.
- README explicitly says all other visible geometry is placeholder. Excellent architecture/behavior proof reference, not a finished art pack or production solution.

### Godot animation and toon candidates
**Godot AI Animation Toolkit 2.0.0** — https://github.com/michaltomczykowski/godot-ai-animation-toolkit
- MIT; latest release commit `e8f57c27c0374a6c76fce0e4b5d35d443ba3510b`; upstream Actions #386 succeeded.
- Requires Godot 4.7.2 stable and separate Godot AI 4.4.2+ plugin/MCP client. Provides 10 tool families / 103 operations: procedural humanoid idle/walk/run/strafe/jump/turn, clips/sequences, rigs, IK, retargeting, AnimationTree graphs, editing, library and inspection.
- This is an AI-agent authoring toolkit, not a mandatory runtime dependency. Windows and Linux clean-install checks passed upstream; README reports an intermittent Linux editor scene-save crash. Use only if the separate Godot AI/MCP dependency is acceptable and if the tools can be safely bounded.

**Godot Toon Shader demo** — https://godotlearning.com/shaders/toon-shader
- CC0 sample for Godot 4.7; lists Forward+, Mobile and Compatibility support.
- Compatibility renderer caveat: shadow-casting lights make toon lit bands much brighter in the demo; its author disables sun shadows there. Use as a visual reference only; create and test Cartoon Studio's own shader/lighting solution.

### Character-creation reference
**Ducz.CharacterCreator** — https://github.com/LuanDucate/Ducz.CharacterCreator
- README describes modular low-poly characters assembled from Quaternius packs, 24 animations, shared skeleton, recoloring and GLB export. Quaternius UAL asset license is listed as CC0 in its credits.
- No code license file or SPDX license was found for the repository. Do not copy or redistribute its code. The character-assembly concept may be independently implemented using separately verified CC0 assets.

### Godot candidate architecture (not frozen)
Godot 4.7.2 Compatibility renderer is now the leading target-hardware runtime candidate. A possible modular stack is Terrain3D (terrain), Road Generator (roads/lanes), Building Generator (buildings), Roommate (interiors), imported CC0 GLB characters/animation and a Cartoon Studio-owned toon shader. OpenCity is a reference for traffic/pedestrian behavior; Godot AI Animation Toolkit is optional authoring support. This stack still needs target-PC proof, license review, memory/scene-size measurements and a decision on how the existing FastAPI/browser UI communicates with the Godot runtime.

## 2026-11-25 — Godot animation and CC0 asset catalog sweep

### Animation libraries and retargeting
- Godot 4.7 has built-in humanoid retargeting through `BoneMap` and `SkeletonProfileHumanoid`, plus AnimationPlayer/AnimationTree. This can reuse clips across compatible humanoid rigs without a custom retargeting engine.
- **Quaternius Universal Animation Library**: official pack page https://quaternius.com/packs/universalanimationlibrary.html explicitly lists CC0 and 120+ retarget-ready humanoid clips (8-direction locomotion, jog/sprint, push, crawl, swim, sit, death, combat/emotes). Exported Godot project is described as tested.
- **Quaternius Universal Animation Library 2**: https://quaternius.com/packs/universalanimationlibrary2.html explicitly lists CC0 and 130+ complementary clips (melee/armed combos, parkour, farming/fishing, zombie locomotion).
- **Godot Motion Matching** — https://github.com/ItsAshn/godot-motion-matching: MIT, Godot 4.7, pure GDScript; pose/trajectory matching, inertialization, foot/hand IK, jump/landing, root motion, tags and one-click setup. Latest inspected update 2026-11-10; zero stars, no GitHub Actions workflow found. README claims ~0.1 ms/search; not independently measured. Demo requires the user to supply a humanoid GLB and animation library. Optional future proof only; basic AnimationTree + CC0 clips should come first.
- **Godot AI Animation Toolkit 2.0.0** remains a separate optional authoring path (MIT, 103 operations, requires Godot AI/MCP). Do not make an AI agent mandatory for runtime animation.

### CC0 character/environment/vehicle packs (verified individually)
These exact Quaternius pack pages explicitly display CC0; they are safe candidates for commercial use and bundling, subject to retaining each pack's own license file and provenance:
- Universal Base Characters: https://quaternius.com/packs/universalbasecharacters.html — 6 humanoid base models, male/female proportions, 20 hairstyles, customizable skin/eye colors, ~13k triangles average, retargetable.
- Modular Character Outfits - Fantasy: https://quaternius.com/packs/modularcharacteroutfitsfantasy.html — 12 outfits / 62 modular parts, compatible with Universal Base Characters.
- Ultimate Modular Men: https://quaternius.com/packs/ultimatemodularcharacters.html — 11 modular characters, 24 animations.
- Downtown City MegaKit: https://quaternius.com/packs/downtowncitymegakit.html — 315 listed models / 300+ modular city pieces; Godot project and shader/collision examples.
- Modular Streets Pack: https://quaternius.com/packs/modularstreets.html — 25 modular street/road pieces.
- Ultimate Buildings Pack: https://quaternius.com/packs/ultimatetexturedbuildings.html — 76 modular buildings.
- Ultimate House Interior Pack: https://quaternius.com/packs/ultimatehomeinterior.html — 123 interior models including doors, windows, kitchen and bathroom furniture.
- Ultimate Furniture Pack: https://quaternius.com/packs/ultimatefurniture.html — 20 furniture essentials.
- Cars Pack: https://quaternius.com/packs/cars.html — 8 car models.
- Public Transport Pack: https://quaternius.com/packs/publictransport.html — 12 transport vehicles including ambulance, school bus and train.
- Stylized Tree Pack: https://quaternius.com/packs/stylizedtrees.html — verify exact page and license at download time before adding; no asset downloaded yet.
- Universal Animation Library and UAL2: 120+ and 130+ retarget-ready clips, both CC0 as above.

Important licensing distinction: Quaternius FAQ says every pack is either CC0 or QAL. QAL v1.0 permits incorporation into a finished Product but prohibits redistribution of the assets themselves as a standalone asset pack. For Cartoon Studio's built-in reusable asset library, prefer only packs whose exact page explicitly says CC0. Never infer CC0 from the creator/site brand alone.

### Character Studio design reference
Ducz.CharacterCreator has a useful modular recipe model: JSON character definition, shared humanoid skeleton, swappable body/outfit/accessory parts, material recoloring, preview animation and GLB export. Its repository code has no license file, so do not copy its implementation. Implement an independent version using verified CC0 packs and Cartoon Studio-owned schemas. The packs above provide base bodies/outfits/animations, but face blendshapes/visemes, Pakistani clothing variants and consistent facial expressions still need original work.

### Updated candidate stack
A Godot-native stack can now cover more of the master brief without requiring Blender at runtime:
- Godot 4.7.2 Compatibility for scene/runtime/animation/preview.
- Terrain3D for terrain and foliage (MIT; Compatibility supported).
- Road Generator for lanes/intersections/traffic (MIT; incomplete).
- Building Generator for procedural low-poly buildings (MIT; no CI).
- Roommate for indoor layouts (MPL-2.0; docs-only CI).
- Quaternius CC0 GLB packs for modular characters, outfits, streets, buildings, interiors, vehicles and animations.
- Original Cartoon Studio code for persistent character/world recipes, face expressions/visemes, scene assembly, Urdu dialogue, camera/lighting, render jobs and episode production.
This is only a research candidate; the full stack has not been imported, tested together or benchmarked on the target PC.

## 2026-11-25 — Audio, lip-sync and final-video pipeline sweep

### Godot animation/audio timeline
- Godot 4.7 AnimationPlayer supports Audio Playback Tracks that display an audio waveform and schedule clips at timeline positions. AudioStreamPlayer nodes can route through named buses.
- Godot Audio Buses support independent routing, VU meters and effect processors. This can separate dialogue, music, ambience and SFX; keep master output below 0 dB to avoid clipping.
- This supports a custom episode timeline without a separate DAW dependency: scene animation tracks, dialogue clips, sound effects, ambience and music can be stored as versioned scene/audio data.

### Godot MovieWriter and FFmpeg
- Official Godot 4.7 Movie Maker docs: https://docs.godotengine.org/en/4.7/tutorials/animation/creating_movies.html
- `--write-movie`, `--fixed-fps`, `--resolution` and `--quit-after` work with exported projects. Movie Maker runs non-real-time with fixed delta, so slow hardware can render without dropped frames or real-time pacing loss.
- Exported-project built-in outputs: AVI/MJPEG with uncompressed audio (maximum 4 GB per file), or PNG image sequence plus WAV. OGV/Theora/Vorbis is only recordable in editor builds, not export templates. Godot docs show FFmpeg commands for converting PNG/WAV to MP4.
- For audio sync, the MovieWriter mix rate must be divisible by the recorded FPS. 48 kHz is divisible by 24, 30 and 60 FPS and is a suitable candidate.
- Custom MovieWriter implementations can be built as GDExtensions and can pipe frames to third-party encoders. This could avoid huge PNG sequences and the 4 GB AVI cap, but it is additional C++ work and not yet proven.
- Candidate render strategy: render independent scene/chunk clips, checkpoint each chunk, then FFmpeg-concatenate and mix dialogue/music/SFX. For a simple first proof use AVI chunks below 4 GB or PNG/WAV chunks; evaluate a custom FFmpeg writer only if required.

### FFmpeg codec and license constraints
- Official legal page: https://www.ffmpeg.org/legal.html
- FFmpeg is LGPL-2.1-or-later by default. Enabling GPL components (notably libx264/libx265) changes the FFmpeg build to GPL; nonfree builds may be unredistributable. Official LGPL checklist requires preserving the exact corresponding source/build configuration and license notices, and dynamic linking when linking libraries.
- **OpenH264** — https://github.com/cisco/openh264: BSD-licensed H.264 codec with a patent grant. It is a possible H.264 encoder in an FFmpeg build without `--enable-gpl`; it has documented limitations (encoder errors above 3840x2160 and bitrate-control caveats). 1080p is within its documented resolution limit, but quality/performance need testing.
- Do not bundle an arbitrary FFmpeg Windows build: many include libx264 and therefore GPL. Pin the exact build, configure flags, enabled codecs and source archive. Prefer an LGPL-compatible build with OpenH264 if its quality is acceptable; otherwise make the licensing decision explicit.

### CC0 audio assets and music
- Kenney Music Jingles (85 CC0 short stingers): https://kenney.nl/assets/music-jingles. These are short cues, not seamless background beds.
- Kenney Impact Sounds (130 CC0 effects): https://kenney.nl/assets/impact-sounds.
- Kenney Digital Audio (60 CC0 effects): https://kenney.nl/assets/digital-audio.
- Kenney Interface Sounds (100 CC0 effects): https://kenney.nl/assets/interface-sounds.
- Kenney UI Audio (50 CC0 effects): https://kenney.nl/assets/ui-audio.
- Kenney RPG Audio (50 CC0 effects): https://kenney.nl/assets/rpg-audio.
- Kenney Voiceover Pack (90 CC0 voice clips): https://kenney.nl/assets/voiceover-pack. These are not Urdu dialogue.
- OpenGameArt CC0 music sources inspected: https://opengameart.org/content/music-loops (pauliuw), https://opengameart.org/content/short-loops-background-music-pack, https://opengameart.org/content/two-simple-game-music-loops, and the CC0 Music collection https://opengameart.org/content/cc0-music. Each track must be individually checked; a collection title is not sufficient proof for every included file.
- A curated GitHub catalog, https://github.com/S3M1TR4SH/asset-library, demonstrates stable asset IDs, genre packs and a `LICENSES.md` provenance table. It has no root code license, so do not copy its code. Its v0.4.0 music entries include CC0 OpenGameArt tracks; verify each original track page before use.
- YouTube Content ID status is separate from copyright license. The catalog https://github.com/TMHSDigital/Free-Game-Dev-Assets explicitly tracks Content ID risk and warns that a legally usable track can still trigger a claim. For episode publishing, prefer original music or tracks whose source has no known Content ID registration; retain track provenance and be ready to replace a claimed track.

### Urdu phoneme/lip-sync correction
- Allosaurus universal model is CPU-capable by default and supports around 2,000 language phone inventories; the only language-dependent acoustic model listed in its README is English. Its phone timestamps are explicitly approximate CTC timestamps, not word-level forced alignment.
- The model archive `uni2005` is about 41.5 MB; PyTorch dependencies and CPU time are additional. The exact Urdu ISO inventory entry must be checked with `python -m allosaurus.bin.list_lang` on the pinned model; no Urdu-specific acoustic model is listed.
- Parrot Lipsync v1.1.2 uses Allosaurus and an editable phoneme-to-mouth-pose table; its release supports Blender 4.5. It is GPL-3.0 and is a Blender add-on, not a Godot plugin. If Godot remains the runtime, only the data-flow concept is relevant; a Godot-owned viseme track generator would be required.
- For Urdu, do not rely on generic “25+ languages” claims. The proof must use native Pakistani Urdu audio, verify phone inventory and pronunciation, map phones to Cartoon Studio visemes, and allow manual timeline correction. Keep manual voice recording and manual mouth-keyframe editing as fallbacks.
