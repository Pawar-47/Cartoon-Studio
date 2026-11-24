# Authoritative Project Specification — Cartoon Studio

This is the durable product specification for the Cartoon Studio repository. It complements the user-approved master prompt. It must be read in full by every coding agent before implementation. The requirement registry and traceability matrix must cover every requirement below.

## 1. Product objective
Deliver a functional, installable, local-first web-based studio that creates original 3D Urdu cartoon episodes from a single user prompt. The target episode length is approximately 5–7 minutes. The final deliverable is a real MP4 with animation, dialogue, character-specific voices, lip-sync, music, effects, scene transitions and an editable project. This is a persistent production system, not a one-off video generator.

All characters, names, designs, stories, voices, logos and assets must be original or properly licensed. Do not copy protected characters, branding, dialogue, stories, voice likenesses or artwork.

## 2. Technical owner and AI coding agent role
The lead agent is accountable for the complete product and must act as:
- Principal software architect.
- Senior frontend/backend developer.
- Public open-source research engineer.
- 3D technical director.
- Character/rigging/animation pipeline engineer.
- AI and multi-provider integration engineer.
- Urdu voice and lip-sync integration engineer.
- DevOps/CI/CD engineer.
- Performance engineer.
- QA and release engineer.
- Security, privacy and licensing reviewer.
- Technical project manager.

The agent must make ordinary technical decisions independently, research alternatives and implement them. It must not merely propose tools, build mockups, write isolated code or wait for the user to describe every step. Ask the user only for decisions materially affecting cost, licensing, privacy, intellectual property or creative direction.

## 3. Full-spec compliance and traceability
Before coding, read this complete document, AGENTS.md, MASTER_PLAN.md, REQUIREMENTS_REGISTRY.md, REQUIREMENT_TRACEABILITY.md, ARCHITECTURE.md, PROJECT_STATUS.md, GITHUB_RESEARCH.md, OPEN_SOURCE_REUSE_MATRIX.md, HARDWARE_PROFILE.md, ASSET_LICENSES.md, AI_PROVIDERS.md, NEXT_STEPS.md, and relevant source/tests.

Every distinct requirement must have an ID, original meaning, priority, dependencies, implementation plan, code path, test method, evidence and status. Allowed statuses: NOT REVIEWED, RESEARCH REQUIRED, PLANNED, IN PROGRESS, IMPLEMENTED, PARTIALLY IMPLEMENTED, TESTED, VERIFIED, BLOCKED, DEFERRED WITH REASON, REJECTED WITH JUSTIFICATION.

Trace each requirement through original spec → architecture → source module → test → evidence. Code presence alone is not proof. Recheck the full registry before every phase, substantial batch, integration milestone and release. Do not use summaries as substitutes for the specification. Never silently omit, downgrade, replace with placeholders or claim untested features complete. When interrupted, resume from GitHub's latest code, original specification, registry, traceability, Actions results and checkpoints.

## 4. GitHub-first development and delivery
Primary source of truth: https://github.com/Pawar-47/Cartoon-Studio

Develop and maintain the app in this repository. Do not create a parallel repository or develop a detached local copy first. Preserve all existing progress. Use coherent, substantial feature batches, not tiny disconnected commits.

GitHub Actions must:
- Build and validate the frontend/backend.
- Install pinned or constrained dependencies.
- Run lint, static checks, unit/integration tests.
- Build/package for Windows using suitable Windows runners.
- Produce downloadable artifacts and logs.
- Support repeatable releases and failure diagnosis.

Deliver an installable Windows application or portable package with a simple launcher. The first bootstrap ZIP is not the final installer.

GitHub Actions are for source compilation, testing and packaging, not a free GPU render farm. Do not assume unlimited runner minutes, storage or GPU access. Actual episode rendering initially runs locally on the user's PC. Optional cloud rendering must be separately researched and must not be mandatory or paid without approval.

## 5. Extensive GitHub/open-source research before new development
Search public GitHub extensively by function, implementation language and architecture. Investigate:
- Existing animation studios and web-based 3D editors.
- Character creation, modeling, auto-rigging and skinning.
- Facial rigs, expressions, visemes and lip-sync.
- Motion capture, retargeting, animation blending and timeline systems.
- Procedural cartoon worlds, cities, roads, buildings, vegetation and props.
- Vehicle models and interactive vehicle animation.
- Story/script-to-scene and story-to-video systems.
- Blender automation, headless rendering and render queues.
- Urdu TTS, audio alignment, sound generation and mixing.
- FFmpeg/video assembly and subtitle systems.
- AI agent frameworks, multi-provider orchestration and research tools.
- Local-first browser apps and Windows packaging/build workflows.

For each candidate inspect complete relevant source, README/docs, branches, releases, commits/activity, issues, dependencies, build scripts, hardware requirements, tests, integration boundary, exact code license and separate model/dataset/asset licenses. Check commercial use, modification, redistribution, attribution, copyleft obligations and provenance.

Reuse hierarchy:
1. Reuse a suitable complete solution.
2. Combine compatible existing projects.
3. Adapt an existing project.
4. Build missing functionality around existing libraries.
5. Build from scratch only when no suitable solution exists.

Do not select by stars alone. Do not blindly copy entire repositories. Test promising components in small proofs of concept. Record discovered, inspected, tested, selected, integrated and rejected separately. Research must lead to implementation decisions rather than endless link collection.

## 6. Target hardware
Target PC:
- Intel Core i3-5005U.
- Intel HD Graphics 5500.
- 8 GB RAM.
- SSD.
- Windows.

Do not promise fast high-quality local rendering or large local AI models. Do not assume an NVIDIA GPU. Keep the browser UI lightweight, bound concurrency, use sequential rendering when needed, cache scenes/assets, reuse characters/environments, monitor memory/disk and resume interrupted jobs. Verify Blender and GPU compatibility; do not assume the latest Blender version works on Intel HD 5500.

Provide Preview, Low Hardware, Balanced and High Quality presets. Clearly disclose quality/performance tradeoffs. Benchmark representative scenes on the actual target PC before estimating episode-rendering time.

## 7. Application architecture
The browser is the primary interface; heavy work runs in a local backend/production engine. Candidate technologies include lightweight HTML/CSS/JS or React, Three.js, Python/FastAPI, SQLite, Blender Python API, FFmpeg, a persistent background job queue, modular AI adapters and a lightweight Windows installer/wrapper. These are candidates, not mandatory choices; use research and compatibility evidence to decide.

The browser must not be responsible for final rendering of a 5–7 minute episode. It handles editing, project management, previews, story approval, asset selection, timeline and job control. The local production engine handles scene creation, 3D animation, lighting, voice, lip-sync, audio, rendering and MP4 assembly.

## 8. Persistent cartoon universe and world builder
Create reusable, consistent locations and sets:
- Towns, neighborhoods, streets, roads, sidewalks, intersections, crossings and streetlights.
- Houses, apartments, shops, markets, restaurants and cafés.
- Schools, colleges, offices, hospitals, clinics and police stations.
- Parks, playgrounds, bus stops, garages, workshops and outdoor areas.
- Kitchens, bedrooms, living rooms, offices, corridors and other interiors.
- Furniture, household objects, trees, plants, grass, flowers, water bodies, fountains and weather effects.

Vehicle library: cars, buses, motorcycles, scooters, bicycles, trucks, vans, delivery and emergency vehicles. Support wheel rotation, steering, acceleration, braking, turning, parking, door operation, character entry/exit and interactions.

Persist world identity, building placement, layouts, materials, lighting presets, props, camera setups and scene templates. A location must remain recognizable across episodes. Reuse modular assets.

## 9. Character Studio
Create original persistent characters. Store identity/name, face, body proportions, height, hair, clothing, accessories, skin/material appearance, eyes, mouth, expressions, personality, behavior, relationships, voice profile, dialogue style and animation rig.

Support character previews, expression previews, clothing/outfit variants, import/export, saved presets and consistent reuse. Character identity must not drift between episodes. Integrate suitable existing generators and rigging systems rather than recreating them unnecessarily.

## 10. Animation system
Support reusable clips/actions: idle, walk, run, turn, jump, sit, stand, fall, laugh, cry, smile, anger, surprise, fear, confusion, thinking, blink, talking, gestures, dance, fight, wave, point, pick up, throw, open doors, drive and character interactions.

Use smooth blending and transitions, motion retargeting and reusable animation packs where licensing allows. Avoid stiff, robotic or repetitive movement. Provide camera control and shot composition.

## 11. Story and scene engine
Accept one prompt in Urdu or English and generate an original episode plan:
- Title and summary.
- Cast and relationships.
- Scene breakdown and durations.
- Natural Urdu dialogue.
- Actions, expressions and body movement.
- Locations, environment and props.
- Camera and lighting instructions.
- Music, sound effects and transitions.
- Ending.

Stories must be coherent, entertaining, character-driven, original and consistent with the persistent universe. Users can review and edit story/dialogue before production.

Convert approved stories into validated structured JSON or an equivalent versioned scene schema. Each scene records location, characters, props, dialogue, actions, expressions, animation references, camera, lighting, audio, duration and transitions. Repair invalid scene data without failing the entire episode.

## 12. Urdu language requirements
Urdu is a core requirement, not optional. Generate natural conversational Pakistani Urdu, prefer Urdu script, support RTL layout and optional Roman Urdu. Do not unintentionally substitute Hindi or mechanically translated text. Preserve script and pronunciation through TTS and subtitles. Support dialogue editing and subtitle export.

## 13. Multi-AI Resource Manager
Do not depend on one AI provider. Investigate FreeMilk by Milq, ChatGPT Free, Gemini, Claude, Microsoft Copilot, Perplexity and other suitable free applications.

For each provider verify official current model availability, free allowance, daily refill/reset, coding/research quality, file support, GitHub/browser/agent features, official API/integration, Pakistan availability, privacy, automation restrictions and terms. Date-stamp findings. Do not invent quotas or call a limited service unlimited.

Assign research, architecture, coding, review, debugging, story writing, Urdu refinement and documentation to appropriate providers. When a provider reaches its limit, recommend an alternative. Use official APIs/integrations only. If no official API exists, use manual handoffs via copyable prompts, structured files, GitHub issues/branches/PRs. Never bypass quotas, extract private APIs or automate prohibited interactions. The core app must work when all external AI services are unavailable.

## 14. Research Agent
When a feature is missing or an error occurs:
1. State the problem.
2. Search official docs, GitHub, issues, research papers and relevant technical discussions.
3. Find multiple alternatives.
4. Compare quality, hardware, license, maintenance, privacy and cost.
5. Test a proof of concept where possible.
6. Recommend and implement the best safe option.
7. Record sources, evidence, risks and results.

Do not fabricate research or tests. Obtain user approval for material cost, license, privacy or IP decisions.

## 15. Urdu voice and lip-sync
Research Urdu TTS models for Urdu-script support, Pakistani pronunciation, naturalness, emotion, speaker consistency, CPU requirements, model size, commercial rights and model-weight license. Hindi support is not proof of Urdu quality.

Support character-specific persistent voices, dialogue timing, pauses, emotions, sentence audio caching and manual recording fallback. Do not clone real voices without authorization.

Integrate lip-sync with mouth shapes/visemes, jaw movement, dialogue timing, facial expressions, blinking and head movement. Test with real Urdu speech samples. If automated Urdu phoneme alignment is weak, provide a documented fallback and never pretend it is accurate.

## 16. Audio and media
Support dialogue, background music, ambience, footsteps, vehicle sounds, object interaction, comedy effects, scene transitions and subtitles. Use original/public-domain/properly licensed audio. Keep speech intelligible and balanced. Assemble final video using FFmpeg or a verified equivalent.

## 17. Complete episode pipeline
Prompt → story generation → user approval → scene breakdown → asset preparation → animation → dialogue → voice → lip-sync → scene rendering → audio mix → subtitles → MP4 assembly → save editable project.

Implement scene-level caching, render checkpoints, persistent job queue, retry of failed scenes, safe cancellation, progress, automatic recovery after restart, memory/disk monitoring and preservation of completed renders. A failed scene must not require rerendering the entire episode.

## 18. UI workspaces
Home dashboard; Projects; Story Generator; Character Studio; World Builder; Asset Library; Animation Library; Voice Studio; Scene Editor; Timeline; 3D Preview; Episode Renderer; Research Agent; AI Resource Manager; Settings; Logs/Diagnostics.

Every visible control must work or be explicitly marked planned. Avoid decorative fake controls. Provide clear progress and actionable errors.

## 19. Asset and dependency management
Central asset library for characters, rigs, animations, buildings, furniture, vehicles, props, textures, materials, audio, music, environments, lighting and scene templates. Support suitable formats such as GLB/glTF and other formats supported by the selected engine.

Record source URL, author, version, license, commercial rights, modification/redistribution rights, attribution, checksum and modifications. Avoid unnecessary duplication and unsafe downloads. Keep generated media and caches outside Git history by default.

## 20. Offline and cost policy
After dependencies/assets are downloaded, project management, characters, world building, scene editing, rendering and video assembly should work offline. Internet is optional for research and external AI services. No mandatory paid API, subscription, cloud inference, daily/monthly credits, cloud rendering or online activation. Obtain approval before adding paid dependencies.

## 21. Reliability and project persistence
Autosave, versioned project metadata, persistent job queue, render caching, crash recovery, asset versioning, dependency registry, memory/disk monitoring, safe cancellation, resume after restart, portable projects and no automatic deletion of user work.

## 22. GitHub documentation
Maintain MASTER_PLAN.md, ARCHITECTURE.md, PROJECT_STATUS.md, REQUIREMENTS_REGISTRY.md, REQUIREMENT_TRACEABILITY.md, GITHUB_RESEARCH.md, REPOSITORY_EVALUATION.md, OPEN_SOURCE_REUSE_MATRIX.md, RESEARCH_LOG.md, DECISION_LOG.md, HARDWARE_PROFILE.md, AI_PROVIDERS.md, ASSET_LICENSES.md, BUILD_AND_INSTALL.md, TEST_REPORT.md and NEXT_STEPS.md. Keep documents synchronized with real source and tests.

## 23. Development phases
P0: full spec and registry, traceability, extensive GitHub research, licensing and architecture.  
P1: repository, local app foundation, CI, Windows bootstrap artifact.  
P2: character studio, rigging and persistence.  
P3: persistent world builder and reusable assets.  
P4: story engine, Urdu dialogue and scene schema.  
P5: animation, camera and facial expression.  
P6: Urdu TTS, audio and lip-sync.  
P7: complete episode renderer, scene cache, MP4 and editable project.  
P8: hardware optimization, reliability, installation and final QA.

Work in complete, coherent batches. For each batch review requirements, dependencies and relevant source; research where necessary; implement; run tests; inspect output; fix issues; commit/push; update docs and traceability.

## 24. QA and final acceptance
Test installation, startup, browser UI, backend, project save/load, character/world persistence, scene generation, animation, Urdu text, TTS, lip-sync, scene rendering, audio, MP4, restart/recovery, CI and Windows installation. Inspect real rendered frames/videos for consistency, motion, facial expression, lip-sync, camera, lighting, dialogue and audio.

The project is not complete until there is:
- A working GitHub repository and full source.
- Extensively researched and documented open-source reuse.
- Verified licenses and provenance.
- Complete requirement traceability.
- Working GitHub Actions pipeline and Windows artifact.
- Working Windows installation.
- Browser-based local studio.
- Persistent original characters and environments.
- Functional animation library.
- One-prompt story generation and natural Urdu dialogue.
- Character voices or documented working fallback.
- Tested lip-sync or clearly documented limitation.
- Actual 3D rendering and complete MP4 assembly.
- Scene caching and recovery.
- Benchmarked target-hardware performance.
- No mandatory paid service.
- Actual test evidence.

A UI mockup, source code presence, green compile, or isolated demo is not by itself proof of a complete production system.
