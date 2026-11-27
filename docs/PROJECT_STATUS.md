# Project Status — 2026-11-28

## Live checkpoint — mainline master-brief alignment review

- Starting main HEAD: `a88379f3ac3a985756d68c25afd22ac7b0a9b4d5`; Windows CI #611 passed on this exact commit.
- The first-pass alignment audit is recorded in `docs/MAINLINE_ALIGNMENT_AUDIT.md`.
- The World Builder browser palette was incomplete relative to its backend: 16 object kinds were accepted by the API/exporter but only 7 were addable in the UI. This batch exposes all supported kinds and adds X/Y/rotation controls with a regression test.
- The Godot World Builder exporter currently generates procedural primitive blockout geometry. It is a real editable Godot scene and GLB preview, but not yet a production-quality reusable environment asset library.
- Vehicle movement/rig/interaction APIs persist state/events; actual vehicle animation and character interaction playback remain incomplete.
- The Story Generator remains a manual prompt/paste workflow. The Urdu audio path exists, but mouth movement is an RMS envelope heuristic rather than phoneme/viseme alignment.
- The durable SQLite job queue is present and wired to episode production, audio, world export and rendering. Earlier status text claiming there is no durable render queue is stale; the current implementation uses in-process execution with durable job records, lease expiry/reclaim, bounded attempts and cooperative cancellation. A separately supervised multi-worker service and scene-level cache/restart-resume remain open.
- No complete 5–7 minute episode has been visually/audio accepted. No target-PC performance benchmark or fresh installer lifecycle acceptance is claimed by this checkpoint.
- Phase 0 and Phase 1 foundations are complete by recorded evidence. Phase 2 Character Studio and Phase 3 World Builder remain partial pending visual/rig/asset acceptance. Phases 4–7 contain useful out-of-order production slices but remain incomplete. Phase 8 is deferred.

## Current phase table

| Phase | Status | Evidence and open acceptance |
|---|---|---|
| 0 — Specification, research, architecture | COMPLETE | Master brief preserved; 171 atomic requirements and matching traceability; research, architecture and bounded engine/queue proofs recorded |
| 1 — GitHub/CI/CD and Windows delivery | COMPLETE | Reproducible locked dependencies, CI, self-contained installer build and install/upgrade/uninstall/reinstall lifecycle proof |
| 2 — Character Studio | PARTIAL | Modular characters, import, profile persistence, proportions, hair/face geometry, morphs and retargeting implemented; interactive visual signoff and broad rig acceptance remain |
| 3 — World Builder | ACTIVE / PARTIAL | Versioned world docs, templates, scene export, GLB preview and 16 object kinds; asset library, visual quality and vehicle runtime behavior remain |
| 4 — Story and Scene Engine | PARTIAL | Structured prompt/schema, validation, world/cast binding and editable scene generation; integrated generation, approval, repair and complete mapping remain |
| 5 — Animation Engine | PARTIAL | Procedural action/camera/expression tracks; reusable motion library, blending, timeline editor and visual acceptance remain |
| 6 — Urdu Voice and Lip-Sync | PARTIAL | Offline Urdu speech/audio mix/subtitles and heuristic mouth envelope; native-speaker evaluation and phoneme/viseme alignment remain |
| 7 — Episode Generator | PARTIAL | Editable scene generation, audio, Godot/FFmpeg MP4 path and durable job records; scene cache/restart-resume and full episode acceptance remain |
| 8 — Optimization and Reliability | DEFERRED | Target-PC benchmarks, quality presets, full visual/audio signoff and final production acceptance |

