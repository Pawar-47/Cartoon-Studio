# Next Steps

## Active phase: Phase 0 — Complete Specification and GitHub Research

Phase 0 has not exited. No new production-feature implementation may begin until P0.2–P0.7 are complete. Preserve all existing source and partial work.

## Verified live checkpoint

- Branch: `main`
- Live HEAD: `c389391643a7b1f7b5683e181421291fdba7abb2`
- Latest CI: [run #67](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45489366441), SUCCESS on the exact live HEAD.
- Windows bootstrap artifact: ID `14964957829`, 78,882 bytes, SHA-256 `f307617262c75506d622ad602e204b85935bc88a7b73797d14d2c2344dd97fd7`.
- This is a bootstrap ZIP only; it is not a self-contained installer.
- Ara proof run #6 (`45486950450`) is CANCELLED during browser MP4 export. It is not an approval or a successful proof.

## Correct execution sequence

### Phase 0 — complete first

1. **P0.2 — Atomic requirement decomposition (NEXT).** Cover every requirement/sub-requirement in the original 25-part master brief and all sections/acceptance bullets of `PROJECT_SPECIFICATION.md`. Every row must include ID, source section, priority, dependencies, module, implementation approach, test method, evidence, status and limitations. Add one traceability row per requirement.
2. **P0.3 — Comparative GitHub research.** Inspect source, docs, releases, activity, issues, dependencies, build scripts, tests, compatibility and exact licenses for character/toon/rigging, worlds, animation, renderers, TTS/lip-sync, audio, packaging, queue/recovery and AI-provider candidates.
3. **P0.4 — Hardware, Urdu and provider feasibility.** Verify Intel HD 5500/Windows paths, memory/render constraints, Pakistani Urdu samples and pronunciation, model/data rights, CPU feasibility, free quotas and Pakistan availability.
4. **P0.5 — Architecture and decisions.** Define engine-neutral versioned contracts, stable IDs/adapters, project storage, offline operation, asset management, job queue/cache/recovery, packaging and rejected options.
5. **P0.6 — Bounded candidate proofs.** Diagnose the cancelled Ara browser export check; make any rerun minimal, time-bounded and diagnostic. Inspect real output and resource use. Do not select Ara automatically.
6. **P0.7 — Phase 0 freeze.** Confirm full coverage, source/license evidence, hardware/Urdu risk decisions and the complete batch plan.

### Phase 1 — application foundation

7. **P1.1–P1.4:** harden persistence and project storage, reproducible CI, portable package, self-contained installer, and clean Windows install/upgrade/data-preservation verification. The current bootstrap ZIP alone does not pass the phase gate.

### Later phases — follow the original master brief exactly

8. Phase 2 Character Studio.
9. Phase 3 World Builder.
10. Phase 4 Story and Scene Engine. Preserve current early Story Generator work, but do not expand it before this phase; normalize its Ara-derived catalogs first.
11. Phase 5 Animation Engine.
12. Phase 6 Urdu Voice and Lip-Sync.
13. Phase 7 Episode Generator.
14. Phase 8 Optimization and Reliability.

## Batch execution rules

- One substantial, coherent batch at a time.
- Re-read linked requirements/dependencies and source before each batch.
- Implement the complete feature group; run tests and inspect real output.
- Update registry, traceability, status, test report, research/decision log and next steps together.
- Make one coherent commit after the batch; do not commit individual documentation edits.
- Run CI after the batch, not after every minor edit.
- No validation-only cycles, no UI-only feature claims, no destructive resets.
- No paid mandatory services, quota bypass or cloud-rendering dependency.
- Keep Pakistani Urdu, target hardware and local-first operation as hard constraints.
