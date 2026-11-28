# Candidate Scorecard — Revised Architecture

## Selected roles
| Technology | Role | Decision |
|---|---|---|
| Blender Python API | Authoring/generation of all 3D assets | Selected as central platform |
| Godot 4.7.2 | Production engine | Retained |
| FastAPI + browser | Control plane | Retained |
| GLB/glTF | Interchange | Selected |
| FFmpeg | MP4 assembly | Retained |

## Evaluation rules
Score candidates by actual source-level capability, quality, maintenance, license, offline operation, hardware fit and integration cost. A score is not proof or authorization to adopt. Pin exact versions and test the specific integration.

## Exclusions and cautions
MPFB is not the product foundation and MPFB GPL code must not be copied. Blender is GPL-3.0; external use does not remove redistribution obligations. Add-ons and generated/source assets have separate licenses. The user's low-end Intel laptop is not assumed capable of all authoring tasks; Blender worker placement is configurable and not required at app launch.
