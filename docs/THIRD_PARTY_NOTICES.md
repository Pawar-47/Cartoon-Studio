# Third-party software notices

This application bundles or is built using the following third-party software.
The complete dependency inventory for each build is supplied as dependency-sbom.cdx.json.

| Component | Version / scope | License and distribution notes |
|---|---|---|
| Python | CPython 3.11 | Python Software Foundation License; full text in LICENSES/Python-PSF-LICENSE.txt. |
| PyInstaller | 6.22.3 | GPL-2.0-or-later with the PyInstaller Bootloader Exception. The exception permits embedding the compiled bootloader in other programs. Runtime hooks and certain bundled runtime modules are Apache-2.0. Full upstream terms are in LICENSES/PyInstaller-COPYING.txt and LICENSES/Apache-2.0.txt. |
| NSIS | 3.13.0, installer build tool and installer stub | NSIS is primarily under the zlib/libpng license. This installer selects the ZLIB compressor; it does not select the BZIP2 or LZMA compressor modules. Full upstream terms are in LICENSES/NSIS-COPYING.txt. |
| Python runtime dependencies | Exact versions in dependency-sbom.cdx.json | Package license metadata and dependency provenance are recorded in the CycloneDX SBOM. Consult each upstream package license before modifying or redistributing individual components. |

The NSIS compiler itself is a build-time tool and is not installed as a separate application dependency. The installed program contains the PyInstaller-built Python runtime and application modules.

Cartoon Studio's own distribution license has not yet been selected by the project owner. This installer is a CI validation artifact, not authorization to publish a public software release. Do not create a public release until the project license and any remaining transitive dependency notices have been reviewed and approved.
