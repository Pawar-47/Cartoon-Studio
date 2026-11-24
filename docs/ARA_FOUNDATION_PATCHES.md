# Ara 3D Foundation Integration Patches

The pinned upstream source is kept unmodified in its own repository. Cartoon Studio applies a versioned patch script during the proof build and, if accepted, during every packaged build.

## Current pinned upstream
- Repository: https://github.com/olatunde85/3d-gen
- Commit: 4151c1124b172fdd918d23e0ef4aad727f4984c1
- Code license: MIT; see docs/ASSET_LICENSES.md for separate asset/model conditions.

## Patches in scripts/patch_ara_foundation.py
1. Extend the Studio film limit from 5 to 7 scenes. Each scene remains limited to 60 seconds, giving a 5–7 minute film range.
2. Increase the JSON film-file limit from 500 KB to 700 KB and update validation messages/tests.
3. Update user-facing documentation and AI Assist guidance to reflect seven scenes.
4. Compact the right-hand inspector at desktop heights up to 800px. The upstream Windows proof run found the landscape, portrait and title-card controls clipped at 1366x768; the patch addresses this without removing controls.

## Patch safety
- Each source replacement asserts its expected occurrence count.
- The patch script fails closed if upstream changes unexpectedly.
- The pinned commit prevents silent upstream drift.
- Re-run upstream type checks, film tests, Studio UI tests and Vite build after every patch change.
- Do not treat the patch as accepted until the Windows proof workflow passes and the output is inspected.
