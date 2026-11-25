# Next Steps — 2026-11-25

## Active batch — Phase 2 Character Studio

1. Confirm Windows CI #224 on current HEAD.
2. Map a real imported GLB skeleton to Godot's canonical `SkeletonProfileHumanoid` profile, with unmatched/ambiguous bone diagnostics and no source-asset mutation.
3. Retarget an actual imported animation to a differently proportioned target skeleton; inspect rendered poses and save/reopen.
4. Validate facial morph-target controls on representative blend-shape GLBs and verify persistence after profile reload.
5. Implement deterministic export/bake only after round-trip integrity and source preservation are proven.

## Current evidence

- Material appearance editor: commit `843ef8d6250b1c442235119911215205fa1bfb6a`.
- Imported facial morph-target editor: commit `533d59415df85be799fd4b28161aef860677a501`.
- Saved profile editing: commit `b02e2bc2c5f0baf12779785b4176d3ebeb0ae927`; multiline metadata correction: `0ef023a66d9837cd8411a603d3f1c3e1210d11af`.
- Skeleton hierarchy and humanoid coverage: commit `3a6f68e55808f5ac7300154493ce51bce2099fce`.
- Native generated-skeleton retarget proof: commit `dac18611028019938c5bf9a1a170836b1fb3ff4e`; dedicated Godot run #5 passed.
- Current Windows CI #224 is pending final lifecycle result; see `docs/SESSION_CHECKPOINT.md`.

## Deferred to their specified phases

- World Builder: Phase 3.
- Full Story/Scene Engine: Phase 4; preserve the existing partial Story Generator and keep its expansion frozen.
- Production animation library and timeline: Phase 5.
- Pakistani Urdu voice/TTS/lip-sync: Phase 6.
- Full episode rendering, audio mix and MP4: Phase 7.
- Target-PC benchmarks and optimization: Phase 8.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate.
