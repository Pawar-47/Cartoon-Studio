# Next Steps — 2026-11-25

## Live checkpoint
- Repository: Pawar-47/Cartoon-Studio
- Branch: main
- Previous verified HEAD: bbca69d5ff9933dd04233a1fd757d86c7e60e83d
- Latest verified CI: run #93 — SUCCESS on the previous verified HEAD facb0dd738e227d643d4e85d80bd5d3f620fc6e1; documentation batch commits are awaiting their own CI run.
- Original 25-part master brief and 171-row registry/traceability baseline remain preserved.

## Gate correction — target-PC testing is deferred
The user's physical Windows PC is not a prerequisite for architecture, implementation or phase progression. P0.4 uses source-level hardware/API requirements, Intel specifications, driver documentation and explicit resource-risk analysis. The existing diagnostic harness remains optional. Actual representative-scene measurements and quality-preset tuning are assigned to Phase 8 / P8.1. Do not ask the user to run the probe as a blocker, and do not claim performance that has not been measured.

## Completed P0.5 architecture batch
- DEPENDENCY_DECISIONS.md records core dependencies, candidate versions, license constraints, optional integrations, queue/media/voice strategy and proof gates.
- ARCHITECTURE_TRACEABILITY.md maps all 171 atomic registry IDs to architecture homes, planned module boundaries and delivery phases.
- ARCHITECTURE.md, contracts, decision log, candidate scorecard and phase plan now reflect these decisions.
- P0.5 documentation is complete. No production engine, queue, FFmpeg build or TTS model is falsely marked integrated.

## Active batch — P0.6 bounded functional proofs
1. Prove the Godot native worker boundary with a bounded import/animate/save/reopen/short-render test in a controlled CI/dev environment; no user-PC benchmark is needed.
2. Verify FFmpeg build/codec licensing and output, and test SQLite queue state/retry/cancel/restart semantics with synthetic jobs.
3. Treat the Web viewport as optional; failure to prove it does not block native production rendering. Keep physical-PC performance measurements in Phase 8.lation, crash recovery and migration strategy.
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
