# Mainline Master-Brief Alignment Audit — 2026-11-28

## Scope and source of truth

- Repository: `Pawar-47/Cartoon-Studio`
- Branch: `main`
- Audited starting commit: `a88379f3ac3a985756d68c25afd22ac7b0a9b4d5`
- Starting CI: Windows CI run #611 — SUCCESS (`46061139390`)
- Binding specification: the complete 25-part `docs/MASTER_EXECUTION_PROMPT.md`, read through Part 25.
- Supporting sources: `PROJECT_SPECIFICATION.md`, `REQUIREMENTS_REGISTRY.md`, `REQUIREMENT_TRACEABILITY.md`, `MASTER_PLAN.md`, `NEXT_STEPS.md`, `PROJECT_STATUS.md`, architecture, research, license and test reports, plus current source and tests.
- The Foundry feature branch is frozen and was not read as an implementation source or modified.

## Executive assessment

The repository has a real and increasingly substantial application foundation. Phase 0 and Phase 1 have meaningful research, requirement governance, reproducible CI, a bundled Godot worker, and a Windows installer lifecycle proof. Character Studio has imported-model editing, modular assembly, profiles, hair/face geometry and retargeting work. World documents are persistent and versioned; Godot can export editable world scenes and GLB previews. The application also has story-plan validation, Urdu speech/audio generation, episode-scene generation and an MP4 assembly path.

However, the product is **not yet aligned with the complete end-to-end acceptance target**. Most major production requirements remain partial. Green CI proves code/test/build contracts, not visual acceptance, a complete 5–7 minute episode, target-PC performance or production readiness.

## Confirmed alignment gaps

### 1. World Builder UI did not expose the backend's full object catalogue

At the audited starting commit, `WorldObjectInput` and the Godot exporter accepted 16 world-object categories, while `worlds.html` exposed only 7 add buttons. Civic buildings, garages, indoor rooms, playgrounds, furniture, water bodies and dedicated streetlights could be stored/exported through API paths but could not be added through the normal browser editor. The selected-object panel also omitted direct position and rotation controls.

**First-pass correction in this batch:** expose every backend-supported category in the browser object palette, add numeric X/Y position and rotation controls, and cover the UI/backend catalogue parity with a regression test. This closes the UI omission; it does not turn procedural blockout geometry into a finished asset library.

### 2. World geometry is still a procedural blockout, not a production asset library

The Godot world exporter builds geometry from primitive boxes, spheres and cylinders. The asset-license register records suitable CC0 environment packs, but the World Builder does not yet provide a browsable, downloadable, reusable model library for roads, buildings, interiors, vegetation, props and vehicles. Many object kinds are represented by generic geometry. The current preview is a real Three.js GLB preview, but it is not proof of production-quality art.

**Required follow-up:** build a project-scoped asset catalogue with verified provenance, lazy downloads, local caching, previews and placement/instantiation; integrate selected CC0 packs only after pinning exact pack versions, per-pack license evidence and file checksums.

### 3. Vehicle data contracts are ahead of the runtime

Vehicle rig, movement and interaction endpoints persist steering, wheel rotation, acceleration, braking, parking and door/enter/exit events. They do not yet drive a reusable vehicle rig, wheel animation, character entry/exit animation or scene-time event system. These are state/API foundations, not completed vehicle behavior.

### 4. Story generation is a manual handoff, not single-prompt automation

The Story Generator builds a structured prompt/schema and validates/saves pasted episode JSON. No supported integrated provider orchestration currently generates and repairs a story directly inside the app. This is an intentional safe boundary because some free AI applications do not expose supported APIs; manual handoff must remain available, but the product needs a clearly labelled optional provider adapter where terms and credentials permit.

### 5. Animation is procedural scene blocking, not a complete animation editor

Godot generates editable episode scenes with action anchors, skeletal keyframes, camera tracks, expressions and audio-envelope mouth cues. A reusable licensed motion library, timeline editor, blend graph, smooth transition authoring and full visual action acceptance remain open.

### 6. Urdu speech and lip-sync are only partially accepted

The current audio path creates Urdu speech WAVs, a mix and subtitles. Mouth movement is driven by an RMS/audio-envelope heuristic, not Urdu phoneme/viseme alignment. Native-speaker review, pronunciation/naturalness scoring, character-specific voice consistency and visible lip-sync acceptance remain open. Do not describe the envelope as phoneme-accurate lip-sync.

### 7. Episode production has a path, but not full production acceptance

The application can generate editable Godot scenes, produce dialogue audio and assemble MP4 through Godot AVI plus FFmpeg. The durable job queue now covers production, audio, world export and render operations; older documentation incorrectly says there is no durable render queue. The queue is still an in-process executor with durable records/leases, not a separately supervised multi-worker service. Scene-level content-addressed render caching and restart-resume without rerendering completed scenes remain open. No full 5–7 minute final episode has been accepted by inspecting its complete video/audio output.

### 8. Required workspaces remain incomplete

Dashboard, Story, Character and World workspaces exist. The complete brief's Asset Library, Animation Library/editor, Voice Studio, Scene Editor, Timeline, Research Agent, AI Resource Manager, Episode Renderer workspace and comprehensive diagnostics/settings are not all implemented as functional end-to-end workspaces. Existing routes and backend APIs should be reused rather than recreating modules.

### 9. Documentation drift and inaccurate phase statements

- `NEXT_STEPS.md` still names an old main commit and old local test count.
- `PROJECT_STATUS.md` says the render queue does not exist, contradicting the queue implementation and the same document's current queue section.
- The phase table marks P3.2/P3.3 complete while its evidence still lists open visual acceptance, asset kits and vehicle runtime behavior. Treat those subphases as implementation slices with outstanding acceptance, not fully accepted deliverables.
- `MASTER_PLAN.md` current-baseline paragraph describes the pre-Godot/pre-installer state. It must be superseded by a current baseline.

## First-pass implementation delivered with this audit

- World Builder now exposes all 16 backend-supported object kinds.
- Selected objects now support numeric X/Y positioning and rotation in addition to size, label and colour.
- Canvas rendering distinguishes water, furniture, playground/park and streetlight object classes.
- Regression test ensures every backend-supported object kind remains reachable from the browser palette and position/rotation controls remain wired.
- Documentation is synchronized to the current mainline checkpoint and records the remaining gaps without overstating completion.

## Next development order

1. Phase 3.2: integrate verified CC0 environment assets into a project-scoped reusable library; prioritize roads, houses/shops, civic buildings, trees, furniture and vehicles.
2. Phase 3.3: connect vehicle rigs and interactions to actual scene-time animation and character actions.
3. Phase 4: complete canonical world-linked scene production mapping and optional supported story-provider integration while retaining manual handoff.
4. Phase 5–7: reusable animation/timeline, accurate Urdu alignment/visemes, scene caching/recovery and full MP4 acceptance.
5. Phase 8: visual/audio signoff, target-PC benchmarks, performance presets and final installation/reliability acceptance.

Do not reopen the frozen Foundry branch, duplicate existing Character Studio work, or declare the application complete while major requirements remain partial.
