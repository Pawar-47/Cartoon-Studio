# Next Steps — 2026-11-28

## Live checkpoint

- Repository: `Pawar-47/Cartoon-Studio`
- Active branch: `main`
- Newest batch: episode contract truthfulness (quality presets, subtitle modes, Urdu-only and voice guards) — awaits its own CI run.
- Previous code-bearing checkpoint: `49516e57577c74f25c33e3d481e0633fa5c2c724` (Windows CI #618 passed; run `46067945723`).
- Binding source: `docs/MASTER_EXECUTION_PROMPT.md`, all 25 parts.
- The frozen Character Foundry branch remains untouched. Do not create or switch to another development branch.

## Current objective

Consolidate the work already completed against the original Master Brief, correct confirmed
defects and establish an evidence-backed baseline. The blocking finding B1 in
`docs/MASTER_BRIEF_AUDIT_2026-11-28.md` still holds: the installed app cannot synthesise
Urdu speech or assemble an MP4 because `piper-tts` and FFmpeg are not bundled.

## Consolidation order

1. Reconcile all 171 atomic requirement rows against live source files, tests, reports and exact CI runs. Preserve each status unless its evidence justifies a change.
2. Traceability path validation is complete: all 171 mapped source paths resolve in the current repository tree. Continue the semantic review of whether each path and cited test actually proves its requirement; distinguish current modules from planned modules and historical claims.
3. Review delivered module behaviour for defects and incomplete wiring: project persistence/import/export; Character Studio; World Builder and GLB catalogue; story/scene generation; animation tracks; audio; queue; Godot render and FFmpeg assembly.
4. Check cross-module IDs, schema versions, project-relative paths, asset provenance, round-trip persistence, cancellation/lease ownership and failure cleanup.
5. Correct confirmed implementation defects in coherent batches. For code changes, run focused tests and then one CI checkpoint after the batch. Documentation-only corrections do not need CI.
6. Freeze the baseline only after the registry, traceability, architecture crosswalk, status, test report and next steps agree on the same source commit and acceptance boundaries.

## Next code batches, in order

1. **Batch A — make the shipped app produce an episode (B1).** Pin the voice path (bundled Piper or a recorded fallback), bundle a licence-reviewed FFmpeg, resolve `_find_ffmpeg` to the bundled binary, and add a real-media Windows CI job that renders a fixture episode end to end.
2. **Batch B — real job execution.** Move production/audio/render work to a background worker with per-scene progress, cooperative cancel, and the Episode Renderer, Logs and Diagnostics workspaces.
3. **Batch C — scene cache and checkpoints**, so one failed scene never re-renders the whole episode.
4. P2.2 remaining visual acceptance proceeds in parallel: interactive browser acceptance of hairstyles, portraits, assembly, morphs and retarget preview; broad rig acceptance on representative models.

## Completed batch in this checkpoint

### Episode contract truthfulness — presets, subtitle modes, guards
Four quality presets in `app/quality.py`, stored in the project document and read by `POST /story/render` (Preview 15 fps/640x360, Low Hardware 24/854x480, Balanced 24/1280x720 — the new default — High Quality 30/1920x1080), with `GET /api/quality-presets`, `GET/PUT /api/projects/{id}/settings` and a Render quality selector on the Story page. `subtitle_mode` is honoured end to end (urdu / roman_urdu / english / none, the last producing no subtitle stream); a subtitle-mode selector in the workspace is still to come. English episodes and unsupported voice profiles are refused at validation, and `roman_urdu`/`english` subtitles require a per-line `subtitle_text`.

## Existing implementation to preserve

- FastAPI local service, SQLite project persistence and versioned project documents.
- Character import, modular CC0 assembly, profile/appearance editing, proportions, procedural hair/face operations, retargeting and browser GLB preview.
- Persistent World Builder documents, templates, 17 object kinds, curated project-scoped CC0 GLB catalogue, integrity checks and Godot scene export.
- Story prompt/schema validation, world/cast binding and editable episode-scene generation.
- Urdu speech/audio/subtitles and heuristic mouth-envelope animation.
- Godot scene rendering and FFmpeg MP4 assembly path.
- Durable SQLite job records, leases, expiry reclaim, bounded attempts, cancellation and progress.
- Windows CI, pinned dependencies, Godot worker and installer lifecycle proof.
