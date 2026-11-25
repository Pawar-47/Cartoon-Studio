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

## P0.3 provider research evidence (not app tests)
- Official FreeMilk Terms and Privacy Policy inspected; no API key or project source was sent to FreeMilk.
- Official Gemini, Groq, Cloudflare Workers AI, OpenRouter, GitHub Copilot, OpenAI billing, Claude, Perplexity, Mistral and Cerebras documentation inspected.
- Provider quota and availability findings are documentation snapshots only; they must be rechecked in the user's own accounts and target region before integration.
- No app integration, API call, quota test, Pakistan-region test or model-quality benchmark was run.

## Godot candidate upstream evidence (not Cartoon Studio tests)
- Godot AI Animation Toolkit 2.0.0: upstream Actions #386 SUCCESS on `e8f57c27c0374a6c76fce0e4b5d35d443ba3510b`.
- Terrain3D: upstream Actions #96/#2685 SUCCESS on `43734bbada0b65fb5a642cfad0d9caeccfafade8`.
- Godot Road Generator: upstream Actions #169 SUCCESS on dev commit `648f07295a6d1cd9e0607c71196f7a2de98e6fc5`.
- Roommate: Actions #12 success is a documentation workflow, not a runtime test.
- Building Generator has manual test scripts but no Actions workflow found. OpenCity has headless behavior test modes but no Actions workflow found.
- None of these repositories has been run on the user's target PC or integrated into Cartoon Studio.

## CC0 asset and animation evidence (not app tests)
- Official Quaternius pages inspected individually for Universal Base Characters, Modular Character Outfits - Fantasy, Ultimate Modular Men, UAL, UAL2, Downtown City MegaKit, Modular Streets, Ultimate Buildings, Ultimate House Interior, Ultimate Furniture, Cars and Public Transport; each exact page showed CC0.
- Quaternius FAQ/license confirms packs may be CC0 or QAL; QAL v1.0 prohibits standalone asset redistribution. The selected CC0 pack list is not a blanket approval for other packs.
- Godot Motion Matching repository has headless test scripts but no Actions workflow; no tests were executed in this research.
- No CC0 pack was downloaded or imported; no Cartoon Studio scene/render test was performed.

## Audio/video pipeline research evidence (not app tests)
- Godot 4.7 MovieWriter, Audio Playback Tracks and Audio Bus documentation inspected; no scene render or audio mix test run.
- FFmpeg official legal documentation and OpenH264 BSD license inspected; no binary built or bundled.
- Kenney CC0 audio packs and OpenGameArt CC0 music pages inspected; no audio downloaded or added to the asset library.
- Allosaurus/Parrot source and model docs inspected; no Urdu audio inference or viseme mapping test performed.

## VRM and Urdu phoneme source evidence (not app tests)
- V-Sekai Godot VRM README/root MIT license, MToon MIT license and sample-model license file inspected; no upstream Actions workflow found.
- VRM 1.0 expressions specification inspected for emotions, vowel visemes, blink/gaze, custom expressions and override behavior.
- eSpeak NG current source and GPL3 license inspected; Urdu `ur` language source and pronunciation files are present. No Windows binary was executed.
- No VRM import/export, MToon rendering, Urdu phoneme output, eSpeak speech or Allosaurus audio alignment was tested.

## P0.3 final source-research evidence (not app tests)
- WhisperX main source/license inspected; current alignment code maps Urdu `ur` to `kingabzpro/wav2vec2-large-xls-r-300m-Urdu` and supports character alignment. Model card is Apache-2.0, 300M parameters, Common Voice 8.0 Urdu, WER 39.89% / CER 16.70%.
- No Urdu audio inference, Pakistani accent test, character-to-viseme timing test or 8 GB CPU benchmark was run.
- Candidate scorecard published at `docs/CANDIDATE_SCORECARD.md`; all scores are source-based and provisional.
- Original uploaded master prompt was added verbatim as `docs/MASTER_EXECUTION_PROMPT.md`; a fresh GitHub fetch matched the text exactly. Source metadata: 1,133 lines, 4,642 words, 33,223 bytes, SHA-256 `541098eebd96b98e0153770f0bc37a1031a7242fd9cb97bc5a6b52c35c9ddfde`.
- Prompt-preservation commit `e51ccdb71a9fe813ffe0ecab2ba78a3b096a11f9` CI run #83 SUCCESS. P0.3 closeout commit CI is pending.
- P0.3 closeout commit: `5bcbf8775014c4b25699a9bdcb5e633c5fa00811`; GitHub Actions run #84 SUCCESS — https://github.com/Pawar-47/Cartoon-Studio/actions/runs/45557418338.
- P0.3 is a research gate only. No engine/plugins/assets/providers have been integrated; no target-PC test has been run.

## Follow-up documentation correction
- Corrected the P0.3 row in `EXECUTION_BATCH_PLAN.md` to the five-column table structure; no application source changed.
- Documentation correction commit `fe33993fb8423c412dde55f9a097e2a14298919a`; GitHub Actions run #85 SUCCESS.

## P0.4 diagnostic harness — source review only
- Added a PowerShell hardware collector and a Godot 4.7.2 Compatibility-renderer probe project. The script is designed for Windows PowerShell 5.1 and does not require admin rights, network access, Python packages or API keys.
- Static source review completed. The Godot project has not yet been launched in a real renderer; no PowerShell run, GPU benchmark, MovieWriter export or target-PC result exists.
- The harness intentionally collects no username, computer name, serial number, MAC/IP address or product key.
