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
- GitHub Actions Windows CI for lint, compile, tests and bootstrap ZIP packaging.

Godot 4.7.2 Compatibility has passed a bounded hosted-runner proof and is selected as the native 3D runtime behind a supervised worker adapter. The production engine integration is still pending. This repository does not yet claim complete 3D cartoon generation, Urdu TTS, lip-sync or final episode rendering.

## Run on Windows

1. Install Python 3.11 or newer.
2. Download/extract the latest Windows bootstrap artifact from [GitHub Actions](https://github.com/Pawar-47/Cartoon-Studio/actions).
3. Run start.bat.
4. The local app opens at http://127.0.0.1:8765.
5. Open Story Generator from the dashboard to prepare a prompt, paste an AI-generated JSON plan, validate it and save it to a project.

The bootstrap ZIP is not yet a standalone installer. Project data defaults to the user's application-data directory (Windows: %LOCALAPPDATA%\\CartoonStudio); set CARTOON_STUDIO_DATA to override it. The self-contained Windows installer is Phase 1.4 work.

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
