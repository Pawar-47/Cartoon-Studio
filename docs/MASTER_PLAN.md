# Cartoon Studio — Master Plan

## Mission
Deliver an installable, local-first web studio for original Urdu 3D cartoon episodes of approximately 5–7 minutes from one prompt, with persistent characters/worlds, animation, dialogue, voice, lip-sync, sound, rendering and editable projects.

## Non-negotiable principles
1. GitHub is the source of truth.
2. Read and trace the complete specification before implementation.
3. Search public GitHub before building components from scratch.
4. Reuse/adapt only after source, compatibility and license review.
5. GitHub Actions builds, tests and packages Windows; it is not a free GPU render farm.
6. Episode rendering initially runs locally on the target PC.
7. Optimize for Intel Core i3-5005U, Intel HD Graphics 5500, 8 GB RAM and SSD.
8. No mandatory paid API, cloud inference, subscription or online activation.
9. Never claim functionality or tests without evidence.
10. Deliver complete features in coherent batches and preserve existing work.

## Phases
- P0: Specification registry, traceability, open-source research, licensing and architecture.
- P1: GitHub CI, local web foundation and Windows bootstrap artifact.
- P2: Character creation, rigging, persistence and import/export.
- P3: Persistent world builder and reusable assets.
- P4: Prompt-to-story, Urdu dialogue and structured scene schema.
- P5: Animation, camera, scene orchestration and facial expression.
- P6: Urdu TTS, audio, lip-sync and manual voice fallback.
- P7: Resumable scene rendering, audio mixing, MP4 assembly and editable project.
- P8: Hardware optimization, reliability, installation and production QA.

## Current strategy
First establish repository governance and a minimal local project dashboard. Keep production architecture evidence-led. Research must determine which existing systems are integrated. Do not lock into an unverified engine or copy a large external application wholesale.
