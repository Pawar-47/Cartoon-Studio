# Repository Baseline Audit

**Audit date:** 2026-11-25  
**Repository:** https://github.com/Pawar-47/Cartoon-Studio  
**Branch:** main  
**Audited HEAD:** 40bec8c423e953a0753c62f53c8a173274ac72e1

## 1. Repository and Git state

- The GitHub repository is public; default branch is `main`.
- Branch search returned only `main`.
- The latest commit is `40bec8c423e953a0753c62f53c8a173274ac72e1` (2026-11-24 21:06:56 UTC), updating `AGENTS.md` with the complete document-reading gate and upstream patch review requirements.
- The recent history includes the Story Plan schema/catalog validation, prompt catalog inclusion, CI and checkpoint documentation. No code change after the latest app CI is required to explain the green run: run #52 tested the current HEAD.
- The project remains in the original repository. No reset, replacement or migration was performed.

## 2. Current application source

Confirmed from current `main`:

- `app/main.py`: FastAPI app, SQLite project metadata, health/status endpoints, project create/list, story prompt, story-plan validation and save/load.
- `app/story.py`: strict Pydantic episode schema; 5–7 scenes; 300–420 seconds; up to five characters; timed dialogue, action, camera and audio cues; exact location, expression and action ID validation; prompt builder includes the current catalogs and Urdu instructions.
- `app/static/`: dashboard and Story Generator UI.
- `tests/test_app.py`: 12 tests covering health, routes, projects, prompt/schema, save/load, duration, seven scenes and invalid catalog references.
- `.github/workflows/ci.yml`: Windows Python lint, compile, pytest, bootstrap ZIP and artifact upload.
- `.github/workflows/ara-foundation-proof.yml`: pinned upstream Ara Windows proof; it clones Ara at a fixed SHA and applies the tracked patch script. It does not integrate Ara into the product.

## 3. Current Cartoon Studio CI — run #52

Run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45487769827  
Run ID: `45487769827`  
Head SHA: `40bec8c423e953a0753c62f53c8a173274ac72e1`  
Job: `test-and-package-windows`  
Conclusion: **success**.

Verified job steps: dependency installation, Ruff lint, Python compile, pytest (12 passed, one Starlette/httpx deprecation warning), Windows bootstrap ZIP packaging and artifact upload.

Artifact:
- Name: `Cartoon-Studio-Windows-Bootstrap`
- ID: `14963389016`
- Size: 74,228 bytes
- SHA-256: `423371c438c3b07a5b2aa3c38f6b26768078ffb1611e96b72d3c08a2e189d0ea`
- Expires: 2026-12-08 21:07:29 UTC

This artifact is a bootstrap ZIP containing source and a launcher. It is not a self-contained installer, production engine or completed application.

## 4. Ara proof — run #6 actual outcome

Run: https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45486950450  
Run ID: `45486950450`  
Tested Cartoon Studio commit: `3beb546b63e9a0a07e1459ea4f4e3ea26d6d41d6`  
Pinned upstream: `olatunde85/3d-gen@4151c1124b172fdd918d23e0ef4aad727f4984c1`  
Job: `Build and test pinned Ara 3D Studio upstream`  
Conclusion: **cancelled**, not success.

Completed before cancellation:
- Upstream clone and dependency installation.
- CC0 asset preparation (including the upstream setup-assets process).
- Cartoon Studio patch application and `git diff --check`.
- TypeScript type-check.
- Film model checks: seven-scene limit, film JSON, timing, editing and related assertions.
- Browser checks for adding scenes, per-scene sets/names/transitions, continuous playback, reload/save, and scene-strip duplication/reordering/deletion up to seven.

The job was cancelled during the browser-level two-scene MP4 export test. Studio-wide checks, Vite build and proof artifact upload were skipped. The run has no artifacts. The logs do not establish why the export did not finish before cancellation; that remains an investigation item, not a proven upstream defect.

Ara is still a candidate only. Neither the type-check nor partial browser checks approve it as the production engine.

## 5. Evidence boundaries and limitations

- The GitHub connector exposed branch search, commit history, selected run jobs/logs and artifacts. It did not expose a complete paginated Actions run listing in this audit. Therefore this document reports the explicitly inspected run #52 and Ara run #6, and does not claim that every historical or currently active run was enumerated.
- The combined commit status endpoint for the current HEAD returned no status records; run #52 itself is directly verified through its job and artifact records.
- No target-PC installation, Intel HD 5500 performance measurement, real final MP4 from Cartoon Studio, Urdu TTS, Urdu lip-sync or end-to-end production render has been verified.

## 6. Actual capability baseline

| Area | Current evidence-backed state |
|---|---|
| Dashboard | FastAPI-served static dashboard |
| Projects | SQLite create/list metadata |
| Story Generator | Prompt construction and manual external-AI handoff |
| Episode schema | Pydantic schema with duration, scene, cast and cue validation |
| Catalog validation | Location/action/expression IDs checked against candidate production catalogs |
| Story persistence | Validated JSON save/load per project |
| Direct AI generation | Not integrated |
| Character Studio | Not implemented |
| Persistent world builder | Not implemented |
| Animation/timeline editor | Not integrated into Cartoon Studio |
| Urdu TTS / lip-sync | Not implemented or verified |
| Production renderer | Not integrated |
| Final MP4 pipeline | Not implemented in Cartoon Studio |
| Windows delivery | Bootstrap ZIP only |
| Target PC | No actual install or performance benchmark |

Catalog validation currently uses Ara-derived identifiers. This is useful input validation, but it couples the schema to an unapproved candidate and does not prove an engine adapter or real animation playback.

## 7. Phase and process assessment

The master plan's Phase 0 exit gate is not met:
1. Registry and traceability do not yet decompose every distinct specification requirement into a fully evidenced row.
2. Comparative research remains incomplete across toon character creation, persistent world assets, animation/retargeting, render compatibility, audio, Urdu lip-sync, packaging and AI provider terms.
3. Target-hardware and Urdu TTS feasibility remain unproven.
4. Architecture is provisional; no production engine has been selected.

Therefore Phase 0 remains active. Do not begin engine-dependent production feature work or integrate Ara until the master-plan gate is met. Continue the highest-priority Phase 0 work in complete documentation/research batches, and keep the existing app foundation intact.

## 8. Preservation rules

- Preserve all current application source, tests, docs, Ara proof workflow and patch script.
- Do not reset the repository or replace the application shell.
- Do not promote Ara from candidate to selected engine based on partial checks.
- Do not call the bootstrap ZIP a final installer.
- Do not mark requirements VERIFIED from code presence or unrelated CI success.
