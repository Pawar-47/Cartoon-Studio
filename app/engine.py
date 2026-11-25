from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from app.storage import default_data_dir

ENGINE_VERSION = "4.7.2-stable"
ENGINE_BINARY_NAME = "Godot_v4.7.2-stable_win64.exe"
WORKER_PROTOCOL_VERSION = 1


class EngineError(RuntimeError):
    """Base error for local engine operations."""


class EngineUnavailableError(EngineError):
    """Raised when the pinned Godot runtime or worker project is missing."""


class EngineTimeoutError(EngineError):
    """Raised when the supervised Godot worker exceeds its time budget."""


class EngineExecutionError(EngineError):
    """Raised when the Godot worker returns an invalid or failed response."""


class GodotEngineAdapter:
    """Supervise one bounded Godot worker process per engine request."""

    def __init__(
        self,
        data_dir: Path | None = None,
        timeout_seconds: float = 30.0,
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

    def ping(self) -> dict[str, Any]:
        return self._run("ping", {})

    def inspect_glb(
        self,
        source_path: Path,
        allowed_root: Path,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        root = Path(allowed_root).resolve()
        source = Path(source_path).resolve()
        if source.suffix.lower() != ".glb":
            raise ValueError("Only .glb files can be inspected by this endpoint.")
        if source == root or root not in source.parents:
            raise ValueError("GLB path escapes the allowed project directory.")
        if not source.is_file():
            raise FileNotFoundError(source)
        return self._run(
            "inspect_glb",
            {"source_path": str(source)},
            timeout_seconds=timeout_seconds,
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
        if timeout <= 0 or timeout > 180:
            raise ValueError("Engine timeout must be greater than zero and at most 180 seconds.")

        request_root = self.data_dir / "engine" / "requests"
        request_root.mkdir(parents=True, exist_ok=True)
        request_id = str(uuid.uuid4())
        started = time.monotonic()

        with tempfile.TemporaryDirectory(prefix="godot-request-", dir=request_root) as temporary:
            temporary_root = Path(temporary)
            request_path = temporary_root / "request.json"
            response_path = temporary_root / "response.json"
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
            try:
                completed = subprocess.run(
                    command,
                    cwd=self.worker_project,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                message = f"Godot {operation} exceeded its {timeout:g}-second time budget."
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    message,
                    stdout=str(error.stdout or ""),
                    stderr=str(error.stderr or ""),
                )
                raise EngineTimeoutError(message) from error
            except OSError as error:
                message = f"Could not start the Godot worker: {error}"
                self._record_failure(request_id, operation, started, message)
                raise EngineUnavailableError(message) from error

            elapsed_ms = round((time.monotonic() - started) * 1000)
            if not response_path.is_file():
                details = (completed.stderr or completed.stdout)[-2000:]
                message = (
                    f"Godot worker exited {completed.returncode} without a response. {details}"
                )
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    message,
                    completed.returncode,
                    completed.stdout,
                    completed.stderr,
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
                    completed.returncode,
                    completed.stdout,
                    completed.stderr,
                )
                raise EngineExecutionError(message) from error

            if not isinstance(response, dict):
                message = "Godot worker response must be a JSON object."
                self._record_failure(request_id, operation, started, message, completed.returncode)
                raise EngineExecutionError(message)
            if response.get("request_id") != request_id:
                message = "Godot worker response request ID did not match."
                self._record_failure(request_id, operation, started, message, completed.returncode)
                raise EngineExecutionError(message)
            if response.get("protocol_version") != WORKER_PROTOCOL_VERSION:
                message = "Godot worker protocol version did not match."
                self._record_failure(request_id, operation, started, message, completed.returncode)
                raise EngineExecutionError(message)
            if completed.returncode != 0 or not response.get("ok", False):
                message = response.get("error", "Godot worker operation failed.")
                details = (completed.stderr or completed.stdout)[-2000:]
                message = f"{message} {details}".strip()
                self._record_failure(
                    request_id,
                    operation,
                    started,
                    message,
                    completed.returncode,
                    completed.stdout,
                    completed.stderr,
                )
                raise EngineExecutionError(message)

            response["elapsed_ms"] = elapsed_ms
            response["worker_exit_code"] = completed.returncode
            self._write_log(
                {
                    "request_id": request_id,
                    "operation": operation,
                    "ok": True,
                    "elapsed_ms": elapsed_ms,
                    "exit_code": completed.returncode,
                    "stdout_tail": completed.stdout[-1000:],
                    "stderr_tail": completed.stderr[-1000:],
                }
            )
            return response
