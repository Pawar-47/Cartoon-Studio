# Requirements Registry
Statuses: NOT REVIEWED, RESEARCH REQUIRED, PLANNED, IN PROGRESS, IMPLEMENTED, PARTIALLY IMPLEMENTED, TESTED, VERIFIED, BLOCKED, DEFERRED WITH REASON, REJECTED WITH JUSTIFICATION.

**Coverage warning:** this is an initial requirement inventory, not yet the complete P0.2 decomposition. Some rows still combine multiple specification sub-requirements and do not yet have their own dependency, implementation, test and evidence fields. The traceability matrix currently maps only the inspected subset. Do not treat this registry as complete until every specification requirement and acceptance bullet has a one-to-one traceability row.

| ID | Requirement | Priority | Status |
|---|---|---|---|
| GOV-001 | Read entire specification before coding | Critical | TESTED |
| GOV-002 | Maintain permanent requirement registry | Critical | IMPLEMENTED |
| GOV-003 | Trace requirements to architecture, code, tests and evidence | Critical | PARTIALLY IMPLEMENTED |
| GOV-004 | Recheck requirements before every phase, batch and release | Critical | PLANNED |
| GOV-005 | Never silently omit, downgrade or fake requirements | Critical | PLANNED |
| GOV-006 | Resume from specification, registry, code and checkpoints | High | IN PROGRESS |
| GIT-001 | Use Pawar-47/Cartoon-Studio as source of truth | Critical | IMPLEMENTED |
| GIT-002 | Develop and maintain source in GitHub | Critical | IN PROGRESS |
| GIT-003 | GitHub Actions build, test and Windows package | Critical | TESTED |
| GIT-004 | Produce downloadable Windows artifacts | High | TESTED |
| GIT-005 | Verify installation on user's Windows PC | Critical | NOT REVIEWED |
| GIT-006 | Keep episode rendering separate from CI runners | High | PLANNED |
| OSS-001 | Search public GitHub extensively before building components | Critical | IN PROGRESS |
| OSS-002 | Inspect source, docs, releases, issues, activity and dependencies | Critical | RESEARCH REQUIRED |
| OSS-003 | Verify software, model, dataset and asset licenses | Critical | RESEARCH REQUIRED |
| OSS-004 | Prefer reuse/integration/adaptation before scratch development | Critical | PLANNED |
| OSS-005 | Record source, version, author, license and provenance | High | IN PROGRESS |
| HW-001 | Support Intel Core i3-5005U | Critical | PLANNED |
| HW-002 | Support Intel HD Graphics 5500 without NVIDIA requirement | Critical | PLANNED |
| HW-003 | Operate within 8 GB RAM using low-memory/sequential processing | Critical | PLANNED |
| HW-004 | Benchmark actual scenes before performance promises | High | PLANNED |
| HW-005 | Preview, Low Hardware, Balanced and High Quality presets | High | PLANNED |
| APP-001 | Lightweight browser-based application | Critical | TESTED |
| APP-002 | Local backend and persistent SQLite project metadata | High | TESTED |
| APP-003 | Dashboard, project creation and listing | High | TESTED |
| APP-004 | Story Generator workspace | High | TESTED |
| APP-005 | Character Studio workspace | High | PLANNED |
| APP-006 | World Builder workspace | High | PLANNED |
| APP-007 | Asset Library workspace | High | PLANNED |
| APP-008 | Animation, Timeline and Scene Editor | High | PLANNED |
| APP-009 | Voice Studio and Episode Renderer | High | PLANNED |
| APP-010 | Research Agent and AI Resource Manager | High | PLANNED |
| WORLD-001 | Persistent original town, neighborhoods and locations | Critical | PLANNED |
| WORLD-002 | Reusable streets, buildings, shops, schools, parks and interiors | High | PLANNED |
| WORLD-003 | Reusable vehicles and interactive movement | High | PLANNED |
| WORLD-004 | Persistent layouts, props, materials and scene templates | High | PLANNED |
| WORLD-005 | Validate temporary Ara-derived location IDs in the early Story Generator prototype | High | PARTIALLY IMPLEMENTED |
| CHAR-001 | Create and save original reusable characters | Critical | PLANNED |
| CHAR-002 | Persistent face, body, clothing, hair and accessories | High | PLANNED |
| CHAR-003 | Personality, relationships, voice and dialogue profiles | High | PLANNED |
| CHAR-004 | Rigging, preview, import and export | Critical | PLANNED |
| ANIM-001 | Reusable body animation library | Critical | PLANNED |
| ANIM-002 | Facial expressions, blinking, talking and gestures | High | PLANNED |
| ANIM-003 | Smooth transitions, blending and retargeting | High | PLANNED |
| ANIM-004 | Validate temporary Ara-derived action IDs in the early Story Generator prototype | High | PARTIALLY IMPLEMENTED |
| ANIM-005 | Validate temporary Ara-derived expression IDs in the early Story Generator prototype | High | PARTIALLY IMPLEMENTED |
| STORY-001 | One-prompt original story generation in Urdu or English | Critical | PARTIALLY IMPLEMENTED |
| STORY-002 | Title, summary, cast, scenes, actions, camera and audio plan | High | PARTIALLY IMPLEMENTED |
| STORY-003 | Natural conversational Pakistani Urdu | Critical | PARTIALLY IMPLEMENTED |
| STORY-004 | Urdu script, RTL and optional Roman Urdu | Critical | PARTIALLY IMPLEMENTED |
| STORY-005 | Edit and approve story before production | High | PARTIALLY IMPLEMENTED |
| STORY-006 | Validate scene data and repair/recover invalid output | High | PARTIALLY IMPLEMENTED |
| AI-001 | Modular multi-provider AI architecture | High | PLANNED |
| AI-002 | Verify free quotas, refill cycles, terms and Pakistan availability | High | PLANNED |
| AI-003 | Manual AI copy/paste handoff for providers without an approved API | High | PARTIALLY IMPLEMENTED |
| AI-004 | Never bypass quotas or use unauthorized APIs | Critical | PLANNED |
| RES-001 | Research agent searches docs, GitHub, issues and alternatives | High | PLANNED |
| RES-002 | Compare capability, compatibility, license, cost and hardware | High | PLANNED |
| RES-003 | Record evidence; never fabricate tests | Critical | PLANNED |
| VOICE-001 | Evaluate Urdu TTS and Pakistani pronunciation | Critical | RESEARCH REQUIRED |
| VOICE-002 | Persistent character-specific voice profiles | High | PLANNED |
| VOICE-003 | Manual recording fallback | High | PLANNED |
| FACE-001 | Lip-sync, visemes, mouth shapes and dialogue timing | Critical | RESEARCH REQUIRED |
| AUDIO-001 | Dialogue, music, ambience and sound effects | High | PLANNED |
| PROD-001 | Complete prompt-to-MP4 production pipeline | Critical | PLANNED |
| PROD-002 | Approximately 5–7 minute episodes | Critical | PLANNED |
| PROD-003 | Preserve editable scene and project data | High | PLANNED |
| PROD-004 | Scene cache, retry, resume and recovery | Critical | PLANNED |
| PROD-005 | FFmpeg or equivalent final assembly | High | RESEARCH REQUIRED |
| UX-001 | Every visible control works or is marked planned | Critical | PARTIALLY IMPLEMENTED |
| UX-002 | Clear progress, logs and diagnostics | High | PLANNED |
| OFF-001 | Core workflow offline after setup/downloads | Critical | PLANNED |
| OFF-002 | No mandatory paid APIs, subscriptions or cloud inference | Critical | PLANNED |
| LIC-001 | Original or properly licensed creative assets | Critical | PLANNED |
| LIC-002 | Preserve third-party notices and attribution | Critical | PLANNED |
| QA-001 | Test app, APIs, projects, rendering and installation | Critical | PARTIALLY IMPLEMENTED |
| QA-002 | Inspect rendered frames/videos, not code alone | Critical | PLANNED |
| QA-003 | Record actual CI and test evidence | Critical | TESTED |
| REL-001 | Persistent job queue, autosave and crash recovery | High | PLANNED |
| REL-002 | Monitor memory, disk, failures and safe cancellation | High | PLANNED |
| REL-003 | Preserve checkpoints and avoid destructive resets | Critical | PLANNED |

## Evidence notes for currently tested catalog requirements

- `WORLD-005`, `ANIM-004` and `ANIM-005` mean only that the Story Plan validator accepts/rejects identifiers from the current Ara-derived location/action/expression catalogs. They do not prove a persistent world, engine-neutral vocabulary, animation playback or facial rig.
- `APP-001` through `APP-004` are tested only for the current lightweight dashboard/project/story workflow.
- `GIT-003` and `GIT-004` refer to current Windows CI and the bootstrap ZIP, not a final installer.
- `STORY-001` through `STORY-005` remain partial because story creation is a manual external-AI handoff, not an integrated AI story-production pipeline.

## Critical coverage gaps identified by the master-brief audit

- The current inventory is not yet atomic: several rows combine multiple distinct requirements. Required per-row fields (source section, dependencies, module, implementation approach, test method, evidence and remaining limitations) are not present in this compact table. P0.2 must replace/expand it without losing IDs or history.
- The existing location/action/expression checks are provisional Ara-derived catalog validation, not production world or animation requirements.
- Story-plan validation does not implement automatic repair/recovery; that part remains open.
- Manual provider handoff exists, but current provider terms/quotas/Pakistan availability have not been fully verified.

Every status change must include evidence. IMPLEMENTED is not TESTED or VERIFIED.
