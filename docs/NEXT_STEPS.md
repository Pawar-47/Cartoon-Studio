# Next Steps — 2026-11-25

## Live checkpoint
- Repository: Pawar-47/Cartoon-Studio
- Branch: main
- Previous verified HEAD: 745d557a5f043bca4a1012ec95d79e2fb87dd91d
- Latest verified CI: run #90 — SUCCESS on that exact HEAD.
- Original 25-part master brief and 171-row registry/traceability baseline remain preserved.

## Gate correction — target-PC testing is deferred
The user's physical Windows PC is not a prerequisite for architecture, implementation or phase progression. P0.4 uses source-level hardware/API requirements, Intel specifications, driver documentation and explicit resource-risk analysis. The existing diagnostic harness remains optional. Actual representative-scene measurements and quality-preset tuning are assigned to Phase 8 / P8.1. Do not ask the user to run the probe as a blocker, and do not claim performance that has not been measured.

## Active batch — P0.5 architecture and dependency decisions
1. Define canonical, engine-neutral project, character, world, scene, animation, audio, asset and render-job contracts with explicit schema versions and stable Cartoon Studio IDs.
2. Compare three integration paths: Godot native shell, Godot renderer sidecar controlled by the existing browser/FastAPI app, and Godot Web viewport. Preserve the FastAPI/SQLite/browser foundation unless evidence justifies a bounded adapter.
3. Define service boundaries, local data layout, asset registry, provider adapters, offline behavior, queue persistence, scene cache, retries, cancellation, crash recovery and migration strategy.
4. Keep Godot Compatibility provisional until architecture-critical P0.6 proofs and licensing review; keep Blender optional for authoring rather than assuming it is the runtime.
5. Keep Urdu TTS unselected until a native Pakistani Urdu sample is evaluated in Phase 6. Human recording, manual timing and manual viseme editing remain first-class fallbacks.
6. Update architecture, decision log and batch plan in one coherent batch.

## Downstream sequence
- P0.6: bounded candidate proofs only for unresolved architecture-critical questions; no physical-PC benchmark prerequisite.
- P0.7: Phase 0 compliance review and architecture freeze.
- Phase 1: finish app foundation, reproducible Windows packaging and clean CI/VM installation path.
- Phase 2 onward: follow the original brief exactly.
- Phase 8: actual target-PC benchmarks, quality presets, optimization, recovery and final acceptance.

## Operating constraints
- GitHub main is the only project source of truth.
- Preserve all existing code and artifacts; no resets or restart from zero.
- Work in substantial coherent batches and commit once per batch.
- No mandatory paid APIs, cloud rendering or hidden quota bypass.
- Do not send user audio/content to external providers without explicit approval.
- Report implementation and test evidence separately; never invent performance, visual or audio results.
