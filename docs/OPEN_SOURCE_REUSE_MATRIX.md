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

| https://github.com/ItsAshn/godot-motion-matching | Advanced locomotion | MIT; Godot 4.7; no CI found | Pose/trajectory search, inertialization, foot/hand IK, jump/landing; no assets | Optional later proof; basic AnimationTree first |
| https://quaternius.com/packs/universalbasecharacters.html | Modular character base | CC0 per exact pack page | 6 humanoid bases, 20 hairstyles, ~13k triangles, retargetable | High-priority asset proof |
| https://quaternius.com/packs/modularcharacteroutfitsfantasy.html | Modular clothing | CC0 per exact pack page | 12 outfits / 62 modular parts | High-priority asset proof; customize local clothing |
| https://quaternius.com/packs/ultimatemodularcharacters.html | Modular characters | CC0 per exact pack page | 11 characters / 24 animations | High-priority asset proof |
| https://quaternius.com/packs/universalanimationlibrary.html | Humanoid animation library | CC0 per exact pack page | 120+ retarget-ready clips | High-priority animation proof |
| https://quaternius.com/packs/universalanimationlibrary2.html | Humanoid animation library | CC0 per exact pack page | 130+ complementary clips | High-priority animation proof |
| https://quaternius.com/packs/downtowncitymegakit.html | Modular city assets | CC0 per exact pack page | 315 listed / 300+ modular city pieces, Godot project | High-priority environment proof |
| https://quaternius.com/packs/modularstreets.html | Street/road pieces | CC0 per exact pack page | 25 modular street assets | Asset proof |
| https://quaternius.com/packs/ultimatetexturedbuildings.html | Buildings | CC0 per exact pack page | 76 modular buildings | Asset proof |
| https://quaternius.com/packs/ultimatehomeinterior.html | Interior props | CC0 per exact pack page | 123 interior models | Asset proof |
| https://quaternius.com/packs/ultimatefurniture.html | Furniture | CC0 per exact pack page | 20 furniture pieces | Asset proof |
| https://quaternius.com/packs/cars.html | Cars | CC0 per exact pack page | 8 car models | Asset proof; rig wheels/doors separately |
| https://quaternius.com/packs/publictransport.html | Public transport | CC0 per exact pack page | 12 vehicles incl. bus/ambulance/train | Asset proof; rig animation separately |

| https://docs.godotengine.org/en/4.7/tutorials/animation/creating_movies.html | Movie render pipeline | Godot docs/API | Non-real-time fixed-FPS render; AVI/PNG+WAV in exported projects; OGV only editor build; custom MovieWriter via extension | Strong proof candidate |
| https://docs.godotengine.org/en/4.7/tutorials/audio/audio_buses.html | Audio mixing | Godot built-in | Independent buses, routing, meters and effects | Use built-in audio engine |
| https://docs.godotengine.org/en/4.7/tutorials/animation/animation_track_types.html | Dialogue/SFX timing | Godot built-in | Audio playback tracks with waveform and animation timing | Use built-in tracks |
| https://github.com/cisco/openh264 | H.264 encoding | BSD | H.264 codec; 4K and bitrate-control caveats | Possible FFmpeg LGPL encoder; test |
| https://kenney.nl/assets/music-jingles | Music cues | CC0 | 85 short stingers, not loops | Safe short cues after pack inventory |
| https://kenney.nl/assets/impact-sounds | SFX | CC0 | 130 impact sounds | Safe SFX pack |
| https://kenney.nl/assets/digital-audio | SFX | CC0 | 60 effects | Safe SFX pack |
| https://kenney.nl/assets/interface-sounds | UI SFX | CC0 | 100 interface sounds | Safe UI pack |
| https://kenney.nl/assets/ui-audio | UI SFX | CC0 | 50 UI sounds | Safe UI pack |
| https://kenney.nl/assets/rpg-audio | Foley/SFX | CC0 | 50 RPG effects | Safe SFX pack |
| https://kenney.nl/assets/voiceover-pack | Voice clips | CC0 | 90 clips; not Urdu dialogue | Placeholder only |
| https://opengameart.org/content/music-loops | Background loops | CC0 per page | 4 loops by pauliuw | Track-level verification and Content ID check |
| https://opengameart.org/content/short-loops-background-music-pack | Background loops | CC0 per page | 4 short seamless loops | Track-level verification |
| https://opengameart.org/content/two-simple-game-music-loops | Background loops | CC0 per page | 2 loops | Track-level verification |
| https://github.com/S3M1TR4SH/asset-library | Asset catalog schema reference | No root code license found; asset licenses listed individually | Stable IDs, genre packs, provenance and CC0/CC-BY metadata | Design reference only; do not copy code |
| https://github.com/TMHSDigital/Free-Game-Dev-Assets | Asset discovery/Content ID catalog | Catalog repo license not evaluated as reusable code | Tracks license and Content ID risk per source | Discovery reference only |

| https://github.com/V-Sekai/godot-vrm | VRM character import/export and face expressions | MIT root + MIT MToon shader; no CI found | VRM0/1 import, VRM1 export, humanoid retarget, expressions as animation tracks; some incomplete/buggy features | High-priority proof candidate |
| https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/expressions.md | Facial-expression/viseme schema | Open specification; no code copied | Emotion presets, 5 vowel visemes, blink/gaze and custom expressions | Candidate canonical expression contract |
| https://github.com/espeak-ng/espeak-ng | Urdu G2P and fallback TTS | GPL-3.0; commit ee9fa7cc4704d683020526f47a9655f14c8d5f4c | Urdu rules/list, phoneme pitch/length, WAV output, compact; robotic/formant voice | Offline phonemizer/placeholder only |

| https://github.com/m-bain/whisperX | Urdu word/character forced alignment | BSD-2-Clause; inspected main 8d8e43bf3698dd1df4b011c0f1a8dd1d468ae365 | Explicit `ur` model mapping; optional character alignments; heavy PyTorch/pyannote stack | High-priority Urdu alignment proof |
| https://huggingface.co/kingabzpro/wav2vec2-large-xls-r-300m-Urdu | Urdu CTC alignment model | Apache-2.0; 0.3B parameters | 16 kHz mono, Common Voice 8.0 Urdu, reported WER 39.89/CER 16.70; accent/noise sensitivity | Align known transcript only; benchmark native Pakistani Urdu |
| https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft | Multilingual phoneme recognition | Apache-2.0 | 60-language list does not include Urdu | Not selected for Urdu |


## Character Studio candidates — follow-up source review, 2026-11-25

| Candidate | Evidence inspected | License / compatibility | Decision |
|---|---|---|---|
| [V-Sekai/godot-vrm](https://github.com/V-Sekai/godot-vrm) | README, root license, repository tree and recent commits. Supports VRM 0.0/1.0 import, VRM 1.0 export, humanoid skeleton profile/retargeting, blend-shape expressions and MToon. Latest observed commit updates import metadata for Godot 4.7 (2026-07-08). | Root code and MToon shader MIT. Sample avatar models have separate licenses; do not bundle samples without individual review. | Strong candidate for a separately pinned VRM import/export adapter and humanoid metadata. Not a complete character creator; validate against our exact Godot 4.7.2 worker before integration. |
| [Configura Godot Asset Store listing](https://store.godotengine.org/asset/configura-team/configura/) | Listing and July 2026 forum thread reviewed. Describes modular meshes/accessories, blend-shape and skeletal deformation, layered materials, color swatches and save/load. | Listing did not expose a public source repository or a verifiable code license in the reviewed page. The forum says its web version is deprecated; workflow requires artist-prepared Blender/GLB assets. | Do not copy, bundle or depend on it until source and redistribution license are verified. Revisit only if license evidence becomes available. |
| [Grumoth/godot-character-creator](https://github.com/Grumoth/godot-character-creator) | Repository tree, README, license and recent commit history inspected. | MIT, but last commit observed 2020-03-08 and project is Godot 3.2-era; no current Godot 4.7 compatibility evidence. | Reject direct integration as stale. May be consulted only for historical concepts, not copied into the production runtime. |
| [Quaternius CC0 character packs](https://quaternius.com/packs/universalbasecharacters.html) | Exact pack pages already recorded in this matrix and asset-license register. | CC0 only for individually confirmed CC0 pack pages; QAL packs are not globally CC0. | Candidate source of original base meshes after pack-level download, hash, and license inventory. No asset is claimed bundled yet. |

No candidate code or character assets were copied or bundled by this research-only checkpoint. The next P2.2 implementation must pin exact upstream commits/releases and record all transitive/model/asset licenses before packaging.
