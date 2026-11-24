# Requirements Registry
Statuses: NOT REVIEWED, RESEARCH REQUIRED, PLANNED, IN PROGRESS, IMPLEMENTED, PARTIALLY IMPLEMENTED, TESTED, VERIFIED, BLOCKED, DEFERRED WITH REASON, REJECTED WITH JUSTIFICATION.

| ID | Requirement | Priority | Status |
|---|---|---|---|
| GOV-001 | Read entire specification before coding | Critical | PARTIALLY IMPLEMENTED |
| GOV-002 | Maintain permanent requirement registry | Critical | IMPLEMENTED |
| GOV-003 | Trace requirement to architecture, code, test and evidence | Critical | IMPLEMENTED |
| GOV-004 | Recheck requirements before every major phase, batch and release | Critical | PLANNED |
| GOV-005 | Never silently omit, downgrade or fake requirements | Critical | PLANNED |
| GOV-006 | Resume from original spec, registry, code and checkpoints | High | PLANNED |
| GIT-001 | Use Pawar-47/Cartoon-Studio as source of truth | Critical | IMPLEMENTED |
| GIT-002 | Develop and maintain source in GitHub | Critical | IN PROGRESS |
| GIT-003 | GitHub Actions build, test and Windows package | Critical | PARTIALLY IMPLEMENTED |
| GIT-004 | Produce downloadable Windows artifacts | High | PARTIALLY IMPLEMENTED |
| GIT-005 | Verify installation on user's PC | Critical | NOT REVIEWED |
| GIT-006 | Keep episode rendering separate from CI runners | High | PLANNED |
| OSS-001 | Extensively search public GitHub before building components | Critical | IN PROGRESS |
| OSS-002 | Inspect source, docs, releases, issues, activity and dependencies | Critical | RESEARCH REQUIRED |
| OSS-003 | Verify software, model, dataset and asset licenses | Critical | RESEARCH REQUIRED |
| OSS-004 | Prefer reuse/integration/adaptation before scratch development | Critical | PLANNED |
| OSS-005 | Record source, version, author, license and provenance | High | PLANNED |
| HW-001 | Support Intel Core i3-5005U | Critical | PLANNED |
| HW-002 | Support Intel HD Graphics 5500 without NVIDIA requirement | Critical | PLANNED |
| HW-003 | Operate within 8 GB RAM using low-memory/sequential processing | Critical | PLANNED |
| HW-004 | Benchmark actual scenes before performance promises | High | PLANNED |
| HW-005 | Preview, Low Hardware, Balanced and High Quality presets | High | PLANNED |
| APP-001 | Lightweight browser-based application | Critical | PARTIALLY IMPLEMENTED |
| APP-002 | Local backend and persistent SQLite project metadata | High | PARTIALLY IMPLEMENTED |
| APP-003 | Dashboard, project creation and listing | High | IMPLEMENTED |
| APP-004 | Story Generator workspace | High | PLANNED |
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
| CHAR-001 | Create and save original reusable characters | Critical | PLANNED |
| CHAR-002 | Persistent face, body, clothing, hair and accessories | High | PLANNED |
| CHAR-003 | Personality, relationships, voice and dialogue profiles | High | PLANNED |
| CHAR-004 | Rigging, preview, import and export | Critical | PLANNED |
| ANIM-001 | Reusable body animation library | Critical | PLANNED |
| ANIM-002 | Facial expressions, blinking, talking and gestures | High | PLANNED |
| ANIM-003 | Smooth transitions, blending and retargeting | High | PLANNED |
| STORY-001 | One-prompt original story generation in Urdu or English | Critical | PLANNED |
| STORY-002 | Title, summary, cast, scenes, actions, camera and audio plan | High | PLANNED |
| STORY-003 | Natural conversational Pakistani Urdu | Critical | PLANNED |
| STORY-004 | Urdu script, RTL and optional Roman Urdu | Critical | PLANNED |
| STORY-005 | Edit and approve story before production | High | PLANNED |
| STORY-006 | Validate scene data and recover invalid output | High | PLANNED |
| AI-001 | Modular multi-provider AI architecture | High | PLANNED |
| AI-002 | Verify free quotas, refill cycles, terms and Pakistan availability | High | PLANNED |
| AI-003 | Manual handoff where official APIs are unavailable | High | PLANNED |
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
| QA-001 | Test app, APIs, projects, rendering and installation | Critical | PLANNED |
| QA-002 | Inspect rendered frames/videos, not code alone | Critical | PLANNED |
| QA-003 | Record actual CI and test evidence | Critical | PLANNED |
| REL-001 | Persistent job queue, autosave and crash recovery | High | PLANNED |
| REL-002 | Monitor memory, disk, failures and safe cancellation | High | PLANNED |
| REL-003 | Preserve checkpoints and avoid destructive resets | Critical | PLANNED |

Every status change must include evidence. IMPLEMENTED is not TESTED or VERIFIED.
