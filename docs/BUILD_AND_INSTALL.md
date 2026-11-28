# Build, Install and Authoring Runtime

## Installed application
The existing Windows application uses FastAPI/browser UI, project data under `%LOCALAPPDATA%\\CartoonStudio` by default, and a bundled Godot 4.7.2 worker where configured. `CARTOON_STUDIO_DATA` overrides the data root. Preserve project data across upgrades and uninstall.

## Blender authoring runtime
Blender is a separate authoring/generation tool, not a prerequisite for launching the installed Cartoon Studio application. The authoring worker must:
- Detect configured/local Blender executable and report version/capabilities.
- Support headless automation and interactive handoff.
- Validate supported Blender version before running a recipe.
- Use isolated project-scoped workspaces and safe paths.
- Save .blend sources and export GLB/glTF, textures and manifests.
- Report unavailable runtime clearly; never pretend an asset was generated.
- Permit a compatible external authoring worker when the user's machine cannot run the required Blender workload.

Do not bundle Blender into the installer by default. Any future bundling requires explicit license/size/runtime review.

## Godot
Godot 4.7.2 remains the production worker. It consumes GLB assets and creates/animates production scenes. Preserve pinned runtime hashes and upstream MIT notices.

## CI and releases
CI validates source, Python/browser syntax, unit/integration tests and bounded Blender/Godot interchange checks. Hosted runners are not assumed to be GPU render farms. Full Windows installers and releases are milestone operations, not every-commit tasks. Keep one CI run at a time.

## Existing artifact evidence
Historical Windows bootstrap/installer and Godot worker evidence remains valid for the exact commits and artifacts recorded in P1 reports; it must not be interpreted as proof of current Blender functionality.
