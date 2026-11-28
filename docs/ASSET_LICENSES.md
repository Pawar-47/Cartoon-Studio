# Asset and Software License Register — Policy

## Mandatory record per dependency or asset
Record project/name, exact version or commit, source URL, author, code license, model/weight license, texture/material license, animation/data license, attribution, commercial-use rights, modification/redistribution terms, provenance, checksum and intended distribution.

Never infer model/asset rights from the source code license. Generated outputs need provenance too.

## Blender
Blender is GPL-3.0. Cartoon Studio uses Blender as an external authoring application through its Python API/tooling. Blender is not bundled as a required installed-app runtime. Before redistributing Blender binaries, add-ons or linked GPL components, complete a separate distribution-license review. The user's generated .blend/GLB assets must retain provenance and the licenses of source components.

## MPFB restriction
Do not use MPFB as the product foundation and do not copy MPFB GPL code. Do not silently reintroduce MPFB through another generator or bundled add-on.

## Existing catalogues and dependencies
Existing Quaternius CC0 items, Kenney CC0 catalogue, Godot MIT runtime, Three.js MIT runtime and Python dependencies retain their exact per-item notices and manifests. Verify pinned source hashes before use. Do not broaden one pack's license to another pack.

## Review gate
No new model, add-on, animation, texture, dataset, voice or source project is accepted until exact rights and provenance are recorded. Keep THIRD_PARTY_NOTICES.md and SBOM aligned with actual redistributed files.
