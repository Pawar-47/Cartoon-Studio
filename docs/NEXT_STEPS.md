# Next Steps

## Current checkpoint — 2026-11-25

P0.1–P0.3 are complete. P0.4 is in progress. The exact master brief is preserved at `docs/MASTER_EXECUTION_PROMPT.md`; source-level candidate scoring is in `docs/CANDIDATE_SCORECARD.md`. No engine, plugin, voice, provider or asset has been selected.

## P0.4 — target-PC, Urdu and provider feasibility

1. Run `scripts/run_target_pc_probe.ps1` on the actual Windows 10 / i3-5005U / Intel HD 5500 / 8 GB machine using Godot 4.7.2 Standard x86_64. Share `system_profile.json`, `godot_interactive_report.json` and `run_summary.json`; include the AVI/report if `-RunMovie` is used.
2. Review OpenGL/API/driver details, average and p95 frame time, memory, draw calls and fixed-FPS render throughput. Decide whether Godot Compatibility remains viable before any engine freeze.
3. Validate eSpeak NG Urdu G2P and WhisperX Urdu word/character alignment with a known transcript. Use native Pakistani Urdu audio before approving quality; Allosaurus remains optional and unverified.
4. Recheck official Pakistan availability, current free quotas, privacy/data-use terms and costs for GroqCloud, Cloudflare Workers AI, Gemini and OpenRouter. FreeMilk remains a manual coding agent, not a programmatic API. Do not connect keys or send project data without explicit approval.
5. Record exact versions, driver details, RAM/render timings, Urdu quality observations, provider limits and remaining gaps in the hardware/provider/voice reports.

## Gates and constraints

- P0.5 architecture freeze starts only after P0.4 feasibility evidence is reviewed.
- P0.6 bounded proofs start only after P0.5.
- P0.7 is the final Phase 0 freeze; do not begin production features before it.
- Preserve all current FastAPI/SQLite/browser and Story Generator work. Do not reset repositories, delete features, or restart audits from zero.
- Local-first and no mandatory paid API remain binding. Keep manual voice recording, manual viseme editing and manual AI handoff fallbacks.
