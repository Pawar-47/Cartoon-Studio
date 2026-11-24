# Research Log

## 2026-11-25 — Repository initialization and first application batch
- Confirmed Pawar-47/Cartoon-Studio exists, is public, uses main, and was empty before bootstrap.
- Created FastAPI + SQLite local dashboard and Windows GitHub Actions validation/package workflow.
- Added requirement registry, traceability, authoritative project specification and AGENTS.md.
- CI run 45483211675 succeeded on windows-latest: Ruff PASS, compile PASS, 3 pytest tests PASS, bootstrap ZIP package/upload PASS.
- Bootstrap ZIP is not a standalone installer or production application.

## 2026-11-25 — Public GitHub research
- Inspected Ara 3D Gen source, package scripts, Studio guide, project/film schema, export path, character importer, scene renderer, procedural set catalogue and asset licensing.
- Ara currently has a 5-scene film cap, 60 seconds per scene, browser MP4 export at 30fps, 5 actors, character import and procedural sets.
- Ara's default local TTS uses Supertonic 2, whose official model card does not list Urdu. It is not acceptable for Urdu dialogue.
- Inspected Ekza Studio, DvaitAI anim-studio, AnimStudio and Rhubarb Lip Sync NG as alternatives/references.
- Inspected Urdu TTS options: Smol Urdu TTS V1, tiny-urdu, DeepSpeak-v1, Dia-1.6B-Urdu and XTTS-v2 Urdu fine-tune. No model passed all license, quality and target-hardware gates.
- Added a dedicated Windows proof workflow for pinned Ara commit 4151c1124b172fdd918d23e0ef4aad727f4984c1. It must complete before integration is accepted.

## Evidence policy
Every future research entry must include date, source URL, what was actually inspected, exact version/commit where relevant, outcome, limitations and next action. A search result alone is not a proof of compatibility.
