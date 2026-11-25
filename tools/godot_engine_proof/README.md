# Cartoon Studio — Godot native-worker proof (P0.6)

This is a bounded architecture proof, not production application code and not a target-PC benchmark.

## What it verifies

1. Godot 4.7.2 Compatibility renderer launches in a controlled CI environment.
2. A self-generated GLB fixture is imported and exposes a MeshInstance3D.
3. A runtime AnimationPlayer/AnimationLibrary creates and plays a keyed transform animation.
4. The combined scene is serialized to a PackedScene, reopened, and checked for the imported model, animated proxy and AnimationPlayer.
5. Godot's MovieWriter produces a short 24 FPS AVI in the CI virtual display; FFprobe inspects the resulting media.

No user data, API key, cloud provider or third-party asset is used. The GLB is a tiny self-generated geometry fixture. The proof does not measure the user's PC, approve Godot for production, or prove a complete 5–7 minute render.

## Reproduce locally

Use the official Godot 4.7.2 stable Standard build and FFmpeg. On Linux, run the project under Xvfb with Mesa software OpenGL:

```sh
godot --headless --path tools/godot_engine_proof --editor --import --quit
mkdir -p tools/godot_engine_proof/artifacts
xvfb-run -a env LIBGL_ALWAYS_SOFTWARE=1 godot --path tools/godot_engine_proof --write-movie artifacts/proof.avi --fixed-fps 24 -- --report=res://artifacts/report.json
ffprobe -v error -show_entries format=duration -of json tools/godot_engine_proof/artifacts/proof.avi
ffmpeg -i tools/godot_engine_proof/artifacts/proof.avi -c:v mpeg4 -q:v 5 -c:a aac -b:a 96k tools/godot_engine_proof/artifacts/proof.mp4
ffprobe -v error -show_entries format=duration -of json tools/godot_engine_proof/artifacts/proof.mp4
```

The GitHub Actions workflow pins Godot to 4.7.2 stable and uploads the JSON report, engine log and AVI for inspection. The CI job also performs a temporary MP4 assembly using FFmpeg's built-in MPEG-4 Part 2/AAC encoders. This is a format-pipeline proof only, not approval of the final distribution codec or FFmpeg build. A passing CI proof demonstrates the engine boundary on the hosted runner only; target-PC performance remains Phase 8.


## Humanoid retargeting proof

The proof scene also builds a canonical humanoid source/target skeleton pair with different limb lengths. A Godot 4.7.2 `RetargetModifier3D` uses `SkeletonProfileHumanoid` to transfer an animated left-upper-arm pose from the source to the target. The JSON report checks modifier creation, source animation playback, different rest lengths, transferred target rotation and scene save/reopen of the retarget pair. This is a native engine API proof with generated skeletons, not yet retarget acceptance for arbitrary imported cartoon GLBs or production animation clips.
