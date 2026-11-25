## Provider API and free-allowance research — 2026-11-25

| Provider | Official free allowance / access evidence | Pakistan and data caveat | Current decision |
|---|---|---|---|
| FreeMilk | Daily allowance; exact quota is not publicly fixed. | Treat only as supported manual coding agent; no scripted/API automation. Session content may be processed by providers/data partners per terms. | Not a backend provider. |
| Gemini Developer API | Free tier exists for selected models; per-model/project rate limits change. Free-tier content may be used to improve Google products; paid tier excludes that use. | Google's official Gemini API/AI Studio supported-region list includes Pakistan. Actual API key, project eligibility and current quota still need a live account check. | Strong text/story candidate; do not send confidential data on free tier. |
| GroqCloud | Official rate-limit docs list model-specific limits; current table includes GPT-OSS 120B/20B and Qwen3.8-27B at 30 RPM, 1,000 RPD, 8K TPM and 200K TPD. Account/plan limits can differ; inspect the organization dashboard. | Groq says its data centres are in US, Australia, Canada, Finland and Saudi Arabia; regional processing endpoints are an Enterprise arrangement. Pakistan user access is not the same as Pakistan data residency. | Strong fast text and transcription API candidate; not a free-unlimited guarantee. |
| Cloudflare Workers AI | 10,000 Neurons/day free; paid overage is $0.011 per 1,000 Neurons; resets 00:00 UTC. Some frontier models require paid billing. | Regional execution controls for Workers are not a blanket guarantee of model inference/data residency. Confirm actual account and model availability. | Useful limited free fallback; model-dependent. |
| OpenRouter | Free variants currently 20 RPM and 50 RPD; cap rises to 1,000 RPD after at least $10 lifetime credits. Other $0 models may have provider-specific caps. | Requests route to third-party providers; data handling and availability depend on selected provider/model. | Useful experimentation/fallback, not dependable daily production capacity. |
| QwenCloud | Qwen Audio TTS 3.1 Flash is paid: official page lists $0.23/M input tokens and $1.87/M output tokens in Singapore; rate limit shown as 180 RPM. | TTS API documents Singapore and China North 2 (Beijing) endpoints; Pakistan is not a serving region. Cross-border processing and account/payment eligibility need review. | Optional Urdu voice candidate only; not free or local. |

Official references (checked 2026-11-25):
- Gemini free-tier pricing/data use: https://ai.google.dev/gemini-api/docs/pricing
- Gemini API supported regions (Pakistan listed): https://ai.google.dev/gemini-api/docs/available-regions
- Groq limits/models: https://console.groq.com/docs/rate-limits and https://console.groq.com/docs/models
- Groq data-centre / residency FAQ: https://trust.groq.com/faq
- Cloudflare Workers AI pricing and limits: https://developers.cloudflare.com/workers-ai/platform/pricing/ and https://developers.cloudflare.com/workers-ai/platform/limits/
- OpenRouter free model limits: https://openrouter.ai/collections/free-models and https://openrouter.ai/docs/api-reference/limits
- Qwen TTS voice, regions, price: https://www.alibabacloud.com/help/en/model-studio/qwen-audio-tts-voice-list and https://docs.qwencloud.com/api-reference/speech-synthesis/qwen-audio-tts/http-api and https://docs.qwencloud.com/models/qwen-audio-3-1-tts-flash

Correction to earlier shorthand: Pakistan is officially listed for Gemini API/AI Studio. Qwen TTS lists Singapore/China North 2 serving regions, and Groq's data centres are not in Pakistan. Do not conflate account access with data residency. No account has been tested and no API key is connected.