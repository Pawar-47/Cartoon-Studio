# Test Report

## Confirmed successful Windows CI run
Workflow run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45483211675  
Commit: da5098d575b856e59efd3b6e911d2b94afc64662  
Runner: GitHub-hosted windows-latest  
Python: 3.11

| Check | Result |
|---|---|
| Dependency installation | PASS |
| Ruff lint | PASS |
| Python compileall | PASS |
| pytest | PASS — 3 passed |
| Windows bootstrap ZIP assembly | PASS |
| Artifact upload | PASS |

Artifact: Cartoon-Studio-Windows-Bootstrap  
Artifact ID: 14963915881  
SHA-256: 36fbf17594f8aa0a0f41ac187834ee26f46cd667262143aa83c5308d06631000  
Expires: 2026-12-08T20:40:58Z

## Tests covered
- Health endpoint returns success.
- Dashboard route returns the application page.
- Local project creation and listing work against a temporary SQLite database.

## Warnings
The successful run reported 3 non-fatal warnings: Starlette recommends httpx2 over httpx for its TestClient, and FastAPI on_event is deprecated. The app startup hook is now being moved to the lifespan API; re-run CI to confirm. Do not suppress warnings without understanding them.

## Not yet tested
No 3D rendering, character import, animation, Urdu speech, lip-sync, episode assembly, target-PC performance or actual Windows installation has been tested. This report must not be interpreted as production readiness.
