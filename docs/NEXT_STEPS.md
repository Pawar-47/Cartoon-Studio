# Next Steps — 2026-11-25

## Active batch — Phase 2 Character Studio

1. Confirm Windows CI #240/#241 and dedicated Godot proof #10.
2. Implement the user-facing non-destructive retarget operation for imported GLB source and target rigs, using the validated Godot modifier/profile arrangement.
3. Add target skeleton binding and clear diagnostics for missing/ambiguous bones, invalid hierarchy, rest transforms and incompatible animation tracks.
4. Validate with more than one real-world humanoid GLB, including different bone naming conventions and body proportions.
5. Confirm imported target pose playback, scene save/reopen and source-asset integrity.
6. Test existing facial morph-target controls on real blend-shape models; then complete deterministic export/round-trip.

## Latest implementation and evidence

- Indexed humanoid profile mapping: 1cac9e93adff60bd051c4029df829ebc5fc662f0.
- Hierarchy diagnostics surfaced in Character Studio: 2b4a88248492833ddd04cd33e9557ebc3a13052b.
- Hierarchy completeness correction: 49d695a57e66858832ce1f3e033467c8151e83cf.
- Imported rest-transform reporting: fbfb0724bb1eec480afe55d3e17095dbd1f115df; association correction: 441f22db6cef1acf8b6dc17f7f1187d0dfdefd53.
- Skinned humanoid fixture and real worker test: c8f7bb3ac83ac46975e385648f773f4e20b951c8.
- Imported humanoid fixture in native proof: ae63724b12a0f2cf670469ac74613acaee07e15c.
- Imported-source to differently proportioned target retarget proof: 59a8ab1510078de7167aaf06147aaeb73509d5ad; explicit rest assignment: edd562d816ab9c9045aeba14753a42a7eb38e565.
- Imported retarget save/reopen assertion: aadce3ed4c8444a3130652f14cc85cdfd4db697b.
- Windows CI #237 and #238 passed. Godot proof #8 and #9 passed. Latest #241 and proof #10 are pending.

## Deferred to their specified phases

- World Builder: Phase 3.
- Full Story/Scene Engine: Phase 4; preserve the existing partial Story Generator and keep its expansion frozen until then.
- Production animation library and timeline: Phase 5.
- Pakistani Urdu voice/TTS/lip-sync: Phase 6.
- Full episode rendering, audio mix and MP4: Phase 7.
- Target-PC benchmarks and optimization: Phase 8.

## Policy

Work in coherent feature batches, preserve all existing work, use GitHub main as the source of truth, and do not use physical-PC testing as an early gate. Do not call the entire project complete while Phases 3–7 remain open.
