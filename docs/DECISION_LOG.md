# Decision Log

## D-001 — GitHub repository is the source of truth
Date: 2026-11-25  
Decision: Use Pawar-47/Cartoon-Studio as the only primary project repository.  
Reason: User explicitly created this repository for the project.  
Status: Accepted.

## D-002 — Local-first production, GitHub-hosted CI
Date: 2026-11-25  
Decision: GitHub Actions handles application validation/build/package; actual episode rendering initially runs on the user's Windows PC.  
Reason: Hosted runners are not a persistent free GPU render service, and the target PC has Intel HD 5500 with 8 GB RAM.  
Status: Accepted.

## D-003 — Do not choose a full 3D foundation before source and hardware evaluation
Date: 2026-11-25  
Decision: Keep the first app shell independent of a final 3D engine.  
Reason: Ara 3D Gen, Ekza Studio and Blender pipelines have different scope, licenses, footprints and maturity.  
Status: Accepted pending proof-of-concept.

## D-004 — Initial local application framework
Date: 2026-11-25  
Decision: FastAPI + static HTML/CSS/JavaScript + SQLite for the initial local project-management shell.  
Reason: Small dependency footprint, Python integration path for Blender, simple local persistence.  
Status: Initial implementation; CI verification pending.
