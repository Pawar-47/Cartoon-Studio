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

## Provider API and free-allowance research — 2026-11-25

| Provider | Current documented free access | API status | Main caveat / intended use |
|---|---|---|---|
| FreeMilk | Daily model allowance; current website lists GLM 5.3 Flash, DeepSeek V4.1 Flash and GPT-6 Luna. Exact daily quota is not published and terms say limits/models may change. | Treat as app-only agent, not a callable backend API. Terms prohibit scripts, bots, unofficial clients and direct server calls; use only supported app features/GitHub integration. | Coding sessions include prompts, responses, files read/written and build logs. Model providers receive session content; eligible sessions may be licensed to AI data partners and used for training. Privacy policy provides an email opt-out for future licensing/training. Do not send secrets or confidential code without authorization. |
| Google Gemini Developer API | Free tier provides free input/output for selected models; model-specific limits apply. | Official API. | Free-tier content may be used to improve Google products; paid tier says it is not. Use only suitable non-sensitive data until privacy/terms reviewed. |
| GroqCloud | Free tier has model-specific RPM/RPD/TPM/TPD limits. Current docs list gpt-oss-120b, gpt-oss-20b and qwen3.8-27b at 30 RPM, 1,000 RPD, 8K TPM and 200K TPD; verify account console because limits change. | Official OpenAI-compatible API. | Candidate for text/story/schema tasks; rate limits are per organization/model and can change. |
| Cloudflare Workers AI | Workers Free includes 10,000 Neurons/day, resetting at 00:00 UTC. Beyond the allowance requires Workers Paid at $0.011 per 1,000 Neurons; some resource-heavy models already require paid access. | Official API / Workers binding. | Model-specific neuron consumption and availability vary. Candidate for low-cost fallback, not guaranteed unlimited free inference. |
| OpenRouter | Free model variants: 20 requests/minute and 50 requests/day; after at least $10 lifetime credit purchase, free-model cap rises to 1,000/day. Current catalog shows 25+ free models and four free providers. | Official OpenAI-compatible API and dynamic `openrouter/free` routing. | Model/provider availability and provider-side limits can change; failed attempts count toward daily cap. Not a production SLA. |
| GitHub Copilot Free | Up to 2,000 code completions/month plus limited access to selected Copilot features. | Developer agent/UI, not a general-purpose model API for Cartoon Studio. | Useful for manual GitHub coding assistance; monthly allowance, not a daily API quota. |
| ChatGPT Free / Plus | Consumer app usage limits vary. | API billing is separate from ChatGPT subscription; Free/Plus does not include API inference. | Use ChatGPT as a manual supported tool; do not assume subscription provides API credits. |
| Claude Free | Consumer web/desktop/mobile plan with usage limits. | Claude Platform API is separate; new API users may receive trial credits, not a permanent free tier. | Manual research/coding assistant only unless paid API is explicitly approved. |
| Perplexity Standard | Basic searches are described as practically unlimited; Pro searches are very limited. | API Platform is a separate product. | Useful for manual research, not a free backend API. |
| Mistral Free mode | Monthly budget for Vibe/Studio testing. | Current Mistral docs state Free mode does not include API access; API keys require billing activation/pay-as-you-go. | Do not treat the consumer/Studio free budget as a free app API. |
| Cerebras Developer | $5 free starting credit. | Official API. | Trial credit only; subsequent use is pay-as-you-go, not a renewable daily free allowance. |
| GitHub Models | Retired 2026-07-30. | Playground, model catalog and inference API are no longer available. | Exclude; do not build against it. |

### FreeMilk operating restrictions and privacy

- Official Terms: https://www.freemilk.ai/terms
- Official Privacy Policy: https://www.freemilk.ai/privacy-policy
- Pakistan App Store listing: https://apps.apple.com/pk/app/freemilk-ai-code-ide-agents/id6767423666
- Terms state that FreeMilk sends prompts to third-party models, daily allowances/limits can change, and direct scripted/bot/unofficial-client access or direct calls to its servers are prohibited. Use only the official app and supported GitHub/integration features.
- Coding Sessions include prompts, model responses, files the agent reads/writes, actions, tools, build results and logs. The privacy policy says sessions are shared with model providers and advertising partners; eligible sessions may be de-identified/licensed to AI data partners for model evaluation/training. Users can email support@freemilk.ai to opt out of future coding-session licensing/AI training. This does not retroactively remove already licensed sessions or models already trained.
- FreeMilk can be a useful manual coding agent with GitHub integration, but it must not be reverse-engineered or used as a programmatic backend. Avoid uploading secrets or confidential material; review its privacy terms and opt-out choice first.

### P0.4 provider feasibility shortlist

1. GroqCloud — current free API limits and supported models; test structured JSON and Pakistani Urdu quality.
2. Cloudflare Workers AI — daily free neuron allowance; measure actual per-request neuron consumption and eligible models.
3. Gemini Developer API — free token tier, but explicitly account for free-tier data-use policy.
4. OpenRouter — dynamic multi-provider fallback with a low free daily request cap.
5. FreeMilk and Copilot — manual developer-agent handoff only, not in-app API adapters.
6. ChatGPT, Claude and Perplexity free apps — manual supported workflows only unless a separate official API/paid benefit is approved.

No API key or provider has been connected. No paid service is approved. P0.4 must verify Pakistan availability, account-specific quotas, data handling, API terms, output quality and whether the selected provider can legally be used in the intended application.
