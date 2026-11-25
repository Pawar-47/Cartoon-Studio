from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Add the pinned Godot runtime to CycloneDX.")
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("engine/godot_runtime.json"))
    parser.add_argument("--runtime-report", type=Path, required=True)
    args = parser.parse_args()

    sbom = json.loads(args.sbom.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    runtime_report = json.loads(args.runtime_report.read_text(encoding="utf-8"))
    if runtime_report.get("archive_sha256") != manifest["archive_sha256"]:
        raise RuntimeError("Godot runtime report does not match the pinned archive manifest.")
    purl = (
        "pkg:generic/godotengine/godot@"
        + manifest["version"]
        + "?arch=x86_64&platform=windows"
    )
    component = {
        "type": "framework",
        "bom-ref": purl,
        "name": manifest["component"],
        "version": manifest["version"],
        "purl": purl,
        "description": "Official Godot Standard Windows x86_64 runtime bundled as the Cartoon Studio native worker.",
        "licenses": [{"license": {"id": manifest["license"]}}],
        "hashes": [
            {
                "alg": "SHA-256",
                "content": runtime_report["binary_sha256"],
            }
        ],
        "properties": [
            {
                "name": "godot.archive.sha256",
                "value": manifest["archive_sha256"],
            }
        ],
        "externalReferences": [
            {
                "type": "distribution",
                "url": manifest["download_url"],
            },
            {
                "type": "website",
                "url": "https://godotengine.org",
            },
        ],
    }

    components = sbom.setdefault("components", [])
    components[:] = [
        item
        for item in components
        if item.get("name") != manifest["component"]
    ]
    components.append(component)
    components.sort(key=lambda item: item.get("name", "").casefold())
    dependencies = sbom.setdefault("dependencies", [])
    dependencies[:] = [item for item in dependencies if item.get("ref") != purl]
    dependencies.append({"ref": purl, "dependsOn": []})
    args.sbom.write_text(
        json.dumps(sbom, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
