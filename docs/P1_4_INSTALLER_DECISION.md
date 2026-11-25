# P1.4 — Windows installer technology decision

**Date:** 2026-11-25  
**Scope:** Self-contained Windows installation, upgrade, uninstall and project-data preservation.

## Requirements

- The user must not need to install Python or Node.js.
- The application runs locally and binds only to 127.0.0.1.
- Program files live under the per-user Programs directory.
- Project data remains under %LOCALAPPDATA%\CartoonStudio (or the explicit CARTOON_STUDIO_DATA override), outside the install directory.
- Upgrade replaces program files without deleting user projects.
- Uninstall removes program files and shortcuts but deliberately preserves project data.
- Installer build and clean install/upgrade/uninstall tests run on a Windows GitHub Actions runner; target-PC performance remains Phase 8.

## Candidate comparison

| Candidate | Evidence | Fit and trade-offs |
|---|---|---|
| PyInstaller 6.22.3 + NSIS 3.13.0 | PyInstaller source/docs describe bundling the active Python interpreter and dependencies into an onedir or onefile application; Windows is a supported build platform. PyInstaller COPYING specifies GPL-2.0-or-later with the Bootloader Exception and Apache-2.0 runtime hooks. NSIS source/docs provide scriptable per-user install/uninstall and zlib compression. | Selected. It freezes the existing FastAPI/Uvicorn entrypoint without requiring a GUI framework migration. NSIS supplies the install/upgrade/uninstall shell. Use onedir inside a single NSIS installer for easier diagnostics and replacement. |
| BeeWare Briefcase | https://github.com/beeware/briefcase; BSD-3-Clause; active cross-platform native packaging project with a Windows Visual Studio backend. | Not selected for this batch. Its Windows workflow is centered on native Windows packaging/Visual Studio project generation; adapting the existing browser-served FastAPI app would introduce more packaging and platform-template work than freezing its current Python entrypoint. Reconsider if a native window or MSIX distribution becomes a requirement. |

## Selected implementation

1. Build a small windowed desktop entrypoint that starts the existing FastAPI app on loopback and opens the browser.
2. Freeze it with PyInstaller in onedir mode. Include app/static, the Python license, third-party notices and the dependency SBOM.
3. Build a per-user NSIS installer using the ZLIB compressor. Avoid NSIS BZIP2/LZMA options in this product installer so their separate license modules are not selected.
4. Install under %LOCALAPPDATA%\Programs\Cartoon Studio; create Start Menu and desktop shortcuts.
5. Keep user data separate under %LOCALAPPDATA%\CartoonStudio. The uninstaller must not delete that path.
6. Validate two app builds (0.1.0 and 0.1.1): install v1, create a project, upgrade to v2, confirm the project survives, uninstall, confirm data remains, reinstall and confirm it is still readable.

## Licensing and release boundary

- Preserve the upstream license texts under LICENSES/.
- Include the generated CycloneDX SBOM and THIRD_PARTY_NOTICES.md with the installed application.
- The repository currently has no root project LICENSE. Building a CI test artifact does not choose a license for Cartoon Studio. Do not publish a public release until the owner approves the project's own license and the final transitive-license review is complete.

## Sources inspected

- PyInstaller repository: https://github.com/pyinstaller/pyinstaller
- PyInstaller v6.22.3 README and usage documentation: https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/README.rst and https://pyinstaller.org/en/v6.22.3/usage.html
- PyInstaller licensing: https://github.com/pyinstaller/pyinstaller/blob/v6.22.3/COPYING.txt
- NSIS source mirror: https://github.com/nsis-dev/nsis
- NSIS license: https://github.com/nsis-dev/nsis/blob/master/COPYING
- NSIS SetCompressor command: https://github.com/nsis-dev/Documentation/blob/main/docs/Commands/SetCompressor.md
- NSIS install/uninstall commands: https://github.com/nsis-dev/Documentation
- BeeWare Briefcase: https://github.com/beeware/briefcase
