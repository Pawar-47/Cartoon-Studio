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

The current artifact is a source/runtime bootstrap ZIP, not yet a self-contained installer. It includes start.bat and the local application source.

## Run on Windows
1. Install Python 3.11 or newer.
2. Extract the ZIP.
3. Double-click start.bat.
4. The script creates a virtual environment, installs Python dependencies and launches the local server.
5. The browser opens at http://127.0.0.1:8765. If it does not, open that address manually.

Story Generator is available from the dashboard. It creates a prompt for a chosen AI provider; the user manually sends it to that provider, pastes the JSON response, validates it and saves the plan to a local project.

## CI pipeline
GitHub Actions runs Ruff, Python compile checks, pytest, Windows ZIP packaging and artifact upload. A green result must be confirmed by a real workflow run.

## Planned final installer
Godot 4.7.2 Compatibility is selected after a bounded hosted-runner proof. Package the application and static production assets into a self-contained Windows installer. Evaluate PyInstaller plus NSIS or an equivalent packaging route. The final installer should not require the user to manually install Python or Node.js. Do not bundle large models or assets until their size and license are verified. Target-PC performance tuning remains Phase 8 and is not an installer prerequisite.
