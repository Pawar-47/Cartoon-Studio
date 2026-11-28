# Urdu Voice and Lip-Sync Feasibility

Urdu voice generation remains a separate production subsystem. It must not block Blender asset authoring or core local workflows.

## Requirements
- Natural conversational Pakistani Urdu, preferably Urdu script.
- Stable character-specific voice profiles and pronunciation.
- Human-editable transcript and timing.
- Word/phoneme alignment suitable for visemes.
- Manual recorded-voice fallback.
- Offline/local fallback where legally and technically practical.

## Research constraints
Evaluate model and dataset licenses separately. Measure CPU/RAM/runtime on target hardware only when a candidate is ready. Cloud TTS is optional and must not become a paid mandatory dependency. Do not upload user dialogue or voice data without explicit authorization.

## Current status
Research notes exist for eSpeak NG Urdu G2P, WhisperX Urdu alignment and cloud TTS candidates. No production Pakistani Urdu TTS/lip-sync path is verified. Prior candidate notes are historical research and require fresh version, quality, license, privacy and pricing checks before adoption.
