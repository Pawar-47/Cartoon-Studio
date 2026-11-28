from __future__ import annotations

import argparse
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.blender_toolchain import BlenderToolchain
from app.engine import GodotEngineAdapter


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
    parser = argparse.ArgumentParser(
        description="Run real Blender asset generation and inspect exported GLBs."
    )
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
        godot = GodotEngineAdapter(data_dir=args.output, timeout_seconds=180)
        godot_status = godot.ping()
        summary = []
        for kind, name in (("character", "Pakistani Shalwar Kameez Character"),
                           ("world", "Lahore Bazaar Lane"),
                           ("prop", "Charpai and Chai Set"),
                           ("building", "Lahore Haveli Shopfront"),
                           ("vehicle", "Pakistani Auto Rickshaw"),
                           ("vegetation", "Mango Tree")):
            asset_id = f"ci-{kind}-proof"
            result = worker.generate(project_root=project, asset_id=asset_id,
                                     asset_kind=kind, name=name, timeout_seconds=900)
            gltf = read_glb(result.glb_path)
            if result.manifest.get("culture_profile") != "pakistani_storybook_v1":
                raise RuntimeError(f"{kind}: Pakistani culture profile was not recorded")
            meshes = gltf.get("meshes", [])
            nodes = gltf.get("nodes", [])
            if not meshes or not nodes:
                raise RuntimeError(f"{kind}: exported GLB has no mesh or scene nodes")
            godot_inspection = godot.inspect_glb(
                result.glb_path, allowed_root=project, timeout_seconds=180
            )
            if not godot_inspection.get("ok"):
                raise RuntimeError(
                    f"{kind}: Godot 4.7.2 could not import the Blender GLB: "
                    + str(godot_inspection)
                )
            if kind == "character":
                if not gltf.get("skins"):
                    raise RuntimeError("character: exported GLB has no skin")
                target_names = {
                    name
                    for mesh in meshes
                    for name in mesh.get("extras", {}).get("targetNames", [])
                }
                required_targets = {
                    "Smile", "JawOpen", "Blink", "Open", "Phoneme_A", "Phoneme_O"
                }
                if not required_targets.issubset(target_names):
                    raise RuntimeError(
                        "character: missing facial morph targets "
                        + ", ".join(sorted(required_targets - target_names))
                    )
                if godot_inspection.get("skeleton_count", 0) < 1:
                    raise RuntimeError("character: Godot did not import the Blender skeleton")
                imported_targets = {
                    str(target.get("name", ""))
                    for target in godot_inspection.get("morph_targets", [])
                }
                if not required_targets.issubset(imported_targets):
                    raise RuntimeError(
                        "character: Godot did not import facial targets "
                        + ", ".join(sorted(required_targets - imported_targets))
                    )
                if not any(
                    mesh.get("skin_bound")
                    for mesh in godot_inspection.get("mesh_inventory", [])
                ):
                    raise RuntimeError("character: Godot imported no skinned mesh")
            target = args.output / kind
            target.mkdir(parents=True, exist_ok=True)
            for source in (
                result.source_path, result.glb_path,
                result.manifest_path, result.preview_path,
            ):
                shutil.copy2(source, target / source.name)
            summary.append({
                "kind": kind, "name": name, "blender_version": result.blender_version,
                "elapsed_seconds": result.elapsed_seconds, "mesh_count": len(meshes),
                "node_count": len(nodes), "skin_count": len(gltf.get("skins", [])),
                "preview": str((target / result.preview_path.name).as_posix()),
                "godot_mesh_count": godot_inspection.get("mesh_count", 0),
                "godot_skeleton_count": godot_inspection.get("skeleton_count", 0),
                "godot_morph_target_count": godot_inspection.get("morph_target_count", 0),
            })
        report = {"blender": status, "godot": godot_status, "assets": summary}
        (args.output / "blender-runtime-report.json").write_text(
            json.dumps(report, indent=2) + "\\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
