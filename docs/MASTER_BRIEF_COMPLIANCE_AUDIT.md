# Master Brief Compliance — Strategy Realignment

## Result
Earlier documentation did not consistently express the user's revised Blender-first strategy. This revision corrects the governing direction and supersedes prior interpretations.

## Mandatory alignment checks
- Blender is central for characters, worlds and props: REQUIRED.
- One shared reusable Blender platform: REQUIRED.
- Godot remains production engine, not asset-authoring source: REQUIRED.
- Browser/FastAPI remains control plane: REQUIRED.
- GLB/glTF interchange; .blend editable sources: REQUIRED.
- Blender not mandatory to launch installed app: REQUIRED.
- Character quality is first user-visible milestone: REQUIRED.
- World and item tools use the same foundation from day one: REQUIRED.
- No MPFB product foundation or copied GPL MPFB code: REQUIRED.
- Preserve current code and project data: REQUIRED.
- User sees actual assets for visual acceptance; screenshot/clipping automation is not a feature: REQUIRED.
- Old main preserved; no merge back: REQUIRED.

## Known implementation gaps
Shared Blender modules and representative character/world/prop generation proofs exist, but full authoring features, visual quality, durable browser orchestration and end-to-end Godot production remain incomplete. CI #630 failed and must be diagnosed separately.

## Completion rule
This audit does not authorize marking a requirement VERIFIED. Each requirement needs implementation and direct test evidence; visual quality requires user review.
