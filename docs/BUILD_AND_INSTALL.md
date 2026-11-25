# Build and Install

## Local data and migration behavior

- Windows default data root: `%LOCALAPPDATA%\CartoonStudio`.
- Override: set `CARTOON_STUDIO_DATA` to a custom writable directory before launching the app.
- SQLite index: `cartoon_studio.sqlite3`; numbered `schema_migrations` records database migrations.
- Existing databases are backed up under `backups/` before schema upgrades.
- Each project has a portable `projects/<project-id>/project.json` document; saved episode plans are stored under `projects/<project-id>/episodes/<episode-id>.json`.
- User data is separate from program files. Upgrades and uninstall must preserve project data.

## Windows artifacts

Latest successful workflow: [Windows CI run #176](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585584886).

| Artifact | Purpose | Availability |
|---|---|---|
| `Cartoon-Studio-Windows-Installer` | Self-contained per-user Windows installer; Python runtime bundled | CI artifact, 30-day retention |
| `Cartoon-Studio-Windows-Bootstrap` | Portable source/runtime bootstrap ZIP; requires Python 3.11 | CI artifact, 14-day retention |
| `Cartoon-Studio-Dependency-SBOM` | CycloneDX dependency inventory | CI artifact, 30-day retention |

The installer is built with PyInstaller one-folder and NSIS 3.13.0. It installs under `%LOCALAPPDATA%\Programs\Cartoon Studio`, creates Start Menu and desktop shortcuts, and does not require a separately installed Python or Node.js runtime. The application stores project data separately under the per-user data directory.

## Installer validation

Windows CI #176 verifies:

1. Clean per-user installation of version 0.1.0.
2. First launch and health/API response.
3. Project creation and save.
4. Upgrade to version 0.1.1 without deleting the project.
5. Uninstall removes program files and shortcuts while preserving project data.
6. Reinstall of version 0.1.1 and recovery of the same project.
7. Final uninstall again preserves user project data.

The NSIS uninstaller runs a temporary copy; the application directory is restored from the per-user registry before file cleanup. The test waits for the temporary uninstaller to finish before inspecting the result.

Detailed evidence: `docs/P1_4_INSTALLER_REPORT.md`.

## Portable bootstrap

The bootstrap ZIP includes `start.bat`, application source, docs and hash-locked runtime requirements. It requires Python 3.11 through the Windows Python launcher. CI extracts it into a clean temporary directory, executes the actual launcher, checks dashboard/static/API, creates/opens a project, restarts the application and verifies persistence.

## CI pipeline

`.github/workflows/ci.yml` verifies `uv.lock`, installs the exact locked environment, runs Ruff, Python compile checks and pytest, exports and drift-checks `requirements.lock`, generates a CycloneDX SBOM, packages the bootstrap, builds both self-contained application versions, compiles the NSIS installers, exercises the complete installer lifecycle and uploads all artifacts.

## Release and licensing caveat

The project has no root `LICENSE` file yet. CI artifacts validate the build and installer; they are not authorization for a public software release. The project owner must approve the project's own distribution license and any remaining bundled dependency notices before public redistribution.

## Next integration milestone

Phase 2 P2.1 adds the pinned Godot 4.7.2 Windows runtime as a bundled native worker behind the FastAPI/browser control plane. The Godot executable must be SHA-256 verified and its MIT license/copyright notice included. The worker must not require a separate user installation.


## P2.1 Godot runtime packaging

The self-contained installer now includes the pinned Godot 4.7.2-stable Windows x86_64 runtime under `_internal/engine/`, the worker project and upstream MIT/COPYRIGHT notices. CI verifies the official archive SHA-256 before extraction and records Godot as a CycloneDX component. The browser/FastAPI app remains the control plane; the native worker runs headlessly and is not a separate user prerequisite. The bootstrap ZIP remains Python-dependent and does not bundle the 86 MB compressed Godot runtime.
