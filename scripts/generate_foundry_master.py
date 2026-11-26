from __future__ import annotations

import argparse

from app.character_foundry import write_master_character


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the original Cartoon Studio stylized adult master GLB."
    )
    parser.add_argument("--output", default="artifacts/foundry/stylized-adult.glb")
    parser.add_argument("--recipe", default=None)
    parser.add_argument("--character-id", default="character-foundry-preview")
    args = parser.parse_args()
    glb_path, recipe_path = write_master_character(
        args.output, args.recipe, args.character_id
    )
    print(f"Generated master mesh: {glb_path}")
    print(f"Generated editable recipe: {recipe_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
