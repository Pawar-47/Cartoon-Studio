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
from app.character_foundry import (
    FEMALE_MASTER_TEMPLATE_ID,
    MORPH_TARGETS,
    default_character_recipe,
    validate_character_recipe,
)
from app.engine import GodotEngineAdapter
from app.rig_analysis import REQUIRED_HUMANOID_BONES, analyze_rig


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
            recipe = None
            if kind == "character":
                recipe = default_character_recipe("ci-character-proof")
                recipe["parameters"].update({
                    "head_width": 0.35, "jaw_width": 0.25,
                    "eye_spacing": 0.20, "torso_width": 0.15,
                })
                recipe["hair_style"] = "spiky"
                recipe = validate_character_recipe(recipe)
            result = worker.generate(
                project_root=project, asset_id=asset_id,
                asset_kind=kind, name=name, recipe=recipe, timeout_seconds=900
            )
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
                required_targets = set(MORPH_TARGETS) | {
                    "GazeLeft", "GazeRight", "GazeUp", "GazeDown",
                    "Frown", "BrowRaise", "BrowInnerDown", "BrowDown",
                    "EyesWide", "Squint", "Smile", "JawOpen", "Blink", "Open",
                    "Phoneme_A", "Phoneme_O"
                }
                if not required_targets.issubset(target_names):
                    raise RuntimeError(
                        "character: missing facial morph targets "
                        + ", ".join(sorted(required_targets - target_names))
                    )
                if godot_inspection.get("skeleton_count", 0) != 1:
                    raise RuntimeError(
                        "character: Godot did not import exactly one Blender skeleton"
                    )
                imported_bones = {
                    str(bone.get("name", ""))
                    for skeleton in godot_inspection.get("skeletons", [])
                    for bone in skeleton.get("bones", [])
                }
                missing_bones = set(REQUIRED_HUMANOID_BONES) - imported_bones
                if len(imported_bones) != 19:
                    raise RuntimeError(
                        f"character: expected 19 rig bones, imported {len(imported_bones)}"
                    )
                if missing_bones:
                    raise RuntimeError(
                        "character: Blender rig is missing canonical bones "
                        + ", ".join(sorted(missing_bones))
                    )
                rig_analysis = analyze_rig(godot_inspection)
                if (
                    rig_analysis.get("matched_bone_count")
                    != rig_analysis.get("required_bone_count")
                    or rig_analysis.get("hierarchy_validation", {}).get("status") != "valid"
                ):
                    raise RuntimeError(
                        "character: canonical humanoid rig mapping/hierarchy is invalid"
                    )
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
            sources = [
                result.source_path, result.glb_path,
                result.manifest_path, result.preview_path,
            ]
            recipe_input = result.glb_path.parent / "recipe-input.json"
            if recipe_input.is_file():
                sources.append(recipe_input)
            for source in sources:
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
        female_recipe = default_character_recipe(
            "ci-character-female-proof", FEMALE_MASTER_TEMPLATE_ID
        )
        female_recipe["hair_style"] = "long"
        female_recipe["hair_color"] = "#4a2419"
        female_recipe = validate_character_recipe(female_recipe)
        female_result = worker.generate(
            project_root=project, asset_id="ci-character-female-proof",
            asset_kind="character", name="Pakistani Female Character",
            recipe=female_recipe, timeout_seconds=900,
        )
        female_inspection = godot.inspect_glb(
            female_result.glb_path, allowed_root=project, timeout_seconds=180
        )
        female_bones = {
            str(bone.get("name", ""))
            for skeleton in female_inspection.get("skeletons", [])
            for bone in skeleton.get("bones", [])
        }
        if len(female_bones) != 19 or set(REQUIRED_HUMANOID_BONES) - female_bones:
            raise RuntimeError("female character: canonical 19-bone rig failed import")
        female_rig_analysis = analyze_rig(female_inspection)
        if (
            female_rig_analysis.get("matched_bone_count")
            != female_rig_analysis.get("required_bone_count")
            or female_rig_analysis.get("hierarchy_validation", {}).get("status") != "valid"
        ):
            raise RuntimeError(
                "female character: canonical humanoid rig mapping/hierarchy is invalid"
            )
        female_targets = {
            str(target.get("name", ""))
            for target in female_inspection.get("morph_targets", [])
        }
        required_face_targets = {
            "GazeLeft", "GazeRight", "GazeUp", "GazeDown",
            "Frown", "BrowRaise", "BrowInnerDown", "BrowDown",
            "EyesWide", "Squint", "Smile", "JawOpen", "Blink", "Open",
            "Phoneme_A", "Phoneme_O",
        }
        if not required_face_targets.issubset(female_targets):
            raise RuntimeError(
                "female character: Godot did not import facial controls "
                + ", ".join(sorted(required_face_targets - female_targets))
            )
        if female_inspection.get("morph_target_count", 0) < len(MORPH_TARGETS) + len(required_face_targets):
            raise RuntimeError("female character: complete facial morph set failed import")
        female_target = args.output / "character-female"
        female_target.mkdir(parents=True, exist_ok=True)
        for source in (
            female_result.source_path, female_result.glb_path,
            female_result.manifest_path, female_result.preview_path,
            female_result.glb_path.parent / "recipe-input.json",
        ):
            if source.is_file():
                shutil.copy2(source, female_target / source.name)
        summary.append({
            "kind": "character-female", "name": "Pakistani Female Character",
            "blender_version": female_result.blender_version,
            "elapsed_seconds": female_result.elapsed_seconds,
            "godot_skeleton_count": female_inspection.get("skeleton_count", 0),
            "godot_morph_target_count": female_inspection.get("morph_target_count", 0),
            "rig_ready": True,
            "matched_bone_count": female_rig_analysis.get("matched_bone_count", 0),
            "required_bone_count": female_rig_analysis.get("required_bone_count", 0),
        })
        report = {"blender": status, "godot": godot_status, "assets": summary}
        (args.output / "blender-runtime-report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())