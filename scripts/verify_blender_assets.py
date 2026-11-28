from __future__ import annotations

import argparse
import json
import shutil
import struct
import tempfile
from pathlib import Path

from app.blender_toolchain import BlenderToolchain


def read_glb(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise RuntimeError(f"{path.name}: invalid GLB header")
    version, total = struct.unpack_from("<II", data, 4)
    if version != 2 or total != len(data):
        raise RuntimeError(f"{path.name}: invalid GLB version or declared length")
    chunk_length, chunk_type = struct.unpack_from("<I4s", data, 12)
    if chunk_type != b"JSON" or 20 + chunk_length > len(data):
        raise RuntimeError(f"{path.name}: missing JSON chunk")
    return json.loads(data[20:20 + chunk_length].decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real Blender asset generation and inspect exported GLBs.")
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cartoon-studio-blender-") as temporary:
        project = Path(temporary) / "project"
        project.mkdir()
        worker = BlenderToolchain(args.output, executable=args.blender, timeout_seconds=900)
        status = worker.status()
        if not status["supported"]:
            raise RuntimeError(f"Blender runtime is not supported: {status}")
        summary = []
        for kind, name in (("character", "Foundry Character Proof"),
                           ("world", "Storybook Village Proof"),
                           ("prop", "Treasure Chest Proof")):
            asset_id = f"ci-{kind}-proof"
            result = worker.generate(project_root=project, asset_id=asset_id,
                                     asset_kind=kind, name=name, timeout_seconds=900)
            gltf = read_glb(result.glb_path)
            meshes = gltf.get("meshes", [])
            nodes = gltf.get("nodes", [])
            if not meshes or not nodes:
                raise RuntimeError(f"{kind}: exported GLB has no mesh or scene nodes")
            if kind == "character":
                if not gltf.get("skins"):
                    raise RuntimeError("character: exported GLB has no skin")
                if not any(primitive.get("targets") for mesh in meshes
                           for primitive in mesh.get("primitives", [])):
                    raise RuntimeError("character: exported GLB has no facial morph targets")
            target = args.output / kind
            target.mkdir(parents=True, exist_ok=True)
            for source in (result.source_path, result.glb_path, result.manifest_path, result.preview_path):
                shutil.copy2(source, target / source.name)
            summary.append({
                "kind": kind, "name": name, "blender_version": result.blender_version,
                "elapsed_seconds": result.elapsed_seconds, "mesh_count": len(meshes),
                "node_count": len(nodes), "skin_count": len(gltf.get("skins", [])),
                "preview": str((target / result.preview_path.name).as_posix()),
            })
        report = {"blender": status, "assets": summary}
        (args.output / "blender-runtime-report.json").write_text(
            json.dumps(report, indent=2) + "\\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
