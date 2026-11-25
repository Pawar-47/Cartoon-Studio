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
