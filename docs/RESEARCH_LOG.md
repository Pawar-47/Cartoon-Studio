# Research Log — Current Direction

## 2026-11-28 — Architecture strategy changed
The project now adopts Blender as the shared authoring/generation foundation for characters, worlds and props. Godot remains production engine; browser/FastAPI remains control plane. This is a strategic revision, not a minor optional add-on.

## Research priorities
1. Blender Python API and reusable headless/interactive automation.
2. High-quality stylized character modeling, rigging and facial authoring.
3. Procedural environment/building/road/vegetation/interior generation.
4. Shared material/style libraries and asset recipe/provenance.
5. GLB export and Godot import/animation round-trip.
6. Job orchestration, FFmpeg and Urdu production.

## Existing research
Earlier source-level reviews of Ara, Godot, Blender add-ons, Quaternius, Kenney, TTS and animation systems remain dated evidence. Revalidate moving upstream sources before selecting. Ara as a monolithic browser/production editor and Godot-only asset authoring are no longer the governing architecture.

## Evidence standard
Every new entry records date, exact source/commit, inspected files, license, capabilities, test proof, limitations and decision. Search-result snippets alone are not evidence.
