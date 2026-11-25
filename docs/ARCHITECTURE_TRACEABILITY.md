# Architecture Traceability Crosswalk

**Checkpoint:** 2026-11-25; main HEAD facb0dd738e227d643d4e85d80bd5d3f620fc6e1.
**Purpose:** map every atomic requirement in the 171-row registry to an architecture owner, planned module boundary and delivery phase. This supplements—not replaces—the original requirement text, dependencies, test method, evidence and status in REQUIREMENTS_REGISTRY.md and REQUIREMENT_TRACEABILITY.md.

## Rules
- IDs and requirement wording below are copied from the registry; source and priority remain authoritative there.
- Paths are planned module boundaries, not claims that modules already exist. Current implementation remains FastAPI/SQLite project and story-plan foundation plus static browser UI.
- A requirement is not implemented or verified merely because it has a target path.
- Physical-PC performance measurements are Phase 8 evidence only. They do not gate P0.5/P0.6/P0.7, Phase 1, or feature implementation.
- New third-party code, models, voices or assets require provenance/license review before adoption.

## Complete 171-row crosswalk

| ID | Priority | Atomic requirement | Architecture home | Planned module boundary | Delivery phase |
|---|---|---|---|---|---|
| GOV-R001 | Critical | Treat the complete 25-part master brief as the binding execution contract. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R002 | Critical | Maintain a permanent registry with unique IDs and original source references. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R003 | Critical | Record priority, dependencies, implementation, test method, result, evidence and limitations for every atomic requirement. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R004 | Critical | Keep every requirement open until verified, reasoned-deferred or justified-rejected. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R005 | Critical | Use only the defined lifecycle statuses and never equate code presence with verification. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R006 | Critical | Re-scan full registry before architecture, each phase and substantial batch, integration, phase completion and release. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R007 | Critical | Trace each requirement through architecture, source modules, implementation, test and evidence. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R008 | High | On resume, inspect live GitHub HEAD, source brief, plans, status, registry, traceability, tests and active-batch code. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R009 | Critical | Do not start production features before Phase 0 research and architecture freeze. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| GOV-R010 | Critical | Deliver working product outcomes, not activity, code volume, mockups or documentation alone. | §10 Governance and evidence | docs/MASTER_EXECUTION_PROMPT.md; docs/MASTER_PLAN.md; docs/PROJECT_STATUS.md; docs/REQUIREMENTS_REGISTRY.md; docs/REQUIREMENT_TRACEABILITY.md | P0 / all phases |
| ROLE-R001 | Critical | Own end-to-end architecture and integration across all product subsystems. | §2 Application services | docs/ARCHITECTURE.md; app/services/; app/engine/ | all phases |
| ROLE-R002 | High | Own frontend, backend, database, APIs and usable UX delivery. | §2 Application services | docs/ARCHITECTURE.md; app/services/; app/engine/ | all phases |
| ROLE-R003 | Critical | Own open-source research, 3D direction, AI integration and animation pipeline decisions. | §2 Application services | docs/ARCHITECTURE.md; app/services/; app/engine/ | all phases |
| ROLE-R004 | Critical | Own CI/CD, Windows packaging, target-hardware performance and QA. | §2 Application services | docs/ARCHITECTURE.md; app/services/; app/engine/ | all phases |
| ROLE-R005 | High | Own security, licensing, project planning, checkpoints and continuity. | §2 Application services | docs/ARCHITECTURE.md; app/services/; app/engine/ | all phases |
| VISION-R001 | Critical | Build an original reusable 3D cartoon-production studio, not a one-off video generator. | §1 Product boundary | docs/PROJECT_SPECIFICATION.md; docs/ARCHITECTURE.md; app/ | all phases |
| VISION-R002 | Critical | Generate an original story from one user prompt. | §1 Product boundary | docs/PROJECT_SPECIFICATION.md; docs/ARCHITECTURE.md; app/ | all phases |
| VISION-R003 | Critical | Generate natural Pakistani Urdu dialogue with English prompt support. | §1 Product boundary | docs/PROJECT_SPECIFICATION.md; docs/ARCHITECTURE.md; app/ | all phases |
| VISION-R004 | Critical | Reuse established characters and locations across episodes. | §1 Product boundary | docs/PROJECT_SPECIFICATION.md; docs/ARCHITECTURE.md; app/ | all phases |
| VISION-R005 | Critical | Automatically create scenes, animate characters and synchronize voice/facial motion. | §1 Product boundary | docs/PROJECT_SPECIFICATION.md; docs/ARCHITECTURE.md; app/ | all phases |
| VISION-R006 | Critical | Assemble and export an editable 5–7 minute MP4 episode. | §1 Product boundary | docs/PROJECT_SPECIFICATION.md; docs/ARCHITECTURE.md; app/ | all phases |
| GIT-R001 | Critical | Use Pawar-47/Cartoon-Studio as the source of truth. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R002 | Critical | Keep frontend, backend, configs, tests, workflows, packaging and documentation in GitHub. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R003 | High | Do not commit generated videos, caches, temporary files or large model weights unnecessarily. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R004 | Critical | Use GitHub Actions for dependency setup, frontend/backend build, tests and static analysis. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R005 | Critical | Package repeatable Windows artifacts and retain logs and failure diagnostics. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R006 | Critical | Deliver a simple Windows launcher and installer that configures required dependencies. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R007 | High | Keep browser as primary UX and heavy rendering local on the user's Windows machine. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| GIT-R008 | Critical | Do not treat GitHub-hosted CI as an unlimited GPU render farm or require paid cloud rendering. | §11 CI/CD and release | .github/workflows/; scripts/; app/; docs/BUILD_AND_INSTALL.md | P0–P1 |
| OSS-R001 | Critical | Search public GitHub by subsystem before implementing major functionality. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R002 | Critical | Inspect candidate README, docs and complete relevant source structure. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R003 | High | Inspect candidate releases, versions, commits, activity and issues. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R004 | Critical | Inspect dependencies, hardware requirements, software/model/asset licenses. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R005 | High | Assess maintainability and integration complexity, not popularity alone. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R006 | Critical | Test candidate functionality where practical and classify reuse/adapt/wrap/build. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R007 | High | Follow reuse hierarchy: complete solution, combine, adapt, wrap libraries, then scratch. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| OSS-R008 | High | Publish research, evaluation, reuse matrix and asset-license records. | §12 Reuse and license controls | docs/GITHUB_RESEARCH.md; docs/REPOSITORY_EVALUATION.md; docs/OPEN_SOURCE_REUSE_MATRIX.md; docs/ASSET_LICENSES.md | P0 / refresh at adoption |
| HW-R001 | Critical | Support Intel Core i3-5005U CPU as target baseline. | §13 Runtime profiles and Phase 8 | app/runtime/capabilities.py; app/rendering/profiles.py; scripts/; docs/HARDWARE_PROFILE.md | P0 policy; P8 measurement |
| HW-R002 | Critical | Support Intel HD Graphics 5500 without requiring NVIDIA GPU. | §13 Runtime profiles and Phase 8 | app/runtime/capabilities.py; app/rendering/profiles.py; scripts/; docs/HARDWARE_PROFILE.md | P0 policy; P8 measurement |
| HW-R003 | Critical | Operate within 8 GB RAM and SSD constraints using low-memory processing. | §13 Runtime profiles and Phase 8 | app/runtime/capabilities.py; app/rendering/profiles.py; scripts/; docs/HARDWARE_PROFILE.md | P0 policy; P8 measurement |
| HW-R004 | Critical | Provide CPU-compatible options and avoid mandatory discrete GPU. | §13 Runtime profiles and Phase 8 | app/runtime/capabilities.py; app/rendering/profiles.py; scripts/; docs/HARDWARE_PROFILE.md | P0 policy; P8 measurement |
| HW-R005 | High | Provide Preview, Low Hardware, Balanced and High Quality presets without silently removing features. | §13 Runtime profiles and Phase 8 | app/runtime/capabilities.py; app/rendering/profiles.py; scripts/; docs/HARDWARE_PROFILE.md | P0 policy; P8 measurement |
| HW-R006 | High | Benchmark representative scenes before making render-time or quality promises. | §13 Runtime profiles and Phase 8 | app/runtime/capabilities.py; app/rendering/profiles.py; scripts/; docs/HARDWARE_PROFILE.md | P0 policy; P8 measurement |
| ARCH-R001 | Critical | Build a lightweight local-first web application with browser as main interface. | §2–§8 Application and adapters | app/main.py; app/services/; app/engine/; app/persistence/; app/jobs/ | P0–P1 foundation |
| ARCH-R002 | Critical | Use a backend for scene generation, animation, rendering, dialogue, lip-sync, audio and assembly. | §2–§8 Application and adapters | app/main.py; app/services/; app/engine/; app/persistence/; app/jobs/ | P0–P1 foundation |
| ARCH-R003 | Critical | Evaluate frontend, 3D preview, backend, database, production engine, video and queue technologies as candidates. | §2–§8 Application and adapters | app/main.py; app/services/; app/engine/; app/persistence/; app/jobs/ | P0–P1 foundation |
| ARCH-R004 | High | Keep production engine and project data contracts engine-neutral where possible. | §2–§8 Application and adapters | app/main.py; app/services/; app/engine/; app/persistence/; app/jobs/ | P0–P1 foundation |
| ARCH-R005 | Critical | Keep browser preview separate from full episode rendering. | §2–§8 Application and adapters | app/main.py; app/services/; app/engine/; app/persistence/; app/jobs/ | P0–P1 foundation |
| ARCH-R006 | High | Provide persistent local data and modular provider adapters. | §2–§8 Application and adapters | app/main.py; app/services/; app/engine/; app/persistence/; app/jobs/ | P0–P1 foundation |
| WORLD-R001 | Critical | Create persistent towns, neighborhoods and reusable location identities. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R002 | High | Support roads, intersections, streets, sidewalks and bus stops. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R003 | High | Support houses, apartments, shops, markets, restaurants and cafés. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R004 | High | Support schools, colleges, offices, hospitals and police stations. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R005 | High | Support parks, playgrounds, garages and indoor rooms such as kitchens and bedrooms. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R006 | High | Support furniture, vegetation, water bodies, streetlights and environmental props. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R007 | High | Provide reusable cars, buses, motorcycles, scooters, bicycles, trucks, vans and emergency vehicles. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R008 | High | Vehicles support steering, wheel rotation, acceleration, braking, turning and parking. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R009 | Medium | Vehicles support doors and character interaction where appropriate. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| WORLD-R010 | Critical | Persist world layout, building placement, materials, props and locations across episodes. | §3 World domain | app/world/; app/assets/; app/engine/; projects/<id>/worlds/ | P3 |
| CHAR-R001 | Critical | Create and import original reusable characters. | §3 Character domain | app/characters/; app/assets/characters/; app/engine/; projects/<id>/characters/ | P2 |
| CHAR-R002 | High | Store persistent character name, face design, body proportions and height. | §3 Character domain | app/characters/; app/assets/characters/; app/engine/; projects/<id>/characters/ | P2 |
| CHAR-R003 | High | Store hair, clothing, accessories, eyes, mouth and expression design. | §3 Character domain | app/characters/; app/assets/characters/; app/engine/; projects/<id>/characters/ | P2 |
| CHAR-R004 | High | Store personality, relationships, voice profile and dialogue style. | §3 Character domain | app/characters/; app/assets/characters/; app/engine/; projects/<id>/characters/ | P2 |
| CHAR-R005 | Critical | Support animation rigging, preview, import and export. | §3 Character domain | app/characters/; app/assets/characters/; app/engine/; projects/<id>/characters/ | P2 |
| CHAR-R006 | Critical | Preserve character visual identity and consistency across episodes. | §3 Character domain | app/characters/; app/assets/characters/; app/engine/; projects/<id>/characters/ | P2 |
| ANIM-R001 | High | Provide reusable idle, walk, run, turn, jump, sit, stand and fall animations. | §4 Animation domain | app/animation/; app/engine/; app/assets/animations/ | P5 |
| ANIM-R002 | High | Provide laugh, cry, smile, anger, surprise, fear, confusion and thinking expressions/actions. | §4 Animation domain | app/animation/; app/engine/; app/assets/animations/ | P5 |
| ANIM-R003 | High | Provide blinking, talking, gestures, waving, pointing and dancing. | §4 Animation domain | app/animation/; app/engine/; app/assets/animations/ | P5 |
| ANIM-R004 | High | Provide fighting, object pickup/throw, door opening, driving and character interactions. | §4 Animation domain | app/animation/; app/engine/; app/assets/animations/ | P5 |
| ANIM-R005 | Critical | Blend animations and transition smoothly without robotic movement. | §4 Animation domain | app/animation/; app/engine/; app/assets/animations/ | P5 |
| ANIM-R006 | High | Support motion retargeting and properly licensed animation assets. | §4 Animation domain | app/animation/; app/engine/; app/assets/animations/ | P5 |
| STORY-R001 | Critical | Accept one Urdu or English prompt and produce an original story. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R002 | High | Generate title, summary, character list and relationships. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R003 | Critical | Generate scene breakdown and scene durations. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R004 | Critical | Generate natural Pakistani Urdu dialogue and support Urdu script. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R005 | Critical | Support correct RTL rendering and optional Roman Urdu. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R006 | High | Generate actions, expressions and animation instructions per scene. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R007 | High | Generate environment, props, camera directions, music and sound effects. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R008 | High | Generate transitions and a coherent ending. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R009 | Critical | Keep stories original, coherent, entertaining and consistent with established characters. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R010 | Critical | Allow story and dialogue editing and explicit user approval before production. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R011 | Critical | Convert story into validated structured scenes with location, cast, props, dialogue, actions, camera, lighting, audio, duration and transitions. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| STORY-R012 | Critical | Repair invalid scene data rather than fail the entire episode. | §3 Story and scene contracts | app/story.py; app/story/; app/scenes/; app/static/story.* | P4 |
| AI-R001 | High | Support modular adapters for multiple AI providers rather than one provider dependency. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R002 | High | Research FreeMilk, ChatGPT Free, Gemini, Claude, Copilot, Perplexity and suitable alternatives. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R003 | Critical | Verify actual free quotas, refill schedules, Pakistan availability, terms and automation permissions. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R004 | Medium | Route research, architecture, coding, review, debugging, stories, Urdu refinement, docs and test planning to suitable tools. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R005 | High | When a provider limit is reached, suggest another legitimate provider without bypassing limits. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R006 | Critical | Use official APIs/supported integrations only; never extract unauthorized APIs or bypass quotas. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R007 | High | Support manual copy/paste handoffs where APIs are unavailable. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| AI-R008 | Critical | Keep core application functional without online AI services. | §8 Provider adapters | app/providers/; app/ai/; app/static/; docs/AI_PROVIDERS.md | P0 research; P1/P4/P6 integrations |
| RES-R001 | High | Identify technical problems and search official documentation. | §8 Research workflow | app/research/; app/providers/; docs/GITHUB_RESEARCH.md; docs/RESEARCH_LOG.md | P0 / P1 onward |
| RES-R002 | High | Search GitHub repositories, issues, discussions and technical research. | §8 Research workflow | app/research/; app/providers/; docs/GITHUB_RESEARCH.md; docs/RESEARCH_LOG.md | P0 / P1 onward |
| RES-R003 | Critical | Compare multiple solutions by capability, compatibility, license, maintenance, cost and hardware. | §8 Research workflow | app/research/; app/providers/; docs/GITHUB_RESEARCH.md; docs/RESEARCH_LOG.md | P0 / P1 onward |
| RES-R004 | High | Test practical alternatives, recommend, implement when appropriate and record evidence/outcomes. | §8 Research workflow | app/research/; app/providers/; docs/GITHUB_RESEARCH.md; docs/RESEARCH_LOG.md | P0 / P1 onward |
| RES-R005 | Critical | Never fabricate research or tests; ask approval for consequential money, license, privacy or IP decisions. | §8 Research workflow | app/research/; app/providers/; docs/GITHUB_RESEARCH.md; docs/RESEARCH_LOG.md | P0 / P1 onward |
| VOICE-R001 | Critical | Evaluate Urdu-script TTS and Pakistani pronunciation, not Hindi support as a proxy. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R002 | Critical | Evaluate TTS naturalness, emotion, speaker consistency, size, CPU, license and commercial rights. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R003 | High | Provide persistent character-specific voice profiles, dialogue timing, pauses and emotions. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R004 | High | Provide manual recording fallback and prohibit unauthorized real-person voice cloning. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R005 | Critical | Implement lip-sync with mouth shapes/visemes, jaw movement and dialogue timing. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R006 | High | Coordinate facial expressions, blinking and head movement with dialogue. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R007 | High | Support dialogue, music, ambience, footsteps, vehicle/object sounds, comedy effects and transitions. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| VOICE-R008 | Critical | Keep speech intelligible and balanced; use original/public-domain/properly licensed audio. | §7 Voice and lip-sync | app/voice/; app/audio/; app/lipsync/; app/characters/ | P6 |
| PROD-R001 | Critical | Implement prompt → story → approval → scene breakdown → asset preparation pipeline. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R002 | Critical | Implement character animation, Urdu dialogue, voice, lip-sync and scene rendering stages. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R003 | Critical | Implement audio mixing and FFmpeg or verified equivalent final MP4 assembly. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R004 | Critical | Target final episodes approximately 5–7 minutes. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R005 | Critical | Preserve editable scene/project data alongside final video. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R006 | Critical | Use scene-level caching and render checkpoints. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R007 | Critical | Use persistent job queue, retry failed scenes and safely cancel jobs. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R008 | Critical | Recover after restart and preserve completed scene renders. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| PROD-R009 | High | Report progress and monitor memory/disk during production. | §6 Jobs and media assembly | app/jobs/; app/rendering/; app/audio/; app/media/; app/persistence/ | P7 |
| UX-R001 | High | Provide Home Dashboard and Projects workspaces. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R002 | High | Provide Story Generator and Character Studio workspaces. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R003 | High | Provide World Builder, Asset Library and Animation Library workspaces. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R004 | High | Provide Voice Studio, Scene Editor, Timeline and 3D Preview. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R005 | High | Provide Episode Renderer, Research Agent and AI Resource Manager. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R006 | High | Provide Settings, Logs and Diagnostics. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R007 | Critical | Every visible control must work or be explicitly marked planned; no fake controls. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| UX-R008 | High | Show meaningful progress and actionable errors. | §2 Browser interface | app/static/; app/main.py; app/ui/ | P1–P7 |
| LIC-R001 | Critical | Maintain central library for characters, rigs, animations, buildings, furniture, vehicles, props and textures. | §9 Licensing and provenance | docs/ASSET_LICENSES.md; third_party/licenses/; app/assets/manifest.json | P0 and every adoption |
| LIC-R002 | High | Maintain materials, audio, music, environments and scene templates in the library. | §9 Licensing and provenance | docs/ASSET_LICENSES.md; third_party/licenses/; app/assets/manifest.json | P0 and every adoption |
| LIC-R003 | High | Support GLB/glTF and other formats selected by the engine research. | §9 Licensing and provenance | docs/ASSET_LICENSES.md; third_party/licenses/; app/assets/manifest.json | P0 and every adoption |
| LIC-R004 | Critical | Record source URL, author, version, license and commercial-use rights for every third-party asset. | §9 Licensing and provenance | docs/ASSET_LICENSES.md; third_party/licenses/; app/assets/manifest.json | P0 and every adoption |
| LIC-R005 | Critical | Record modification, redistribution, attribution, checksum and modification history. | §9 Licensing and provenance | docs/ASSET_LICENSES.md; third_party/licenses/; app/assets/manifest.json | P0 and every adoption |
| LIC-R006 | Critical | Use original or appropriately licensed creative elements; never silently include unclear rights. | §9 Licensing and provenance | docs/ASSET_LICENSES.md; third_party/licenses/; app/assets/manifest.json | P0 and every adoption |
| OFF-R001 | Critical | Do not require paid APIs, subscriptions or mandatory cloud inference. | §8 Offline operation | app/providers/; app/config/; app/persistence/; app/rendering/ | P1–P7 |
| OFF-R002 | Critical | Do not require daily/monthly AI credits or online activation. | §8 Offline operation | app/providers/; app/config/; app/persistence/; app/rendering/ | P1–P7 |
| OFF-R003 | Critical | Do not require cloud rendering. | §8 Offline operation | app/providers/; app/config/; app/persistence/; app/rendering/ | P1–P7 |
| OFF-R004 | Critical | After dependencies/assets are downloaded, core production should work offline. | §8 Offline operation | app/providers/; app/config/; app/persistence/; app/rendering/ | P1–P7 |
| OFF-R005 | High | Identify optional online features and obtain approval before paid dependencies. | §8 Offline operation | app/providers/; app/config/; app/persistence/; app/rendering/ | P1–P7 |
| REL-R001 | Critical | Autosave projects and maintain versioned project metadata. | §5 Persistence and recovery | app/persistence/; app/jobs/; app/cache/; app/assets/ | P1/P7/P8 |
| REL-R002 | Critical | Maintain persistent job queue and resumable production jobs. | §5 Persistence and recovery | app/persistence/; app/jobs/; app/cache/; app/assets/ | P1/P7/P8 |
| REL-R003 | Critical | Cache renders and preserve completed outputs. | §5 Persistence and recovery | app/persistence/; app/jobs/; app/cache/; app/assets/ | P1/P7/P8 |
| REL-R004 | Critical | Support crash recovery, safe cancellation and memory/disk monitoring. | §5 Persistence and recovery | app/persistence/; app/jobs/; app/cache/; app/assets/ | P1/P7/P8 |
| REL-R005 | High | Version assets and dependencies; preserve portable projects. | §5 Persistence and recovery | app/persistence/; app/jobs/; app/cache/; app/assets/ | P1/P7/P8 |
| REL-R006 | Critical | Never automatically delete user work or destructive-reset existing progress. | §5 Persistence and recovery | app/persistence/; app/jobs/; app/cache/; app/assets/ | P1/P7/P8 |
| DOC-R001 | Critical | Maintain MASTER_PLAN, ARCHITECTURE, PROJECT_STATUS, REQUIREMENTS_REGISTRY and REQUIREMENT_TRACEABILITY. | §10 Documentation | docs/; README.md; docs/BUILD_AND_INSTALL.md | all phases |
| DOC-R002 | High | Maintain GITHUB_RESEARCH, REPOSITORY_EVALUATION, OPEN_SOURCE_REUSE_MATRIX and RESEARCH_LOG. | §10 Documentation | docs/; README.md; docs/BUILD_AND_INSTALL.md | all phases |
| DOC-R003 | High | Maintain DECISION_LOG, HARDWARE_PROFILE, AI_PROVIDERS and ASSET_LICENSES. | §10 Documentation | docs/; README.md; docs/BUILD_AND_INSTALL.md | all phases |
| DOC-R004 | High | Maintain BUILD_AND_INSTALL, TEST_REPORT and NEXT_STEPS. | §10 Documentation | docs/; README.md; docs/BUILD_AND_INSTALL.md | all phases |
| DOC-R005 | Critical | PROJECT_STATUS must distinguish implemented, partial, not implemented, test outcomes, untested, blocked, deferred and next batch. | §10 Documentation | docs/; README.md; docs/BUILD_AND_INSTALL.md | all phases |
| DOC-R006 | Critical | Keep all documents synchronized with actual source and test evidence. | §10 Documentation | docs/; README.md; docs/BUILD_AND_INSTALL.md | all phases |
| PHASE-R001 | Critical | Complete Phase 0 specification, registry, research, licensing and architecture before production feature work. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R002 | Critical | Phase 1 delivers repository, app foundation, CI, tests, Windows artifact and verified installation. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R003 | Critical | Phase 2 delivers character generation/import, rigging, profiles, persistence and export. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R004 | Critical | Phase 3 delivers persistent environments, buildings, streets, vehicles, props and locations. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R005 | Critical | Phase 4 delivers prompt/story generation, Urdu dialogue, structured scenes and approval/editing. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R006 | Critical | Phase 5 delivers animation, expressions, transitions, camera and scene transitions. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R007 | Critical | Phase 6 delivers Urdu TTS, character voices, audio, lip-sync and recording fallback. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R008 | Critical | Phase 7 delivers complete episode generation, rendering, audio mix, MP4 and editable project. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| PHASE-R009 | Critical | Phase 8 delivers optimization, recovery, final installation and acceptance. | §10 Phase sequencing | docs/MASTER_PLAN.md; docs/EXECUTION_BATCH_PLAN.md; docs/PROJECT_STATUS.md | all phases |
| BATCH-R001 | Critical | Work in complete features or substantial related groups, not endless tiny disconnected edits. | §10 Batch execution | docs/EXECUTION_BATCH_PLAN.md; docs/NEXT_STEPS.md; docs/TEST_REPORT.md | all phases |
| BATCH-R002 | Critical | For each batch inspect requirements, dependencies, research, affected modules and configurations before implementation. | §10 Batch execution | docs/EXECUTION_BATCH_PLAN.md; docs/NEXT_STEPS.md; docs/TEST_REPORT.md | all phases |
| BATCH-R003 | Critical | Run tests, inspect actual output, fix issues, then commit/push and update docs. | §10 Batch execution | docs/EXECUTION_BATCH_PLAN.md; docs/NEXT_STEPS.md; docs/TEST_REPORT.md | all phases |
| BATCH-R004 | High | Do not stop after planning when implementation is possible, and do not stall in validation-only cycles. | §10 Batch execution | docs/EXECUTION_BATCH_PLAN.md; docs/NEXT_STEPS.md; docs/TEST_REPORT.md | all phases |
| BATCH-R005 | Critical | Commit and push one completed batch; do not commit trivial intermediate changes. | §10 Batch execution | docs/EXECUTION_BATCH_PLAN.md; docs/NEXT_STEPS.md; docs/TEST_REPORT.md | all phases |
| QA-R001 | Critical | Test installation, startup, browser UI, backend communication and project create/save/load. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R002 | Critical | Test character and world persistence, scene generation and animation playback. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R003 | Critical | Test Urdu rendering, TTS, lip-sync and audio mixing. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R004 | Critical | Test scene rendering, MP4 assembly and full episode duration. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R005 | Critical | Test restart/recovery, CI and Windows installer. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R006 | Critical | Inspect real frames/videos for consistency, motion, expression, lip-sync, camera, lighting, dialogue and continuity. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R007 | Critical | Demonstrate extensive open-source research and verified third-party licenses. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R008 | Critical | Demonstrate complete requirement traceability and no mandatory paid service. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R009 | Critical | Deliver persistent original characters, reusable environments and functional animation library. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R010 | Critical | Deliver one-prompt stories, natural Urdu, character voices or documented fallback, and lip-sync or explicit limitation. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R011 | Critical | Deliver actual 3D rendering, complete MP4, editable project, scene caching and recovery. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R012 | Critical | Demonstrate practical target-hardware performance and successful Windows installation. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |
| QA-R013 | Critical | Maintain a working GitHub repo, complete source, Actions pipeline and Windows artifact. | §11 CI and acceptance | tests/; .github/workflows/; docs/TEST_REPORT.md | all phases |

## Audit result
- Registry rows: 171.
- Crosswalk rows: 171.
- Missing IDs: none.
- Duplicate IDs in source registry: none.
- This is a complete domain/module ownership map. Individual source paths and tests must replace planned paths as each subsystem is implemented before requirements can advance to IMPLEMENTED, TESTED or VERIFIED.
- Hardware requirements remain active product constraints. Exact-PC benchmark tests are retained for Phase 8 but are not prerequisites for architecture freeze or phase progression.
