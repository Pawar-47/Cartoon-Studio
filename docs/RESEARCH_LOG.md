# Research Log

## 2026-11-25 — Repository initialization and application foundation
- Confirmed Pawar-47/Cartoon-Studio exists, is public, uses main, and was empty before bootstrap.
- Created FastAPI + SQLite dashboard, project persistence and Windows GitHub Actions validation/package workflow.
- Added authoritative project specification, AGENTS.md, requirement registry and traceability.
- Windows CI run 45486108853 succeeded: Ruff PASS, compile PASS, 10 pytest tests PASS, bootstrap ZIP package/upload PASS.
- Bootstrap ZIP is not a standalone installer or production application.

## 2026-11-25 — Public GitHub research
- Inspected Ara 3D Gen source, package scripts, Studio guide, project/film schema, export path, character importer, scene renderer, procedural set catalogue and asset licensing.
- Ara has a 5-scene film cap, 60 seconds per scene, browser MP4 export at 30fps, up to 5 actors and imported rigged character support.
- Ara's default Supertonic 2 voices do not support Urdu.
- Inspected Ekza Studio, DvaitAI anim-studio, AnimStudio and Rhubarb Lip Sync NG as alternatives/references.
- Inspected Smol Urdu TTS V1, tiny-urdu, DeepSpeak-v1, Dia-1.6B-Urdu and XTTS-v2 Urdu fine-tune. No model has passed all license, quality and target-hardware gates.

## 2026-11-25 — Ara Windows proof and patch iteration
- Baseline pinned Windows proof successfully cloned source, installed dependencies and prepared CC0 character assets, then found landscape/portrait/title-card controls clipped at 1366x768.
- Added a compact inspector patch and expanded the film limit to 7 scenes/700 KB.
- First patched proof showed the upstream browser scene-strip test still expected the old 5-scene cap.
- A subsequent patch attempt exposed an exact-indentation mismatch in the final browser assertion. Updated the patch script to target the correct assertion line and added git diff checks.
- Corrected pinned Windows proof is running; do not accept Ara until all checks and build succeed.

## Evidence policy
Every future research entry must include date, source URL, what was actually inspected, exact version/commit where relevant, outcome, limitations and next action. A search result alone is not proof of compatibility.
