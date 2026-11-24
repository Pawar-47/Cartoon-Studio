# Target Hardware Profile
- CPU: Intel Core i3-5005U
- GPU: Intel HD Graphics 5500
- RAM: 8 GB
- Storage: SSD
- OS: Windows

No dedicated NVIDIA GPU is assumed. Large local LLM/TTS models must not be mandatory. Keep the UI lightweight, use sequential rendering and bounded concurrency, reuse cached assets, and benchmark Blender compatibility and CPU render times. Do not promise episode render times before measurement.

Required benchmarks: app idle RAM/startup; dashboard latency; small GLB viewport load/frame rate; character rig import time/memory; 5–10 second low-poly render time; TTS inference memory/time; scene-cache hit/miss; full sample episode render time. Record OS, Blender version, render engine, resolution, samples, scene complexity, CPU/RAM, elapsed time and quality.
