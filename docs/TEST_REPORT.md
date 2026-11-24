# Test Report

## Successful Windows application CI
Workflow run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45487439930  
Commit: 3dc006102f7b911c0b24db119f0fc166b5807a41  
Runner: GitHub-hosted windows-latest  
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
Artifact ID: 14965370345  
SHA-256: ffc96c280d403ac6b33a3ea35bacf49c48a1d10fc4bf943925c75db0a09634ce  
Expires: 2026-12-08

## Application tests covered
- Health endpoint.
- Dashboard and Story Generator routes.
- Local project creation and listing.
- Story prompt generation and schema return.
- Urdu prompt instruction and production action catalog inclusion.
- Validation of actual location IDs, expression IDs and animation clip IDs.
- Story plan save/load against SQLite.
- Invalid episode duration rejection.
- Seven-scene episode acceptance and over-seven-scene rejection.
- Unknown location, expression and animation ID rejection.

## Warning
One non-fatal Starlette TestClient/httpx deprecation warning remains. Investigate the supported httpx2 path or pin a compatible test dependency; do not suppress without understanding.

## Ara 3D foundation proof
Pinned upstream source and assets prepared. The seven-scene/700 KB and compact-inspector patches applied; patch diff and TypeScript type-check passed. Seven-scene browser and MP4 export checks are running. Studio UI checks and Vite build have not yet completed.

## Not yet tested
No final 3D character generation, toon shading, animation quality, Urdu TTS, Urdu lip-sync, complete episode rendering, target-PC performance or actual Windows installation has been verified.
