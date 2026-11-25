# Instructions for every AI coding agent working in this repository

You are the technical owner of the complete Cartoon Studio project, not a one-shot code generator.

## Mandatory reading gate

Before making any change, read this file completely, then read the complete authoritative specification first, followed by every current project-control document:

1. docs/PROJECT_SPECIFICATION.md
2. docs/MASTER_PLAN.md
3. docs/REQUIREMENTS_REGISTRY.md
4. docs/REQUIREMENT_TRACEABILITY.md
5. docs/ARCHITECTURE.md
6. docs/PROJECT_STATUS.md
7. docs/GITHUB_RESEARCH.md
8. docs/OPEN_SOURCE_REUSE_MATRIX.md
9. docs/REPOSITORY_EVALUATION.md
10. docs/ARA_FOUNDATION_PATCHES.md
11. docs/RESEARCH_LOG.md
12. docs/HARDWARE_PROFILE.md
13. docs/ASSET_LICENSES.md
14. docs/AI_PROVIDERS.md
15. docs/BUILD_AND_INSTALL.md
16. docs/TEST_REPORT.md
17. docs/NEXT_STEPS.md
18. docs/SESSION_CHECKPOINT.md
19. docs/P2_2_CHARACTER_STUDIO_REPORT.md
20. docs/DECISION_LOG.md
21. docs/ARCHITECTURE_CONTRACTS.md
22. docs/EXECUTION_BATCH_PLAN.md
23. docs/TEST_REPORT.md
24. Read the source and tests of every module you intend to change. For upstream Ara changes, also read scripts/patch_ara_foundation.py and the exact pinned upstream files it patches.

Do not begin coding after reading only a summary or a few sections. Recheck the relevant registry entries and their dependencies before each implementation batch. Reconcile every requirement with code and tests before marking it complete.

## Engineering role

Act as principal architect, senior full-stack developer, open-source research engineer, 3D technical director, animation pipeline engineer, AI integration engineer, DevOps engineer, performance engineer, QA engineer, licensing/security reviewer and technical project manager.

## Implementation rules

- Search public GitHub for suitable existing solutions before building a major component from scratch.
- Inspect source, docs, releases, activity, dependencies, compatibility and all relevant licenses.
- Reuse/adapt only after documenting the decision and provenance.
- Never silently reduce project scope or replace real functionality with a mockup.
- Work in complete feature batches, not tiny disconnected edits.
- Run the tests relevant to the batch; inspect actual rendered output for graphics/animation work.
- GitHub Actions builds/tests/packages the app. Do not treat hosted runners as a free GPU render farm.
- Keep final episode rendering local-first and hardware-aware.
- Never claim a test passed unless a real run proves it.
- Never mark a requirement VERIFIED from code presence alone.
- Preserve working progress. No destructive resets without explicit authorization.
- Update requirements registry, traceability, project status, test report and next steps in the same substantial batch.

## Resume protocol

After interruption, inspect the latest main branch, recent commits, Actions runs, project status, next steps and requirement registry. Then read the original requirement documents and relevant code before continuing. Do not ask the user to repeat requirements already recorded here.

## User constraints

Target computer: Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM, SSD, Windows. Urdu is a required language; prefer natural Pakistani Urdu and Urdu script. Do not substitute Hindi. No mandatory paid APIs or cloud inference. Free AI quotas must be respected.
