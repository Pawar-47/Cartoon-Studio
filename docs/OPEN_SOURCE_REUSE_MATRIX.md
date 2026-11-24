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
