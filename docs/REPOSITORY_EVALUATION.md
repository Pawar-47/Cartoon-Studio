# Repository Evaluation

Evaluation date: 2026-11-25  
Target repository: https://github.com/Pawar-47/Cartoon-Studio

## Evaluation method
Score candidates by actual capability coverage, maturity, license clarity, integration effort, target-hardware fit, testability and the amount of required custom work. Stars are not a deciding factor. No candidate is accepted without a build/test proof and asset/model license review.

## Candidate A — Ara 3D Gen
Source: https://github.com/olatunde85/3d-gen  
Pinned proof commit: 4151c1124b172fdd918d23e0ef4aad727f4984c1  
Code license: MIT.

**Existing functionality:** character builder; import rigged GLB/FBX/VRM; procedural sets; 5-character cast; action beats and timeline; camera shots; dialogue/audio/text tracks; local project save/import; browser canvas MP4 export; scene composition; spatial/staging checks; animation and vehicle systems.

**Important source facts:** Studio currently limits each scene to 60 seconds and films to 5 scenes. Current total ceiling is therefore 5 minutes. The user's requirement is 5–7 minutes, so at least 7 scenes are needed. Export renders at 30fps using Mediabunny. The Studio guide calls it an early preview. The default character data derives from MakeHuman; motion clips include CMU mocap with no-direct-resale and acknowledgement conditions. Built-in TTS uses Supertonic 2; official model card lists English, Korean, Spanish, Portuguese and French only, so it cannot satisfy Urdu dialogue.

**Advantages:** by far the broadest existing match among inspected candidates; avoids rebuilding the 3D editor, timeline, scene sets, character rigging and MP4 export from scratch. Latest upstream commit supports importing rigged models and mapping facial shapes/visemes for imported characters, which creates a path for original stylized cartoon characters.

**Risks/gaps:** early-preview maturity; current 5-minute ceiling; default style is human/MakeHuman-derived rather than the requested cartoon style; default TTS is not Urdu; browser WebGL rendering may be demanding on Intel HD 5500; setup downloads approximately 280 MB of CC0 MakeHuman system assets; all other bundled/downloaded media must be audited.

**Integration approach under evaluation:** pin upstream commit as a submodule or build dependency; build the upstream multi-page Vite app on GitHub Actions; serve it locally under /ara/ from the FastAPI shell; keep Cartoon Studio-specific changes as patches/adapters in this repository. Extend scene limit to 7, create original toon character presets/imports, add Urdu TTS adapter, connect project persistence, and implement low-hardware render options. Preserve all notices and asset conditions.

**Proof result:** Ara Foundation Proof run #6 (ID `45486950450`) was CANCELLED during browser MP4 export. Type-check, film model checks and several editor browser checks completed; Studio-wide checks, Vite build and artifact upload were skipped. No proof artifact exists. The logs do not establish the cancellation cause.

**Decision:** HIGH PRIORITY FOUNDATION CANDIDATE ONLY. Ara is not selected, integrated or production-ready. Do not auto-integrate after a future green CI; inspect the full build, export output, asset notices and target-like hardware evidence first.

## Candidate B — Ekza Studio
Source: https://github.com/ekza-space/ekza-studio  
Main license MIT; anim-core Apache-2.0; fixtures separately licensed. Alpha status, Node >=24.11. Strong GLB/VRM rigging, IK and timeline editor; no complete story-to-film pipeline. Good focused alternative if Ara's editor is unsuitable.

**Decision:** SECONDARY CANDIDATE; do not integrate wholesale.

## Candidate C — DvaitAI anim-studio
Source: https://github.com/DvaitAI-tech/anim-studio  
GitHub metadata reports MIT. YAML story-to-Blender/FFmpeg prototype. Speech sample is Hindi-oriented and word-accurate lip-sync is not complete.

**Decision:** REFERENCE for schema/orchestration only.

## Candidate D — AnimStudio
Source: https://github.com/Sheggyb/AnimStudio  
AGPL-3.0-or-later. Rigging and animation editor with third-party motion packs.

**Decision:** REFERENCE ONLY pending copyleft compatibility review.

## Urdu TTS evaluation
- Supertonic 2: excluded for Urdu; supported language list does not include Urdu.
- Smol Urdu TTS V1: experimental, 135M, Apache-2.0 model card; CPU quality/performance untested.
- tiny-urdu: 21MB and CPU/browser inference but Roman Urdu only, one male voice, robotic quality; trained on a CC-BY-NC dataset; no explicit repo license found.
- DeepSpeak-v1: experimental ~400M, codec weights separately licensed; target-hardware risk.
- Dia-1.6B-Urdu: ~1.6B and 24GB VRAM noted; not suitable for target PC.
- XTTS-v2 Urdu fine-tune: 5.65GB; upstream base model has Coqui Public Model License concerns.

**Decision:** no TTS model approved. Keep TTS modular and support recorded voice. Benchmark Smol Urdu TTS and any new permissively licensed models before adoption.

## Next evaluation gate
1. Diagnose the browser MP4 export timeout/cancellation with a bounded, instrumented test.
2. Complete the Windows proof workflow: browser film/export test, Studio checks, Vite production build and artifact upload.
3. Inspect resulting build, notices and actual MP4 output.
4. Test app load, original character import, one scene edit, save/reopen and 720p MP4 export.
5. Measure browser memory and render time on comparable low-end hardware; later validate on the actual target PC.
6. Verify model and asset downloads and their licenses.
7. Only then decide whether Ara or an alternative is accepted.

## Candidate E — Blender 4.5 LTS as local production engine
Source: https://www.blender.org/releases/4-5/  
Current inspected release: 4.5.17 LTS (2026-11-24), support until July 2027.

**Advantages:** mature 3D authoring, materials/NPR, rigging, animation, cameras, scene management, Python automation, background mode and CPU Cycles rendering. Blender 4.5 Windows support includes Intel Broadwell; Blender 5.0+ raises the Intel GPU floor to Kaby Lake.

**Critical hardware risk:** i3-5005U is 2 cores / 4 threads, below Blender's published 4-core minimum; 8 GB RAM is only the minimum. Blender's Windows Intel troubleshooting page warns of startup crashes on 3rd–5th gen Intel iGPUs with several newer drivers.

**Decision:** LEADING ENGINE CANDIDATE, NOT SELECTED. Run a controlled Blender 4.5.17 startup/viewport/headless/CPU-render test on the actual target PC before P0.5 architecture freeze.

## Candidate F — Bene Procgen Maps
Source: https://github.com/Beneking102/bene-proggen-maps  
Inspected main commit `f883ddb59eadcff319d3b28eee59da90d7c8c21f`; upstream Actions #18 SUCCESS. GPL-3.0, Blender 4.2+.

**Advantages:** modular procedural city/countryside/dungeon generation; roads, buildings, terrain, parks, rivers/bridges, props, lighting and GLB export; deterministic seeds and upstream CI.

**Risks:** GPL-3.0; dense scenes can exceed 1M vertices; upstream timings are not target-PC benchmarks; no Cartoon Studio persistent-world contract or animated vehicle system.

**Decision:** HIGH-PRIORITY WORLD GENERATOR PROOF CANDIDATE; no code copied.

## Candidate G — Blender Level Architect
Source: https://github.com/dottyboy/BlenderLevelArchitect  
Inspected main commit `660e2113a2987a172f001a95d305e303b6a2aad9`; upstream Actions #87 SUCCESS. GPL-3.0, Blender 4.2+.

**Advantages:** seeded rooms/corridors/stairs, castles, villages, hill cities, floor-plan-to-house generation, terrain/biomes, walkability checks and GLB export; README claims 1,400+ automated checks.

**Risks:** main implementation is approximately 1.2 MB in one Python file; integration/maintenance risk.

**Decision:** SECOND WORLD/INTERIOR PROOF CANDIDATE; isolated add-on evaluation or selective reference, not wholesale merge.

## Candidate H — MPFB2 / CharacterCreator
MPFB2 (https://github.com/makehumancommunity/mpfb2): GPL-3.0 code, separate CC0 supplied assets, Blender 4.2+. CharacterCreator (https://github.com/kblood/CharacterCreator): GPL-3.0 code and CC0 output claim only where source assets are CC0. Both create human-like base characters; substantial stylization is still needed.

**Decision:** character-profile/rig/export research, not a final toon character solution.

## Candidate I — NPR/toon rendering
Anime-Tools describes Blender 4.5.2 cel shading/outline workflows but has no verified license file. blender-add-outline is MIT but old and narrow.

**Decision:** no shader dependency selected; build a Cartoon Studio-owned material/outline system after engine freeze.

## Candidate J — Urdu lip-sync
Parrot Lipsync + Allosaurus are GPL-3.0; custom phoneme table is promising but Urdu recognition/timing and CPU performance are unverified. Charley3d Lip Sync 1.0.6 is GPL-3.0-or-later, Blender 4.4+, Vosk/Phonemizer/eSpeak; Urdu model is not confirmed.

**Decision:** no lip-sync dependency selected. Native Urdu audio and mouth-timing tests are mandatory.

## Candidate K — local queue and packaging
sqlite-workqueue is MIT and implements SQLite leases/retries/idempotency, but lacks cancellation/results/migrations. Huey is MIT and richer, but in-flight crash recovery needs explicit handling. PyInstaller + NSIS are plausible packaging; Tauri 2 / pywebview are alternate shells with WebView2/toolchain costs. FFmpeg build configuration and codec licenses must be pinned.

**Decision:** compare queue designs and packaging only after P0.4; no dependency selected.

## Candidate L — Godot 4.7.2 as local runtime/editor

Source: https://github.com/godotengine/godot  
Inspected tag: `4.7.2-stable`; MIT license; 4.8 is still beta.

**Advantages:** Compatibility renderer uses OpenGL 3.3; target HD 5500 reports OpenGL 4.3. Minimum CPU instruction set is x86_64/SSE4.2 and minimum RAM 4 GB; target i3-5005U meets those minimums and 8 GB meets the recommended memory, though 2 physical cores are below the recommended 4. Native 3D scene editor, GLTF, Skeleton3D, AnimationPlayer/Tree, retargeting, toon diffuse/specular modes, audio tracks, custom editor plugins and MovieWriter.

**Limitations:** no full mesh sculpting or auto-rig character studio. Compatibility renderer is more limited than Forward+. MovieWriter produces OGV/AVI or PNG+WAV, not MP4; FFmpeg needed for MP4. Target driver/performance still untested. Existing FastAPI/browser UI integration requires a design decision.

**Decision:** LEADING TARGET-HARDWARE RUNTIME CANDIDATE, NOT SELECTED. Test 4.7.2 Compatibility on the target PC and compare native Godot shell versus Godot sidecar with the existing FastAPI UI.

## Candidate M — Terrain3D
Source: https://github.com/TokisanGames/Terrain3D  
MIT, C++ GDExtension, current v1.1.0 supports Godot 4.3–4.8 builds. Upstream CI passed. Compatibility/OpenGL ES 3 is documented as fully supported since v1.0/Godot 4.4. Provides clipmap LOD terrain, foliage instancing, sculpting, texture painting and heightmap import.

**Decision:** HIGH-PRIORITY Godot terrain proof candidate; benchmark low-LOD settings on HD 5500.

## Candidate N — Godot Road Generator
Source: https://github.com/TheDuckCow/godot-road-generator  
MIT, release 0.9.5, Godot 4.4+, upstream Actions #169 success. Procedural cross-section roads, intersections, lanes, reusable containers, terrain flattening and AI traffic helpers. README explicitly says it is not feature complete.

**Decision:** HIGH-PRIORITY road/traffic proof candidate; no integration yet.

## Candidate O — Building Generator
Source: https://github.com/Oli4k/building-generator  
MIT, Godot 4.7, commit `c6e662360dbd8d51fb1e62e0d9ce03190ee5fa79`. 26 procedural building variants, 3 LOD levels, low polygon counts, demo and manual test scripts; no CI workflow found.

**Decision:** HIGH-PRIORITY building proof candidate; expand catalog only after performance proof.

## Candidate P — Roommate
Source: https://github.com/hoork/roommate  
MPL-2.0, Godot 4 plugin. Generates indoor meshes, collisions, scenes and navigation from block layouts and style rules; no background tasks. Its current CI checks docs, not runtime. MPL-2.0 obligations need review.

**Decision:** interior-layout reference/proof candidate; not selected.

## Candidate Q — OpenCity
Source: https://github.com/webgl-games/opencity  
MIT code, Godot 4.7, procedural city/traffic/pedestrians and vehicle controls with headless test modes. Only two commits, no CI and most visible geometry is placeholder; player mannequin is Quaternius CC0.

**Decision:** behavior/architecture reference, not production world art.

## Candidate R — Godot AI Animation Toolkit 2.0.0
Source: https://github.com/michaltomczykowski/godot-ai-animation-toolkit  
MIT, release commit `e8f57c27c0374a6c76fce0e4b5d35d443ba3510b`, upstream CI #386 success. Godot 4.7.2 + Godot AI 4.4.2/MCP required; 103 operations for motion, rigs, IK, retargeting, AnimationTree and clip editing.

**Decision:** optional authoring tool only; avoid mandatory external AI/MCP dependency in runtime.

## Updated architecture comparison

Godot 4.7.2 now has the best on-paper target-hardware fit. Blender 4.5 remains useful as an optional asset-authoring path but is below the target CPU minimum and carries Intel driver risk. A Godot-native world stack (Terrain3D + Road Generator + Building Generator + Roommate) is more compatible with the target than Blender-only procedural addons, but must be tested together for renderer compatibility, memory, object counts, license compatibility and visual quality. The existing FastAPI/browser shell must be preserved; P0.5 must decide native Godot UI vs sidecar/local IPC vs browser-hosted preview.

## Candidate S — Godot Motion Matching
Source: https://github.com/ItsAshn/godot-motion-matching  
MIT, Godot 4.7, pure GDScript, updated 2026-11-10. Includes pose/trajectory search, inertialization, root motion, foot/hand IK, jump/landing, tags and headless tests. No GitHub Actions workflow found; no animation assets included; author claims about 0.1 ms/search are unverified.

**Decision:** optional advanced animation candidate only after a simple AnimationTree + CC0 animation library works. Do not start with motion matching; it increases data and CPU complexity.

## Candidate T — Quaternius CC0 character and animation packs
Official pack pages individually verified as CC0:
- Universal Base Characters: 6 humanoid models, 20 hairstyles, ~13k triangles, rigged and retargetable.
- Modular Character Outfits - Fantasy: 12 outfits / 62 modular parts.
- Ultimate Modular Men: 11 modular characters / 24 animations.
- Universal Animation Library and UAL2: 120+ and 130+ retarget-ready clips.
- These packs are a strong base for a persistent modular Character Studio, but do not supply all required face expressions, Urdu visemes, Pakistani clothing or full character personalization.

**Decision:** HIGH-PRIORITY asset acquisition and retarget proof after P0.5; retain each exact CC0 pack's license file and provenance. Do not use any Quaternius pack whose current page lists QAL rather than CC0 in the in-app redistributable asset library.

## Candidate U — Quaternius CC0 environment, interior and vehicle packs
Official pack pages individually verified as CC0:
- Downtown City MegaKit: 315 listed models / 300+ modular city pieces, Godot project/shader examples.
- Modular Streets: 25 street pieces.
- Ultimate Buildings: 76 modular buildings.
- Ultimate House Interior: 123 interior models.
- Ultimate Furniture: 20 furniture pieces.
- Cars Pack: 8 car models.
- Public Transport Pack: 12 vehicles including ambulance, school bus and train.

**Decision:** HIGH-PRIORITY asset pack proof. Use these as modular starting assets, not as final Pakistani environment art without local adaptation. Check exact downloaded pack license and file provenance.

## Revised Godot implementation hypothesis
A low-hardware-friendly path may use Godot 4.7.2 Compatibility plus the verified MIT plugins and exact CC0 Quaternius packs. A custom recipe-based character editor can assemble modular GLB parts on a shared skeleton, store JSON project data and retarget the CC0 animation libraries. Godot-native world plugins can generate terrain/roads/buildings/interiors, while the asset packs provide detailed modular pieces. This preserves the current FastAPI/story backend and avoids requiring Blender on the user's target PC. The approach remains unselected pending target-PC proof and license review.

## Candidate V — Godot audio timeline and non-real-time episode rendering

Source: Godot 4.7 docs: https://docs.godotengine.org/en/4.7/tutorials/animation/creating_movies.html

**Advantages:** Audio Playback Tracks display waveforms and schedule audio with animation; Audio Buses separate dialogue/music/ambience/SFX and provide effects/meters. Exported projects can use `--write-movie`, `--fixed-fps`, `--resolution` and `--quit-after`; non-real-time recording maintains exact frame pacing even on slow hardware.

**Limits:** exported-project MovieWriter outputs AVI/MJPEG (4 GB cap) or PNG+WAV. OGV/Theora/Vorbis recording is editor-build only. MP4 requires FFmpeg. PNG sequences are disk-heavy; AVI chunks need to remain below 4 GB. A custom GDExtension MovieWriter could pipe frames to FFmpeg but is extra C++ work.

**Decision:** STRONG RENDER PIPELINE CANDIDATE. First proof should render short scene chunks to AVI and PNG/WAV, then assemble MP4 with a pinned LGPL-compatible FFmpeg build. Evaluate a custom FFmpeg MovieWriter only if the basic chunk pipeline is insufficient.

## Candidate W — FFmpeg + OpenH264 for MP4

- FFmpeg default is LGPL-2.1-or-later; `--enable-gpl` components such as libx264/libx265 change the build license to GPL. Do not use an arbitrary prebuilt Windows package.
- OpenH264 is BSD-licensed and is a possible H.264 encoder in an LGPL FFmpeg build without GPL components. It has documented bitrate-control and 4K limits; target 1080p is within the resolution limit.
- Exact binary, source, configure flags, codec list, notices and dynamic-linking compliance must be pinned before packaging.

**Decision:** candidate final encoder only; no binary selected or bundled.

## Candidate X — CC0 audio and music assets

Kenney's Music Jingles, Impact Sounds, Digital Audio, Interface Sounds, UI Audio, RPG Audio and Voiceover Pack are individually marked CC0. Music Jingles are short stingers, not background loops. OpenGameArt has CC0 music loop packs/collections, but every track needs its own license and Content ID check.

**Decision:** build an audio asset catalog with stable IDs, source URLs, exact license, attribution, duration, loop points and Content ID status. No audio asset is downloaded or bundled yet. Prefer original music or tracks with no known Content ID registration for YouTube-safe publishing.

## Candidate Y — V-Sekai Godot VRM + MToon
Source: https://github.com/V-Sekai/godot-vrm  
MIT root code and MIT MToon shader; 486 stars; latest inspected commit `e15199f980064028bfa4fbee5e70dddb82dd55c3` updates Godot 4.7 imports; no upstream CI found.

**Advantages:** VRM 0.0/1.0 import, VRM 1.0 export, MToon toon shader, humanoid SkeletonProfile retargeting, facial expression blendshape/material binds as animation tracks, metadata including avatar license information. VRM 1.0 standardizes emotional expressions, five vowel visemes, blink and gaze plus custom expressions.

**Risks:** node constraints have retargeting bugs; spring bones need optimization; lookAt tracks require app logic; VRM animation extension not implemented; standalone glTF export can corrupt materials. Sample avatar licenses differ from the add-on; do not bundle samples. Compatibility renderer behavior and HD 5500 performance untested.

**Decision:** HIGH-PRIORITY Character Studio/face-expression proof candidate; no code or sample model copied.

## Candidate Z — eSpeak NG Urdu phonemizer and fallback TTS
Source: https://github.com/espeak-ng/espeak-ng  
GPL-3.0, latest inspected commit `ee9fa7cc4704d683020526f47a9655f14c8d5f4c`, compact C implementation, Windows support, Urdu `ur` source rules/list and WAV/phoneme output.

**Advantages:** offline Urdu grapheme-to-phoneme conversion, pitch/length information for phonemes, small runtime footprint, potential timing seed for its own synthesized speech.

**Risks:** formant synthesis is less natural than neural/human speech; Pakistani accent quality not independently evaluated; GPL-3.0 distribution implications; eSpeak text phoneme durations do not align to unrelated human/neural audio.

**Decision:** OFFLINE PHONEMIZER / EMERGENCY TTS CANDIDATE, not the main voice solution. Native Urdu samples must be tested; preserve manual recording and manual viseme editing.

## Revised facial-animation data contract candidate
VRM 1.0 offers a useful standard: `happy/angry/sad/relaxed/surprised`, `aa/ih/ou/ee/oh`, `blink`, left/right blink and gaze, plus custom expressions and mouth/blink/look overrides. The actual mesh must supply blendshapes; the spec does not define their shape. Add Cartoon Studio custom Urdu visemes and emotion layering rather than assuming the five vowel presets cover every Urdu consonant.

## Candidate AA — WhisperX Urdu forced alignment

Source: https://github.com/m-bain/whisperX  
Inspected main commit `8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365`; BSD-2-Clause; current pyproject version `3.8.7rc1`.

- Current alignment source explicitly maps `ur` to `kingabzpro/wav2vec2-large-xls-r-300m-Urdu` and can return character-level alignments as well as word timings.
- Model card: https://huggingface.co/kingabzpro/wav2vec2-large-xls-r-300m-Urdu — Apache-2.0, 300M parameters, 16 kHz mono, Common Voice 8.0 Urdu; reported WER 39.89% / CER 16.70% with 5-gram decoding.
- Good candidate for aligning a known Urdu transcript to audio at word/character level. It does not directly output IPA phoneme timing. Combine experimentally with eSpeak NG G2P and VRM custom visemes, then manually correct.
- Full WhisperX dependency stack is heavy for 8 GB RAM; a minimal align-only package is preferable but not yet implemented or tested. The model card warns of accent, code-switching, noise and domain-vocabulary sensitivity.

**Decision:** HIGH-PRIORITY Urdu alignment proof candidate; no model downloaded, no audio tested, no production approval.

## Updated voice/lip-sync comparison
1. WhisperX Urdu aligner: word/character timing, Apache2 model + BSD2 code, heavy runtime, quality not yet measured on Pakistani Urdu.
2. Allosaurus universal model: phone labels/approximate timestamps, possible broad Urdu inventory, but Urdu inventory and timing accuracy not yet verified; GPL3.
3. eSpeak NG: reliable local Urdu G2P source and phoneme duration output for its own synthetic voice; compact but robotic and GPL3.
4. Qwen Audio TTS Flash: official Urdu voice option, cloud-only, region/price/privacy and Pakistani accent quality unknown.
5. Smol Urdu TTS: Apache2 model card but linked code has no explicit license; BF16/PyTorch path and target CPU suitability unproven.

**Decision:** no natural Pakistani Urdu TTS or automatic phone-level lip-sync is selected. Keep human recording, word/character alignment and manual viseme correction as supported fallbacks.


## P2.2 Character Studio source evaluation — 2026-11-25

### V-Sekai Godot VRM add-on
- Repository: https://github.com/V-Sekai/godot-vrm
- Current default branch: master; observed latest commit `e15199f980064028bfa4fbee5e70dddb82dd55c3` (2026-07-08), updating import files for Godot 4.7.
- License: root MIT; the repository explicitly states that sample VRM models have separate licenses.
- Relevant capabilities documented in README: VRM 0.0/1.0 import, VRM 1.0 export, MToon, humanoid skeleton profile compatibility, blend-shape expressions and animation-track output for expressions/visemes.
- Limitations documented upstream: VRMC_node_constraint is described as buggy with retargeting; VRM animation extension support is not implemented; sample avatar licenses differ.
- Decision: candidate adapter for VRM model import/export and expression metadata. Pin an exact commit and prove compatibility with the project's Godot 4.7.2 worker before adding it. Do not copy sample avatars.

### Configura
- Asset-store listing: https://store.godotengine.org/asset/configura-team/configura/
- The listing describes modular assets, blend-shape/skeletal deformation, layered materials, color swatches and character save/load. The linked page does not expose a public source repository or code license.
- Decision: no integration or redistribution until source and license are independently verified. The forum thread reports the web version deprecated and explains that artists prepare Blender models and accessory scenes.

### Grumoth/godot-character-creator
- Repository: https://github.com/Grumoth/godot-character-creator
- License: MIT.
- Latest observed commit: 2020-03-08; the project targets the Godot 3.2 era.
- Decision: too old for direct Godot 4.7.2 integration; do not copy or port without a separate cost/benefit case.
