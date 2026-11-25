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
- Character Studio: import and inspect GLB 2.0 models, preview saved models in an interactive local 3D viewer, customize and persist material colour/roughness/metalness recipes and existing facial morph targets, check mesh/skeleton/animation readiness, and save versioned reusable character profiles to a project.
- GitHub Actions Windows CI installs exact uv-locked dependencies, runs lint/compile/tests and packages a hash-locked bootstrap ZIP.

Godot 4.7.2 Compatibility is integrated as a pinned, bundled native worker behind a supervised Python adapter. P2.1 passed Windows CI #204. The first P2.2 Character Studio vertical slice also passed Windows CI #208 (45 pytest tests): project-scoped GLB 2.0 import/inspection, rig-readiness reporting, versioned character profiles, project references and recovery. The Character Studio phase is still active; mesh/rig authoring, texture painting, new blend-shape authoring, export and animation authoring remain future work.

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
