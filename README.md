# Cartoon Studio

An original, local-first Urdu 3D cartoon production studio. This repository is the source of truth for development, Windows builds and releases.

## Current working foundation

- Local FastAPI application served in the browser.
- SQLite-backed project index with numbered migrations, backup-before-migrate and a portable versioned project.json per project.
- Project open/update and story-plan save/reload using portable episode JSON documents; SQLite remains the local index and compatibility store.
- Story Generator prompt builder for use with FreeMilk by Milq and other AI applications.
- Copyable structured story prompt and JSON Schema.
- Validation of 5–7 minute episode plans, 5–7 scenes, character references and timed production cues.
- Save and reload validated episode plans inside a local project.
- Character Studio: import and inspect GLB 2.0 models, preview saved models in an interactive local 3D viewer, edit saved character profiles, customize and persist material colour/roughness/metalness recipes and existing facial morph targets, check mesh/skeleton/animation readiness, and save versioned reusable character profiles to a project.
- World Builder: persistent project worlds with stable IDs, versioned schema migration, reusable templates and a Godot-authored 3D scene with a browser preview.
- Episode workshop: validate and save a 5–7 minute Urdu episode plan, generate editable Godot scenes from saved worlds and project characters, generate Urdu dialogue audio with timed SRT subtitles (or record a line by hand), and render the episode MP4 from the project's quality preset (Preview, Low Hardware, Balanced or High Quality).
- Episode Renderer and Logs and Diagnostics workspaces: queue a render and watch per-scene progress, cancel safely, read a job's event journal, and check Godot/FFmpeg/voice readiness.
- Project export/import as a portable ZIP package; a durable SQLite job record for long operations, executed by a background worker with per-scene progress, cancellation and a dependency diagnostics endpoint.
- GitHub Actions Windows CI installs exact uv-locked dependencies, runs lint/compile/tests and packages a hash-locked bootstrap ZIP.

**Known limitations:** the installed app can now assemble an MP4 with the bundled LGPL FFmpeg and a redistribution-safe encoder; the Story page queues its render through the background worker, has a recorded-line panel (mono 16-bit 22,050 Hz WAV) and a subtitle-mode selector. Urdu speech synthesis still needs `piper-tts`, which is not yet in the locked environment; recorded lines are the working dialogue path until the lock is regenerated. See the blocking finding in [`docs/MASTER_BRIEF_AUDIT_2026-11-28.md`](docs/MASTER_BRIEF_AUDIT_2026-11-28.md).

Godot 4.7.2 Compatibility is integrated as a pinned, bundled native worker behind a supervised Python adapter. P2.1 passed Windows CI #204. The first P2.2 Character Studio vertical slice also passed Windows CI #208 (45 pytest tests): project-scoped GLB 2.0 import/inspection, rig-readiness reporting, versioned character profiles, project references and recovery. The Character Studio phase is still active; rig authoring, texture painting, new blend-shape authoring, export and animation authoring remain future work.

## Run on Windows

1. Install Python 3.11 or newer.
2. Download/extract the latest Windows bootstrap artifact from the GitHub Actions page.
3. Keep requirements.lock beside start.bat.
4. Run start.bat; dependencies are installed with pip hash verification.
5. The local app opens at http://127.0.0.1:8765.
6. Open Character Studio to import a GLB 2.0 character model, inspect its geometry/rig/animation readiness and save a reusable profile.
7. Open Story Generator to prepare a prompt, paste an AI-generated JSON plan, validate it and save it to a project.

The Windows bootstrap ZIP is Python-dependent. A self-contained Windows installer is also built and uploaded as a GitHub Actions artifact. Project data defaults to the user's application-data directory; on Windows this is `%LOCALAPPDATA%\\CartoonStudio`. Set `CARTOON_STUDIO_DATA` to override it.

## Development principles

- Read and trace the complete project specification before implementation.
- Search public GitHub and evaluate existing projects before building components.
- Preserve software, model and asset licenses and provenance.
- Use GitHub Actions for repeatable validation and Windows packaging.
- Render actual episodes locally; hosted Actions runners are not treated as a free GPU render farm.
- Keep Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM and SSD as design constraints; physical-PC benchmarking is Phase 8, not a development gate.
- Never claim untested features are complete.

## Documentation

Every coding agent must follow AGENTS.md and read docs/PROJECT_SPECIFICATION.md in full before changing code. The execution plan, requirement registry, traceability, research, tests and status are maintained under docs/.
