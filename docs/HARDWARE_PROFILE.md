# Target Hardware Profile
- CPU: Intel Core i3-5005U
- GPU: Intel HD Graphics 5500
- RAM: 8 GB
- Storage: SSD
- OS: Windows

No dedicated NVIDIA GPU is assumed. Large local LLM/TTS models must not be mandatory. Keep the UI lightweight, use sequential rendering and bounded concurrency, reuse cached assets, and benchmark Blender compatibility and CPU render times. Do not promise episode render times before measurement.

Required benchmarks: app idle RAM/startup; dashboard latency; small GLB viewport load/frame rate; character rig import time/memory; 5–10 second low-poly render time; TTS inference memory/time; scene-cache hit/miss; full sample episode render time. Record OS, Blender version, render engine, resolution, samples, scene complexity, CPU/RAM, elapsed time and quality.

## 2026-11-25 compatibility findings
- Intel's official i3-5005U page confirms 2 cores / 4 threads, 2.00 GHz, SSE4.2, AVX2, Broadwell, Intel HD Graphics 5500 and OpenGL 4.3: https://www.intel.com/content/www/us/en/products/sku/84695/intel-core-i35005u-processor-3m-cache-2-00-ghz/specifications.html
- Blender 4.5 LTS is the relevant Blender branch: Windows support includes Intel Broadwell. Blender 5.0+ raises the supported Intel GPU floor to Kaby Lake, so HD 5500 is below that official floor.
- Blender's published minimum is 4 CPU cores with SSE4.2 and 8 GB RAM. This target has only 2 physical cores and exactly 8 GB. It is below the CPU minimum and at the RAM minimum; do not promise full-episode rendering performance.
- Blender 4.5's Windows Intel troubleshooting page warns that some newer Intel drivers crash on 3rd–5th generation iGPUs. Known-working versions listed: 20.19.15.4835, .4963, .5063. Known-failing versions listed: .5126, .5144, .5166, .5171. The target PC's installed driver is unknown.
- Intel lists HD 5500 OpenGL 4.3 support, but this does not remove the Blender driver caveat or imply good viewport/render performance.
- Blender 4.5.17 LTS was listed on 2026-11-24 and is supported until July 2027. Candidate version only; no target-PC test has been run.

## Required compatibility gate before selecting Blender
Record exact Windows build, driver version, Blender 4.5.17 startup result, viewport stability, headless background operation, CPU render time, peak RAM, scene vertex/object counts and crash logs. Test a minimal toon character scene and a generated town. If it fails or is unusable, evaluate a lighter browser-first/WebGL production route before architecture freeze.

## Performance policy
Use sequential scene generation/rendering, strict object/vertex budgets, low-density procedural presets, low-resolution previews, cached assets and bounded worker concurrency. Do not assume CPU/GPU parallel rendering. The 5–7 minute episode target is a product requirement, not a render-time promise; measure first.

## Godot 4.7.2 compatibility findings

- Godot 4.7.2 stable is the pinned runtime candidate; 4.8 is beta in the current release stream.
- Godot Compatibility renderer requires OpenGL 3.3. Intel HD 5500 reports OpenGL 4.3, so it meets the API floor on paper. Use Compatibility renderer, not Forward+, until Vulkan/driver support is proven.
- Godot's minimum CPU is x86_64 with SSE4.2 and minimum RAM 4 GB; recommended is 4 cores and 8 GB. The i3-5005U meets minimum instruction-set and RAM requirements, but 2 physical cores are below recommended CPU.
- Compatibility renderer has reduced advanced lighting/post-processing features. Use low light counts, baked lighting and toon shaders; inspect shadows and color bands carefully.
- Godot's MovieWriter can record non-real-time with fixed frame pacing; built-in output is OGV, AVI or PNG sequence plus WAV. FFmpeg is needed for MP4. It can render slower than real time without losing frame pacing, but the 5–7 minute episode render time is unknown.
- No Godot 4.7.2 target-PC startup, preview, render or memory benchmark has been run.

## Revised engine shortlist
1. Godot 4.7.2 Compatibility — leading on-paper runtime candidate for i3-5005U / HD 5500 / 8 GB.
2. Blender 4.5.17 LTS — optional asset authoring candidate; below CPU minimum and has legacy Intel driver crash warnings.
3. Browser WebGL2 editor/preview (Ara/Ekza/Three.js) — alternative preview/editor candidate; must measure browser memory and GPU stability.

The actual installed Intel driver and Windows build must be recorded before selecting the engine.
