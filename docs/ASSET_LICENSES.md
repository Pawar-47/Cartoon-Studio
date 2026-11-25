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
