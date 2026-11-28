# Hardware Profile and Execution Placement

## Target system
- Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM, SSD, Windows 10 (user-provided project target).

## Architecture implications
- Keep browser control plane lightweight.
- Bound worker concurrency; use sequential jobs where needed.
- Reuse cached assets, geometry and scene data.
- Support low-resolution/low-complexity previews.
- Do not assume CUDA/NVIDIA or modern GPU features.
- Do not require Blender installed to launch the app.
- Blender generation may run on a compatible authoring machine or configured worker if the target laptop is unsuitable.
- Godot production must use the Compatibility renderer where appropriate.
- Hosted CI is for deterministic validation/package tasks, not assumed free GPU rendering.

## Benchmark timing
Physical-PC benchmarks are late-stage optimization work, not a blocker to documentation, architecture, Blender tool development or intermediate functional milestones. Benchmark representative scenes only when meaningful workloads exist. Record Blender version, driver, scene complexity, RAM, time, quality and output hashes.

## Presets
Plan Preview, Low Hardware, Balanced and High Quality presets. Presets may adjust resolution, samples, lighting complexity, texture size and concurrency, but must not silently remove requested features.
