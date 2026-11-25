# Godot Native Worker Protocol — P2.1

**Protocol version:** 1  
**Engine:** Godot 4.7.2-stable, Compatibility renderer  
**Transport:** one supervised headless process per request; UTF-8 JSON request/response files in a private temporary directory.

## Process contract

The Python adapter launches the bundled executable with:

```text
godot.exe --headless --path <worker-project> --script res://worker.gd -- --request <request.json> --response <response.json>
```

The adapter uses argument arrays (never a shell), a bounded timeout, optional cancellation, a dedicated log file and guaranteed terminate/kill cleanup. The temporary request, response and log directory is removed when the call ends.

## Request

```json
{
  "protocol_version": 1,
  "request_id": "UUID",
  "action": "handshake"
}
```

The second supported action is `inspect_glb`, with `project_root` and an absolute `asset_path`. Both Python and the worker independently verify that the asset resolves beneath the project root. Only GLB files are accepted; the API accepts a project-relative path, never a client-supplied absolute path.

## Response

Every response includes `protocol_version`, the matching `request_id`, `status` and engine metadata. A successful handshake returns the Godot version, renderer and capability list. A successful GLB inspection returns the file name/size and mesh, skeleton and animation counts. Errors return a stable `error_code` and human-readable message; nonzero process exit codes are treated as failures.

## Security and limits

- Worker process is local and headless; no network listener or cloud service is opened.
- Request/response files are private temporary files and are not placed in the project.
- Python resolves symlinks and rejects absolute paths, parent traversal, paths outside the project, non-files, non-GLB extensions and files over 512 MiB.
- The worker repeats the root-boundary check before calling `GLTFDocument.append_from_file`.
- Requests have a 60-second default deadline. Callers can pass a cancellation event; timeout/cancellation terminates and waits for the child, then force-kills if needed.
- Worker logs are captured for diagnostics; no project contents or provider secrets are written to application logs.
- This batch implements engine discovery, handshake and GLB inspection only. It does not claim character creation, rigging, preview rendering or animation authoring.
