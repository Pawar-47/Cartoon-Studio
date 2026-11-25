# Next Steps

## Current checkpoint — 2026-11-25

P0.1–P0.3 are complete. P0.4 is in progress. Latest verified main HEAD before this documentation batch: 46ac1a8e3a1523a0db52c6cc600e8cca82750bdd, CI #87 SUCCESS. Exact master brief and 171-row requirement/traceability baseline remain preserved.

## P0.4 — complete feasibility evidence

### A. Target hardware
1. Run scripts/run_target_pc_probe.ps1 on the actual Windows 10 / i3-5005U / Intel HD 5500 / 8 GB machine using Godot 4.7.2 Standard x86_64.
2. Share system_profile.json, godot_interactive_report.json, run_summary.json, and optional AVI/report from -RunMovie.
3. Review installed driver, OpenGL/API, average/p95 frame time, memory, draw calls and fixed-FPS throughput. Do not freeze Godot before this.

### B. Urdu G2P, alignment and TTS
1. Prepare a 30–60 second native Pakistani Urdu sample with speaker consent and an exact human-corrected transcript. Include retroflex/aspirated consonants, nasalization, vowel length, proper names and natural code-switching.
2. Run eSpeak NG -v ur --ipa and -v ur -x on the exact transcript; manually assess each word and phoneme. eSpeak NG is a G2P/phoneme diagnostic only, not an approved natural voice.
3. Run WhisperX with --language ur, explicit aligner kingabzpro/wav2vec2-large-xls-r-300m-Urdu, CPU --device cpu --compute_type int8 --batch_size 1. Measure peak RAM and elapsed time; compare word boundaries to human timestamps. It may be too heavy for the 8 GB target.
4. Keep manual transcript correction and manual viseme/timing editing as mandatory fallback. No Urdu TTS or automatic lip-sync is approved yet.
5. Qwen Sahar sample is optional only if the user explicitly approves sending test text/audio to an external paid service after reviewing its region, price and privacy terms.

### C. Provider feasibility
- Verify live project/account quotas and terms before enabling Gemini, Groq, Cloudflare or OpenRouter. Do not assume web-published base quotas equal the user's account quota.
- Keep FreeMilk as manual coding agent only; do not script or scrape its UI.
- No keys, payment methods, external accounts or user data are to be connected/sent without explicit approval.

## Gates

- P0.5 architecture freeze only after target hardware, Urdu and provider evidence is reviewed.
- P0.6 bounded proofs only after P0.5.
- P0.7 final Phase 0 compliance review/freeze only after P0.2–P0.6.
- No production feature work before P0.7; preserve the existing Story Generator but do not expand it until Phase 4.
- Phase 2 waits for Phase 1's tested installation gate.
