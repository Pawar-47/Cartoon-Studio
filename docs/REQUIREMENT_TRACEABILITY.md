# Requirement Traceability

This matrix records only source/test/evidence relationships that have been inspected. It is not yet a complete decomposition of the 25-part master brief plus the repository specification; unlisted sub-requirements remain open and must be added during P0.2.

The current Story Generator/schema is an early, out-of-sequence partial slice. Its catalog checks are Ara-derived and provisional; they do not establish the canonical engine-neutral Cartoon Studio data contract. Preserve the code, freeze feature expansion until Phase 4, and migrate identifiers through explicit engine adapters.

| Requirement IDs | Area | Implementation | Test/evidence | Status / limitation |
|---|---|---|---|---|
| GIT-001/002 | Repository governance | Pawar-47/Cartoon-Studio, main | Code-audited source baseline commit `40bec8c423e953a0753c62f53c8a173274ac72e1`; subsequent commits reconciled checkpoint documents on `main` | IN PROGRESS |
| GIT-003 | CI/CD validation | `.github/workflows/ci.yml` | Run `45487769827`: Ruff, compile, pytest and package all passed | TESTED |
| GIT-004 | Windows bootstrap artifact | Windows bootstrap ZIP | Artifact `14963389016` from run `45487769827`; SHA-256 recorded in TEST_REPORT | TESTED; not final installer |
| APP-001 | Browser interface | `app/static/index.html`, `styles.css`, `app.js` | Dashboard route test in `tests/test_app.py`, run `45487769827` | TESTED |
| APP-002/003 | Local project API and SQLite | `app/main.py` | Project create/list tests in run `45487769827` | TESTED |
| APP-004 | Story Generator workspace | `app/static/story.html`, `story.css`, `story.js` | Story route and prompt tests in run `45487769827` | TESTED |
| STORY-001/002/003/004/005 | Prompt-to-story handoff and editable schema | `app/story.py`, `app/static/story.html` | Prompt builder, Pakistani Urdu instruction, JSON schema and editing UI | PARTIALLY IMPLEMENTED; no direct AI generation, complete RTL proof or rendered episode |
| STORY-006 | Scene schema validation and persistence | `app/story.py`, `app/main.py` | Duration, scene count, cast, cue timing, location, expression and animation ID tests in run `45487769827` | TESTED as schema validation only |
| ANIM-004 | Candidate action catalog validation | `app/story.py: AVAILABLE_ACTION_IDS` | Unknown animation ID rejected in run `45487769827` | TESTED; IDs derive from unapproved Ara candidate, no engine adapter/playback |
| ANIM-005 | Candidate expression catalog validation | `app/story.py: ExpressionId` | Unknown expression rejected in run `45487769827` | TESTED; does not prove facial rig/animation |
| WORLD-005 | Candidate location catalog validation | `app/story.py: LOCATION_CATALOG` | Unknown location rejected in run `45487769827` | TESTED; does not prove persistent world/location generation |
| AI-003 | Manual AI provider handoff | Story Generator copy-prompt/paste-JSON workflow | Prompt builder and schema validation tests in run `45487769827` | TESTED |
| GOV-002 | Requirements governance | `docs/REQUIREMENTS_REGISTRY.md` | Registry exists; coverage is incomplete | IMPLEMENTED |
| GOV-003 | Traceability | This document | Partial mapping only | PARTIALLY IMPLEMENTED |
| OSS-001..005 | Open-source research | Research, evaluation, reuse and licensing docs | Ara, Ekza, DvaitAI, AnimStudio and several Urdu TTS candidates recorded | IN PROGRESS; coverage and source/license verification incomplete |

## Known uncovered or only planned areas

Character persistence and rigging; original toon style; complete world builder and vehicle interactions; stable engine-neutral action vocabulary; animation blending/retargeting/timeline; direct AI provider integration and free-quota policy; research-agent execution; Urdu TTS quality and rights; character-specific voices; Urdu lip-sync; audio mixing and subtitles; renderer/MP4 assembly; job queue/cache/recovery; offline operation; installer; actual Windows install; target-hardware benchmarks; complete visual/audio acceptance.

No item is VERIFIED. The registry and traceability still need a full requirement-by-requirement coverage pass against all 25 parts of the original master brief and every section/acceptance bullet in `PROJECT_SPECIFICATION.md`.
