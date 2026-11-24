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

**Decision:** HIGH PRIORITY FOUNDATION CANDIDATE. Do not call it production-ready or integrate it as a final dependency until the Windows proof workflow succeeds and its output is inspected.

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
1. Windows build proof succeeds.
2. Inspect resulting dist and notices.
3. Test app load, character import, one scene edit, save/reopen, 720p MP4 export.
4. Measure browser memory and render time on comparable low-end hardware.
5. Verify model and asset downloads and their licenses.
6. Only then accept submodule/upstream integration.
