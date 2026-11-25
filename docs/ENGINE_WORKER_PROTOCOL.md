# Godot Native Worker Protocol — P2.1

**Protocol version:** 1  
**Engine:** Godot 4.7.2-stable, Compatibility renderer  
**Transport:** one supervised headless process per request; UTF-8 JSON request/response files in a private temporary directory.

## Process contract

The Python adapter launches the bundled executable with:

```text
Godot_v4.7.2-stable_win64.exe --headless --path <worker-project> --script res://worker.gd -- --request-file=<request.json> --response-file=<response.json>
```

The adapter uses argument arrays (never a shell), a bounded timeout, optional cancellation and guaranteed terminate/kill cleanup. Request/response files and captured worker output live in a private temporary directory; concise structured JSONL records are retained in the per-user application log directory.

## Request

```json
{
  "protocol_version": 1,
  "request_id": "UUID",
  "operation": "ping",\n  "payload": {}
}
```

The second supported operation is `inspect_glb`, with `payload.project_root` and an absolute `payload.source_path`. Both Python and the worker independently verify that the asset resolves beneath the project root. Only GLB files are accepted; the API accepts a project-relative path, never a client-supplied absolute path.

## Response

Every response includes `protocol_version`, the matching `request_id`, `ok`, `engine_version` and renderer metadata. A successful `ping` returns the capability list. A successful GLB inspection returns mesh, skeleton, animation-player, animation and node counts. Errors return a stable `error_code` and human-readable `error`; nonzero process exit codes are treated as failures.

## Security and limits

- Worker process is local and headless; no network listener or cloud service is opened.
- Request/response files are private temporary files and are not placed in the project.
- Python resolves symlinks and rejects absolute paths, parent traversal, paths outside the project, non-files, non-GLB extensions and files over 512 MiB.
- The worker repeats the root-boundary check before calling `GLTFDocument.append_from_file`.
- GLB files are capped at 512 MiB before import.
- Requests have a 60-second default deadline. Callers can pass a cancellation event; timeout/cancellation terminates and waits for the child, then force-kills if needed.
- Worker logs are captured for diagnostics; no project contents or provider secrets are written to application logs.
- This batch implements engine discovery, handshake and GLB inspection only. It does not claim character creation, rigging, preview rendering or animation authoring.


## Skeleton hierarchy inspection — protocol extension

The existing `inspect_glb` operation now includes a `skeletons` array. Each entry reports the imported Skeleton3D node path, bone count, and each bone's index, name, parent index and parent name. The top-level `skeleton_count` is derived from the same collected nodes. This is metadata inspection only: it does not create a rig, validate skin weights/rest pose, or claim animation retarget compatibility.


## Imported skeleton rest-transform payload

The inspect_glb skeleton report now includes a rest_transform object per bone when available:
- origin: local rest offset [x, y, z]
- rotation: local rest quaternion [x, y, z, w]
- scale: local rest scale [x, y, z]

The Python rig analyzer preserves the transform alongside the canonical profile-bone mapping and reports local offset lengths with an explicit scene-unit/local-space note. These values are diagnostics for later retarget preparation; they are not world-space limb lengths and do not establish retarget readiness.
