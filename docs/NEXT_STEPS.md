# Next Steps

## Active phase: Phase 0 — specification, research and architecture freeze

Phase 0 has **not** exited. The master plan prohibits engine-dependent production feature development until the full requirements, comparative research, target-hardware/Urdu feasibility and architecture gates are complete.

## Current verified checkpoint

- Branch: `main`
- Source baseline tested by CI run #52: `40bec8c423e953a0753c62f53c8a173274ac72e1`.
- Checkpoint documents have since been reconciled in additional `main` commits; fetch the live `main` HEAD before every subsequent batch.
- Latest Cartoon Studio CI: run #52, ID `45487769827`, SUCCESS on the current HEAD.
- Test evidence: Ruff PASS, compile PASS, 12 pytest tests PASS (one deprecation warning), Windows bootstrap ZIP uploaded.
- Artifact: `Cartoon-Studio-Windows-Bootstrap`, ID `14963389016`, SHA-256 `423371c438c3b07a5b2aa3c38f6b26768078ffb1611e96b72d3c08a2e189d0ea`.
- Ara proof run #6, ID `45486950450`: CANCELLED during browser MP4 export. Type-check and partial film/editor tests passed; Studio checks, production build and artifact upload did not run. Ara is not selected.

## Ordered work queue

1. **P0.2 — Full requirement decomposition (highest priority).** Expand the registry beyond its current coarse feature rows. Every distinct requirement and sub-requirement in `PROJECT_SPECIFICATION.md` must have an ID, priority, dependencies, target module, implementation approach, test method, evidence and status. Trace every row through spec → architecture → source → test → evidence. Include cross-cutting and acceptance requirements.
2. **P0.3 — Comparative open-source research.** Complete source-level comparisons for toon character generation/rigging, persistent world assets, animation/retargeting, Blender or alternative rendering, facial animation/lip-sync, Urdu speech/audio, video assembly, job queue/recovery, Windows packaging and multi-provider research. Verify code, model, dataset and asset licenses separately.
3. **P0.4 — Target-hardware and Urdu feasibility.** Gather evidence for Intel HD 5500/WebGL and Blender compatibility, memory/render constraints, Urdu-script Pakistani pronunciation, model rights and CPU TTS viability. No performance claims without measurements.
4. **P0.5 — Architecture and dependency decisions.** Keep the story schema engine-neutral; document adapters, versioned contracts, persistence, local paths, render queue, cache/recovery, offline behavior, packaging and rejected options.
5. **P0.6 — Bounded candidate proofs.** Investigate why Ara run #6 did not finish the browser MP4 export test. Re-run only after the proof is made bounded/reproducible and logs/artifact capture are adequate. A passing proof is still not automatic approval; inspect the output and target-like hardware evidence.
6. **P0.7 — Architecture freeze.** Publish the final decision and execution batch plan. Only then start the master plan's dependent production phases.

## Constraints

- Preserve all current source, tests, research and proof patches.
- Do not integrate Ara or bind the permanent data model to it without the evaluation gate.
- No validation-only loops: research must lead to explicit decisions and bounded proofs.
- Do not use GitHub Actions as a GPU render farm.
- No mandatory paid AI APIs, cloud inference, subscriptions or online activation.
- Keep Urdu/Pakistani pronunciation as a core requirement; do not substitute Hindi.
- Never call the bootstrap ZIP a final installer.
