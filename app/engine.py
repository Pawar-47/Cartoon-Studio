from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

LOGGER = logging.getLogger(__name__)
PROTOCOL_VERSION = 1
EXPECTED_GODOT_VERSION = "4.7.2"
MAX_GLB_BYTES = 512 * 1024 * 1024


class EngineAdapterError(RuntimeError):
    """Base class for native engine adapter failures."""


class EngineUnavailableError(EngineAdapterError):
    """The pinned Godot runtime or worker project is unavailable."""


class EngineWorkerError(EngineAdapterError):
    """The Godot worker returned an error or malformed response."""


class EngineTimeoutError(EngineAdapterError):
    """A Godot worker request exceeded its deadline."""


class EngineCancelledError(EngineAdapterError):
    """A caller cancelled a running Godot worker request."""


class EnginePathError(EngineAdapterError, ValueError):
    """An asset path is invalid or escapes its project directory."""


class GodotEngineAdapter:
    """Supervise short-lived Godot worker processes behind the FastAPI control plane."""

    def __init__(
        self,
        executable: str | Path | None = None,
        worker_project: str | Path | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self.engine_root = Path(__file__).resolve().parents[1] / "engine"
        self.executable = (
            Path(executable).expanduser().resolve()
            if executable is not None
            else self._discover_executable()
        )
        self.worker_project = (
            Path(worker_project).expanduser().resolve()
            if worker_project is not None
            else (self.engine_root / "worker").resolve()
        )
        self.timeout_seconds = max(0.0, float(timeout_seconds))

    def _discover_executable(self) -> Path | None:
        override = os.environ.get("CARTOON_STUDIO_GODOT_PATH", "").strip()
        candidates: list[Path] = []
        if override:
            candidates.append(Path(override).expanduser())
        candidates.extend(
            [
                self.engine_root / "godot.exe",
                self.engine_root / "Godot_v4.7.2-stable_win64.exe",
                self.engine_root / "godot",
            ]
        )
        discovered = shutil.which("godot") or shutil.which("godot.exe")
        if discovered:
            candidates.append(Path(discovered))
        for candidate in candidates:
            try:
                resolved = candidate.resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if resolved.is_file():
                return resolved
        return None

    @staticmethod
    def _validated_asset(project_root: str | Path, relative_path: str) -> tuple[Path, Path]:
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise EnginePathError("A project-relative GLB asset path is required.")
        normalized = relative_path.strip().replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(normalized)
        if posix_path.is_absolute() or windows_path.is_absolute() or ".." in posix_path.parts:
            raise EnginePathError("Asset paths must stay inside the project directory.")
        try:
            root = Path(project_root).expanduser().resolve(strict=True)
            asset = (root / Path(*posix_path.parts)).resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise EnginePathError("The project directory or GLB asset does not exist.") from error
        if not root.is_dir() or root == asset or root not in asset.parents:
            raise EnginePathError("Asset path resolves outside the project directory.")
        if not asset.is_file():
            raise EnginePathError("The requested GLB asset is not a file.")
        if asset.suffix.lower() != ".glb":
            raise EnginePathError("Only binary glTF (.glb) files are accepted by this endpoint.")
        if asset.stat().st_size > MAX_GLB_BYTES:
            raise EnginePathError("The GLB exceeds the 512 MiB inspection limit.")
        return root, asset

    def handshake(self, cancel_event: threading.Event | None = None) -> dict[str, Any]:
        response = self._invoke("handshake", cancel_event=cancel_event)
        engine = response.get("engine", {})
        version = str(engine.get("version", ""))
        if not version.startswith(EXPECTED_GODOT_VERSION):
            raise EngineWorkerError(
                f"Expected Godot {EXPECTED_GODOT_VERSION}, received {version or 'unknown'}."
            )
        return response

    def inspect_glb(
        self,
        project_root: str | Path,
        relative_path: str,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        root, asset = self._validated_asset(project_root, relative_path)
        return self._invoke(
            "inspect_glb",
            project_root=str(root),
            asset_path=str(asset),
            cancel_event=cancel_event,
        )

    def _invoke(
        self,
        action: str,
        *,
        project_root: str | None = None,
        asset_path: str | None = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        if self.executable is None or not self.executable.is_file():
            raise EngineUnavailableError(
                "Godot 4.7.2 is not available. Use the self-contained installer or set "
                "CARTOON_STUDIO_GODOT_PATH to the verified Godot executable."
            )
        if not (self.worker_project / "project.godot").is_file():
            raise EngineUnavailableError("The bundled Godot worker project is missing.")

        request_id = str(uuid.uuid4())
        request: dict[str, Any] = {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "action": action,
        }
        if project_root is not None:
            request["project_root"] = project_root
        if asset_path is not None:
            request["asset_path"] = asset_path

        with tempfile.TemporaryDirectory(prefix="cartoon-studio-godot-") as temporary:
            temporary_dir = Path(temporary)
            request_path = temporary_dir / "request.json"
            response_path = temporary_dir / "response.json"
            log_path = temporary_dir / "worker.log"
            request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            command = [
                str(self.executable),
                "--headless",
                "--path",
                str(self.worker_project),
                "--script",
                "res://worker.gd",
                "--",
                "--request",
                str(request_path),
                "--response",
                str(response_path),
            ]
            environment = os.environ.copy()
            environment["GODOT_SILENCE_ROOT_WARNING"] = "1"
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            started_at = time.monotonic()
            LOGGER.info(
                "Starting Godot worker",
                extra={"request_id": request_id, "action": action},
            )
            try:
                with log_path.open("ab") as log_handle:
                    process = subprocess.Popen(
                        command,
                        cwd=self.worker_project,
                        env=environment,
                        stdin=subprocess.DEVNULL,
                        stdout=log_handle,
                        stderr=subprocess.STDOUT,
                        creationflags=creationflags,
                    )
                    try:
                        while process.poll() is None:
                            if cancel_event is not None and cancel_event.is_set():
                                raise EngineCancelledError("Godot worker request was cancelled.")
                            if time.monotonic() - started_at >= self.timeout_seconds:
                                raise EngineTimeoutError(
                                    f"Godot worker exceeded {self.timeout_seconds:.1f} seconds."
                                )
                            time.sleep(0.05)
                    finally:
                        if process.poll() is None:
                            self._stop_process(process)
            except OSError as error:
                raise EngineUnavailableError(f"Could not start the Godot worker: {error}") from error

            log_text = log_path.read_text(encoding="utf-8", errors="replace")
            if not response_path.is_file():
                raise EngineWorkerError(
                    "Godot worker did not write a response file. "
                    f"Exit code: {process.returncode}. Log: {log_text[-4000:]}"
                )
            try:
                response = json.loads(response_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise EngineWorkerError(
                    f"Godot worker wrote an invalid response. Log: {log_text[-4000:]}"
                ) from error
            if not isinstance(response, dict):
                raise EngineWorkerError("Godot worker response must be a JSON object.")
            if response.get("protocol_version") != PROTOCOL_VERSION:
                raise EngineWorkerError("Godot worker protocol version mismatch.")
            if response.get("request_id") != request_id:
                raise EngineWorkerError("Godot worker response request ID mismatch.")
            if response.get("status") != "ok":
                raise EngineWorkerError(
                    str(response.get("message", "Godot worker reported an unknown error."))
                )
            if process.returncode != 0:
                raise EngineWorkerError(
                    f"Godot worker exited with code {process.returncode}. Log: {log_text[-4000:]}"
                )
            LOGGER.info(
                "Godot worker request completed",
                extra={"request_id": request_id, "action": action},
            )
            return response

    @staticmethod
    def _stop_process(process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
