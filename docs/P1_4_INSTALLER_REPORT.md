# P1.4 — Self-contained Windows Installer and Lifecycle Verification

**Date:** 2026-11-25  
**Repository:** Pawar-47/Cartoon-Studio  
**Branch:** main  
**Verified implementation commit:** `24f1617cff4d592e981908c7ceea641225c05ac0`  
**Windows CI:** [Run #175 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585234644)

## Delivered

- PyInstaller onedir bundles for Cartoon Studio 0.1.0 and 0.1.1.
- NSIS 3.13.0 per-user installers; the installed app does not require a separately installed Python runtime.
- Default program directory: `%LOCALAPPDATA%\\Programs\\Cartoon Studio`.
- Start Menu and desktop shortcuts, per-user install metadata and an uninstaller.
- User data remains separate under `%LOCALAPPDATA%\\CartoonStudio`, with `CARTOON_STUDIO_DATA` available for explicit override.
- Upgrade replaces only known application-owned files and does not invoke the previous uninstaller during the new install.
- Uninstaller restores the real install directory from the per-user registry before deleting program files. User project data is intentionally outside the install directory.

## Windows CI acceptance evidence

The smoke test uses the actual versioned installers on a clean Windows runner:

1. Install version 0.1.0 silently.
2. Launch the installed executable and wait for the real health endpoint.
3. Create a project and verify its portable project document exists.
4. Install version 0.1.1 over version 0.1.0.
5. Launch version 0.1.1 and verify the project created before upgrade remains available.
6. Uninstall and verify program files, install directory, Start Menu shortcut, desktop shortcut and per-user registry keys are removed.
7. Verify the project document remains intact.
8. Reinstall version 0.1.1, launch it and verify the same project remains readable.
9. Uninstall again and verify project data still exists.

**CI #175 passed every step**, including lint, Python compilation, the 22-test application suite, bootstrap extraction/launcher smoke, both PyInstaller builds, NSIS compilation, installer lifecycle and artifact uploads.

## Uploaded artifacts from run #175

| Artifact | Size | Artifact ID |
|---|---:|---:|
| Cartoon-Studio-Windows-Installer | 17,543,577 bytes | 15009070345 |
| Cartoon-Studio-Windows-Bootstrap | 259,634 bytes | 15008472421 |
| Cartoon-Studio-Dependency-SBOM | 31,634 bytes | 15008008481 |

Download the installer from the [run #175 Actions artifacts](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585234644).

## Boundaries

- The installer lifecycle is verified on GitHub's clean Windows runner; no installation on the user's personal PC was required.
- Actual target-PC frame-time, memory and rendering benchmarks remain Phase 8 and do not block Phase 2.
- No code signing, automatic update service, production 3D character creation, Urdu TTS, lip-sync or final episode rendering is claimed complete.
- The bootstrap ZIP remains available as a separate Python-dependent development/portable route.
