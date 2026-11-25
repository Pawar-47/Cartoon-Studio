# Candidate Scorecard — P0.3 source-level comparison

**Date:** 2026-11-25  
**Purpose:** compare serious candidates before target-PC proof and architecture freeze. This is a source-based scorecard, not a benchmark or final selection.

## Scoring method

Scores are 1–5 (5 is strongest). Weighted score:

- Target-hardware fit: 25%
- Feature coverage: 20%
- License and redistribution fit: 15%
- Offline / no-mandatory-cost fit: 15%
- Maturity and upstream test evidence: 15%
- Integration effort (5 = easiest): 10%

Scores reflect public source/docs inspected on 2026-11-25. Unknown target performance is not assumed to be good; confidence is shown separately. A high score does not authorize reuse. Exact versions, licenses and asset files must be pinned before integration.

## Engine and editor

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Godot 4.7.2 Compatibility | 4 | 4 | 5 | 5 | 5 | 3 | **4.35** | Medium. OpenGL 3.3 floor fits HD 5500's reported 4.3; target has only 2 CPU cores vs 4 recommended; no target test; custom UI/backend integration required. |
| Blender 4.5.17 LTS | 2 | 5 | 3 | 5 | 5 | 2 | **3.65** | Medium. Full 3D authoring/rendering; target is below published CPU minimum and has legacy Intel driver risk; GPL3 obligations. |
| Browser WebGL / Ara / Ekza | 3 | 3 | 3 | 4 | 2 | 3 | **3.00** | Low. Fast UI/preview path but editor maturity, CI and MP4 export proof are incomplete/cancelled; browser memory needs testing. |

**Current research leader:** Godot 4.7.2 Compatibility as the target runtime candidate. This is not frozen; P0.4 target-PC tests and P0.6 bounded proofs can change the ranking.

## World and environment

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Godot-native stack (Terrain3D + Road Generator + Building Generator + Roommate) | 4 | 4 | 4 | 5 | 3 | 3 | **3.90** | Low–medium. Compatibility renderer supported by Terrain3D; road generator incomplete, building generator lacks CI, Roommate MPL-2.0/docs-only CI; stack not tested together. |
| Blender addons (Bene Procgen Maps + Blender Level Architect) | 2 | 5 | 2 | 5 | 4 | 2 | **3.35** | Medium. Rich procedural cities/interiors and upstream CI; GPL3 and Blender target-hardware risk. |
| OpenCity prototype | 4 | 3 | 5 | 5 | 1 | 4 | **3.65** | Low. Traffic/pedestrian behavior and headless test modes; only two commits, no CI, visible geometry mostly placeholders. |

## Character and facial expression

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| VRM 1.0 + Godot VRM/MToon + verified CC0 Quaternius parts + custom editor | 4 | 4 | 5 | 5 | 3 | 3 | **4.05** | Medium. Standard emotions/visemes/custom expressions, MIT plugin and CC0 assets; no finished recipe-based creator; add-on has known gaps and no CI. |
| MPFB2 / CharacterCreator | 2 | 4 | 2 | 5 | 4 | 2 | **3.15** | Medium. Procedural human base/rig workflow; Blender dependency and GPL3 code; not final toon style. |
| Ducz.CharacterCreator implementation | 4 | 4 | 1 | 5 | 1 | 3 | **3.15** | Low. Strong modular-character concept but repository code has no license; do not copy. Reimplement independently with CC0 assets. |

## Animation

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Godot AnimationTree/AnimationPlayer + CC0 UAL/UAL2 | 4 | 4 | 5 | 5 | 4 | 4 | **4.30** | Medium. 250+ retarget-ready clips; simple state machine first; facial animation still custom. |
| Godot AI Animation Toolkit 2.0.0 | 3 | 4 | 5 | 5 | 3 | 2 | **3.70** | Low–medium. 103 authoring operations but requires separate Godot AI/MCP plugin; not runtime-required. |
| Godot Motion Matching | 3 | 4 | 5 | 5 | 1 | 2 | **3.40** | Low. MIT and promising features, but new/no CI/no assets; unnecessary complexity before baseline animation works. |

## Urdu speech, alignment and lip-sync

No candidate is approved as the production voice or fully automatic Urdu lip-sync.

| Candidate | Current role | Strength | Blocking limitation |
|---|---|---|---|
| WhisperX + Urdu Wav2Vec2 model | Word/character alignment | WhisperX BSD2 explicitly maps `ur`; model Apache2 | 300M parameters; full dependency stack heavy; model WER 39.89% on Common Voice 8; no Pakistani sample test; not phone-level |
| eSpeak NG | Urdu G2P / emergency voice | Compact, offline `ur` rules; phoneme/pitch/length output | GPL3; formant voice is robotic; not main natural voice |
| Allosaurus + custom viseme map | Possible phone recognition | Universal phone model; approximate phone timestamps | Urdu inventory/timing not verified; GPL3/PyTorch |
| Parrot Lipsync | Blender-side phoneme-to-mouth reference | Editable phoneme/viseme table; Blender 4.5 support | GPL3 Blender add-on; not Godot; Urdu quality untested |
| Qwen Audio TTS Flash | Optional cloud Urdu voice | Official docs list Urdu voice | Cloud-only; Pakistan access, price, privacy, accent and quality unverified |
| Smol Urdu TTS / tiny-urdu | Local model research | Small/Urdu-specific model claims | Code-license gap or Roman-Urdu-only; BF16/PyTorch/quality not proven |

**Working hypothesis:** approved Urdu transcript → human recording or approved TTS → WhisperX word/character alignment → eSpeak G2P → VRM/custom viseme mapping → manual timeline correction. P0.4 must validate on native Pakistani Urdu samples.

## Audio and MP4

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Godot MovieWriter + FFmpeg/OpenH264 | 4 | 4 | 4 | 5 | 4 | 3 | **4.05** | Medium. Non-real-time fixed-FPS render; exported AVI/PNG+WAV; AVI 4 GB cap; FFmpeg needed for MP4. |
| Blender VSE + FFmpeg | 2 | 5 | 3 | 5 | 5 | 3 | **3.75** | Medium. Rich editing/render path but target CPU/driver risk and Blender dependency. |

Kenney CC0 packs cover SFX and short jingles; OpenGameArt CC0 loops need per-track license and YouTube Content ID checks. They do not replace original soundtrack or Urdu voice work.

## Queue and recovery

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Huey / SqliteHuey | 5 | 4 | 5 | 5 | 4 | 4 | **4.55** | Medium. MIT, retries/results/scheduling; in-flight task recovery requires explicit idempotent stages. |
| sqlite-workqueue | 5 | 3 | 5 | 5 | 2 | 3 | **3.95** | Medium. MIT, leases/retries/idempotency; lacks cancellation/results/migrations. |

A minimal Cartoon Studio-owned SQLite queue may still be simpler; choose in P0.5 after the current app's job requirements are mapped.

## Windows packaging

| Candidate | Hardware | Features | License | Offline/cost | Maturity | Integration | Weighted | Confidence / trade-off |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| PyInstaller + NSIS | 4 | 4 | 4 | 5 | 5 | 4 | **4.30** | Medium. Fits existing Python app; dependency and FFmpeg notices must be preserved; installer not built yet. |
| pywebview | 4 | 3 | 5 | 5 | 4 | 4 | **4.10** | Medium. Light WebView shell; WebView2/runtime integration and Godot sidecar still need proof. |
| Tauri 2 | 4 | 3 | 5 | 5 | 5 | 2 | **4.05** | Medium. Mature shell, but Rust/WebView2 and backend sidecar integration add complexity. |

## AI provider shortlist

- **API candidates:** GroqCloud, Cloudflare Workers AI, Gemini Developer API, OpenRouter. Their free quotas, privacy and model access differ; exact Pakistan availability and user-account quotas are P0.4.
- **Manual agent workflows:** FreeMilk (daily allowance but exact quota not public; privacy and direct-script restrictions), Copilot Free, ChatGPT Free, Claude Free and Perplexity Standard. These are not free general-purpose backend APIs.
- **No provider is selected or connected. No paid API is approved.**

## P0.3 outcome and next gates

P0.3 source-level research and provisional scorecard are complete. The scorecard does not select an engine or authorize code/assets. P0.4 now owns target-PC compatibility, Pakistan region/account quota, native Urdu quality, privacy and cost feasibility. P0.5 will freeze the engine-neutral architecture only after P0.4; P0.6 will run bounded proofs after P0.5. Preserve the current FastAPI/browser/SQLite and Story Generator work; do not restart or expand production features before P0.7.
