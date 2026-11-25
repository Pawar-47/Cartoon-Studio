# Third-party software notices

This application bundles or is built using the following third-party software.
The complete dependency inventory for each build is supplied as dependency-sbom.cdx.json.

| Component | Version / scope | License and distribution notes |
|---|---|---|
| Python | CPython 3.11 | Python Software Foundation License; full text in LICENSES/Python-PSF-LICENSE.txt. |
| PyInstaller | 6.22.3 | GPL-2.0-or-later with the PyInstaller Bootloader Exception. The exception permits embedding the compiled bootloader in other programs. Runtime hooks and certain bundled runtime modules are Apache-2.0. Full upstream terms are in LICENSES/PyInstaller-COPYING.txt and LICENSES/Apache-2.0.txt. |
| NSIS | 3.13.0, installer build tool and installer stub | NSIS is primarily under the zlib/libpng license. This installer selects the ZLIB compressor; it does not select the BZIP2 or LZMA compressor modules. Full upstream terms are in LICENSES/NSIS-COPYING.txt. |
| Godot Engine | 4.7.2-stable, Windows x86_64 native worker | MIT; exact upstream LICENSE.txt, COPYRIGHT.txt and AUTHORS.md are retained in third_party/godot-4.7.2 and copied into the installed engine/notices directory. Release archive SHA-256 is pinned in engine/godot_runtime.json; the extracted binary hash is recorded in the CycloneDX SBOM. |
| Python runtime dependencies | Exact versions in dependency-sbom.cdx.json | Package license metadata and dependency provenance are recorded in the CycloneDX SBOM. Consult each upstream package license before modifying or redistributing individual components. |

The NSIS compiler itself is a build-time tool and is not installed as a separate application dependency. The installed program contains the PyInstaller-built Python runtime, application modules and the pinned Godot 4.7.2 native worker runtime.

Cartoon Studio's own distribution license has not yet been selected by the project owner. This installer is a CI validation artifact, not authorization to publish a public software release. Do not create a public release until the project license and any remaining transitive dependency notices have been reviewed and approved.


## Godot Engine 4.7.2-stable (Windows x86_64 native worker)

- Godot Engine contributors; MIT license. The exact standard Windows x86_64 release archive is SHA-256 verified in CI before packaging.
- Runtime binary is installed inside the application's private `_internal/engine/godot.exe` directory and invoked in `--headless` mode. It is not a separate user prerequisite.
- The redistributed runtime includes the exact upstream `LICENSE.txt` and exhaustive `COPYRIGHT.txt` from the `4.7.2-stable` tag under `engine/notices/`. The copyright inventory includes Godot's bundled third-party component notices and license identifiers.
- Source: https://github.com/godotengine/godot/tree/4.7.2-stable
- Release archive: https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_win64.exe.zip
- SHA-256: `731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`


| three.js | 0.187.0 (tag r187, commit 7e89746a687bb88271253698fa108b1dd59825d0), vendored browser GLB preview runtime | MIT; upstream license retained at LICENSES/three.js/LICENSE. The pinned runtime manifest is third_party/threejs-runtime.json and the vendored source modules are under app/static/vendor/three/. Included in the CycloneDX SBOM. |
