# Next Steps — 2026-11-25

## Active batch — Phase 2 Character Studio

The first user-facing non-destructive imported-GLB retarget workflow and saved browser preview are implemented. Windows CI #299 passed the complete pipeline, including a real third-party Khronos Rigged Figure retargeted onto the canonical target after scene save/reopen. It includes source/target selectors, preflight validation, a saved Godot scene, a persistent project record, scene download, and a runtime check that the reopened source animation transfers its pose to the target skeleton.

Saved retarget records now also have a browser preview action. The preview endpoint resolves the project's original source/target GLBs and canonical humanoid mappings; the browser uses the locally vendored Three.js SkeletonUtils retarget pass to animate the target GLB. This is a visual aid, not the authoritative saved-scene renderer. The Godot scene remains the authoritative native artifact.

## Verification

- Windows CI #299 passed on commit `570c6f9b2d0fe35b64ec74e84ab8d0e702d7665d` on 2026-11-25: Ruff lint, Python compilation, full pytest including pinned Godot 4.7.2 tests, third-party GLB inspection and retarget, morph-target inspection, bootstrap smoke, both self-contained builds, NSIS installer and full install/upgrade/uninstall/reinstall lifecycle.
- Windows CI #293 also passed the complete pipeline for Godot facial blend-shape inspection, imported default values, signed morph weights and Character Studio reporting.
- Earlier Windows CI #279 passed on commit 56c61487089097108b6baa862f9ac9125568b9a5: lint, Python compilation, full pytest suite including the pinned Godot 4.7.2 worker scenario, Windows bootstrap packaging/smoke test, both self-contained application builds, NSIS installer compilation, clean install, upgrade, uninstall, reinstall and artifact uploads.
- CI #279 artifacts: Windows installer (103,861,406 bytes), bootstrap (819,154 bytes), dependency SBOM (32,632 bytes).
- The worker test covers a Mixamo-named animated source and a distinct differently proportioned target; it checks source animation playback, pose transfer after scene save/reopen and byte-identical source asset preservation.
- Browser retarget preview is newly implemented in this batch; its API contract is covered by a new FastAPI test. Browser visual fidelity and diverse third-party GLBs still require acceptance testing.

## Next substantial batch

1. Expand third-party acceptance beyond the single Khronos Rigged Figure model, prioritizing different rest axes, bone roll, proportions and multi-clip animations.
2. Add a real facial blend-shape model fixture and verify browser preview, save/reopen, signed weights and reset-to-imported-default behavior.
3. Compare browser retarget preview motion against the authoritative Godot scene across multiple rig families.
4. Continue deterministic export and animation round-trip after broader compatibility acceptance.

## Deferred to their specified phases

- World Builder: Phase 3.
- Full Story/Scene Engine: Phase 4; preserve the existing partial Story Generator and keep its expansion frozen until then.
- Production animation library and timeline: Phase 5.
- Pakistani Urdu voice/TTS/lip-sync: Phase 6.
- Full episode rendering, audio mix and MP4: Phase 7.
- Target-PC benchmarks and optimization: Phase 8.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 2–7 remain open.
