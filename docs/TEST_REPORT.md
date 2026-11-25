# Test Report — 2026-11-25

## Current repository checkpoint
- Latest verified Windows CI: [run #176 — SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45585584886), commit 815cc32a1cb56c3357c37310745e900a8a197c7f.
- Run #176 passed exact dependency locking, Ruff, compilation, 22 pytest tests, bootstrap launcher smoke, self-contained PyInstaller builds, NSIS installer compilation, clean install, launch, upgrade, project-data preservation, uninstall, reinstall and artifact upload.
- Artifacts: installer 15008168874, bootstrap 15007954336, SBOM 15008014096.
- The self-contained installer no longer requires a user-installed Python/Node runtime. The separate bootstrap ZIP still requires Python 3.11.

## P0.5 architecture and dependency documentation
- Registry and traceability were parsed from live GitHub: 171 unique requirement IDs in each; exact ID-set equality; no missing or extra IDs.
- Added a 171-row architecture crosswalk. Planned module paths are ownership targets, not implemented-code claims.
- Reviewed current source: FastAPI/Uvicorn/Pydantic/stdlib SQLite, static HTML/CSS/JS, project metadata and saved story plan. No renderer, durable queue, asset registry, migration framework, provider registry or installer is implemented.
- Reviewed current requirements: range constraints only; no fully resolved runtime lock file.
- Confirmed no root LICENSE file in the current repository tree. Copyleft adoption/bundling remains excluded until the project distribution-license decision is made.
- P0.5 is documentation-complete; P0.6 proofs have not yet run.

## Target-PC benchmark policy
- scripts/run_target_pc_probe.ps1 and tools/godot_target_probe/ remain optional diagnostics.
- No PowerShell execution or Godot renderer launch on the user's PC has occurred.
- No actual FPS, frame-time, memory, driver, AVI or full episode render measurement exists.
- This is not a gate for P0.5/P0.6/P0.7 or Phases 1–7. Representative performance and quality-preset tuning are Phase 8.

## P1.1 project lifecycle and portable storage — 2026-11-25
- Implemented app/storage.py with per-user data directory, CARTOON_STUDIO_DATA override, connection PRAGMAs, numbered schema migrations (v1 legacy tables, v2 portable document index), and online SQLite backup before legacy upgrades.
- Added atomic JSON writes, SHA-256 document indexing, safe project-relative path resolution and startup reconciliation.
- Added project open/update APIs; project creation writes a versioned project.json. Story plans write versioned episode JSON under each project while retaining the legacy story_plans row for compatibility.
- Startup recovery rebuilds missing project/episode files from legacy SQLite rows and restores SQLite story_plans/index rows from portable episode files.
- CI run #115 on 565d211ce3009c081e60d48778d3ba89acd4a4f7: Ruff passed, compile passed, 21 pytest tests passed, Windows bootstrap ZIP packaged/uploaded. One Starlette TestClient/httpx deprecation warning remains; it is a P1.2 dependency/test-client follow-up, not a functional failure.
- Current artifact remains a bootstrap ZIP, not a self-contained installer.

## P0.4 Urdu/provider research
- Source-level inspection only: eSpeak NG Urdu rules/CLI, WhisperX Urdu alignment model, Qwen Urdu voice/regions/pricing, and official provider free-tier/region docs.
- No Pakistani Urdu audio sample was processed. No voice quality, WER, forced-alignment accuracy or phoneme timing has been tested.
- No API key/account has been connected and no content has been sent to an external provider.
- See docs/URDU_VOICE_FEASIBILITY.md for a repeatable acceptance protocol.

## Existing proof limitations
- Ara proof run #6 was cancelled during browser MP4 export. No successful production MP4 export artifact exists.
- Do not mark any production engine, character, world, animation, TTS, lip-sync, installer or episode pipeline verified based on current CI.

## Verification standard
Every new test result must record exact commit/version, environment, command, exit code, elapsed time, artifacts, observed output and unresolved limitations. CI success is not a substitute for target-PC or visual/audio quality verification.

## P0.4 follow-up model audit
- Inspected WhisperX Urdu aligner model card/file size, Urdu Whisper Turbo ASR model card/file size and Smol Urdu TTS source tree. Evidence is documented in URDU_VOICE_FEASIBILITY.md and CANDIDATE_SCORECARD.md.
- This was source/model-card inspection only. No model weights were downloaded, no inference was run, and no Pakistani audio was processed.


## P0.6 bounded functional proofs — 2026-11-25

See P0_6_PROOF_REPORT.md for exact run IDs, acceptance checks and limitations.

- Godot native-worker proof run #2: SUCCESS on b05024110e76b684a5f8cee35eb57fa0428b2c11. Godot 4.7.2-stable official, Compatibility renderer, GLB imported with MeshInstance3D, animation created/playing, scene saved/reopened, 72 frames at 24 FPS; AVI is 640x360, MJPEG/PCM, 3.0 seconds. All six JSON checks true. Runner adapter was Mesa llvmpipe, not the user's GPU.
- Godot + FFmpeg proof run #3: SUCCESS on ae9bad178c9999d5f5b7017a6409c7ee9c490786. Same scene checks passed; FFmpeg converted AVI to 640x360, 24 FPS, 3.0-second MP4 with MPEG-4 Part 2 video and AAC audio. This proves container/assembly path only, not final distribution codec choice.
- SQLite queue proof: Windows CI run #101 SUCCESS on b05024110e76b684a5f8cee35eb57fa0428b2c11; 17 tests passed, including five isolated queue-prototype tests for serial claims, lease-expiry retry, completed-scene preservation, cancellation and stale-worker rejection.
- First Godot attempt #1 failed: dynamically created nodes lacked PackedScene ownership and the MovieWriter output directory was not created inside the Godot project. Both were corrected; runs #2 and #3 passed. The failed attempt is retained as diagnostic history, not hidden.
- These are bounded hosted-runner proofs, not production app integration, full episode rendering, or user-PC benchmarks. Actual target-PC measurements remain Phase 8.

## P1.2 reproducible dependency lock and CI — 2026-11-25

- Added a committed universal uv.lock for the declared Python range (>=3.11,<3.14).
- Added requirements.lock, a fully pinned runtime export with package hashes; the Windows launcher uses pip's --require-hashes.
- Windows CI verifies uv lock --check, installs with uv sync --locked, runs Ruff, Python compileall and pytest, exports the runtime lock and fails if it differs from the committed file.
- Generated CycloneDX 1.5 dependency inventory for the complete locked environment.
- Replaced the deprecated TestClient dependency path with httpx2; the warning is not suppressed.
- CI #125 passed the initial locked environment; CI #136 passed the subsequent complete batch with 22 tests.

## P1.3 clean Windows bootstrap and launcher smoke test — 2026-11-25

- Added tests/smoke_windows_package.py; it validates ZIP members and required application files, extracts the artifact into a clean temporary directory and executes the real start.bat.
- The launcher creates a Python 3.11 virtual environment, installs hash-locked runtime dependencies, starts Uvicorn on loopback and optionally opens the browser. Test-only environment variables provide an ephemeral port, isolated data directory and browser suppression.
- Smoke test verified dashboard HTML, static CSS, health endpoint, project creation/opening, application restart and persistence of the saved project.
- CI #136: SUCCESS on commit d60def463e34575bab26b3a5da6c573b4f2bc4ee; 22 pytest tests passed; Ruff, compile, lock consistency, package creation, actual launcher smoke, artifact upload and SBOM upload all passed.
- Artifacts: Cartoon-Studio-Windows-Bootstrap (250,410 bytes; artifact ID 15002480559) and Cartoon-Studio-Dependency-SBOM (29,041 bytes; artifact ID 15002700150).
- Limitations: the bootstrap still requires Python 3.11 installed or available via the Windows Python launcher. It is not the P1.4 self-contained installer. No user-PC or rendering performance test was run.


## P1.4 self-contained Windows installer — 2026-11-25

- Built self-contained PyInstaller onedir application bundles for versions 0.1.0 and 0.1.1 and compiled per-user NSIS 3.13.0 installers.
- Installer default location: `%LOCALAPPDATA%\\Programs\\Cartoon Studio`; user data remains separate under `%LOCALAPPDATA%\\CartoonStudio` or the explicit `CARTOON_STUDIO_DATA` override.
- Upgrade replaces known program-owned files without invoking the prior uninstaller mid-install. The uninstaller restores its original install directory from the per-user registry before cleanup.
- Windows CI #175 passed: clean v1 install, launch and project creation; v1-to-v2 upgrade; project visibility after upgrade; uninstall; program/shortcut/registry cleanup; user project preservation; reinstall; project visibility after reinstall; final uninstall.
- Exact verified commit: `24f1617cff4d592e981908c7ceea641225c05ac0`.
- Artifacts: installer 17,543,577 bytes (ID `15009070345`); bootstrap 259,634 bytes (ID `15008472421`); CycloneDX SBOM 31,634 bytes (ID `15008008481`).
- Limitations: no code signing or automatic updater is claimed; no installation on the user's personal PC or target-PC performance benchmark was performed or required. Target-PC optimization remains Phase 8.


## P1.4 self-contained Windows installer — 2026-11-25

- Windows CI run #175: SUCCESS on commit 24f1617cff4d592e981908c7ceea641225c05ac0.
- Windows CI run #176: SUCCESS on commit 815cc32a1cb56c3357c37310745e900a8a197c7f.
- Both runs built application versions 0.1.0 and 0.1.1, compiled NSIS installers, installed v1, launched the app, created a project, upgraded to v2, confirmed project preservation, uninstalled, reinstalled v2 and confirmed the same project remained available.
- Uninstall removed program files and Start Menu/desktop shortcuts while preserving the isolated project-data directory.
- NSIS uninstaller path restoration is handled in un.onInit; the smoke test waits for the temporary uninstaller process to finish before checking cleanup.
- Artifacts from run #176: Cartoon-Studio-Windows-Installer (15008168874), Cartoon-Studio-Windows-Bootstrap (15007954336), Cartoon-Studio-Dependency-SBOM (15008014096).
- Full acceptance detail: docs/P1_4_INSTALLER_REPORT.md.
- No target-PC performance benchmark or user-PC installation was performed or required. Public redistribution remains subject to the project owner's license decision.


## P2.1 Godot native-worker integration — implementation in progress

- Pinned official Godot 4.7.2-stable Windows x86_64 release archive: `Godot_v4.7.2-stable_win64.exe.zip`, 86,013,866 bytes, SHA-256 `731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953`.
- Added the Python adapter, one-shot JSON worker protocol, handshake and GLB inspection, project-root/symlink/path validation, timeout, cancellation and child-process cleanup.
- Added FastAPI engine status and project-relative GLB inspection endpoints.
- CI is being extended to download and hash-verify the official binary, execute real worker integration tests, add the runtime to CycloneDX and bundle it with both installer builds.
- Status: implementation committed; Windows CI result pending. No character creation, rigging, animation authoring or production rendering is claimed by this batch.


## P2.1 Godot native-worker integration — Windows CI #204 — 2026-11-25

- Commit: `1f68fe8e5e87dab3115c7ed95788a7eab4176aab`.
- Workflow: [Cartoon Studio CI #204](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45590769693).
- Result: SUCCESS. The pytest step displayed 39 passing tests (39 dots, no skips or failures) on Windows Server with Python 3.11 and the actual pinned Godot 4.7.2 executable supplied through `CARTOON_STUDIO_GODOT_PATH`.
- Verified in the real worker path: protocol/version handshake and capabilities; import/inspection of the checked-in GLB fixture; malformed GLB failure; independent worker-side project-root boundary rejection; FastAPI status and project-relative GLB inspection endpoints.
- Adapter-level tests additionally cover missing runtime, path traversal, symlink escape, non-GLB input, timeout termination, cancellation termination, wait/cleanup and structured failure logging.
- Ruff and Python compilation passed. Godot archive SHA-256 verification passed. CycloneDX inventory includes the Godot runtime. Both self-contained application builds include the runtime, worker project and upstream license/copyright/author notices.
- Installer smoke test passed clean install, first launch, project creation, v1-to-v2 upgrade, project preservation, uninstall cleanup and reinstall. The follow-up commits fixed worker-file removal and stop the app/worker before uninstaller cleanup; CI #204 confirms the final state.
- Limitations: this validates the native worker integration and GLB inspection only. It is not proof of character creation, rigging, modular appearance, rendered character preview, animation authoring or final episode rendering. Hosted runner renderer is not the user's Intel GPU; target-PC benchmarking remains Phase 8.


## P2.2 Character Studio import/profile vertical slice — 2026-11-25

New test module: `tests/test_characters.py`.

Coverage added:
- Character Studio page route.
- GLB 2.0 binary container validation and rejection of malformed files/unsafe filenames.
- Project-scoped upload and Godot worker inspection contract.
- Skeleton and animation readiness derived from engine inspection.
- Character profile create/list/get/update and revision increments.
- Canonical character IDs stored in project.json.
- Recovery of character profiles and document index from portable JSON after SQLite index loss.

The tests use a deterministic fake adapter for API contract tests; the existing Windows CI continues to exercise the real Godot worker with the pinned runtime. The combined suite has not yet been accepted by CI at the time this report was authored. No target-PC benchmark is required.


## P2.2 Character Studio vertical slice — Windows CI #208 — 2026-11-25

- Commit: `41aabbb627e36f3f02f306e79e3cba33bd19dc84`.
- Result: SUCCESS — [workflow run #208](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45593773278).
- Pytest: 45 tests passed on Windows Server / Python 3.11 with the pinned Godot 4.7.2 runtime path configured. This includes the new Character Studio API tests for GLB upload validation, worker-inspection contract, profile create/list/get/update, project references and portable-file recovery.
- Ruff: all checks passed. Python compilation passed.
- Runtime archive SHA-256 verification passed; dependency lock remained current; CycloneDX SBOM export and Godot runtime augmentation passed.
- Windows bootstrap smoke passed: archive integrity, actual `start.bat` launch, HTTP UI/API, project save/open and restart persistence.
- Both self-contained PyInstaller application builds passed. Both versioned NSIS installers compiled.
- Full installer smoke passed: clean install, shortcuts, v1-to-v2 upgrade, project-data preservation, uninstall and reinstall.
- All three CI artifacts uploaded: Windows bootstrap, self-contained Windows installer and dependency SBOM.
- Scope limitation: tests validate import and inspection, not live rendering/preview or mesh/rig authoring. Target-PC benchmarking remains Phase 8.


## P2.2 browser preview extension — Windows CI pending

New coverage: project-scoped retrieval of a validated imported GLB asset for browser preview. The vendored three.js runtime is added to the CycloneDX SBOM via `third_party/threejs-runtime.json`. CI will verify lint, Python compilation, the API regression test, package contents, installer build and lifecycle. Visual browser rendering still requires an interactive WebGL 2 browser; the headless Godot CI worker is not used as a screenshot renderer.


## Character material appearance batch — 2026-11-25

Added API coverage for material recipe validation, persistence, revision increments, reload and preservation through profile updates. The browser editor applies base colour, roughness and metalness to imported GLB materials through the locally bundled Three.js runtime. CI and visual browser review are pending; no mesh mutation or export is claimed.
