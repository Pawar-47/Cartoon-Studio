# Next Steps — 2026-11-25

## Active batch — Phase 2 Character Studio

The first user-facing non-destructive imported-GLB retarget workflow and saved browser preview are implemented. Facial morph-target metadata is now reported by the Godot worker; named and unnamed morph fixtures are covered, and the appearance API has save/reopen/range-validation regression tests. The appearance editor now pauses embedded animation playback to prevent morph animation tracks from fighting expression sliders; ordinary previews still auto-play. Windows CI #299 passed the complete pipeline, including a real third-party Khronos Rigged Figure retargeted onto the canonical target after scene save/reopen. It includes source/target selectors, preflight validation, a saved Godot scene, a persistent project record, scene download, and a runtime check that the reopened source animation transfers its pose to the target skeleton.

Saved retarget records now also have a browser preview action. The preview endpoint resolves the project's original source/target GLBs and canonical humanoid mappings; the browser uses the locally vendored Three.js SkeletonUtils retarget pass to animate the target GLB. This is a visual aid, not the authoritative saved-scene renderer. The Godot scene remains the authoritative native artifact.

## Verification

- Windows CI #303 passed on commit `0bfce71625d6e3084b4ceda9b64a9825cca95101`: Ruff lint, Python compilation, full pytest including pinned Godot 4.7.2 tests, third-party GLB inspection/retarget, morph-target inspection, bootstrap smoke, both self-contained builds, NSIS installer and full install/upgrade/uninstall/reinstall lifecycle.
- Windows CI #304 on commit `7b703ec14b116440f5d6f1401ffce8bec5c7a16c`: lint, Python compilation and full pytest passed, including the new API persistence and signed-weight range test; Windows packaging and installer lifecycle are still running.
- Windows CI #293 passed the complete pipeline for Godot facial blend-shape inspection, imported default values, signed morph weights and Character Studio reporting.
- Windows CI #285 passed four DCC naming families and malformed hierarchy rejection.
- Earlier Windows CI #279 passed on commit 56c61487089097108b6baa862f9ac9125568b9a5: lint, Python compilation, full pytest suite including the pinned Godot 4.7.2 worker scenario, Windows bootstrap packaging/smoke test, both self-contained application builds, NSIS installer compilation, clean install, upgrade, uninstall, reinstall and artifact uploads.
- CI #279 artifacts: Windows installer (103,861,406 bytes), bootstrap (819,154 bytes), dependency SBOM (32,632 bytes).
- The worker test covers a Mixamo-named animated source and a distinct differently proportioned target; it checks source animation playback, pose transfer after scene save/reopen and byte-identical source asset preservation.
- Browser retarget preview is implemented and its API contract is covered by FastAPI tests. Browser visual fidelity and diverse third-party GLBs still require acceptance testing.

## Next substantial batch

1. Expand third-party acceptance beyond the single Khronos Rigged Figure model, prioritizing different rest axes, bone roll, proportions and multi-clip animations.
2. Add a genuinely facial third-party blend-shape model fixture and verify browser preview, save/reopen, signed weights and reset-to-imported-default behavior. Current named Smile/Blink fixture is synthetic; the third-party CC0 morph fixture is animated but not facial.
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
