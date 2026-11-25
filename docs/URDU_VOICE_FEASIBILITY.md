# Urdu Voice, G2P and Lip-Sync Feasibility — P0.4

**Status:** research and test design only. No Pakistani Urdu sample has been processed; no TTS, G2P or alignment candidate is approved for production.

## 1. What the source code establishes

### eSpeak NG Urdu G2P
- Upstream contains an Urdu-specific rules file: https://github.com/espeak-ng/espeak-ng/blob/master/dictsource/ur_rules
- CLI supports Urdu voice selection and phoneme output: -v ur -x (eSpeak mnemonic phones), -v ur --ipa (IPA), and --phonout=FILE: https://github.com/espeak-ng/espeak-ng/blob/master/src/espeak-ng.c and https://github.com/espeak-ng/espeak-ng/blob/master/src/speak-ng.1.ronn
- This provides a useful offline grapheme-to-phoneme baseline, but Urdu orthography omits short vowels in ordinary writing and pronunciation depends on context, dialect and lexical knowledge. Its generated phone string must be reviewed by a native Pakistani Urdu speaker.
- eSpeak NG is GPL-3.0. Do not bundle or link it into the product until distribution obligations and notices are reviewed.
- It is not an approved natural Urdu TTS voice.

### WhisperX Urdu alignment
- WhisperX README documents word-level timestamps via forced alignment, CPU operation using --device cpu --compute_type int8, and the need for a language-specific alignment model: https://github.com/m-bain/whisperX
- Current upstream alignment.py explicitly maps ur to kingabzpro/wav2vec2-large-xls-r-300m-Urdu: https://github.com/m-bain/whisperX/blob/main/whisperx/alignment.py
- WhisperX is BSD-2-Clause; the Hugging Face Urdu model is a separate artifact. Inspect its model card, license and training-data provenance before redistribution.
- CPU int8 support does not establish that the 300M aligner will fit comfortably or run fast on an i3-5005U with 8 GB RAM. Measure peak RAM and alignment time with batch size 1.
- Forced alignment is not speech recognition quality assurance. If transcript words are wrong, timestamps can still be wrong; align only to a human-corrected transcript.

Suggested first command (after installing a pinned WhisperX version and its dependencies):
```powershell
whisperx .\sample_urdu.wav --language ur --align_model kingabzpro/wav2vec2-large-xls-r-300m-Urdu --device cpu --compute_type int8 --batch_size 1 --output_format json
```

### Qwen Audio TTS Urdu voice
- Official voice list names qwen-audio-3.1-tts-flash-sahar_ur (Sahar / سحر), male Urdu voice, with timestamps and SSML: https://www.alibabacloud.com/help/en/model-studio/qwen-audio-tts-voice-list
- Official HTTP API documents Singapore and China North 2 (Beijing) endpoints: https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-audio-tts/http-api
- Standard Singapore pricing listed on the model page is $0.23 per million input tokens and $1.87 per million output tokens: https://docs.qwencloud.com/models/qwen-audio-3-1-tts-flash
- It is cloud-only, paid, and not Pakistan-hosted. Pakistan account/payment access, data processing terms, Pakistani accent quality and exact timestamp semantics remain unverified. Do not send user content or enable this provider without explicit approval.

## 2. Test corpus requirements

Use a 30–60 second recording by a consenting native Pakistani Urdu speaker, recorded in a quiet room. Store locally. Prepare a verbatim transcript checked by a second listener. Include:
- aspirated/unaspirated and retroflex/dental contrasts;
- nasalization and long/short vowels;
- Urdu proper names and uncommon words;
- natural conversational speed, pauses and sentence boundaries;
- modest Urdu-English code-switching;
- one sentence with numbers/date/time spoken naturally.

Do not use synthetic Hindi as a substitute for Pakistani Urdu. Keep the same recording and corrected transcript for all alignment comparisons.

## 3. Acceptance measurements

| Test | Measurement | Required evidence |
|---|---|---|
| G2P | Human-reviewed phone correctness; missing/extra phones; names and code-switching | Raw eSpeak output + reviewer corrections |
| ASR/transcript | Word error rate against the corrected transcript | Raw transcript + edit-distance calculation |
| Alignment | Median and 95th-percentile absolute word-boundary error against manually marked boundaries | WhisperX JSON + human boundary reference |
| Runtime | Wall-clock seconds per audio second; peak RAM; CPU utilization | Timed command log and system monitor |
| Robustness | OOV names, pauses, overlapping speech, code-switching | Per-case failure notes |
| Lip-sync mapping | Viseme confusion, closure timing for /p,b,m/, jaw/open-vowel timing | Frame-by-frame review against the audio |

Provisional quality gate (must be reviewed with native speaker): at least 90% of words receive usable timestamps; median boundary error <=150 ms and p95 <=300 ms on clean single-speaker speech; all critical names and code-switched words manually reviewed. These are project acceptance targets, not claims about current model performance.

## 4. Recommended modular flow (not yet frozen)

1. Approved Urdu script and human-corrected transcript.
2. Human recording or separately approved TTS.
3. ASR/transcript comparison and word-level forced alignment.
4. G2P/phoneme sequence for fallback timing and viseme mapping.
5. Urdu-specific viseme table (multiple phonemes may share a viseme).
6. Manual timeline/viseme correction.
7. Store transcript, audio, timings and viseme events as editable project data.

Keep audio and timing independent from the 3D engine. Never make cloud TTS mandatory; manual recording must always work offline.

## 5. Open blockers

- Actual Pakistani Urdu recording and transcript are not yet supplied.
- eSpeak Urdu pronunciation accuracy has not been reviewed by a native speaker.
- WhisperX Urdu aligner memory, speed and timing accuracy on target hardware are unknown.
- Hugging Face aligner model license/data provenance needs separate review.
- Qwen voice access, price, privacy and accent quality need approval and testing.
- No automatic Urdu lip-sync system is proven. Manual viseme editing remains required.
