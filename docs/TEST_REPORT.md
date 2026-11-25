# Test Report — 2026-11-25

## Latest live-main workflow before and during P0.2 commit

| Check | Result | Evidence |
|---|---|---|
| CI run #68 | SUCCESS | Commit `4171bb320a10c3d7cfec561f706f7e10ebd3bacd`; completed 2026-11-25 |
| Ruff | PASS | Run #67 |
| Python compileall | PASS | Run #67 |
| pytest | PASS — 12 passed, 1 warning | Run #67 |
| Windows bootstrap ZIP | PASS | Run #67; artifact ID `14964957829`; 78,882 bytes |
| Artifact SHA-256 | Recorded | `f307617262c75506d622ad602e204b85935bc88a7b73797d14d2c2344dd97fd7` |

Run #68 is the successful CI for the plan-alignment documentation commit. P0.2 commit CI run #70 is in progress at this checkpoint; its result must be checked before declaring this batch fully complete.

## P0.2 source and coverage checks

- Original prompt reread in full: 1,133 lines, 4,642 words, 33,223 bytes.
- Original prompt SHA-256: `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`.
- Atomic registry rows: 171.
- Traceability rows: 171, generated one-to-one from the same requirement inventory.
- Original prompt parts mapped: 25/25.
- Repository specification sections mapped: 24/24.
- Legacy IDs preserved as aliases: 75.
- No requirement marked VERIFIED.

These are documentation-structure checks based on the generated source inventory. They are not application feature tests and do not prove production functionality.

## Not yet tested / not accepted

- Clean Windows installation and self-contained installer.
- Target-PC performance on i3-5005U / Intel HD 5500 / 8 GB.
- Character creation/rigging, persistent world, animation playback and retargeting.
- Pakistani Urdu TTS naturalness, character voices and lip-sync.
- Real 3D scene rendering, audio mix, MP4 export and 5–7 minute episode.
- Scene caching, retry, cancellation, restart recovery and editable project reopen.

## Candidate proof status

Ara foundation proof run #6 remains CANCELLED during MP4 export. It is not accepted as a successful render or engine selection.

## Evidence policy

A green CI run proves only the checks that actually ran. Source presence, documentation, a schema validator, a mockup or a partial candidate demo is not proof of end-to-end functionality. Do not mark a requirement VERIFIED without direct acceptance evidence.

## P0.2 final batch CI
- Final P0.2 commit: `d997115db8fab5dbe1f899681fd47f2800222378`.
- Final workflow run #71: SUCCESS — https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45553395541
- Intermediate P0.2 identifier/checkpoint corrections triggered runs #69 and #70 before the final corrected commit; both also succeeded. This was more than the intended one CI run for a single batch. The final result is #71; future batches should avoid rewriting pushed commits after CI starts.

## P0.3 research evidence (not app tests)
- Bene Procgen Maps upstream Actions #18 SUCCESS on `f883ddb59eadcff319d3b28eee59da90d7c8c21f`.
- Blender Level Architect upstream Actions #87 SUCCESS on `660e2113a2987a172f001a95d305e303b6a2aad9`.
- sqlite-workqueue upstream Actions #19 SUCCESS on `4f7cf094a77ea44f984de61b39a13594efd5f7c5`.
- Ekza's inspected GitHub Actions runs #1–#3 were cancelled; Ara/3d-gen's inspected CI run failed and Cartoon Studio's Ara proof #6 remains cancelled. These candidates are not accepted.
- No candidate was executed on the target PC. Upstream CI is evidence about the upstream repository only; it does not prove Cartoon Studio integration or target compatibility.
