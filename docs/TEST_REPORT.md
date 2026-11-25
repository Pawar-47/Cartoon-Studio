# Test Report

## Cartoon Studio CI — current HEAD

Workflow run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45487769827  
Run ID: `45487769827`  
Commit: `40bec8c423e953a0753c62f53c8a173274ac72e1`  
Runner: GitHub-hosted Windows Server 2025  
Python: 3.11

| Check | Result |
|---|---|
| Dependency installation | PASS |
| Ruff lint | PASS |
| Python compileall | PASS |
| pytest | PASS — 12 passed, 1 warning |
| Windows bootstrap ZIP assembly | PASS |
| Artifact upload | PASS |

Artifact: Cartoon-Studio-Windows-Bootstrap  
Artifact ID: `14963389016`  
Size: 74,228 bytes  
SHA-256: `423371c438c3b07a5b2aa3c38f6b26768078ffb1611e96b72d3c08a2e189d0ea`  
Expires: 2026-12-08 21:07:29 UTC

The ZIP contains README, launcher, requirements, app source and docs. It is not a self-contained installer and does not include a 3D engine.

## Application test coverage

Source: `tests/test_app.py`.

- Health endpoint.
- Dashboard and Story Generator routes.
- Local project creation and listing.
- Story prompt generation and schema return.
- Pakistani Urdu instruction and production action/location catalog inclusion.
- Story-plan validation and SQLite save/load.
- Episode duration and 5–7 scene constraints.
- Unknown location, expression and animation ID rejection.

The latest run reports 12 passing tests and one non-fatal warning: Starlette `TestClient` with `httpx` is deprecated; the warning recommends `httpx2`. Investigate compatibility before changing the test dependency; do not suppress it without understanding.

## Ara 3D Foundation proof — run #6

Run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45486950450  
Run ID: `45486950450`  
Cartoon Studio commit tested: `3beb546b63e9a0a07e1459ea4f4e3ea26d6d41d6`  
Ara upstream: `olatunde85/3d-gen@4151c1124b172fdd918d23e0ef4aad727f4984c1`  
Final conclusion: **CANCELLED**.

Completed:
- Windows runner setup, pinned source clone, npm dependency installation.
- `npm run setup-assets` (MakeHuman data/system assets and upstream media preparation).
- Cartoon Studio patch script, `git diff --check`.
- `npm run typecheck`.
- Film unit/model checks for seven-scene cap, file limits, timing, editing and travel-set data.
- Several browser checks: scene add, set/name/transition changes, playback, reload/save, duplication, reordering and deletion.

Not completed:
- Browser-level two-scene MP4 export test. The log stops at the export wait and the job was cancelled.
- Studio-wide checks.
- Vite production build with `BASE_PATH=/ara/`.
- Proof artifact upload.

There are no artifacts for this run. Do not describe it as a successful proof. The reason the browser export did not finish is not established by the logs; investigate the export path and test timeout/cancellation before any rerun.

## Not yet tested

- Complete 3D character creation and persistent identity.
- Cartoon/toon visual quality and actual animation playback.
- Urdu TTS, Pakistani pronunciation, character voice consistency or Urdu lip-sync.
- End-to-end scene rendering and complete 5–7 minute MP4.
- Target-PC installation, GPU compatibility, memory use or render speed.
- Persistent render queue, retries and restart recovery.
- Final Windows installer.

## Evidence policy

A type-check, source inspection or partial test is not a production proof. Visual features require inspection of actual rendered output. No requirement is VERIFIED without direct evidence for its acceptance criteria.


## Latest live-main CI — run #67

Run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45489366441  
Run ID: `45489366441`; run number: `67`  
Commit: `c389391643a7b1f7b5683e181421291fdba7abb2` (exact live `main` HEAD at audit)  
Conclusion: **SUCCESS**. The Windows job completed dependency installation, Ruff, Python compile, pytest, bootstrap ZIP assembly and artifact upload.

Artifact: `Cartoon-Studio-Windows-Bootstrap`  
Artifact ID: `14964957829`  
Size: 78,882 bytes  
SHA-256: `f307617262c75506d622ad602e204b85935bc88a7b73797d14d2c2344dd97fd7`  
Expires: 2026-12-08 21:16:41 UTC

This is the latest verified build artifact. It remains a bootstrap ZIP, not a self-contained installer or completed production studio. The 15 docs-only commits from #53 through #67 each triggered CI; this is recorded as a process violation, not as 15 meaningful development batches.
