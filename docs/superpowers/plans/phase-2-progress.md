# Phase 2 progress ledger

Plan: `docs/superpowers/plans/2026-11-27-phase-2-character-studio.md`
Base: `c5631247b0b3d3144b2c6b3df9b9be318f6e9c1a`

- Ruling: Use the existing PR #23 pull_request synchronize trigger to run the browser acceptance workflow instead of adding a separate manual dispatch workflow; the current CI already targets PRs into main and concurrency is non-cancelling. This avoids another workflow and an unnecessary CI run.
- Ruling: Use an ephemeral pinned Node Playwright install in the Windows job instead of adding a Python package or changing uv.lock; this keeps the Python lock untouched and browser automation remains isolated to CI.
- Current: Phase 2 requirements CHAR-R001–CHAR-R006 remain partial in the registry. Phase 3 is progressing independently on main; no changes to main are permitted.


## 2026-11-27 — Browser acceptance implementation

- Fixed a JavaScript parse error in the Foundry saved-recipe editor loop.
- Extended the existing Windows CI job with a pinned Playwright Chromium install and real FastAPI/Godot-backed browser acceptance.
- The browser run creates male and female Foundry characters through the UI, downloads the GLB, reopens and edits a saved recipe, checks stable identity and revision, verifies Godot rig/morph inspection, exercises portrait/turnaround export, and saves screenshots/logs as an artifact.
- Acceptance remains pending until the workflow has run and its screenshots have been inspected. No requirement is marked verified by adding the automation alone.

## 2026-11-27 — Godot 4.7.2 CI repair

- Run #557 verified Ruff, browser JavaScript syntax and Python compilation, then exposed existing worker parser errors in generated-face ArrayMesh handling: untyped Variant values and an incorrect add_surface_from_arrays LOD dictionary argument.
- The same run exposed two Foundry test defects: male/female geometry was compared only by bounding boxes (which legitimately match), and pole triangles from ellipsoid details had zero area.
- Feature-only repair: add explicit GDScript types, pass the Godot 4.7.2 LOD dictionary argument, compare actual generated vertex buffers, and omit zero-area triangles before GLB export.
- Run #557 did not reach browser acceptance because the unit/Godot test step failed. Re-run only after this coherent repair is committed.
