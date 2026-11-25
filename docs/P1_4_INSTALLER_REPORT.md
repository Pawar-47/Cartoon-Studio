# P1.4 Installer Validation Report

**Date:** 2026-11-25  
**Repository:** Pawar-47/Cartoon-Studio  
**Branch:** main  
**Status:** COMPLETE

## Build

- Self-contained Python application built with PyInstaller one-folder.
- Version 0.1.0 and 0.1.1 bundles built from the same locked Python environment.
- NSIS 3.13.0 generated versioned per-user Windows installers.
- Installer does not require a separately installed Python or Node.js runtime.
- Start Menu and desktop shortcuts are created.
- Program files are installed under `%LOCALAPPDATA%\Programs\Cartoon Studio`.
- Project data remains separate from program files.

## Windows CI evidence

- [Run #175 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585234644), commit `24f1617cff4d592e981908c7ceea641225c05ac0`.
- [Run #176 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585584886), commit `815cc32a1cb56c3357c37310745e900a8a197c7f`.
- Both runs passed the full installer lifecycle. Run #176 additionally included temporary uninstaller lifecycle diagnostics; those diagnostics are not retained in the production installer script.

## Acceptance sequence

1. Build application version 0.1.0 and compile its NSIS installer.
2. Build application version 0.1.1 and compile its NSIS installer.
3. Install version 0.1.0 silently into the per-user program directory.
4. Launch the installed application and verify its health endpoint and UI.
5. Create a project and save it to an isolated persistent data directory.
6. Install version 0.1.1 over version 0.1.0.
7. Launch version 0.1.1 and confirm the original project remains available.
8. Uninstall and wait for NSIS's temporary uninstaller process to complete.
9. Confirm program files and shortcuts are removed while project data remains.
10. Reinstall version 0.1.1 and confirm the same project can still be opened.
11. Uninstall again and confirm project data remains intact.

## Artifacts from run #176

| Artifact | GitHub artifact ID |
|---|---:|
| Cartoon-Studio-Windows-Installer | 15008168874 |
| Cartoon-Studio-Windows-Bootstrap | 15007954336 |
| Cartoon-Studio-Dependency-SBOM | 15008014096 |

Open the [run #176 page](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585584886) to download the artifacts.

## Technical notes

- NSIS silently starts a temporary copy of its uninstaller. The smoke test waits for the temporary process to finish before inspecting removed files.
- The uninstaller restores the real installation directory from the per-user registry in `un.onInit`; it removes known application-owned files and shortcuts only.
- User project data is intentionally stored outside the installation directory and is not deleted by upgrade or uninstall.
- The test uses an isolated `CARTOON_STUDIO_DATA` directory to avoid contaminating the GitHub runner account.
- The application default data path is `%LOCALAPPDATA%\CartoonStudio`.

## Limitations and release caveat

- No installation was performed on the user's personal PC; this is not required for phase progression.
- No target-PC rendering/performance benchmark was performed; those measurements belong to Phase 8.
- The repository still has no root project `LICENSE`. The artifacts are CI validation outputs, not authorization for public redistribution. The project owner must approve the project license and final dependency notices before a public release.
- Godot is not yet included in the installer; that is P2.1 work.
