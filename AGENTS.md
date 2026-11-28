# Cartoon Studio — Agent Operating Contract

This file is binding for every human or AI contributor. The GitHub repository is the source of truth. Current primary development line: `feature/cartoon-character-foundry` until the owner completes the requested independent-primary-branch promotion. The existing `main` branch is a separate preserved baseline; never merge into it, force-push it, rename/delete it, or change the default branch without explicit owner approval.

## Mandatory reading order
1. This file.
2. `docs/MASTER_EXECUTION_PROMPT.md`
3. `docs/PROJECT_SPECIFICATION.md`
4. `docs/MASTER_PLAN.md`
5. `docs/ARCHITECTURE.md`
6. `docs/CHARACTER_FOUNDRY_ARCHITECTURE.md`
7. `docs/REQUIREMENTS_REGISTRY.md` and `docs/REQUIREMENT_TRACEABILITY.md`
8. `docs/PROJECT_STATUS.md`, `docs/NEXT_STEPS.md`, `docs/SESSION_CHECKPOINT.md`
9. Relevant research, licensing, hardware, build, test and decision records.
10. The actual source/tests/workflows for every component being changed.

Read complete documents, not summaries. Re-fetch current GitHub HEAD and Actions state after interruptions. Never assume old chat context overrides repository state.

## Product strategy — non-negotiable
- **Blender is the central asset-authoring and generation platform** for original characters AND all world/environment/item assets: buildings, roads, streets, terrain, vegetation, interiors, vehicles, furniture, props, objects, accessories and set dressing.
- Build one shared, reusable Blender automation/tooling platform, with domain-specific tools and recipes on top. Do not create disconnected character-only and world-only generators.
- Blender is used through its Python API, reusable modules/operators and interactive/headless automation. Preserve editable `.blend` source projects and export production-ready GLB/glTF plus textures, manifests, metadata, thumbnails and provenance.
- **Godot 4.7.2 remains the production engine** for project/scene assembly, animation, cameras, timeline, preview, lighting and rendering. It consumes exported assets; it does not replace Blender as the authoring platform.
- The browser-first FastAPI application remains the control plane for projects, prompts, asset jobs, recipes, review/approval, scene/timeline control and render jobs.
- FFmpeg handles final video/audio assembly into MP4.
- Blender is an offline authoring dependency, not a required installed-app runtime dependency. Generated GLB assets must work in Godot without Blender installed.
- Character quality is the first quality-critical deliverable. The same Blender foundation must be designed for worlds and props from day one.
- User visual acceptance is performed by the user seeing the actual generated asset. Automated clipping/screenshot scripts are diagnostics only, never product features or a substitute for user review.

## Implementation rules
- Preserve existing code, APIs, project data and assets. Extend rather than restart.
- Inspect current source before changing it; search/research upstream alternatives before major new subsystems.
- No paid API, mandatory API key, cloud inference, online activation, credits or quota may block core asset creation or local production. External AI is optional.
- Do not use MPFB as the product foundation or copy GPL code into the project. Evaluate licenses per code, model, texture, animation and generated asset.
- Keep existing procedural GLB generation as a prototype/fallback where useful; it must not set the visual quality ceiling or compete with the Blender authoring path.
- Prefer reusable tools and real editing/generation functions over mockups, audits, validation-only scripts or cosmetic polish.
- Do not implement screenshot clipping acceptance as a feature.
- Never claim a capability or test is complete without direct evidence.
- Update status, registry, traceability, tests and next steps in the same substantial batch.

## Branch and CI discipline
- Work only on the current feature development line until owner-approved promotion is completed.
- Preserve old `main`; do not merge feature work back into it.
- Do not create extra task branches.
- One CI run at a time. Never push while a run is active/queued. Batch coherent changes; documentation-only changes do not require full build/package workflows.
- Do not trigger CI for single-line changes. Use CI at meaningful checkpoints, not as a constant build gate.
- Never force-push or delete branches without explicit approval.

## User-facing delivery
Report concrete files/features changed, commit, tests actually run, CI outcome, remaining work and any blockers. Keep updates concise. Always communicate in English. Do not ask the user to repeat requirements already in this repository.
