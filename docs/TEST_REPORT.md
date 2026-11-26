# Test Report — 2026-11-27

## 2026-11-27 — Main CI repair and local proof

- **Scope:** repair the failing main CI test without weakening generated-face coverage, and stop automatic deletion of non-main branches.
- **Change 1:** `tests/test_engine_adapter.py::test_pinned_godot_worker_builds_episode_scenes_with_world_and_character_glb` now obtains the pinned CC0 Male Adventurer via `ensure_model_asset` and bakes the generated face onto it. The previous RobotExpressive fixture has no separable `Skin` surface, so commit `3c57d1f` correctly rejects generated-face replacement on it. Expression and speech tracks target baked `CartoonStudio_Face_*` nodes, so the episode test needs a face-capable character. The test also asserts `face_features_verified is True`.
- **Change 2:** added `test_generated_face_replacement_rejects_rig_without_skin_surface`. It requests generated-face replacement on RobotExpressive, expects `EngineExecutionError` matching `separable skin surface`, and asserts the output GLB was not created. This pins the fail-fast contract introduced by `3c57d1f`.
- **Change 3:** `.github/workflows/cleanup-retired-branches.yml` is now manual-dispatch only. It deletes only exact branch names supplied by a maintainer and always preserves `main`. Previously it ran after every successful main CI and deleted every non-main branch, including open feature work.
- **Environment:** Windows, Python 3.12.10, pinned Godot `4.7.2-stable` (`build/godot-runtime/Godot_v4.7.2-stable_win64.exe`), pinned CC0 RobotExpressive fixture and cached CC0 Adventurer.
- **Command:** `python -m pytest -q -rs` with `CARTOON_STUDIO_GODOT_PATH` set.
- **Result:** **152 passed, 4 skipped, 0 failed**. Skips: `test_animation_clip_resolver`, `test_browser_retarget`, `test_character_expression_presets` (Node.js unavailable locally; CI runs them) and `test_engine_adapter.py:132` (symlink creation unavailable). One existing Starlette/httpx deprecation warning.
- **Targeted reruns:** the repaired episode test and the new rejection test both passed with the pinned Godot runtime; the dedicated Adventurer generated-face test also passed.
- **Static checks:** `python -m ruff check app tests scripts` passed; `python -m compileall -q app scripts` passed; all `.github/workflows/*.yml` parsed as valid YAML; `git diff --check` passed.
- **Not claimed:** this is local proof, not GitHub Actions proof. The new CI run is pending. No visual browser acceptance, target-PC benchmark, installer rebuild or full episode render was performed in this batch.
- **Follow-up:** the 171-row requirements registry and traceability matrix remain stale and require a dedicated reconciliation batch; do not treat this report as closing those rows.

## Historical test reports — 2026-11-26 and earlier

## Current main regression and working-branch verification — 2026-11-26

- Current main commit `062400e58cbbf491ec92869dc140b60a9b354d7f` failed Windows CI [#471](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45791209337): Godot rejected the duplicate `"action_cue_count"` dictionary key in `engine/godot_worker/worker.gd`, preventing the worker script from loading.
- The working-branch fix removes the redundant raw-list count and keeps the count returned by timeline generation. `tests/test_engine_adapter.py::test_pinned_godot_worker_builds_episode_scenes_with_world_and_character_glb` supplies one valid wave action cue and one targeted dolly camera cue, asserting counts of 1/1 and five animation tracks; empty scenes retain three camera tracks.
- Pinned Godot 4.7.2 targeted test: **1 passed**. Full local suite with `CARTOON_STUDIO_GODOT_PATH` set: **136 passed, 4 skipped, 1 existing Starlette/httpx deprecation warning** in 132.52 seconds.
- These are local results for commit `be169c4` on pushed branch `work/mainline-followup`. No post-fix GitHub Actions run has completed; the workflow runs on pushes to `main` and pull requests targeting `main`, so #471 is not yet fixed or passing in CI.

## Latest main validation and CI coverage audit — 2026-11-25

- Main quick CI [45663866235](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45663866235) passed on `d42a6e766fdae22e9a742435228cfdb4431c656b`: locked dependency verification/install, pinned Godot and RobotExpressive fixture acquisition, Ruff, Node syntax check, Python compileall and full pytest.
- Read-only coverage review found that the Ruff command named only selected scripts, omitting `scripts/patch_ara_foundation.py` and `scripts/set_build_version.py`; the browser syntax step directly checked only `characters.js`, leaving other first-party browser entry points unchecked.
- The accompanying maintenance change broadens Ruff to all of `scripts` and parses every first-party top-level `.js`/`.mjs` file under `app/static`, excluding the vendored subdirectory. The maintenance PR's CI result is recorded after that run completes; this entry does not pre-claim it passed.

## Phase 2 — imported morph metadata and appearance persistence — 2026-11-25

- Windows CI #303: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45631358729) on commit `0bfce71625d6e3084b4ceda9b64a9825cca95101`. Full lint, compile, pytest, pinned Godot 4.7.2 worker, bootstrap, both self-contained builds, NSIS installer and clean install/upgrade/uninstall/reinstall lifecycle passed.
- Added third-party animated morph fixture `tests/fixtures/third_party/animated_morph_cube_cc0.glb`. Godot imports it, reports two morph targets, deterministic fallback names `morph_0` / `morph_1`, default weights, and the embedded animation. Source fixture remains unchanged.
- A separate compact GLB fixture verifies named `Smile` and `Blink` targets, mesh association and imported default weights. This fixture is synthetic, not a production facial character.
- Added a FastAPI regression test for saving facial morph weights into the persistent character appearance recipe and rejecting weights outside [-1, 1].
- Windows CI #304: [IN PROGRESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45631770407) on commit `7b703ec14b116440f5d6f1401ffce8bec5c7a16c`. Lint, Python compilation and the full pytest suite passed, including the new persistence test; Windows packaging and installer lifecycle remain in progress at this checkpoint.
- Facial morph controls already preview in Three.js, save as a non-destructive appearance recipe, and reset to imported defaults. No genuinely facial third-party morph model or native Godot expression playback has yet been accepted; keep those requirements PARTIAL.


## Phase 2 — third-party humanoid retarget and facial morph inspection — 2026-11-25

- Windows CI #299: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45629963495) on commit `570c6f9b2d0fe35b64ec74e84ab8d0e702d7665d`.
- Full pipeline passed: Ruff, Python compilation, full pytest, pinned Godot 4.7.2 worker, dependency-lock checks, CycloneDX SBOM, Windows bootstrap package/smoke, both self-contained application builds, NSIS installer and clean install/upgrade/uninstall/reinstall lifecycle.
- Added the unchanged Khronos glTF Sample Assets **Rigged Figure** GLB (Cesium, 2017, CC-BY-4.0) with its upstream license and attribution. The Godot worker imports its distinct 19-joint rig, maps 15 core humanoid bones, and retargets its animated source to the canonical target after saving and reopening the scene. Both source and target files are checked byte-identical after the proof.
- The first real-model assertion exposed that comparing raw source/target local rotation angles is invalid when rest axes and bone-roll conventions differ. The worker now validates the target pose against Godot's documented model-space rest-correction transform, while separately requiring the source animation to be playing and the source pose to have changed. The full real-model test passes in CI #299.
- Windows CI #293: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45628963188) for Godot facial blend-shape import reporting, the valid two-target GLB fixture, Character Studio blend-shape reporting, signed morph weights and reset-to-imported-default behavior.
- Windows CI #285: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45627949590) for 3ds Max Biped, Character Creator, Unreal-style and Blender Rigify naming tests plus malformed hierarchy rejection.
- Compatibility remains PARTIAL: one real third-party humanoid model has passed native retarget acceptance. This does not establish universal GLB support, multi-clip support, every rest-pose convention or browser/native visual equivalence. The morph fixture is synthetic; a real facial model remains to be tested.


## Phase 2 retarget-preview and DCC rig compatibility — 2026-11-25

- Windows CI #281: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45626571819) on commit `dd0354d8c264a5d2449a0b5249b0502e5b9b6be8`.
- CI passed Ruff lint, Python compilation, the complete pytest suite (including the pinned Godot 4.7.2 native-worker fixture), runtime-lock verification, CycloneDX SBOM generation, bootstrap package/smoke test, both self-contained builds, NSIS installer compilation and clean install/upgrade/uninstall/reinstall lifecycle.
- The run validates the retarget-preview API contract and the existing native imported-pair retarget proof. It does not establish browser visual fidelity or arbitrary third-party GLB compatibility.
- After CI #281, code commits `e17ed5d`, `3e2e6e0`, `08f2392` and `bdad978` expanded bone-name normalization for 3ds Max Biped, Character Creator, Unreal-style and Blender Rigify naming conventions, rejected malformed duplicate/negative hierarchy indices, and added focused regression tests. These commits are newer than CI #281; their tests have not yet run in CI at this checkpoint.
- No real third-party GLB files with differing bone axes/rest poses or multiple animation clips have yet been accepted. No real facial blend-shape fixture has yet been validated. Do not mark those requirements VERIFIED.


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


## Imported facial morph-target batch — 2026-11-25

Added API coverage for saving morph-target weights and rejecting values outside 0–1. The browser viewer discovers morph targets from GLB mesh dictionaries and applies slider weights to the live preview. Windows CI and visual validation with a real morph-enabled character are pending.


## Character Studio appearance and morph-target checkpoint — 2026-11-25

- Windows CI #214: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45599984676), commit `e58b40d75ae10431051980246b468b736544f464`.
- All 49 pytest tests passed; Ruff lint and Python compilation passed.
- Both self-contained Windows application builds, NSIS installer compilation and clean install/upgrade/uninstall/reinstall smoke tests passed.
- This run validates the material/morph appearance API persistence and validation tests plus packaging. Browser visual review with a representative facial-morph GLB remains outstanding.


## Phase 2 retarget checkpoint — Windows CI #279

- Workflow: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45622238283
- Commit: 56c61487089097108b6baa862f9ac9125568b9a5.
- Result: SUCCESS. The complete Windows job passed lint, Python compilation, full pytest, the actual pinned Godot 4.7.2 worker test, bootstrap packaging/smoke, both self-contained application builds, NSIS compilation, clean install, upgrade, uninstall, reinstall and artifact uploads.
- Artifacts: Windows installer 103,861,406 bytes; bootstrap 819,154 bytes; dependency SBOM 32,632 bytes.
- The Mixamo-named animated-source fixture and distinct target pose-transfer test passed.
- The browser retarget-preview API and UI are in the current implementation batch; this new code has not yet been tested by CI.


## Phase 2 — modular character assembly and mixed-outfit round-trip — 2026-11-25

- Feature integration commit: `67f31aed09a6b54e5a71869dd4ec5c8fe1d65386`.
- Feature CI: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45653413604).
- Merge commit: `b4dd8237e6369bbb74c58ef844e0fac5c9667c77`; main CI: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45653650908).
- Added a native Godot integration test using the pinned Quaternius CC0 outfits: Male Adventurer base, Beach head, Casual_2 body, Farmer legs and King feet. The worker imports all four sources, checks their shared skeleton, bone hierarchy/rest pose, rig transform and skin-bind references, then assembles the selected meshes on the base skeleton.
- Base skinned outfit meshes are removed before selected parts are attached, preventing the original outfit from remaining underneath the assembled outfit.
- The worker exports the assembled GLB, re-imports it, checks that all four named modular meshes remain, and verifies the complete base animation-name set. The integration test confirms the base's 24 animation clips are preserved.
- The API stores the base/part recipe in the versioned asset manifest; the Character Studio builder exposes slot-filtered selectors and restores saved assembly sources through manifest endpoints.
- A separate fix validates mesh skeleton paths relative to the cloned MeshInstance3D and rejects using the same source mesh for multiple slots.
- Limitations: CI proves the native mixed-outfit assembly and clip preservation, not interactive browser visual quality, arbitrary-rig conversion, animation deformation playback, mesh sculpting, new rig authoring, texture painting or final Character Studio acceptance. Phase 2 remains active.


## Phase 2 — modular accessories and bone attachment — 2026-11-25

- PR #4 feature commit tested by [CI run 45654673022](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45654673022): SUCCESS (Ruff, Python compilation, full pytest and Godot 4.7.2 integration).
- Merge commit: `f00bb3dbba55af7b6f3a02ca5b602bf773872a35`. Main-branch validation was queued as run 45654934870 at this checkpoint.
- Added accessory discovery to Godot mesh inventory, including source `BoneAttachment3D` bone metadata. The builder accepts up to eight accessories, records each source mesh and attachment bone, and supports removing selected accessory chips.
- Skinned accessories must match the base skeleton and rig transform and pass skin-bind checks before rebinding. Static accessories must originate from a matching `BoneAttachment3D` and are recreated under the same named bone on the target skeleton.
- The mixed-outfit integration test now adds the Quaternius Adventurer Backpack, exports/re-imports the result, verifies the accessory mesh is present, and confirms the base animation clips remain.
- The versioned assembly manifest stores accessory paths/bone names; reopening a saved assembly restores its accessory selections.
- Limitations remain: no arbitrary-rig conversion, general hair/face geometry authoring, or interactive visual acceptance is claimed.


## Phase 2 — outfit shuffle, GLB download and animation playback probe — 2026-11-25

- PR #6 feature CI [45655967987](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45655967987): SUCCESS. Main CI [45656217264](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45656217264): SUCCESS.
- Added a one-click outfit shuffler that selects four distinct source meshes and can add optional accessories. Saved and newly assembled characters now expose direct GLB download links.
- PR #7 feature CI [45655936153](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45655936153): SUCCESS. Main CI [45656445021](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45656445021): SUCCESS.
- Added the Godot `probe_glb_animation` worker operation and Python adapter. It imports a GLB, plays a requested clip at a deterministic sample ratio, compares skeleton bone poses, counts meshes whose skin binding resolves to the same Skeleton3D and reports valid BoneAttachment3D bones.
- The real mixed outfit plus Backpack test now probes `Walk` after export/re-import and asserts that bone poses change and at least four modular skinned meshes remain bound. This is stronger than clip-name preservation alone; it does not claim browser visual acceptance.
- PR #9 feature CI [45656755304](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45656755304): SUCCESS. Main CI run 45657010942 was pending at this checkpoint.
- Added Smile/Frown/Surprise/Angry semantic presets for imported morph targets, with name matching, unmatched-target preservation, manual slider integration, live preview and versioned appearance persistence. Presets are disabled when the model has no morph targets.
- PR #5 added Node 22 syntax validation for `app/static/characters.js`; feature CI 45655204627 and main CI 45655471623 passed.


## Phase 2 — rig-based body-proportion editing and morph grouping — 2026-11-25

- Main commit: `f9a03b9613d22c8bf99e96c5cf3d5de9997e0fd2`.
- Windows quick CI #417: [SUCCESS](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45672883272), completed in 73 seconds. Locked dependencies, pinned Godot 4.7.2 and the CC0 facial-morph fixture, Ruff, Node syntax checks, Python compilation and the full pytest step all passed. This quick workflow did not build the Windows application or installer.
- The new API/worker coverage checks that body-proportion edits create a verified new GLB, report changed bones, preserve animation clips/playback and leave the input GLB byte-identical. Face/body morph groups expose only morph targets already in the imported GLB; this does not create new blend shapes.
- Local Windows/Python 3.12.10 run (`.venv312\Scripts\python.exe`): `python -m pytest -o addopts= -q -r s tests/test_app.py tests/test_characters.py tests/test_engine.py`; exit code 0, 39 passed and 5 skipped in 7.54 seconds. The five skips require the pinned Godot runtime, which was unavailable locally; the same integration tests ran in CI.
- Local Ruff: `python -m ruff check app/main.py tests/test_app.py` passed. The isolated app smoke returned HTTP 200 for `/characters`, `ok` for `/api/health`, and the updated Character Studio milestone from `/api/status`.
- Earlier smoke only loaded the Character Studio shell; the later browser acceptance below supersedes that limited check.

## 2026-11-25 — Local integrated-browser acceptance

- With pinned Godot 4.7.2 enabled, imported the pinned CC0 Male Adventurer through the Character Studio library and confirmed browser rendering with 24 selectable animations. The Godot inspection reported 5 meshes, one skeleton, 13/15 humanoid-name coverage and hierarchy warnings.
- Applied a 1.10 torso-length edit in the browser. Godot exported a new GLB, reported two changed rig bones, and retained skin binding and all 24 animation clips. The source asset hash matched the pinned library SHA-256 (`2caf3ea58a06744c44a360c941c3355b499ba5adf8edf549b98fc347c45faa28`); the edited export hash differed (`a14529497467da31f4c8af3bd62d80cf141b131aa4352913cc4f55cc711116fa`).
- Saved the edited character profile, reloaded the page, reopened the profile and confirmed the stored 1.10 proportion and Walk playback. Also exercised the same UI path with the synthetic humanoid fixture; that fixture proves plumbing only, not character visual quality.
- Fixed two browser defects found during acceptance: the CSS grid rule overrode the preview placeholder's `hidden` state, and a loop variable shadowed the global DOM `document`, breaking saved-character card rendering. After the fixes, the preview placeholder was hidden while a model was loaded and both saved character cards rendered/reopened.
- Local targeted suite with the pinned Godot runtime: `tests/test_app.py tests/test_characters.py tests/test_engine.py` — 44 passed in 39.72 seconds. The first attempt lacked the CI-fetched RobotExpressive fixture; `scripts/fetch_robot_expressive_fixture.py` downloaded and checksum-verified it before the successful rerun.
- Node was not available on the local PATH for `node --check`; the changed browser module was fetched with a cache-busted URL and executed by the integrated browser during the acceptance workflow. CI #417's Node syntax checks apply to main, not this local branch.
- The Quaternius sample's rig warnings remain a compatibility limitation. This is functional browser acceptance, not blanket visual signoff, full modular-assembly acceptance, or original face/hair geometry authoring.

## 2026-11-25 — Upstream hairstyle and portrait-export integration

- Integrated the current main baseline `6a3406efb320a0895d4b2a7253395a107d6a394d`, containing PR #17 procedural Head-attached hairstyles and PR #19 transparent PNG portrait export. Main CI #421 and #423 passed; the hairstyle CI included pinned Godot worker coverage.
- The local feature branch preserves the saved-profile and preview-placeholder fixes. Current local full suite: `python -m pytest -o addopts= -q -rs` — **96 passed, 28 skipped** in 14.11 seconds. Skips: 24 pinned-Godot tests, three Node.js tests and one symlink-capability test. These runtimes/capabilities were unavailable locally.
- `python -m ruff check app tests`, `python -m compileall -q app tests` and `git diff --check` passed. Pytest emitted one Starlette deprecation warning about using `httpx`; it did not fail tests.
- PR #20's four-view turnaround export remains open and separate; CI #425 passed. Its feature is not included in this branch.
- No local visual acceptance was performed for generated hairstyles or PNG export. Existing Adventurer hierarchy warnings and the absence of original face geometry keep P2.2 PARTIAL.

## 2026-11-25 — Character preview default animation

- Added `resolveDefaultAnimationClip`: exact normalized `Idle` takes priority, followed by an Idle variant and then the first playable clip. RESET-only assets now show “No playable animations” without starting playback.
- Added Node tests for exact Idle preference, Idle-variant fallback, first-playable fallback and RESET-only behavior, plus a Python preview-wiring assertion.
- Local targeted run: `python -m pytest -o addopts= -q -rs tests/test_characters.py` — **16 passed**. Node.js was unavailable on the local PATH.
- Windows GitHub Actions [CI #429](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45691314081) passed on `4945beb7555c55fed2477de405e4e1a1b5b0f9a9`, including Node-backed helper tests, JavaScript syntax checks, Ruff, Python compilation and the full pytest suite. Packaging/installer validation was not part of this quick workflow.
- PR #21 remains open and separate from PR #20. No fresh visual browser acceptance was performed for this batch; Phase 2 and P2.2 remain active/partial.

## 2026-11-25 — Isolated branch integration validation

- Integrated the live proportion-preview/composable-edit branch, four-view turnaround export, Idle-default preview and geometry-aware hairstyle fit in a separate worktree based on `origin/main` at `4d2a7848b7c123358b868f56eac0704a80f6c58d`. The original checkout and user WIP stash were preserved. The tested integration was pushed to `main`; PRs #20 and #21 are now merged.
- `python -m pytest -o addopts= -q -rs tests/test_engine.py`: **14 passed** with the pinned Godot 4.7.2 runtime. Coverage includes short hair and ponytail placement on the real Male Adventurer, retained animation playback and unchanged source bytes.
- After fetching the checksum-verified RobotExpressive fixture in the integration worktree, `python -m pytest -o addopts= -q -rs`: **122 passed, 4 skipped**. Three skips require Node.js and one requires symlink support unavailable in this environment. One existing Starlette/httpx deprecation warning was reported.
- GitHub Actions run #431 initially failed at Ruff import ordering in `tests/test_characters.py`. Ruff's standard fix was pushed as `7d396e5`; run [#432](https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45703715915) passed. Local Ruff, Python compilation and the full integrated test suite pass.
- No new browser visual acceptance was performed, so P2.2 remains PARTIAL.
