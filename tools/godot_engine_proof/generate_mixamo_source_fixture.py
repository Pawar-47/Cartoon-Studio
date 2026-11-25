from __future__ import annotations

import argparse
from pathlib import Path

from tools.godot_engine_proof.generate_humanoid_target_fixture import (
    NAME_MAP,
    read_glb,
    write_glb,
)


def generate_mixamo_source_fixture(source: Path, output: Path) -> None:
    document, chunks = read_glb(source)
    nodes = document.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("Source GLB has no node array.")
    found = {str(node.get("name", "")) for node in nodes if isinstance(node, dict)}
    if not set(NAME_MAP).issubset(found):
        raise ValueError("Source GLB does not contain all 15 canonical humanoid bones.")
    for node in nodes:
        if isinstance(node, dict):
            name = str(node.get("name", ""))
            if name in NAME_MAP:
                node["name"] = NAME_MAP[name]
    if not document.get("animations"):
        raise ValueError("The Mixamo source fixture must retain its imported animation.")
    write_glb(output, document, chunks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a Mixamo-named animated humanoid source GLB."
    )
    fixture_dir = Path(__file__).resolve().parent / "fixtures"
    parser.add_argument("--source", type=Path, default=fixture_dir / "proof_humanoid.glb")
    parser.add_argument(
        "--output",
        type=Path,
        default=fixture_dir / "proof_humanoid_source_mixamo.glb",
    )
    args = parser.parse_args()
    generate_mixamo_source_fixture(args.source, args.output)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
