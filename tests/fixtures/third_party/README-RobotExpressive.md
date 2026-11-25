# RobotExpressive facial morph fixture

- Source repository: https://github.com/mrdoob/three.js
- Pinned source commit: `eba30de865cfbf31ac736f792defd9a60ff28d57`
- Source file: `examples/models/gltf/RobotExpressive/RobotExpressive.glb`
- SHA-256: `047f5e5fb3bb6d378bd1df16ca6137f2a596c99b3a1b5690b4020c05aaf6f319`
- License: CC0 1.0 Universal
- Original model: Tomás Laulhé (Quaternius)
- Modifications: Don McCurdy, including three facial-expression morph targets

The facial morphs are attached to the `Head_4` mesh. The upstream Three.js
skinning/morph example exposes the expression dictionary on that mesh. The
fixture fetch script downloads the exact pinned binary during CI and verifies
its SHA-256 before the Godot import test uses it. The binary is intentionally
not duplicated in Git; this attribution record and pinned acquisition logic
are the project source of truth for this test asset.
