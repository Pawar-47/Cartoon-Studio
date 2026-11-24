# Decision Log

## D-001 — GitHub repository is source of truth
Date: 2026-11-25. Use Pawar-47/Cartoon-Studio as the only primary repository. User explicitly created it for this project. Accepted.

## D-002 — Local-first production, GitHub-hosted CI
Date: 2026-11-25. GitHub Actions builds, tests and packages the application; episode rendering initially runs on the user's Windows PC. Hosted runners are not a permanent free GPU render service. Accepted.

## D-003 — Do not lock a full 3D engine before source and hardware evaluation
Date: 2026-11-25. Initial app shell stays independent of the final engine until source and target-hardware proofs are complete. Accepted.

## D-004 — Initial local application framework
Date: 2026-11-25. FastAPI + static HTML/CSS/JavaScript + SQLite for project management. Small dependency footprint and a Python integration path. Implemented; CI verification pending.

## D-005 — Ara 3D Gen is the leading 3D foundation candidate, not yet accepted as production dependency
Date: 2026-11-25. Source has character builder, procedural sets, timeline, animation, audio and browser MP4 export. It is early preview, currently capped at five scenes of up to 60 seconds each, has a realistic MakeHuman-derived style, and its Supertonic 2 voices do not support Urdu. Next step is a Windows build and low-end rendering proof, then decide on submodule/upstream integration and cartoon-style patches. No external code has been copied.
