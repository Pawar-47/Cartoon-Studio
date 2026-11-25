# Next Steps — 2026-11-25

## Active batch — Phase 2 Character Studio

The first user-facing non-destructive imported-GLB retarget workflow is implemented. Saved retarget preview API and UI are covered by the successful Windows CI #281 run. It includes source/target selectors, preflight validation, a saved Godot scene, a persistent project record, scene download, and a runtime check that the reopened source animation transfers its pose to the target skeleton.

Saved retarget records now also have a browser preview action. The preview endpoint resolves the project's original source/target GLBs and canonical humanoid mappings; the browser uses the locally vendored Three.js SkeletonUtils retarget pass to animate the target GLB. This is a visual aid, not the authoritative saved-scene renderer. The Godot scene remains the authoritative native artifact.

## Verification

- Windows CI #281 passed on commit `dd0354d8c264a5d2449a0b5249b0502e5b9b6be8` on 2026-11-25. It passed lint, Python compilation, the full pytest suite including the pinned Godot 4.7.2 worker test, bootstrap package/smoke, both self-contained builds, NSIS installer, install/upgrade/uninstall/reinstall lifecycle and artifact upload.
- CI #281 also validated the saved retarget-preview API contract. The later commits adding DCC bone-name aliases, malformed-index rejection and four naming-family tests are newer than that run and remain pending CI.
- Earlier Windows CI #279 passed on commit 56c61487089097108b6baa862f9ac9125568b9a5: lint, Python compilation, full pytest suite including the pinned Godot 4.7.2 worker scenario, Windows bootstrap packaging/smoke test, both self-contained application builds, NSIS installer compilation, clean install, upgrade, uninstall, reinstall and artifact uploads.
- CI #279 artifacts: Windows installer (103,861,406 bytes), bootstrap (819,154 bytes), dependency SBOM (32,632 bytes).
- The worker test covers a Mixamo-named animated source and a distinct differently proportioned target; it checks source animation playback, pose transfer after scene save/reopen and byte-identical source asset preservation.
- Browser retarget preview is newly implemented in this batch; its API contract is covered by a new FastAPI test. Browser visual fidelity and diverse third-party GLBs still require acceptance testing.

## Next substantial batch

1. Validate the newly committed naming coverage for 3ds Max Biped, Character Creator, Unreal-style and Blender Rigify skeletons in CI; then add real imported GLB fixtures.
2. Exercise rest-pose axes, bone roll, scale and multi-clip animation behavior; report compatibility limits instead of guessing.
3. Validate real facial morph controls on blend-shape GLBs, including preview, save/reopen and neutral reset.
4. Compare browser preview motion against the authoritative Godot scene before expanding deterministic export.

## Deferred to their specified phases

- World Builder: Phase 3.
- Full Story/Scene Engine: Phase 4; preserve the existing partial Story Generator and keep its expansion frozen until then.
- Production animation library and timeline: Phase 5.
- Pakistani Urdu voice/TTS/lip-sync: Phase 6.
- Full episode rendering, audio mix and MP4: Phase 7.
- Target-PC benchmarks and optimization: Phase 8.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 2–7 remain open.
