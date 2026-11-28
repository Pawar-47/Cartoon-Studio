# Character Studio Report — Blender Foundry Transition

## Current direction
Character creation is now based on the shared Blender authoring platform. The Foundry must produce original stylized geometry, rigging, skinning, facial expressions, hair and clothing, retain editable .blend sources and export GLB/glTF for Godot.

## Existing work to preserve
Imported GLB workflows, profiles, recipes, modular outfit support, appearance controls, procedural GLB generator and Godot worker remain useful. They are not a substitute for high-quality Blender-authored characters.

## Current gap
The generated character face/overall visual quality has not yet received user acceptance. The latest CI #630 Blender-to-Godot round-trip failed. Do not claim phase exit. Next work is real Blender tool functionality and an actual user-reviewable character, not screenshot-only validation.
