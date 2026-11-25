# Godot target-PC probe

This is a **Phase 0.4 diagnostic only**, not a Cartoon Studio feature and not an engine-selection decision. It creates a small procedural low-poly town, uses the Godot Compatibility renderer, toon-shaded materials and a directional shadow, then records renderer, GPU driver, frame-time and memory information.

## Requirements

- Windows 10/11 x64.
- PowerShell 5.1 (built into Windows 10).
- Godot **4.7.2 stable Standard Windows x86_64** editor executable. Do not download the .NET build.
- No administrator rights, Python packages, model weights, network connection or API keys are required.

Official download: https://godotengine.org/download/archive/4.7.2-stable/

Extract the downloaded ZIP. Do not install it; point the script to the extracted `Godot_v4.7.2-stable_win64.exe`.

## Run

Open PowerShell in the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\run_target_pc_probe.ps1 -GodotExe "C:\Tools\Godot\Godot_v4.7.2-stable_win64.exe"
```

This collects the Windows/CPU/RAM/GPU/driver/disk profile and runs a 12-second interactive 1280×720 Compatibility-renderer test.

To also render a 10-second 720p / 24 FPS AVI:

```powershell
.\scripts\run_target_pc_probe.ps1 -GodotExe "C:\Tools\Godot\Godot_v4.7.2-stable_win64.exe" -RunMovie
```

Close other heavy applications and connect the laptop to power before running. Do not change drivers or Windows settings just for this test.

## Output

The script creates a timestamped `target_pc_probe_*` folder containing:

- `system_profile.json` — Windows build, CPU, RAM, GPU model/driver, display and fixed-disk capacity.
- `godot_interactive_report.json` — renderer/API, GPU driver info, viewport, average/p95 frame times, memory and draw-call counters.
- `run_summary.json` and `godot_interactive.log`.
- With `-RunMovie`: `godot_movie_report.json`, `godot_movie.log` and `godot_probe_720p_24fps.avi`.

Please share `system_profile.json`, `godot_interactive_report.json` and `run_summary.json`. If you ran the movie test, also share `godot_movie_report.json`; the AVI is useful for visual inspection.

The script does not upload anything. It deliberately excludes usernames, computer names, serial numbers, MAC/IP addresses and product keys. The result is a baseline diagnostic, not proof that a full 5–7 minute episode will render at real-time speed.
