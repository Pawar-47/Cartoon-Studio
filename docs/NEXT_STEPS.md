# Next Steps — 2026-11-25

## Active batch — Phase 2 Character Studio

The first user-facing non-destructive imported-GLB retarget workflow is implemented. It includes source/target selectors, preflight validation, a saved Godot scene, a persistent project record, scene download, and a runtime check that the reopened source animation actually transfers its pose to the target skeleton.

## Verification

- Windows CI #250 passed the full pipeline after fixing the 15-bone mapping-key comparison.
- Windows CI #251 passed the full pipeline with GLB container skin-count preflight.
- Windows CI #252 passed the full pipeline with exact-one-skeleton preflight and saved-scene download.
- Windows CI #257 passed the full pipeline, including the real two-imported-GLB worker test. The worker reopens the saved scene, advances 72 frames, verifies the source AnimationPlayer is playing, and checks the target LeftUpperArm pose against the animated source.
- The worker test currently uses two separate copies of the same humanoid fixture. The original source and target GLBs are verified unchanged.
- Dedicated Godot native-worker proof #11 passed. Its differently proportioned target skeleton is generated from the imported source hierarchy, not a second imported GLB.

## Next substantial batch

1. Create a second imported humanoid target GLB with different rest proportions and bone ordering, plus a reproducible fixture-generation/validation path.
2. Verify animation track paths after source/target bone names are normalized to the 15 canonical Godot humanoid profile names. Avoid silently breaking animation tracks.
3. Extend the imported-pair worker test to the distinct-proportion target fixture and verify pose transfer, mesh binding, scene save/reopen and unchanged source assets.
4. Exercise representative third-party GLBs with different naming conventions and document supported/unsupported cases.
5. Add a practical preview/open action for saved retarget scenes in Character Studio.
6. Validate real facial morph controls on blend-shape GLBs and continue deterministic export/round-trip only after rig/animation behavior is proven.

## Deferred to their specified phases

- World Builder: Phase 3.
- Full Story/Scene Engine: Phase 4; preserve the existing partial Story Generator and keep its expansion frozen until then.
- Production animation library and timeline: Phase 5.
- Pakistani Urdu voice/TTS/lip-sync: Phase 6.
- Full episode rendering, audio mix and MP4: Phase 7.
- Target-PC benchmarks and optimization: Phase 8.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 3–7 remain open.
