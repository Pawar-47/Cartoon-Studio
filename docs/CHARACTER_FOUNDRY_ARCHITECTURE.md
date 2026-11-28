# Blender Character Foundry — Shared Asset Platform First

## Objective
Produce original, visually compelling, editable cartoon characters using Blender, then export them for Godot production. The Foundry is the first quality-critical domain built on the same Blender foundation that will generate worlds and props.

## Shared platform requirement
Character tools must use common Blender services for scene lifecycle, asset IDs, recipes, materials, geometry utilities, rigging, textures, validation, export, thumbnails, metadata and provenance. These services must also be usable by building, road, vegetation, interior, vehicle, furniture and prop tools.

## Character authoring pipeline
1. Select a versioned original character template/style recipe.
2. Generate/edit body and facial geometry with coherent topology and controlled proportions.
3. Create readable eyes, brows, nose, mouth, ears and silhouette; avoid primitive-looking placeholder faces.
4. Build fitted clothing, footwear, hair and accessories as editable components.
5. Create a reusable humanoid rig, bind skin weights and validate deformation.
6. Author facial expression morphs/visemes and reusable animation-ready rig metadata.
7. Save editable `.blend` source and a versioned recipe.
8. Export GLB/glTF with materials, textures, skeleton, skin, morph targets and stable metadata.
9. Import into Godot 4.7.2, save/reopen a scene and test animation/pose compatibility.
10. Present the actual character to the user for visual acceptance.

## Recipe contract
Persist stable character ID, schema version, template ID, generator version, style preset, body/face parameters, component asset IDs, rig profile, material choices, expressions, source provenance, output hash and dependency versions. Editing regenerates from recipe/source, not destructive edits to the last GLB.

## Quality gates
- Structural: topology, nonzero geometry, rig hierarchy, skin weights, morph targets, export validity.
- Functional: GLB imports, scene saves/reopens, animation/rig data survives.
- Visual: user sees the actual output and judges style, face readability, proportions, clothing fit, hair and overall quality. Automated screenshots/clipping are diagnostics only.
- Do not claim broad rig compatibility based on one fixture.

## Preservation
Keep existing Foundry APIs/UI, recipe persistence, pure-Python generator as prototype/fallback, imported-GLB workflows, modular Quaternius/Kenney catalogues and Godot worker. The Blender authoring path must improve output quality, not break existing projects.
