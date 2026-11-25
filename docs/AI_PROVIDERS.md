# AI Provider Research Register

No external AI provider is currently integrated. Never store API keys in source code or commit secrets.

Investigate FreeMilk by Milq, ChatGPT Free, Gemini, Claude, Microsoft Copilot, Perplexity and other suitable free services.

For each provider record official terms, current free allowance and reset schedule, Pakistan availability, models, coding/research/file abilities, GitHub/browser/agent support, official API, automation restrictions, privacy/data retention, fallback and verification date.

Do not assume a web app has a public API. Use official APIs and supported integrations only. Never bypass quotas, extract private endpoints, automate prohibited UI flows or store provider credentials in Git.

## Local Urdu TTS candidate status
- Supertonic 2: not Urdu-capable; exclude for Urdu.
- Smol Urdu TTS V1: experimental, Apache-2.0 model card; benchmark CPU and naturalness.
- tiny-urdu: Roman Urdu only, one male voice, low quality; dataset licensing is non-commercial and repo license unclear.
- DeepSpeak-v1: experimental, 400M; not a target-PC default.
- Dia-1.6B-Urdu: too large for target hardware.
- XTTS Urdu fine-tune: 5.65 GB and base model license concerns.

No local Urdu TTS is approved yet. Keep TTS modular and provide manual recording fallback. Do not substitute Hindi or unsupported model output for Urdu.

## Updated Urdu TTS research — 2026-11-25
- **Smol Urdu TTS V1**: model card says Apache-2.0 and 135M parameters, but linked GitHub inference package has no explicit LICENSE file. It depends on PyTorch, torchaudio, Transformers, Liger Kernel and separate WavTokenizer checkpoint/config; inference uses BF16. CPU quality, memory, speed and codec rights are unverified.
- **tiny-urdu**: Roman Urdu only, one voice, small ONNX model. GitHub README says 1,000 training clips while its model card says 5,000; unresolved discrepancy. UrduTTS corpus is CC-BY-NC 4.0 and the code repo has no explicit license.
- **URDUTTS**: about 89 hours / 55,450 utterances / four male speakers reported; dataset CC-BY-NC 4.0, code MIT. Do not treat the dataset as a commercial training license.
- **Qwen-Audio-TTS 3.1 Flash**: official Alibaba Cloud documentation explicitly lists Urdu and a male Urdu voice named Sahar; only the Flash family lists Urdu among its additional languages. Qwen3-TTS system voices do not list Urdu. This is cloud-only, not an offline/local dependency. Pakistan availability, region, price, API terms, privacy, voice naturalness and Pakistani pronunciation remain P0.4 research tasks.
- No local Urdu TTS has passed licensing, quality and target-hardware tests. Keep TTS modular and retain a manual recording fallback.
