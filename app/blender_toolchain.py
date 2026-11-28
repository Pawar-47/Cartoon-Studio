# ruff: noqa: E501, E302
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

AssetKind = Literal["character", "world", "prop"]
KINDS = {"character", "world", "prop"}
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _-]{0,63}$")

class BlenderToolchainError(RuntimeError):
    pass


class BlenderUnavailableError(BlenderToolchainError):
    pass


class BlenderTimeoutError(BlenderToolchainError):
    pass


class BlenderExecutionError(BlenderToolchainError):
    pass

@dataclass(frozen=True)
class BlenderAssetResult:
    asset_id: str
    asset_kind: AssetKind
    name: str
    source_path: Path
    glb_path: Path
    manifest_path: Path
    preview_path: Path
    blender_version: str
    elapsed_seconds: float
    manifest: dict[str, Any]

class BlenderToolchain:
    """Optional supervised Blender authoring worker shared by character, world and prop tools."""
    def __init__(self, data_dir: Path, executable: Path | None = None,
                 script_path: Path | None = None, timeout_seconds: float = 600.0):
        self.data_dir = Path(data_dir).expanduser().resolve()
        root = Path(__file__).resolve().parents[1]
        override = os.environ.get("CARTOON_STUDIO_BLENDER_PATH", "").strip()
        if executable is not None:
            self.executable = Path(executable).expanduser()
        elif override:
            self.executable = Path(override).expanduser()
        else:
            found = shutil.which("blender")
            candidates = [Path(found)] if found else []
            candidates += [
                Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Blender Foundation/Blender 4.5/blender.exe",
                Path("/usr/bin/blender"), Path("/usr/local/bin/blender"),
                Path("/Applications/Blender.app/Contents/MacOS/Blender"),
            ]
            self.executable = next((p for p in candidates if p.is_file()), candidates[0] if candidates else Path("blender"))
        self.script_path = Path(script_path).resolve() if script_path else root / "scripts/blender/asset_factory.py"
        self.timeout_seconds = max(1.0, float(timeout_seconds))

    @property
    def available(self) -> bool:
        return self.executable.is_file() and self.script_path.is_file()

    def version(self) -> dict[str, Any]:
        if not self.executable.is_file():
            raise BlenderUnavailableError("Blender executable was not found.")
        try:
            result = subprocess.run([str(self.executable), "--version"], capture_output=True,
                                    text=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BlenderExecutionError(f"Could not query Blender version: {exc}") from exc
        match = re.search(r"Blender\s+(\d+)\.(\d+)\.(\d+)", result.stdout + result.stderr)
        if result.returncode or not match:
            raise BlenderExecutionError("Blender returned an unreadable version response.")
        parts = tuple(map(int, match.groups()))
        supported = (4, 2, 0) <= parts < (5, 0, 0)
        return {"version": ".".join(map(str, parts)), "version_tuple": list(parts),
                "supported": supported,
                "message": "Blender version is supported." if supported
                else "Use a qualified Blender 4.x release (4.2.0 or newer); Blender 5.x is not yet qualified."}

    def status(self) -> dict[str, Any]:
        if not self.executable.is_file():
            return {"available": False, "supported": False, "version": None,
                    "executable": None, "supported_asset_kinds": sorted(KINDS),
                    "message": "Blender is optional. Install Blender 4.2 LTS or newer (4.x) to enable offline authoring."}
        info = self.version()
        return {"available": True, "executable": str(self.executable),
                "supported_asset_kinds": sorted(KINDS), **info}

    def generate(self, *, project_root: Path, asset_id: str, asset_kind: AssetKind,
                 name: str, timeout_seconds: float | None = None) -> BlenderAssetResult:
        if asset_kind not in KINDS:
            raise ValueError("asset_kind must be character, world, or prop.")
        if not isinstance(asset_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", asset_id):
            raise ValueError("asset_id must contain 1-64 safe identifier characters.")
        if not isinstance(name, str) or not NAME.fullmatch(name.strip()):
            raise ValueError("name must be 1-64 letters, numbers, spaces, underscores, or hyphens.")
        if not self.executable.is_file():
            raise BlenderUnavailableError("Blender is not installed; existing projects remain usable.")
        if not self.script_path.is_file():
            raise BlenderUnavailableError(f"Blender asset factory is missing: {self.script_path}")
        info = self.version()
        if not info["supported"]:
            raise BlenderExecutionError(info["message"])
        root = Path(project_root).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("project_root must be an existing project directory.")
        output = (root / "assets" / "blender" / asset_id).resolve()
        if root not in output.parents:
            raise ValueError("Blender output directory escapes the project.")
        output.mkdir(parents=True, exist_ok=True)
        source, glb, manifest_path = (output / f"{asset_id}.blend",
                                      output / f"{asset_id}.glb", output / "manifest.json")
        preview = output / f"{asset_id}_preview.png"
        if any(path.exists() for path in (source, glb, manifest_path, preview)):
            raise FileExistsError("Refusing to overwrite existing Blender asset output.")
        command = [str(self.executable), "--background", "--factory-startup", "--python",
                   str(self.script_path), "--", "--asset-kind", asset_kind, "--asset-id", asset_id,
                   "--name", name.strip(), "--output-dir", str(output)]
        started = time.monotonic()
        budget = max(1.0, float(timeout_seconds or self.timeout_seconds))
        try:
            result = subprocess.run(command, cwd=str(root), capture_output=True, text=True,
                                    timeout=budget, check=False,
                                    env={**os.environ, "BLENDER_USER_CONFIG": str(output / ".config")})
        except subprocess.TimeoutExpired as exc:
            raise BlenderTimeoutError(f"Blender generation exceeded {budget:.0f} seconds.") from exc
        except OSError as exc:
            raise BlenderExecutionError(f"Could not launch Blender: {exc}") from exc
        elapsed = time.monotonic() - started
        log = (result.stdout + "\n" + result.stderr)[-12000:]
        if result.returncode:
            raise BlenderExecutionError(f"Blender exited with {result.returncode}.\n{log}")
        missing = [p.name for p in (source, glb, manifest_path, preview) if not p.is_file()]
        if missing:
            raise BlenderExecutionError("Blender did not produce " + ", ".join(missing) + f".\n{log}")
        if source.stat().st_size < 1024 or glb.stat().st_size < 1024:
            raise BlenderExecutionError("Blender produced an incomplete asset.")
        if preview.stat().st_size < 4096 or preview.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise BlenderExecutionError("Blender did not produce a valid review PNG.")
        with glb.open("rb") as stream:
            header = stream.read(12)
        if len(header) != 12 or header[:4] != b"glTF" or int.from_bytes(header[4:8], "little") != 2:
            raise BlenderExecutionError("Blender output is not a valid GLB 2.0 container.")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BlenderExecutionError(f"Blender manifest is invalid: {exc}") from exc
        expected = {"asset_id": asset_id, "asset_kind": asset_kind, "name": name.strip(),
                    "source_file": source.name, "glb_file": glb.name,
                    "preview_file": preview.name}
        if any(manifest.get(key) != value for key, value in expected.items()):
            raise BlenderExecutionError("Blender manifest does not match the requested asset.")
        return BlenderAssetResult(asset_id, asset_kind, name.strip(), source, glb,
                                  manifest_path, preview, info["version"], round(elapsed, 3), manifest)
