# Build and Install

## Local data and migration behavior
- Windows default data root: %LOCALAPPDATA%\\CartoonStudio.
- Override: set CARTOON_STUDIO_DATA to a custom writable directory before launching start.bat.
- SQLite index: cartoon_studio.sqlite3; numbered schema_migrations table records database migrations.
- Existing databases are backed up under backups/ before schema upgrades.
- Each project has a portable projects/<project-id>/project.json document; saved episode plans are stored under projects/<project-id>/episodes/<episode-id>.json. SQLite indexes these documents and retains the legacy story_plans compatibility table.
- The project JSON is versioned and uses stable project/episode IDs. Keep the entire project folder when copying or backing up project files.

## Current Windows bootstrap
Workflow: .github/workflows/ci.yml  
Runner: windows-latest  
Python: 3.11  
Artifact: Cartoon-Studio-Windows-Bootstrap.zip

The current artifact is a source/runtime bootstrap ZIP, not yet a self-contained installer. It includes start.bat, the local application source, docs and hash-locked runtime requirements. CI #136 extracted it into a clean Windows temporary directory and executed the actual launcher successfully.

## Run on Windows
1. Install Python 3.11 or newer.
2. Extract the ZIP.
3. Double-click start.bat (Python 3.11 must be installed and available through the Windows Python launcher).
4. The script creates a virtual environment and installs the exact hash-locked runtime dependencies.
5. The local server listens on http://127.0.0.1:8765. The browser opens automatically; if it does not, open that address manually.
6. Optional automation settings: CARTOON_STUDIO_PORT changes the loopback port; CARTOON_STUDIO_DATA changes the user-data directory; CARTOON_STUDIO_NO_BROWSER=1 suppresses automatic browser opening.

Story Generator is available from the dashboard. It creates a prompt for a chosen AI provider; the user manually sends it to that provider, pastes the JSON response, validates it and saves the plan to a local project.

## CI pipeline
GitHub Actions verifies uv.lock, installs the exact locked environment, runs Ruff, Python compile checks and pytest, exports and drift-checks requirements.lock, generates a CycloneDX SBOM, packages the Windows ZIP, extracts it in a clean temporary directory, runs the real start.bat, tests HTTP/UI/API and project persistence across restart, then uploads the ZIP and SBOM. CI #136 passed this full sequence (22 pytest tests).

## Planned final installer
Godot 4.7.2 Compatibility is selected after a bounded hosted-runner proof. Package the application and static production assets into a self-contained Windows installer. Evaluate PyInstaller plus NSIS or an equivalent packaging route. The final installer should not require the user to manually install Python or Node.js. Do not bundle large models or assets until their size and license are verified. Target-PC performance tuning remains Phase 8 and is not an installer prerequisite.
