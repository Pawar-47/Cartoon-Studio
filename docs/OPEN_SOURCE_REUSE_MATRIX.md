# Open-Source Reuse Matrix

| Candidate | Role | License/asset evidence | Capability and risk | Decision |
|---|---|---|---|---|
| https://github.com/olatunde85/3d-gen | Primary 3D character/scene/film editor candidate | Source MIT; MakeHuman assets CC0; CMU mocap has no-direct-resale and acknowledgement terms; model Supertonic 2 OpenRAIL-M | 71 sets, 5 actors, multiple scenes, browser MP4; early preview; current cap 5 scenes x 60s; not toon-styled; TTS not Urdu | High-priority proof-of-concept; not integrated yet |
| https://github.com/ekza-space/ekza-studio | Rigging and animation editor | Main MIT; anim-core Apache-2.0; fixtures separately licensed | Alpha, GLB/VRM, IK and keyframes; modern Node >=24.11 | Secondary candidate |
| https://github.com/DvaitAI-tech/anim-studio | Story schema and Blender/FFmpeg orchestration | GitHub metadata reports MIT | Prototype; Hindi-oriented speech; incomplete lip-sync | Study patterns |
| https://github.com/Sheggyb/AnimStudio | Character rigging/animation editor | AGPL-3.0-or-later | Copyleft and separate asset terms | Reference only |
| https://github.com/Premik/blender_rhubarb_lipsync_ng | Lip-sync adapter | Exact release/source license not verified | Blender 4.2+; Urdu accuracy untested | Research required |
| https://huggingface.co/ProximaAI/smol-urdu-tts-v1 | Urdu TTS | Apache-2.0 model card | 135M, experimental; CPU and voice quality untested | Proof of concept |
| https://github.com/Zafar205/tiny-urdu | Roman Urdu TTS | No GitHub license file located; training corpus CC-BY-NC 4.0 | 21 MB, CPU/ONNX, one male voice, robotic limitations | Do not redistribute; research only pending rights |
| https://huggingface.co/mahwizzzz/deepspeak-v1 | Urdu TTS | Apache-2.0 stated; codec weights separately licensed | 400M, experimental/incomplete; target hardware risk | Research only |
| https://huggingface.co/mahwizzzz/Dia-1.6B-Urdu | Urdu TTS | Verify full model/data rights | 1.6B; 24GB GPU requirement cited | Not suitable for target PC |
| https://huggingface.co/suhaibrashid17/XTTS-v2-Urdu-FT | Urdu TTS | Model card says MIT; base XTTS uses Coqui Public Model License | 5.65GB; resource and derivative rights concerns | Not a default local dependency |

Adoption gate: no dependency until exact version, source, compatibility, software/model/asset license, runtime footprint, and integration test are documented.

| https://www.blender.org/releases/4-5/ | Local 3D production engine | Blender 4.5 GPL-3.0 | Broad 3D, animation, NPR and CPU rendering; target i3 below published CPU minimum and HD 5500 driver risk | Leading candidate; target-PC proof required |
| https://github.com/Beneking102/bene-proggen-maps | Procedural city/world generator | GPL-3.0; commit f883ddb59eadcff319d3b28eee59da90d7c8c21f; Actions #18 success | Modular seeded city/countryside/dungeon; dense scenes can exceed 1M vertices | High-priority proof candidate |
| https://github.com/dottyboy/BlenderLevelArchitect | Procedural world/interior generator | GPL-3.0; commit 660e2113a2987a172f001a95d305e303b6a2aad9; Actions #87 success | 1,400+ claimed checks, floor-plan houses and walkable levels; monolithic 1.2 MB main source | Secondary proof candidate |
| https://github.com/makehumancommunity/mpfb2 | Character generator/rigging | GPL-3.0 code; separate CC0 asset license; Blender 4.2+ | Human base generation; not toon-styled | Character research only |
| https://github.com/kblood/CharacterCreator | Character profiles and GLB export | GPL-3.0 code; generated CC0 output only from CC0 sources | MakeHuman/MPFB-derived human generator | Reference/proof candidate |
| https://github.com/Kraxziss/Anime-Tools | Toon/NPR shader techniques | No verified SPDX/license file | Blender 4.5.2 cel shader and outlines | Do not copy |
| https://github.com/azeemba/blender-add-outline | Outline technique | MIT; last update 2023 | Small Solidify/inverted-hull outline add-on | Reference only |
| https://github.com/blackears/parrotLipsync | Audio-to-phoneme lip-sync | GPL-3.0; uses Allosaurus; custom phoneme table | Urdu recognition unverified | Proof only; copyleft review |
| https://github.com/xinjli/allosaurus | Multilingual phoneme recognition | GPL-3.0; latest inspected commit 2021 | Broad language inventory, Urdu accuracy unknown | Research only |
| https://github.com/Charley3d/lip-sync | Blender lip-sync | GPL-3.0-or-later; Blender 4.4+ | Vosk/Phonemizer/eSpeak; Urdu model not confirmed | Not selected |
| https://github.com/SammyRyuga/sqlite-workqueue | Persistent local job queue | MIT; Python >=3.11; Actions #19 success | SQLite leases/retries/idempotency; no cancellation/results/migrations | Compare only |
| https://github.com/coleifer/huey | Local task queue | MIT; SqliteHuey | Mature retries/results/scheduling; in-flight crash recovery needs explicit handling | Compare |
| https://github.com/pyinstaller/pyinstaller | Python Windows packaging | GPL-2.0 with bundling exception | Self-contained Python bundle; one-folder preferred initially | Packaging candidate |
| https://github.com/NSIS-Dev/nsis | Windows installer | Mostly zlib/libpng; optional compression modules differ | Installer framework | Packaging candidate |
| https://github.com/tauri-apps/tauri | Desktop shell | MIT/Apache-2.0 | WebView2 on Windows 10+, Rust toolchain and sidecar/backend integration | Alternative shell |
| https://github.com/FFmpeg/FFmpeg | Video/audio assembly | LGPL-2.1+ default; GPL components change license | MP4 assembly/audio mix; exact encoder/build config matters | Build/license review required |
| https://kenney.nl/support | CC0 assets | CC0 per pack; inspect included License.txt | Rigged low-poly characters, roads, city/environment | Safe source after per-pack inventory |
| https://polyhaven.com/license | HDRIs, PBR textures, 3D models | CC0 site-wide | Lighting/material assets | Safe source after inventory |
| https://quaternius.com/license.html | Low-poly packs | Pack-specific CC0 or QAL v1.0; QAL restricts standalone asset redistribution | Useful packs; cannot assume all CC0 | Use only exact packs listing CC0 |
| https://github.com/KAABSHAHID/URDUTTS | Urdu TTS data | Dataset CC-BY-NC 4.0; code MIT | 89-hour dataset reported; non-commercial restriction | Research only |
| https://www.alibabacloud.com/help/en/model-studio/tts-model/ | Urdu cloud TTS | Service terms/pricing to verify | qwen-audio-3.1-tts-flash lists Urdu; Qwen3-TTS system voices do not | Optional cloud candidate; P0.4 gate |

| https://github.com/godotengine/godot | 3D runtime/editor | MIT; inspected 4.7.2-stable | Compatibility OpenGL 3.3, GLTF, animation, retargeting, toon modes, MovieWriter; target fits minimum better than Blender | Leading runtime candidate; target-PC proof required |
| https://github.com/TokisanGames/Terrain3D | Terrain/foliage | MIT; v1.1.0; Compatibility renderer supported since 1.0/Godot 4.4 | Clipmap LOD, foliage instancing, sculpting, heightmaps; C++ GDExtension | High-priority proof candidate |
| https://github.com/TheDuckCow/godot-road-generator | Roads/intersections/traffic | MIT; Godot 4.4+; Actions #169 success | Reusable road containers, intersections, lanes, AI traffic; explicitly incomplete | High-priority proof candidate |
| https://github.com/Oli4k/building-generator | Procedural buildings | MIT; Godot 4.7; commit c6e662360dbd8d51fb1e62e0d9ce03190ee5fa79 | 26 variants, 3 LODs, low triangle counts; no CI | High-priority proof candidate |
| https://github.com/hoork/roommate | Indoor room/level builder | MPL-2.0; Actions #12 docs workflow only | Mesh/collision/scene/navigation generation, style rules, no idle background tasks | Interior proof/reference; file-level copyleft review |
| https://github.com/webgl-games/opencity | City/traffic/pedestrian prototype | MIT code; Quaternius player mannequin CC0 | Procedural city, traffic, enterable vehicles, headless behavior tests; other geometry placeholder, no CI | Behavior reference only |
| https://github.com/michaltomczykowski/godot-ai-animation-toolkit | Animation authoring/retarget | MIT; release 2.0.0; Actions #386 success; requires Godot AI/MCP | 103 operations across motion, rigs, IK, retarget, graphs and clip editing | Optional authoring candidate |
| https://godotlearning.com/shaders/toon-shader | Toon shader sample | CC0 | Godot 4.7, Compatibility support; shadow-casting lights make lit bands too bright in sample | Visual reference; build own shader |
| https://github.com/LuanDucate/Ducz.CharacterCreator | Modular low-poly character builder | Code license not found; Quaternius assets credited CC0 | Modular characters, 24 animations, GLB export | Do not copy code; independent design reference |
