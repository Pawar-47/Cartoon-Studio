# SQLite job queue proof — P0.6

This is a deliberately isolated prototype, not the production queue. It tests the architecture's minimum reliability contract using only Python's standard library and SQLite:

- transactionally claim one scene at a time;
- persist job and scene state plus event history;
- use worker leases to recover after a simulated crash;
- preserve already completed scene outputs;
- reject stale workers after lease reassignment;
- cancel without deleting completed checkpoints;
- transition to assembly only after every scene is complete.

Run: python -m pytest tests/test_sqlite_queue_proof.py

The production implementation belongs in Phase 1/7 after P0.7 architecture freeze. Do not import this prototype directly into app code without a separate review and migration plan.
