# Build and Install
Current workflow: .github/workflows/ci.yml  
Runner: windows-latest  
Python: 3.11  
Artifact: Cartoon-Studio-Windows-Bootstrap.zip

This is a source/runtime bootstrap ZIP, not yet a standalone installer. It includes start.bat, which creates a Python virtual environment, installs dependencies and starts FastAPI.

## Local run
1. Install Python 3.11 or newer on Windows.
2. Extract the project package.
3. Double-click start.bat.
4. Open http://127.0.0.1:8765 if the browser does not open automatically.

CI runs Ruff, Python compile checks, pytest and creates a Windows ZIP artifact. A green result must be confirmed by an actual Actions run. A standalone installer or bundled portable runtime will be evaluated after production dependencies stabilize.
