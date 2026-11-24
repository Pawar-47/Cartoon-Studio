# Research Log

## 2026-11-25 — Live repository reconciliation

- Confirmed repository `Pawar-47/Cartoon-Studio`, default branch `main`, and current HEAD `40bec8c423e953a0753c62f53c8a173274ac72e1`.
- Branch search returned only `main`.
- Read all 19 requested project documents; all 19 paths were present.
- Read current FastAPI/story source, application tests, CI workflow, Ara proof workflow and Ara patch script.
- Verified Cartoon Studio CI run #52 (`45487769827`) on current HEAD: Ruff, compile, 12 pytest tests, bootstrap ZIP packaging and upload all passed.
- Verified bootstrap artifact ID `14963389016`, 74,228 bytes, SHA-256 `423371c438c3b07a5b2aa3c38f6b26768078ffb1611e96b72d3c08a2e189d0ea`.
- Inspected Ara proof run #6 (`45486950450`) jobs and full logs. It was cancelled during browser-level MP4 export. Type-check and partial film/editor tests passed; Studio checks, Vite build and artifact upload were skipped. No artifact exists.
- Ara remains an unapproved candidate; the run does not prove export, complete build, target hardware compatibility or production readiness.

## 2026-11-25 — Existing source baseline

- `app/main.py` contains FastAPI routes, SQLite project metadata, story-plan validation and persistence.
- `app/story.py` contains a strict Pydantic episode schema, 5–7 scene/300–420 second constraints, cue timing checks and Ara-derived location/action/expression ID validation.
- `tests/test_app.py` contains 12 application tests.
- `.github/workflows/ci.yml` runs on Windows and packages a bootstrap ZIP.
- `.github/workflows/ara-foundation-proof.yml` clones Ara at `4151c1124b172fdd918d23e0ef4aad727f4984c1`, applies `scripts/patch_ara_foundation.py`, then runs type, film, Studio and build checks.

## 2026-11-25 — Ara export proof diagnosis

- Run #6 completed the film model checks and several browser editor checks, then entered the browser MP4 export test.
- The workflow log ends at the browser test's wait for the rendered/downloadable film; the job conclusion is cancelled.
- The evidence does not distinguish a slow export, encoder/browser limitation, export failure hidden behind the wait, or manual cancellation. Do not invent a root cause.
- Next: inspect the exact upstream export implementation and browser harness, make the proof bounded and failure-diagnostic, then run one controlled proof only after the Phase 0 gates and proof design are ready.

## 2026-11-25 — Prior research retained

- Ara 3D Gen source at `4151c1124b172fdd918d23e0ef4aad727f4984c1` has a Studio editor, scene/film timeline, procedural sets, character import, and browser MP4 export. It is early-preview software, not approved.
- Ara's original proof patches expand the film from five to seven scenes, increase JSON size to 700 KB and compact the inspector for short desktop viewports.
- Ara's default Supertonic 2 speech does not support Urdu.
- Ekza Studio, DvaitAI anim-studio, AnimStudio and Rhubarb Lip Sync NG remain comparative candidates/references.
- Smol Urdu TTS, tiny-urdu, DeepSpeak, Dia and XTTS Urdu fine-tune have unresolved quality, resource or licensing constraints; no TTS is approved.

## Evidence policy

Every research entry must include date, source URL, exact version/commit where relevant, what was actually inspected, outcome, limitations and next action. Search results alone are not evidence. Never convert partial CI success into a production capability claim.
