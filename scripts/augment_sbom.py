from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Add the pinned Godot runtime to CycloneDX.")
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=Path("engine/godot_runtime.json"))
    parser.add_argument("--runtime-report", type=Path, required=True)
    parser.add_argument("--web-runtime-manifest", type=Path)
    parser.add_argument("--ffmpeg-manifest", type=Path)
    parser.add_argument("--ffmpeg-report", type=Path)
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
        "description": (
            "Official Godot Standard Windows x86_64 runtime bundled "
            "as the Cartoon Studio native worker."
        ),
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

    if args.web_runtime_manifest:
        web_manifest = json.loads(args.web_runtime_manifest.read_text(encoding="utf-8"))
        web_purl = f"pkg:npm/three@{web_manifest['version']}"
        web_component = {
            "type": "library",
            "bom-ref": web_purl,
            "name": web_manifest["component"],
            "version": web_manifest["version"],
            "purl": web_purl,
            "description": (
                "Vendored browser-side glTF/GLB viewer runtime and controls "
                "used by Cartoon Studio Character Studio."
            ),
            "licenses": [{"license": {"id": web_manifest["license"]}}],
            "externalReferences": [
                {"type": "vcs", "url": web_manifest["source"]}
            ],
            "properties": [
                {"name": "threejs.git.tag", "value": web_manifest["tag"]},
                {"name": "threejs.git.commit", "value": web_manifest["commit"]},
                {
                    "name": "threejs.vendored.files",
                    "value": ";".join(web_manifest["files"]),
                },
            ],
        }
        components[:] = [
            item for item in components if item.get("name") != web_manifest["component"]
        ]
        components.append(web_component)
        dependencies[:] = [
            item for item in dependencies if item.get("ref") != web_purl
        ]
        dependencies.append({"ref": web_purl, "dependsOn": []})

    if args.ffmpeg_manifest and args.ffmpeg_report:
        ffmpeg_manifest = json.loads(args.ffmpeg_manifest.read_text(encoding="utf-8"))
        ffmpeg_report = json.loads(args.ffmpeg_report.read_text(encoding="utf-8"))
        if ffmpeg_report.get("archive_sha256") != ffmpeg_manifest["archive_sha256"]:
            raise RuntimeError(
                "FFmpeg runtime report does not match the pinned archive manifest."
            )
        ffmpeg_purl = (
            "pkg:generic/ffmpeg/ffmpeg@"
            + ffmpeg_manifest["version"]
            + "?arch=x86_64&platform=windows&distro=bgtbn-lgpl"
        )
        ffmpeg_component = {
            "type": "application",
            "bom-ref": ffmpeg_purl,
            "name": ffmpeg_manifest["component"],
            "version": ffmpeg_manifest["version"],
            "purl": ffmpeg_purl,
            "description": (
                "LGPL FFmpeg Windows build bundled for episode MP4 assembly. "
                "It omits GPL-only encoders; a redistribution-safe video encoder "
                "is selected from the build at render time."
            ),
            "licenses": [{"license": {"id": "LGPL-2.1-or-later"}}],
            "hashes": [
                {"alg": "SHA-256", "content": ffmpeg_report["binary_sha256"]}
            ],
            "properties": [
                {
                    "name": "ffmpeg.archive.sha256",
                    "value": ffmpeg_manifest["archive_sha256"],
                },
                {
                    "name": "ffmpeg.video.encoders.allowed",
                    "value": ";".join(ffmpeg_manifest["allowed_video_encoders"]),
                },
                {
                    "name": "ffmpeg.video.encoders.forbidden",
                    "value": ";".join(ffmpeg_manifest["forbidden_video_encoders"]),
                },
            ],
            "externalReferences": [
                {"type": "distribution", "url": ffmpeg_manifest["download_url"]},
                {"type": "website", "url": ffmpeg_manifest["source_url"]},
                {"type": "license", "url": ffmpeg_manifest["license_url"]},
            ],
        }
        components[:] = [
            item
            for item in components
            if item.get("name") != ffmpeg_manifest["component"]
        ]
        components.append(ffmpeg_component)
        components.sort(key=lambda item: item.get("name", "").casefold())
        dependencies[:] = [
            item for item in dependencies if item.get("ref") != ffmpeg_purl
        ]
        dependencies.append({"ref": ffmpeg_purl, "dependsOn": []})
    args.sbom.write_text(
        json.dumps(sbom, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
