# Decision Log

## D-001 — GitHub repository is source of truth
Date: 2026-11-25. Use Pawar-47/Cartoon-Studio as the only primary repository. User explicitly created it for this project. Accepted.

## D-002 — Local-first production, GitHub-hosted CI
Date: 2026-11-25. GitHub Actions builds, tests and packages the application; episode rendering initially runs on the user's Windows PC. Hosted runners are not a permanent free GPU render service. Accepted.

## D-003 — Do not lock a full 3D engine before source and hardware evaluation
Date: 2026-11-25. Initial app shell stays independent of the final engine until source and target-hardware proofs are complete. Accepted.

## D-004 — Initial local application framework
Date: 2026-11-25. FastAPI + static HTML/CSS/JavaScript + SQLite for project management. Small dependency footprint and a Python integration path. Implemented; CI verification pending.

## D-005 — Ara 3D Gen is the leading 3D foundation candidate, not yet accepted as production dependency
Date: 2026-11-25. Source has character builder, procedural sets, timeline, animation, audio and browser MP4 export. It is early preview, currently capped at five scenes of up to 60 seconds each, has a realistic MakeHuman-derived style, and its Supertonic 2 voices do not support Urdu. Next step is a Windows build and low-end rendering proof, then decide on submodule/upstream integration and cartoon-style patches. No external code has been copied.


## D-006 — Preserve the exact original phase order
Date: 2026-11-25. The user-approved master brief's numbered sequence is binding: Phase 0 research/architecture; Phase 1 installable foundation; Phase 2 Character Studio; Phase 3 World Builder; Phase 4 Story/Scene Engine; Phase 5 Animation; Phase 6 Urdu Voice/Lip-Sync; Phase 7 Episode Generator; Phase 8 Optimization/Reliability. Candidate engine proofs belong in Phase 0 research; selected-engine integration is performed as needed within Phase 2, not as a separate numbered phase. Accepted.

## D-007 — Freeze out-of-sequence Story Generator expansion
Date: 2026-11-25. The existing Story Generator/schema is preserved as early partial work. Do not expand it before Phase 4. Its Ara-derived location/action/expression IDs are provisional and must be replaced by stable Cartoon Studio IDs and engine adapters before production use. Accepted.

## D-008 — One coherent commit per substantial batch
Date: 2026-11-25. The previous checkpoint update created 15 documentation-only commits and 15 CI runs (#53–#67), contrary to the anti-stall/batch rules. Going forward, related source, tests, docs and traceability updates must be committed together once per coherent batch; do not trigger CI for each documentation edit. Accepted.


## D-009 — Physical target-PC testing is a Phase 8 benchmark, not an upstream gate
Date: 2026-11-25. The user's i3-5005U / Intel HD 5500 / 8 GB PC remains the design target, but testing on that physical machine must not block P0.5 architecture, P0.6 bounded proofs, P0.7 freeze or Phases 1–7. P0.4 uses official specifications, upstream source and documented driver/API evidence with explicit uncertainty. Architecture-critical candidate proofs may run in CI/VM or other controlled environments. Actual representative-scene performance, quality-preset tuning and target-PC acceptance are performed in Phase 8 / P8.1. Slow performance is addressed through scalable quality modes and optimization without silently dropping required features. Accepted per user instruction.


## D-010 — Preserve FastAPI/browser control plane; isolate 3D behind a dual-target engine adapter
Date: 2026-11-25. P0.5 architecture direction is to retain the current FastAPI + browser UI + SQLite foundation as the control plane. Godot is the leading engine candidate, not yet accepted. Preferred boundary: supervised native Godot render worker, with an optional Godot Web export for an embedded viewport if P0.6 proves browser integration and resource behavior. The native-shell replacement path is rejected as default because it would replace/duplicate working UI and project services. Canonical JSON project/character/world/episode/scene/asset/job contracts remain engine-neutral. P0.6 must prove selected engine operations and licensing before engine approval. Actual target-PC performance remains Phase 8. This is a provisional architecture direction, not an engine approval.


## D-011 — Hardware benchmark is Phase 8 only; architecture progresses on source evidence

Date: 2026-11-25. User explicitly clarified that testing on their personal PC is not important enough to gate progress; slower operation is acceptable and performance tuning can happen later. The PowerShell/Godot target probe remains optional. Source/API compatibility, sequential processing, four quality modes, caching and bounded workloads remain design constraints. Actual frame-time, peak RAM, render duration, driver stability and preset tuning are Phase 8 work. Do not ask the user to run the probe as a prerequisite and do not claim measured performance without a real run.

## D-012 — Dependency strategy: minimal local core, adapters at subsystem edges

Date: 2026-11-25. Retain Python 3.11+, FastAPI/Uvicorn, Pydantic, stdlib SQLite and the existing vanilla browser UI. Keep Godot 4.7.2 Compatibility as the leading native worker candidate pending P0.6 proof; Web export is optional. Start with an app-owned SQLite job queue. FFmpeg is behind a process adapter, but no binary/encoder is selected until build flags, codec and license are verified. AI/TTS remain optional and manual Urdu recording remains a supported baseline. See DEPENDENCY_DECISIONS.md for exact boundaries and evidence.

## D-013 — Complete registry-to-architecture crosswalk

Date: 2026-11-25. Added ARCHITECTURE_TRACEABILITY.md with one row for every one of the 171 atomic registry IDs, including architecture home, planned module boundary and delivery phase. This is an ownership/architecture map, not evidence that the planned code exists.

## D-014 — Select Godot 4.7.2 Compatibility as the production 3D runtime

Date: 2026-11-25. Godot 4.7.2-stable passed the bounded P0.6 hosted-runner proof: GLB import, MeshInstance3D discovery, AnimationPlayer creation/playback, PackedScene save/reopen and 72-frame MovieWriter AVI. The follow-up FFmpeg conversion produced a 3-second MP4 inspected by FFprobe. Select Godot Compatibility as the native production worker runtime behind a versioned engine adapter controlled by FastAPI. This is functional candidate proof, not a target-PC performance claim or complete product acceptance. See P0_6_PROOF_REPORT.md.

## D-015 — Use a Cartoon Studio-owned SQLite job queue

Date: 2026-11-25. The isolated SQLite prototype passed five queue-specific tests in Windows CI: serial scene leases, lease-expiry retry, checkpoint preservation, safe cancellation and stale-worker rejection. Use the app-owned SQLite queue as the Phase 1/7 implementation baseline; do not add Huey/sqlite-workqueue unless requirements expand beyond this bounded local model. The proof prototype remains under tools/ and is not production code.

## D-016 — Defer optional Godot Web viewport

Date: 2026-11-25. The Godot Web export/embedded viewport is not needed to validate native rendering and is not required for Phase 1. Keep the browser as the main UI and keep viewport integration behind an adapter. Revisit only if Character Studio/World Builder interaction proves a browser-embedded 3D viewport materially improves the workflow. Its absence must not block the native renderer or phase progression.

## D-017 — Keep production MP4 codec and FFmpeg distribution build open

Date: 2026-11-25. The hosted proof successfully converted AVI to MP4 using MPEG-4 Part 2/AAC. This proves a functional assembly path, not the final production codec, patent position or redistributable FFmpeg build. The production FFmpeg adapter remains a separate process boundary; exact binary, configure flags, codec, notices and source compliance must be approved before bundling.

## DEC-CHAR-002 — Start P2.2 with the lighter Quaternius modular men/women packs (2026-11-25)

**Decision:** use the Quaternius Ultimate Modular Men and Ultimate Modular Women CC0 1.0 model files for the first modular-character builder slice; implement assembly, customization, UI, recipes and export in Cartoon Studio.

**Why:** the two packs provide 21 stylized outfit bases, four interchangeable parts per model, 24 embedded animations and 34.92 MiB total ready-to-use GLBs. Three representative models can verify the shared 62-bone rig before assembly. The newer Universal Base Characters + Modular Character Outfits - Fantasy packs have a standard humanoid rig and a larger wardrobe, but the standard outfit archive is 280 MiB and the animation library is separate; defer them until the first creator path is proven.

**Boundaries:** pin the asset-hosting commit and every model's byte size/Git blob SHA-1; cache downloads locally; use only the CC0 model files. Do not reuse the unlicensed host repository's application code. Configura was evaluated but not adopted as a runtime dependency because it is an unstable editor-time Godot plugin and the app's control plane is browser-first.

**Acceptance:** Godot verifies representative models; a later batch assembles four selected parts onto one skeleton, preserves all clips, exports/reopens GLB, and persists a versioned creation recipe. P2.2 remains PARTIAL until the creator UI and save/reopen flow pass.


## D-018 — Retired-branch deletion is manual-only

Date: 2026-11-27. The previous `cleanup-retired-branches.yml` ran on every successful `main` CI and deleted every non-`main` branch, including open feature branches. That conflicts with the owner's instruction to leave feature branches untouched and with the repository rule against destructive resets. The workflow now runs only on explicit `workflow_dispatch`, deletes only the exact branch names supplied by a maintainer, and always preserves `main`. Branch cleanup is an intentional maintainer action, never a side effect of CI success.

## D-019 — Generated-face replacement fails fast on rigs without a separable skin surface

Date: 2026-11-27. Generated-face replacement suppresses the imported head's replaceable surfaces and fits a generated head/eyes/nose/mouth to the detected skin bounds. Commit `3c57d1f` tightened this path to require a separable `Skin` surface, preventing a duplicate, misaligned imported face. When the surface is missing, the worker returns `face_template_skin_surface_missing` instead of silently producing broken geometry. Tests use the pinned CC0 Adventurer (which has `Skin`/`Eyebrows`/`Eye` surfaces) for positive coverage and RobotExpressive for the rejection contract. A future UX batch may map this structured code to HTTP 422 and guide the user to a compatible character; the current API surfaces the explanatory message through `EngineError`.
