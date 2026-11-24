# Next Steps

## Active phase: Phase 0 — planning and research

No new feature implementation batch is authorized until Phase 0 exits.

1. **P0.2 — Full requirements decomposition:** re-read the complete project specification and approved master prompt; expand the registry so every distinct requirement and sub-requirement has an ID, priority, dependency, target module, implementation plan, test method and evidence field. Build one-to-one traceability coverage.
2. **P0.3 — 3D and animation research:** compare multiple complete editors and focused tools for character modeling, toon style, rigging, animation, timeline, camera, world building and rendering. Inspect sources, build systems, tests, release health and licenses.
3. **P0.4 — Hardware and rendering research:** compare browser/WebGL and local rendering options against Intel HD 5500 and 8 GB RAM. No engine is selected yet.
4. **P0.5 — Urdu voice and AI provider research:** verify Urdu-script quality, Pakistani pronunciation, CPU footprint, licensing, free quotas, terms and official integration options. Keep manual fallbacks.
5. **P0.6 — Bounded candidate proofs:** run only the proofs needed to decide between candidates. Inspect actual output; do not auto-integrate a passing candidate.
6. **P0.7 — Architecture freeze:** publish module boundaries, engine-neutral data contracts, selected dependencies, risks and detailed implementation batches.

## Current evidence

- Latest application CI run 45 is green: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45486332959.
- Current Windows artifact is a bootstrap package, not the final installer.
- Ara proof run 5 was already active at the seven-scene film test; its final result must be inspected before closing the candidate record.
- No integrated 3D renderer or final episode pipeline exists yet.

Do not skip P0 gates or start character/world/voice/render implementation ahead of the frozen architecture.
