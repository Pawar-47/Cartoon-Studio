# Third-Party Software and Asset Notices

This file is a policy index, not a substitute for the exact license text and per-build SBOM. Every redistributed dependency and asset must have its own recorded version, license and provenance.

## Runtime/toolchain components
- Godot Engine 4.7.2: MIT; retain exact upstream LICENSE/COPYRIGHT/AUTHORS notices and pinned hashes when bundled.
- three.js: MIT; retain vendored upstream license and version/hash.
- Python and locked runtime dependencies: preserve package license metadata and CycloneDX SBOM.
- Blender: GPL-3.0; used as a separate authoring application/toolchain. It is not bundled as a required runtime dependency. Any future redistribution/bundling requires explicit license review.
- FFmpeg: build/configuration-specific license obligations; record exact configure flags and enabled codecs before redistribution.
- NSIS/PyInstaller: preserve upstream notices and applicable exceptions for the exact build versions.

## Asset libraries
Quaternius and Kenney assets are used only under the license of the exact selected pack/file. Retain source URL, pack/version, license text, attribution if required and checksum. Model, texture, animation and dataset terms may differ from code licenses.

## MPFB
MPFB is not the product foundation. Do not copy or bundle MPFB GPL code.

## Release gate
Do not publish a release until Cartoon Studio's own distribution license, all bundled dependency notices, Blender/FFmpeg distribution posture and every included asset's rights have been reviewed.
