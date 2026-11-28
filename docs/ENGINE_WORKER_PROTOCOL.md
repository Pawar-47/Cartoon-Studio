# Blender and Godot Worker Protocols

## Blender authoring worker
The Blender worker is responsible for authoring/generation, not final episode production. It must support headless batch and interactive authoring modes and expose capability/version metadata.

Request envelope: protocol_version, request_id, operation, project_id, asset_id, recipe_version, payload, output_policy.
Response envelope: protocol_version, request_id, ok, worker_version, operation, outputs, manifest, diagnostics, error_code/error.
Long operations use durable job IDs and progress events through the backend job system; cancellation is cooperative and outputs are published atomically.

Security: argument arrays only; no shell interpolation; project-root containment; bounded input sizes/timeouts; isolated temp dirs; no network listener; redact secrets; preserve previous accepted outputs on failure.

Supported operation families should grow from shared primitives: create scene, build geometry, assign materials, rig/skin, generate domain asset, save .blend, export GLB, validate, thumbnail and package manifest. Do not advertise an operation until implemented and tested.

## Godot production worker
Godot 4.7.2 consumes approved GLB and canonical scene data. It assembles scenes, plays/retargets animation, controls cameras/timeline, previews and renders. It returns structured capability, import, scene and render results.

## Interchange contract
Blender output manifest identifies .blend source, GLB export, textures, stable asset ID/version, generator version, recipe, hashes, rig/morph/animation capabilities, dependencies and license provenance. Godot validates required data on import and reports unsupported features.

## Legacy protocol
Earlier Godot-only GLB inspection request/response protocol remains a compatibility contract for existing APIs. Extend it additively; do not break imported-character projects.
