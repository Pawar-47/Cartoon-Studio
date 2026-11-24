# Test Report

## Successful Windows application CI
Workflow run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45484822969  
Commit: 36da0a7515904f11248bc8d29e12f8b8cc8ea199  
Runner: GitHub-hosted windows-latest  
Python: 3.11

| Check | Result |
|---|---|
| Dependency installation | PASS |
| Ruff lint | PASS |
| Python compileall | PASS |
| pytest | PASS — 9 passed, 1 warning |
| Windows bootstrap ZIP assembly | PASS |
| Artifact upload | PASS |

Artifact: Cartoon-Studio-Windows-Bootstrap  
Artifact ID: 14963402893  
SHA-256: 1c19f0f98e39bcd2042045bed681d1a36f28a240452dfc47b7e4a36953900483  
Expires: 2026-12-08

## Application tests covered
- Health endpoint.
- Dashboard route.
- Story Generator route.
- Local project creation and listing.
- Story prompt generation and schema return.
- Story plan validation.
- Story plan save/load against SQLite.
- Invalid episode duration rejection.
- Seven-scene episode acceptance and over-seven-scene rejection.

## Warning
One non-fatal Starlette TestClient/httpx deprecation warning remains. Investigate the supported httpx2 path or pin a compatible test dependency; do not suppress without understanding.

## Ara 3D foundation proof
Baseline run found the inspector controls clipped at 1366x768. This is a real UI defect, not a test to skip. A patch is being applied for compact desktop viewports. The updated pinned Windows proof must pass typecheck, seven-scene film checks, Studio checks, browser scene-strip checks and Vite build before integration is accepted.

## Not yet tested
No final 3D character generation, toon shading, animation quality, Urdu TTS, Urdu lip-sync, complete episode rendering, target-PC performance or actual Windows installation has been verified.
