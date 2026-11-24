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

## Current research conclusion
Ara is the best 3D production foundation candidate. No Urdu TTS model has yet passed both licensing and target-hardware/quality checks. The voice architecture must remain modular and provide a manual recording fallback. Do not mark a TTS model selected merely because it supports Urdu on a model card.
