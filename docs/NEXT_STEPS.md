# Next Steps

## Current checkpoint — 2026-11-25

P0.1, P0.2 and P0.3 are complete. The exact master brief is version-controlled at `docs/MASTER_EXECUTION_PROMPT.md`. The source-level candidate comparison and provisional weighted scorecard are in `docs/CANDIDATE_SCORECARD.md`. No engine, plugin, voice, provider or asset has been selected.

## Next batch: P0.4 — target hardware, Urdu and provider feasibility

1. Create a no-admin, no-network Windows diagnostics script to capture Windows build, CPU, RAM, Intel HD 5500 driver/version, display resolution and available disk.
2. Create a small Godot 4.7.2 Compatibility probe (not a product feature) to report renderer/API, render a fixed test scene, capture frame time/peak memory and export a short fixed-FPS test clip.
3. Test the VRM/MToon import path and Compatibility renderer only to the extent needed to establish basic feasibility; full subsystem proofs remain P0.6.
4. Validate eSpeak NG Urdu G2P and WhisperX Urdu word/character alignment with a known transcript. Use native Pakistani Urdu audio before approving quality; Allosaurus remains optional and unverified.
5. Recheck official Pakistan availability, current free quotas, privacy/data-use terms and costs for GroqCloud, Cloudflare Workers AI, Gemini and OpenRouter. FreeMilk remains a manual coding agent, not a programmatic API. Do not connect keys or send project data without explicit approval.
6. Record all results, exact versions, driver details, RAM/render timings, Urdu quality observations, provider limits and remaining gaps in the hardware/provider/voice reports.

## Gates and constraints

- P0.5 architecture freeze starts only after P0.4 feasibility evidence is reviewed.
- P0.6 bounded proofs start only after P0.5.
- P0.7 is the final Phase 0 freeze; do not begin production features before it.
- Preserve all current FastAPI/SQLite/browser and Story Generator work. Do not reset repositories, delete features, or restart audits from zero.
- Local-first and no mandatory paid API remain binding. Keep manual voice recording, manual viseme editing and manual AI handoff fallbacks.
