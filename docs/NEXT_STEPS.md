# Next Steps — Cartoon Studio

## Active branch and safety

Continue only on `feature/cartoon-character-foundry` until Phase 2 is complete. Keep `main` intact. Do not merge PR #23 or change the default branch without explicit authorization and a deliberate reconciliation of the two lines of work.

## Current checkpoint

- CI #663 passed at `ff32d086e41d15c40210aa7e065ded65360081e5`.
- Blender 4.5.17 generated male and female Foundry characters with editable `.blend` sources and GLB exports.
- Godot 4.7.2 imported both characters, each with the full 26-target body/facial morph set.
- Character Studio browser workflow and expression-control tests passed.
- The current models are still development-quality blockouts; CI success is not visual acceptance.

## Next implementation batch

1. Finish actual Pakistani textile texture support: packed woven and Ajrak-inspired image textures, UV mapping, embedded GLB images and Godot import verification.
2. Improve character production geometry: head/face proportions, eye sockets and lids, mouth/lips, hair clumps, connected clothing silhouette, hands/fingers and footwear.
3. Improve rig deformation beyond rigid component weights; preserve the canonical humanoid mapping while adding functional controls and animation compatibility.
4. Produce a dedicated male and female character preview variant for user inspection. User visual approval remains separate from CI.
5. Extend the same shared Blender geometry/material/UV/assembly tools to all Master Brief environment, interior, building, road, vehicle, furniture, vegetation and prop requirements.

## Completion discipline

- Use the complete Master Brief and requirement registry, not only the current six builder names.
- Do not call primitive blockouts production assets.
- Keep editable Blender sources, GLB outputs, manifests, stable IDs and provenance.
- Run one CI at a time; use CI to prove coherent milestones.
- Report only work actually implemented and tested.