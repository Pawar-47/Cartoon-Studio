# Test Report

## Successful Windows application CI
Workflow run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45486108853  
Commit: 364372a21ccc319f1e6c2df9fd60869640f58174  
Runner: GitHub-hosted windows-latest  
Python: 3.11

| Check | Result |
|---|---|
| Dependency installation | PASS |
| Ruff lint | PASS |
| Python compileall | PASS |
| pytest | PASS — 10 passed, 1 warning |
| Windows bootstrap ZIP assembly | PASS |
| Artifact upload | PASS |

Artifact: Cartoon-Studio-Windows-Bootstrap  
Artifact ID: 14964581836  
SHA-256: 2fe23b9bd65e8dab6d1d24e5878987993d3aab67677a0bef51c681a2a08961a9  
Expires: 2026-12-08

## Application tests covered
- Health endpoint.
- Dashboard and Story Generator routes.
- Local project creation and listing.
- Story prompt generation and schema return.
- Urdu prompt instruction and production action catalog inclusion.
- Story plan validation.
- Story plan save/load against SQLite.
- Invalid episode duration rejection.
- Seven-scene episode acceptance and over-seven-scene rejection.
- Unknown animation clip ID rejection.

## Warning
One non-fatal Starlette TestClient/httpx deprecation warning remains. Investigate the supported httpx2 path or pin a compatible test dependency; do not suppress without understanding.

## Ara 3D foundation proof
The baseline proof identified inspector controls clipped at 1366x768. The first seven-scene patch proof found an assertion mismatch in the upstream browser test; the patch script was corrected to update the correct final scene-count assertion. A fresh pinned Windows proof is running and must pass typecheck, seven-scene film tests, Studio UI checks and Vite build before integration is accepted.

## Not yet tested
No final 3D character generation, toon shading, animation quality, Urdu TTS, Urdu lip-sync, complete episode rendering, target-PC performance or actual Windows installation has been verified.
