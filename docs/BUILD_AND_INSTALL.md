# Build and Install

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
After the 3D runtime is selected and stable, package the application and static production assets into a self-contained Windows installer. Evaluate PyInstaller plus Inno Setup or an equivalent packaging route. The final installer should not require the user to manually install Python or Node.js. Do not bundle large models or assets until their size, license and target-PC compatibility are verified.
