# Asset and Dependency License Register

No third-party source project has yet been copied into this repository.

| Project / asset | Source | License evidence | Current decision |
|---|---|---|---|
| Ara 3D Gen source | https://github.com/olatunde85/3d-gen | Repository LICENSE says MIT | Candidate only; no code copied |
| Ara MakeHuman character data | Ara scripts/ASSETS_LICENSE.txt | CC0 1.0, attribution not required under CC0 | Potential reuse after checking each asset |
| Ara CMU motion data | Ara scripts/ASSETS_LICENSE.txt and CMU terms | Commercial use allowed; direct resale, including converted data, prohibited; acknowledgement required | Preserve acknowledgement; do not sell/resell motion data directly |
| Ara Supertonic 2 weights | https://huggingface.co/Supertone/supertonic-2 | OpenRAIL-M; only five listed languages, no Urdu | Do not use for Urdu; no model bundling decision |
| Ekza Studio | https://github.com/ekza-space/ekza-studio | Main MIT; anim-core Apache-2.0; fixtures separately licensed | Research only |
| DvaitAI anim-studio | https://github.com/DvaitAI-tech/anim-studio | GitHub API reports MIT | Research only |
| AnimStudio | https://github.com/Sheggyb/AnimStudio | AGPL-3.0-or-later | Reference only pending copyleft review |
| Smol Urdu TTS | https://huggingface.co/ProximaAI/smol-urdu-tts-v1 | Apache-2.0 model card | Experimental; validate dependencies and model card |
| tiny-urdu | https://github.com/Zafar205/tiny-urdu | No explicit repository license found; dataset UrduTTS is CC-BY-NC 4.0 | Do not redistribute pending rights clarification |
| DeepSpeak-v1 | https://huggingface.co/mahwizzzz/deepspeak-v1 | Apache-2.0 stated; codec weights have separate license | Research only |
| Dia-1.6B-Urdu | https://huggingface.co/mahwizzzz/Dia-1.6B-Urdu | Verify complete model/data license | Not selected |
| XTTS-v2 Urdu fine-tune | https://huggingface.co/suhaibrashid17/XTTS-v2-Urdu-FT | Model card says MIT; upstream XTTS base is Coqui Public Model License | Derivative rights unresolved |

For every future code/model/voice/texture/animation/dataset, record exact version, author, source, license text, attribution, commercial rights, modifications, redistribution conditions and checksum before adoption.

## Additional candidates inspected — 2026-11-25
| Project / asset | Source | License evidence | Current decision |
|---|---|---|---|
| Bene Procgen Maps | https://github.com/Beneking102/bene-proggen-maps | GPL-3.0 | Candidate only; no code copied |
| Blender Level Architect | https://github.com/dottyboy/BlenderLevelArchitect | GPL-3.0 | Candidate only; no code copied |
| MPFB2 code | https://github.com/makehumancommunity/mpfb2 | LICENSE.CODE.md: GPL-3.0 | Candidate only; copyleft review |
| MPFB2 supplied assets | https://github.com/makehumancommunity/mpfb2 | LICENSE.ASSETS.md: CC0 | Candidate assets only; inspect per asset |
| CharacterCreator code | https://github.com/kblood/CharacterCreator | GPL-3.0 | Candidate only |
| CharacterCreator generated output | https://github.com/kblood/CharacterCreator | CC0 only where source assets are CC0, per project notes | Verify provenance for every output |
| Anime-Tools | https://github.com/Kraxziss/Anime-Tools | GitHub metadata NOASSERTION; no standalone LICENSE file found | Do not copy |
| blender-add-outline | https://github.com/azeemba/blender-add-outline | MIT | Technique reference only |
| Parrot Lipsync | https://github.com/blackears/parrotLipsync | GPL-3.0 | Do not bundle before copyleft review |
| Allosaurus | https://github.com/xinjli/allosaurus | GPL-3.0 | Research only |
| Charley3d Lip Sync | https://github.com/Charley3d/lip-sync | GPL-3.0-or-later | Do not bundle before copyleft review |
| sqlite-workqueue | https://github.com/SammyRyuga/sqlite-workqueue | MIT | Queue candidate only |
| Huey | https://github.com/coleifer/huey | MIT | Queue candidate only |
| PyInstaller | https://github.com/pyinstaller/pyinstaller | GPL-2.0 with specific bundling exception | Packaging candidate; preserve exact exception and dependency notices |
| NSIS | https://github.com/NSIS-Dev/nsis | Mostly zlib/libpng; bzip2 and LZMA modules have separate licenses | Packaging candidate; audit enabled modules |
| FFmpeg | https://github.com/FFmpeg/FFmpeg | LGPL-2.1+ default; optional GPL components; nonfree builds may be unredistributable | No binary selected; record configure flags/codecs |
| Kenney assets | https://kenney.nl/support | CC0 per pack; retain included License.txt in provenance record | Download only individually inventoried packs |
| Poly Haven assets | https://polyhaven.com/license | CC0 site-wide | Candidate HDRIs/textures/models |
| Quaternius packs | https://quaternius.com/license.html | Pack-specific CC0 or QAL v1.0; QAL restricts standalone redistribution | Use only pack pages explicitly confirming CC0 |
| URDUTTS dataset | https://github.com/KAABSHAHID/URDUTTS | Dataset CC-BY-NC 4.0; code MIT | Non-commercial research only unless rights clarified |
| Qwen-Audio-TTS Flash | https://www.alibabacloud.com/help/en/model-studio/tts-model/ | Cloud service; model/API terms and pricing to verify | No integration without P0.4 review |

No code or asset from these candidates has been copied into Cartoon Studio in this research batch.

## Godot-native candidates inspected — 2026-11-25

| Project / asset | Source | License evidence | Current decision |
|---|---|---|---|
| Godot Engine 4.7.2 | https://github.com/godotengine/godot | MIT | Leading runtime candidate; retain third-party notices |
| Terrain3D | https://github.com/TokisanGames/Terrain3D | MIT | Candidate; use official release binaries and preserve license |
| Godot Road Generator | https://github.com/TheDuckCow/godot-road-generator | MIT | Candidate; no code copied |
| Building Generator | https://github.com/Oli4k/building-generator | MIT | Candidate; no code copied |
| Roommate | https://github.com/hoork/roommate | MPL-2.0 | Candidate; review file-level copyleft obligations |
| OpenCity | https://github.com/webgl-games/opencity | MIT code; Quaternius player mannequin CC0 per credits | Reference; other art is placeholder |
| Godot AI Animation Toolkit | https://github.com/michaltomczykowski/godot-ai-animation-toolkit | MIT; separate Godot AI/MCP dependency | Optional authoring candidate; inspect dependency license |
| Godot Toon Shader demo | https://godotlearning.com/shaders/toon-shader | CC0 | Visual reference only |
| Ducz CharacterCreator | https://github.com/LuanDucate/Ducz.CharacterCreator | No code license found; Quaternius assets credited CC0 | Do not copy code; only separately verified CC0 assets may be used |

No Godot plugin or asset was copied into Cartoon Studio in this research batch.

## Quaternius packs individually verified as CC0 — 2026-11-25

The creator's site now offers both CC0 and QAL packs; only the exact pages below explicitly show CC0. Keep the downloaded `License.txt` with each pack and record the pack version/date/hash in the asset manifest.

| Pack | Exact source | CC0 pack evidence / contents |
|---|---|---|
| Universal Base Characters | https://quaternius.com/packs/universalbasecharacters.html | 6 humanoid bases, 20 hairstyles, rigged, retargetable |
| Modular Character Outfits - Fantasy | https://quaternius.com/packs/modularcharacteroutfitsfantasy.html | 12 outfits / 62 modular parts |
| Ultimate Modular Men | https://quaternius.com/packs/ultimatemodularcharacters.html | 11 modular characters / 24 animations |
| Universal Animation Library | https://quaternius.com/packs/universalanimationlibrary.html | 120+ retarget-ready humanoid clips |
| Universal Animation Library 2 | https://quaternius.com/packs/universalanimationlibrary2.html | 130+ retarget-ready humanoid clips |
| Downtown City MegaKit | https://quaternius.com/packs/downtowncitymegakit.html | 300+ modular city pieces / 315 listed models |
| Modular Streets Pack | https://quaternius.com/packs/modularstreets.html | 25 road/street pieces |
| Ultimate Buildings Pack | https://quaternius.com/packs/ultimatetexturedbuildings.html | 76 buildings |
| Ultimate House Interior Pack | https://quaternius.com/packs/ultimatehomeinterior.html | 123 interior models |
| Ultimate Furniture Pack | https://quaternius.com/packs/ultimatefurniture.html | 20 furniture pieces |
| Cars Pack | https://quaternius.com/packs/cars.html | 8 cars |
| Public Transport Pack | https://quaternius.com/packs/publictransport.html | 12 public transport vehicles |

QAL v1.0 (https://quaternius.com/license.html, updated 2026-08-28) allows incorporation into a finished product but prohibits redistributing the assets themselves as a standalone pack. For Cartoon Studio's downloadable in-app asset library, prefer CC0 packs to avoid ambiguity. Never label all Quaternius assets CC0 globally.

Ducz.CharacterCreator code remains unlicensed and must not be copied. The Quaternius packs it credits may be used only under their own CC0 pack licenses. No pack has been downloaded or bundled yet.

## Audio assets individually inspected — 2026-11-25

| Pack / source | Exact source | License evidence | Notes |
|---|---|---|---|
| Kenney Music Jingles | https://kenney.nl/assets/music-jingles | CC0 | 85 short stingers; not seamless background loops |
| Kenney Impact Sounds | https://kenney.nl/assets/impact-sounds | CC0 | 130 SFX |
| Kenney Digital Audio | https://kenney.nl/assets/digital-audio | CC0 | 60 SFX |
| Kenney Interface Sounds | https://kenney.nl/assets/interface-sounds | CC0 | 100 UI sounds |
| Kenney UI Audio | https://kenney.nl/assets/ui-audio | CC0 | 50 UI sounds |
| Kenney RPG Audio | https://kenney.nl/assets/rpg-audio | CC0 | 50 foley/RPG sounds |
| Kenney Voiceover Pack | https://kenney.nl/assets/voiceover-pack | CC0 | 90 voice clips; not Urdu dialogue |
| OpenGameArt Music Loops (pauliuw) | https://opengameart.org/content/music-loops | CC0 per page | Four loop files; retain author/source record |
| Short Loops Background Music Pack | https://opengameart.org/content/short-loops-background-music-pack | CC0 per page | Four short seamless OGG loops |
| Two Simple Game Music Loops | https://opengameart.org/content/two-simple-game-music-loops | CC0 per page | Two WAV/OGG loops |
| OpenGameArt CC0 Music collections | https://opengameart.org/content/cc0-music | Collection includes CC0 entries; inspect each original track | Do not assume every track in a collection has identical license |
| Abstraction Music Loop Bundle | https://tallbeard.itch.io/abstraction | CC0 per source catalog | 200+ loops reported; Content ID status not established |
| S3M1TR4SH asset-library catalog | https://github.com/S3M1TR4SH/asset-library | No root code license found; `LICENSES.md` records source asset licenses | Catalog schema reference only; do not copy code |
| OpenH264 | https://github.com/cisco/openh264 | BSD | Candidate H.264 codec; review patent grant and exact binary |
| FFmpeg | https://www.ffmpeg.org/legal.html | LGPL-2.1+ default; GPL components change build to GPL | Use known LGPL build, no libx264/libx265; preserve source/config/notice |

YouTube Content ID status is not the same as copyright permission. For every music track, record whether the source reports Content ID registration/claims. Prefer original music or sources with no known Content ID registration; no claim-free guarantee is made. No audio assets or FFmpeg binaries have been downloaded or bundled.

## Facial-expression and Urdu phoneme components — 2026-11-25

| Component | Source | License evidence | Notes |
|---|---|---|---|
| Godot VRM add-on | https://github.com/V-Sekai/godot-vrm | Root MIT | Import/export code; no CI; sample avatars separately licensed |
| Godot MToon shader | https://github.com/V-Sekai/godot-vrm/tree/master/addons/Godot-MToon-Shader | Separate MIT LICENSE | Toon shader and outlines; test Compatibility renderer |
| VRM sample Alicia Solid | https://github.com/V-Sekai/godot-vrm/tree/master/vrm_samples | Separate Alicia terms | Do not bundle without separate permission |
| VRM sample Godette | https://github.com/V-Sekai/godot-vrm/tree/master/vrm_samples | CC-BY 3.0 per sample license file | Attribution required; not bundled |
| VRM 1.0 expression specification | https://github.com/vrm-c/vrm-specification/blob/master/specification/VRMC_vrm-1.0/expressions.md | Specification reference only | No sample models or implementation code copied |
| eSpeak NG | https://github.com/espeak-ng/espeak-ng | GPL-3.0 | Urdu phoneme data and formant TTS; copyleft review required before bundling |

No VRM sample model, eSpeak binary or model has been downloaded or included in Cartoon Studio.

## Urdu alignment model license — 2026-11-25

| Component | Source | License evidence | Notes |
|---|---|---|---|
| WhisperX alignment code | https://github.com/m-bain/whisperX | BSD-2-Clause | Current main includes an explicit Urdu aligner mapping; full dependency stack is heavy |
| Urdu Wav2Vec2 aligner | https://huggingface.co/kingabzpro/wav2vec2-large-xls-r-300m-Urdu | Apache-2.0 | 300M parameter model trained on Common Voice 8.0 Urdu; model card reports WER/CER and accent/noise limitations |
| Multilingual eSpeak CTC model | https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft | Apache-2.0 | Language list does not include Urdu; not selected for Urdu alignment |

No alignment model weights were downloaded or bundled.


## Additional engine and distribution-license evidence — 2026-11-25

| Dependency | Official evidence | Decision |
|---|---|---|
| Godot Engine 4.7.2 | MIT license and third-party notice requirements: https://godotengine.org/license/ ; https://docs.godotengine.org/en/latest/about/complying_with_licenses.html | Leading native worker candidate; if distributed, include Godot license and third-party copyright notices. |
| FFmpeg | Default LGPL-2.1+; optional GPL components and external libraries change obligations: https://ffmpeg.org/legal.html ; https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md | Adapter boundary approved; no binary/codec selected. Do not enable GPL/nonfree or libx264 in an LGPL distribution build. |
| PyInstaller | GPL-2.0 with bundling exception; generated bundles can be distributed under the application's license subject to dependency licenses: https://pyinstaller.org/en/stable/license.html | Phase 1 packaging candidate; pin release and audit dependencies. |
| SQLite | Public domain: https://www.sqlite.org/copyright.html | Existing stdlib SQLite remains the local data/index layer. |

**Project-level IP note:** no root LICENSE file is present in the repository tree at this checkpoint. This is not permission to assume any license for Cartoon Studio. Before redistribution, the project owner must decide the project license and approve any copyleft dependencies. Until then, avoid bundling GPL/AGPL code/models/assets and prefer permissive dependencies.

## P0.6 proof evidence — 2026-11-25

- Godot 4.7.2-stable is selected as the native worker runtime after the P0.6 CI proof passed GLB import, animation, PackedScene save/reopen and MovieWriter AVI.
- FFmpeg converted the proof AVI to a 3-second 640x360/24 FPS MP4 with MPEG-4 Part 2 video and AAC audio. This is a functional assembly proof only; the production codec and redistributable build are not selected.
- The SQLite queue prototype passed five queue-specific reliability tests in Windows CI.
- See docs/P0_6_PROOF_REPORT.md for run IDs, logs and explicit limitations.