# Ara 3D Foundation Integration Patches

The pinned upstream source is kept unmodified in its own repository. Cartoon Studio applies a versioned patch script during the proof build and, if accepted, during every packaged build.

## Current pinned upstream
- Repository: https://github.com/olatunde85/3d-gen
- Commit: 4151c1124b172fdd918d23e0ef4aad727f4984c1
- Code license: MIT; see docs/ASSET_LICENSES.md for separate asset/model conditions.

## Patches in scripts/patch_ara_foundation.py
1. Extend the Studio film limit from 5 to 7 scenes. Each scene remains limited to 60 seconds, giving a 5–7 minute film range.
2. Increase the JSON film-file limit from 500 KB to 700 KB and update validation messages/tests.
3. Update user-facing documentation, AI Assist, MCP/CLI guides, metadata and the browser scene-strip test to reflect seven scenes.
4. Compact the right-hand inspector at desktop heights up to 800px. The upstream Windows proof run found the landscape, portrait and title-card controls clipped at 1366x768; the patch addresses this without removing controls.

## Latest proof evidence — run #6
- Workflow: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45486950450
- Tested Cartoon Studio commit: `3beb546b63e9a0a07e1459ea4f4e3ea26d6d41d6`
- Result: **CANCELLED**, not passed.
- Clone, dependency install, asset preparation, patch application, diff check, TypeScript type-check, film model checks and several editor browser checks completed.
- Browser MP4 export did not complete. Studio-wide checks, Vite build and artifact upload were skipped. No proof artifact exists.
- Logs do not prove whether export was slow, unsupported, failed without a surfaced message, or manually cancelled. Root cause remains unknown.
- Do not approve or integrate Ara on the basis of the partial checks.

## Patch safety
- Each source replacement asserts its expected occurrence count.
- The patch script fails closed if upstream changes unexpectedly.
- The pinned commit prevents silent upstream drift.
- Re-run upstream type checks, film tests, Studio UI tests and Vite build after every patch change.
- Before another proof run, make the browser export test bounded and diagnostic: surface export errors, capture progress/timeout state and retain browser logs/screenshots; keep the test clip minimal.
- Do not treat the patch as accepted until the full Windows proof workflow passes and the output is inspected.
