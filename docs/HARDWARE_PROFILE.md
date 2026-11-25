# Target Hardware Profile and Deferred Benchmark Plan

## User-provided baseline
- CPU: Intel Core i3-5005U (2 cores / 4 threads, 2.00 GHz, Broadwell, SSE4.2, AVX2)
- GPU: Intel HD Graphics 5500
- RAM: 8 GB
- Storage: SSD (previously stated as 256 GB)
- OS: Windows 10

## Policy: design now, benchmark in Phase 8
This profile informs architecture and implementation choices immediately. A physical run on the user's PC is not required to close Phase 0, select architecture, begin implementation or pass intermediate phase gates. The optional diagnostic harness remains available at `scripts/run_target_pc_probe.ps1` and `tools/godot_target_probe/`.

Actual representative-scene measurements, quality-preset tuning and optimization are scheduled for Phase 8 / P8.1. If the complete application is slow on this machine, reduce preview quality, resolution, concurrency and render throughput while preserving features; do not silently remove functionality. Keep Preview, Low Hardware, Balanced and High Quality modes.

## Source-based compatibility evidence (not a benchmark)
- Intel's official i3-5005U page confirms 2 cores / 4 threads, 2.00 GHz, SSE4.2, AVX2, Broadwell, Intel HD Graphics 5500 and OpenGL 4.3: https://www.intel.com/content/www/us/en/products/sku/84695/intel-core-i35005u-processor-3m-cache-2-00-ghz/specifications.html
- Godot 4.7.2 Compatibility renderer requires OpenGL 3.3; HD 5500 reports OpenGL 4.3, so the API floor matches on paper. This does not establish driver stability, FPS or render throughput.
- Godot's documented CPU floor is x86_64/SSE4.2 and 4 GB RAM; the target meets instruction-set and memory floors but has 2 physical CPU cores versus 4 recommended.
- Blender 4.5 LTS supports Broadwell in its Windows build, but its published minimum is 4 CPU cores and 8 GB RAM. The target is below the CPU minimum and at the RAM minimum.
- Blender's Windows Intel troubleshooting page records driver-specific crash caveats on older Intel iGPUs. The installed driver version is unknown.
- Blender 5.0+ raises the supported Intel GPU floor; do not assume HD 5500 compatibility with that branch.
- Godot Compatibility renderer has fewer advanced lighting/post-processing features than Forward+; use scalable lighting, baked options and efficient toon shading where appropriate.

## Candidate implications
1. Godot 4.7.2 Compatibility — leading source-based runtime candidate; still requires architecture-critical proof and integration validation. Physical-PC performance is deferred to Phase 8.
2. Blender 4.5.17 LTS — optional authoring/import pipeline candidate; not assumed as mandatory runtime.
3. Browser WebGL2 — useful lightweight UI/preview option; memory and GPU limits remain design risks.

## Phase 8 / P8.1 benchmark protocol
When the complete workflow and representative scenes exist, record app idle RAM/startup, dashboard latency, GLB viewport load/frame pacing, character rig import time/memory, representative low-poly render time, scene-cache hit/miss, recovery behavior, approved TTS/alignment memory/runtime and full sample-episode render time/output quality/disk footprint. Capture OS build, GPU driver, engine/version, renderer, resolution, scene complexity, object/vertex counts, quality preset, CPU/RAM use, elapsed time, output artifact and limitations. Benchmark before estimating production time. This is a Phase 8 optimization/acceptance task, not an upstream development gate.

## Optional diagnostic harness
The no-admin diagnostic records OS/CPU/RAM/GPU/driver/display/disk information and runs a bounded Godot Compatibility scene; optional AVI export is diagnostic only. No output is claimed until an actual run is performed.
