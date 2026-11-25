from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from app.rig_analysis import REQUIRED_HUMANOID_BONES
from app.storage import default_data_dir

ENGINE_VERSION = "4.7.2-stable"
ENGINE_BINARY_NAME = "Godot_v4.7.2-stable_win64.exe"
WORKER_PROTOCOL_VERSION = 1
MAX_TIMEOUT_SECONDS = 180.0
MAX_GLB_BYTES = 512 * 1024 * 1024


class EngineError(RuntimeError):
    """Base error for local engine operations."""


class EngineUnavailableError(EngineError):
    """Raised when the pinned Godot runtime or worker project is missing."""


class EngineTimeoutError(EngineError):
    """Raised when the supervised Godot worker exceeds its time budget."""


class EngineCancelledError(EngineError):
    """Raised when a caller cancels a running worker request."""


class EngineExecutionError(EngineError):
    """Raised when the Godot worker returns an invalid or failed response."""


class EnginePathError(EngineError, ValueError):
    """Raised when a GLB path is outside the allowed project directory."""


class GodotEngineAdapter:
    """Supervise one bounded Godot worker process per engine request."""

    def __init__(
        self,
        data_dir: Path | None = None,
        timeout_seconds: float = 60.0,
        executable: Path | None = None,
        worker_project: Path | None = None,
    ) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else default_data_dir()
        self.timeout_seconds = timeout_seconds
        self.bundle_root = self._bundle_root()
        self.executable = Path(executable) if executable else self._find_executable()
        self.worker_project = (
            Path(worker_project)
            if worker_project
            else self.bundle_root / "engine" / "godot_worker"
        )

    @staticmethod
    def _bundle_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[1]

    def _find_executable(self) -> Path:
        override = os.environ.get("CARTOON_STUDIO_GODOT_PATH", "").strip()
        if override:
            return Path(override).expanduser()
        candidates = (
            self.bundle_root / "engine" / ENGINE_BINARY_NAME,
            self.bundle_root / "third_party" / "godot" / ENGINE_BINARY_NAME,
            self.bundle_root / "build" / "godot-runtime" / ENGINE_BINARY_NAME,
        )
        return next((candidate for candidate in candidates if candidate.is_file()), candidates[0])

    @property
    def available(self) -> bool:
        return self.executable.is_file() and (self.worker_project / "project.godot").is_file()

    def ping(self, cancel_event: threading.Event | None = None) -> dict[str, Any]:
        response = self._run("ping", {}, cancel_event=cancel_event)
        version = str(response.get("engine_version", ""))
        if not version.startswith("4.7.2"):
            raise EngineExecutionError(
                f"Expected Godot {ENGINE_VERSION}, received {version or 'unknown'}."
            )
        return response

    def inspect_glb(
        self,
        source_path: Path,
        allowed_root: Path,
        timeout_seconds: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        root = Path(allowed_root).resolve(strict=False)
        source = Path(source_path).resolve(strict=True)
        if source == root or root not in source.parents:
            raise EnginePathError("GLB path escapes the allowed project directory.")
        if not root.is_dir():
            raise EnginePathError("The allowed project root does not exist.")
        if source.suffix.lower() != ".glb":
            raise EnginePathError("Only .glb files can be inspected by this endpoint.")
        if not source.is_file():
            raise FileNotFoundError(source)
        if source.stat().st_size > MAX_GLB_BYTES:
            raise EnginePathError("The GLB exceeds the 512 MiB inspection limit.")
        return self._run(
            "inspect_glb",
            {"source_path": str(source), "project_root": str(root)},
            timeout_seconds=timeout_seconds,
            cancel_event=cancel_event,
        )


    def retarget_glb_pair(
        self,
        source_path: Path,
        target_path: Path,
        output_path: Path,
        allowed_root: Path,
        source_profile_mapping: dict[str, dict[str, Any]],
        target_profile_mapping: dict[str, dict[str, Any]],
        animation_name: str = "",
        timeout_seconds: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        root = Path(allowed_root).resolve(strict=False)
        paths = [Path(source_path).resolve(strict=True), Path(target_path).resolve(strict=True)]
        for path in paths:
            if path == root or root not in path.parents:
                raise EnginePathError("A GLB path escapes the allowed project directory.")
            if path.suffix.lower() != ".glb" or not path.is_file():
                raise EnginePathError("Only existing .glb files can be retargeted.")
            if path.stat().st_size > MAX_GLB_BYTES:
                raise EnginePathError("A GLB exceeds the 512 MiB retarget limit.")
        output = Path(output_path).resolve(strict=False)
        if output == root or root not in output.parents:
            raise EnginePathError("Retarget output escapes the allowed project directory.")
        if output.suffix.lower() != ".tscn":
            raise EnginePathError("Retarget output must use the .tscn extension.")
        if output.exists():
            raise EnginePathError("Refusing to overwrite an existing retarget scene.")
        if set(source_profile_mapping) != REQUIRED_HUMANOID_BONES or set(
            target_profile_mapping
        ) != REQUIRED_HUMANOID_BONES:
            raise EnginePathError("Both rigs must have complete, unambiguous humanoid mappings.")
        output.parent.mkdir(parents=True, exist_ok=True)
        return self._run(
            "retarget_glb_pair",
            {
                "project_root": str(root),
                "source_path": str(paths[0]),
                "target_path": str(paths[1]),
                "output_path": str(output),
                "source_profile_mapping": source_profile_mapping,
                "target_profile_mapping": target_profile_mapping,
                "animation_name": animation_name,
            },
            timeout_seconds=timeout_seconds,
            cancel_event=cancel_event,
        )

    def _write_log(self, record: dict[str, Any]) -> None:
        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "godot-worker.jsonl"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _record_failure(
        self,
        request_id: str,
        operation: str,
        started: float,
        message: str,
        exit_code: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        self._write_log(
            {
                "request_id": request_id,
                "operation": operation,
                "ok": False,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "exit_code": exit_code,
                "error": message,
                "stdout_tail": stdout[-1000:],
                "stderr_tail": stderr[-1000:],
            }
        )

    def _run(
        self,
        operation: str,
        payload: dict[str, Any],
        timeout_seconds: float | None = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        if not self.executable.is_file():
            raise EngineUnavailableError(
                f"Godot {ENGINE_VERSION} runtime was not found at {self.executable}."
            )
        if not (self.worker_project / "project.godot").is_file():
            raise EngineUnavailableError(
                f"Godot worker project was not found at {self.worker_project}."
            )

        timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
        if timeout <= 0 or timeout > MAX_TIMEOUT_SECONDS:
            raise ValueError(
                "Engine timeout must be greater than zero and at most "
                f"{MAX_TIMEOUT_SECONDS:g} seconds."
            )

        request_root = self.data_dir / "engine" / "requests"
        request_root.mkdir(parents=True, exist_ok=True)
        request_id = str(uuid.uuid4())
        started = time.monotonic()

        with tempfile.TemporaryDirectory(prefix="godot-request-", dir=request_root) as temporary:
            temporary_root = Path(temporary)
            request_path = temporary_root / "request.json"
            response_path = temporary_root / "response.json"
            stdout_path = temporary_root / "stdout.log"
            stderr_path = temporary_root / "stderr.log"
            request_document = {
                "protocol_version": WORKER_PROTOCOL_VERSION,
                "request_id": request_id,
                "operation": operation,
                "payload": payload,
            }
            request_path.write_text(
                json.dumps(request_document, ensure_ascii=False),
                encoding="utf-8",
            )

            command = [
                str(self.executable),
                "--headless",
                "--path",
                str(self.worker_project),
                "--script",
                "res://worker.gd",
                "--",
                f"--request-file={request_path}",
                f"--response-file={response_path}",
            ]
            process: subprocess.Popen | None = None
            try:
                with (
                    stdout_path.open("wb") as stdout_handle,
                    stderr_path.open("wb") as stderr_handle,
                ):
                    process = subprocess.Popen(
                        command,
                        cwd=self.worker_project,
                        stdin=subprocess.DEVNULL,
                        stdout=stdout_handle,
                        stderr=stderr_handle,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    try:
                        while process.poll() is None:
                            if cancel_event is not None and cancel_event.is_set():
                                raise EngineCancelledError("Godot worker request was cancelled.")
                            if time.monotonic() - started >= timeout:
                                raise EngineTimeoutError(
                                    f"Godot {operation} exceeded its {timeout:g}-second "
                                    "time budget."
                                )
                            time.sleep(0.05)
                    finally:
                        if process.poll() is None:
                            self._stop_process(process)
            except (EngineTimeoutError, EngineCancelledError) as error:
                stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
                stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    str(error),
                    process.returncode if process else None,
                    stdout_text,
                    stderr_text,
                )
                raise
            except OSError as error:
                message = f"Could not start the Godot worker: {error}"
                self._record_failure(request_id, operation, started, message)
                raise EngineUnavailableError(message) from error

            stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
            stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
            if process is None:
                raise EngineUnavailableError("Godot worker process did not start.")
            if not response_path.is_file():
                details = (stderr_text or stdout_text)[-2000:]
                message = f"Godot worker exited {process.returncode} without a response. {details}"
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    message,
                    process.returncode,
                    stdout_text,
                    stderr_text,
                )
                raise EngineExecutionError(message)
            try:
                response = json.loads(response_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                message = "Godot worker returned invalid JSON."
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    message,
                    process.returncode,
                    stdout_text,
                    stderr_text,
                )
                raise EngineExecutionError(message) from error

            if not isinstance(response, dict):
                message = "Godot worker response must be a JSON object."
                self._record_failure(request_id, operation, started, message, process.returncode)
                raise EngineExecutionError(message)
            if response.get("request_id") != request_id:
                message = "Godot worker response request ID did not match."
                self._record_failure(request_id, operation, started, message, process.returncode)
                raise EngineExecutionError(message)
            if response.get("protocol_version") != WORKER_PROTOCOL_VERSION:
                message = "Godot worker protocol version did not match."
                self._record_failure(request_id, operation, started, message, process.returncode)
                raise EngineExecutionError(message)
            if process.returncode != 0 or not response.get("ok", False):
                message = str(response.get("error", "Godot worker operation failed."))
                details = (stderr_text or stdout_text)[-2000:]
                message = f"{message} {details}".strip()
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    message,
                    process.returncode,
                    stdout_text,
                    stderr_text,
                )
                raise EngineExecutionError(message)

            elapsed_ms = round((time.monotonic() - started) * 1000)
            response["elapsed_ms"] = elapsed_ms
            response["worker_exit_code"] = process.returncode
            self._write_log(
                {
                    "request_id": request_id,
                    "operation": operation,
                    "ok": True,
                    "elapsed_ms": elapsed_ms,
                    "exit_code": process.returncode,
                    "stdout_tail": stdout_text[-1000:],
                    "stderr_tail": stderr_text[-1000:],
                }
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
