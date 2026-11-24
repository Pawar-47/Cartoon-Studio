# GitHub Open-Source Research Log
Research date: 2026-11-25  
Target: https://github.com/Pawar-47/Cartoon-Studio

## Initial candidates

### Ara 3D Gen — https://github.com/olatunde85/3d-gen
README describes a browser character generator and 3D Studio for short films, character export and animation library. GitHub metadata: TypeScript, active push observed 2026-11-24, large repository (~198 MB), API license field NOASSERTION. Repository LICENSE says source MIT and MakeHuman data CC0; every other asset/module needs inspection. Strong broad candidate/reference, but footprint and target hardware need testing. Discovered; README/LICENSE inspected; not integrated.

### Ekza Studio — https://github.com/ekza-space/ekza-studio
Browser GLB/VRM modeling, rigging, IK, keyframe animation, Dope Sheet and Graph Editor. README identifies alpha status and known gaps. package.json requires Node >=24.11 and pnpm. Main LICENSE MIT; anim-core Apache-2.0; fixtures separately licensed; Ekza name/logo not licensed. Strong editor candidate, not complete episode generator. README/package/LICENSE inspected; not integrated.

### DvaitAI anim-studio — https://github.com/DvaitAI-tech/anim-studio
YAML story to Blender-rendered voiced/captioned 3D video using Python, Blender and FFmpeg. GitHub metadata reports MIT. Small prototype; sample voice/dialogue is Hindi-oriented and its scene schema says word-accurate lip-sync is incomplete. Useful schema/orchestration reference; GPU assumptions need CPU fallback. README and schema inspected; not integrated.

### AnimStudio — https://github.com/Sheggyb/AnimStudio
Browser character rigging and animation editor; GLB/FBX import, animation packs, keyframes and export. README says AGPL-3.0-or-later. Motion packs have separate terms; Mixamo raw files cannot be redistributed. Reference only pending copyleft review.

### Rhubarb Lip Sync NG — https://github.com/Premik/blender_rhubarb_lipsync_ng
Blender integration for Rhubarb cue capture and baking to animation actions/NLA. README says Blender 4.2+ extension. English dialog file is an optional cue aid; Urdu accuracy is unproven. README inspected; exact license/release and Urdu tests pending.

### Urdu TTS — https://github.com/ahmedHanzala/urdu-tts
README claims Urdu-script TTS and MIT code license; weights are separately hosted on Hugging Face. Model-weight license, dataset provenance, Pakistani accent, commercial rights, model size and CPU inference unresolved. README inspected; not integrated.

## Preliminary conclusion
No single candidate is proven to meet the full specification. A modular architecture is likely: local web studio + character/animation foundation + independent scene/render/audio pipeline. This is a hypothesis until proof-of-concept tests pass.

## Next actions
- Inspect Ara subpackages, Studio, build scripts, asset downloads and license manifests.
- Inspect Ekza integration boundaries, license tooling and CI requirements.
- Inspect Dvait renderer, scene builder, Blender assumptions and CPU fallback.
- Verify Urdu TTS model card and weight license.
- Verify Rhubarb executable/source license and Urdu cue behavior.
- Search for cartoon-style low-poly characters, sets, vehicles, props and CC0 motion libraries.
- Build isolated proofs before selecting dependencies.
