# Optional AI Providers — Non-Blocking Policy

The Cartoon Studio core must work without external AI. Providers may assist with story drafting, dialogue refinement, research or code assistance, but cannot be required for Blender asset creation, project editing, Godot production or MP4 assembly.

## Rules
- No mandatory paid API, API key, subscription, credits or cloud account.
- No provider quota may stop local core workflows.
- Use official APIs/integrations only; never bypass quotas or automate prohibited consumer interfaces.
- Manual copy/paste handoff is acceptable.
- Verify current Pakistan availability, pricing, limits, privacy, retention and terms before integration. Do not describe a limited free tier as unlimited.
- Never upload private project assets or dialogue without explicit user authorization and provider review.
- Store secrets outside Git and project manifests.

## Current decision
No external provider is a required dependency. FreeMilk by Milq and other free AI applications may be used manually as optional assistants. API integrations remain opt-in and provider-specific. The application must degrade gracefully when all providers are unavailable.
