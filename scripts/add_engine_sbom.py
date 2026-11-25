from __future__ import annotations

import json
import sys
from pathlib import Path

GODOT_SHA256 = "731980f9608d61333e5baf54a2ef17210acc7a538446c0cb9969f002aca1e953"
GODOT_RELEASE = "https://github.com/godotengine/godot/releases/tag/4.7.2-stable"
GODOT_ARCHIVE = (
    "https://github.com/godotengine/godot/releases/download/4.7.2-stable/"
    "Godot_v4.7.2-stable_win64.exe.zip"
)
COMPONENT_REF = "godot-engine-4.7.2-stable-win64"


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: add_engine_sbom.py <cyclonedx-json>")
    path = Path(sys.argv[1])
    bom = json.loads(path.read_text(encoding="utf-8"))
    if bom.get("bomFormat") != "CycloneDX":
        raise SystemExit("The dependency inventory is not a CycloneDX BOM.")
    components = bom.setdefault("components", [])
    if not isinstance(components, list):
        raise SystemExit("CycloneDX components must be an array.")
    components[:] = [item for item in components if item.get("bom-ref") != COMPONENT_REF]
    components.append(
        {
            "type": "framework",
            "bom-ref": COMPONENT_REF,
            "name": "Godot Engine",
            "version": "4.7.2-stable",
            "description": "Pinned Windows x86_64 native worker runtime, headless mode.",
            "purl": "pkg:generic/godotengine/godot@4.7.2-stable?arch=x86_64&os=windows",
            "scope": "required",
            "licenses": [{"license": {"id": "MIT"}}],
            "hashes": [{"alg": "SHA-256", "content": GODOT_SHA256}],
            "externalReferences": [
                {"type": "distribution", "url": GODOT_ARCHIVE},
                {"type": "vcs", "url": "https://github.com/godotengine/godot"},
                {"type": "website", "url": GODOT_RELEASE},
            ],
            "properties": [
                {"name": "cartoon-studio:runtime-path", "value": "_internal/engine/godot.exe"},
                {"name": "cartoon-studio:worker-protocol", "value": "1"},
            ],
        }
    )
    path.write_text(json.dumps(bom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
