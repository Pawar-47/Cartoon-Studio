from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


def request(base: str, path: str, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        raw = response.read()
        is_json = raw.startswith((b"{", b"["))
        return response.status, json.loads(raw) if is_json else raw


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: smoke_windows_package.py <bootstrap-zip>")
    archive = Path(sys.argv[1]).resolve()
    if not archive.is_file():
        raise SystemExit(f"Bootstrap archive not found: {archive}")

    with tempfile.TemporaryDirectory(prefix="cartoon-studio-smoke-") as temporary:
        root = Path(temporary)
        extracted = root / "package"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            bad_member = next(
                (
                    name
                    for name in bundle.namelist()
                    if Path(name).is_absolute() or ".." in Path(name).parts
                ),
                None,
            )
            if bad_member:
                raise AssertionError(f"Unsafe archive member: {bad_member}")
            bundle.extractall(extracted)

        required = [
            "README.md",
            "start.bat",
            "requirements.lock",
            "app/main.py",
            "app/storage.py",
            "app/static/index.html",
            "app/static/styles.css",
        ]
        missing = [item for item in required if not (extracted / item).is_file()]
        if missing:
            raise AssertionError(f"Bootstrap package is missing required files: {missing}")

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        data_dir = root / "persistent-data"
        environment = os.environ.copy()
        environment["CARTOON_STUDIO_DATA"] = str(data_dir)
        environment["CARTOON_STUDIO_PORT"] = str(port)
        environment["CARTOON_STUDIO_NO_BROWSER"] = "1"
        log_path = root / "launcher.log"

        def launch():
            log_handle = log_path.open("ab")
            return subprocess.Popen(
                ["cmd.exe", "/c", "start.bat"],
                cwd=extracted,
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )

        def stop(process):
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

        process = launch()
        try:
            for attempt in range(40):
                if process.poll() is not None:
                    raise AssertionError(
                    "Packaged start.bat exited early. Launcher log: "
                    + log_path.read_text(encoding="utf-8", errors="replace")
                )
                try:
                    status, health = request(base, "/api/health")
                    if status == 200 and health.get("status") == "ok":
                        break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.25)
            else:
                raise AssertionError(
                    "Packaged application did not become healthy within 10 seconds"
                )

            status, dashboard = request(base, "/")
            assert status == 200 and b"Cartoon Studio" in dashboard
            status, static = request(base, "/static/styles.css")
            assert status == 200 and static

            status, created = request(
                base,
                "/api/projects",
                "POST",
                {"name": "Clean Package Smoke Test", "description": "Persistence across restart"},
            )
            assert status == 201
            project_id = created["id"]
            status, opened = request(base, f"/api/projects/{project_id}")
            assert status == 200 and opened["project"]["id"] == project_id
        finally:
            stop(process)

        process = launch()
        try:
            for _ in range(40):
                if process.poll() is not None:
                    raise AssertionError(
                    "Packaged start.bat failed on restart. Launcher log: "
                    + log_path.read_text(encoding="utf-8", errors="replace")
                )
                try:
                    status, health = request(base, "/api/health")
                    if status == 200 and health.get("status") == "ok":
                        break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.25)
            else:
                raise AssertionError("Packaged application did not recover after restart")

            status, projects = request(base, "/api/projects")
            assert status == 200
            assert any(project["id"] == project_id for project in projects)
            status, reopened = request(base, f"/api/projects/{project_id}")
            assert status == 200 and reopened["project"]["name"] == "Clean Package Smoke Test"
        finally:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print(
        "Windows bootstrap smoke test passed: archive integrity, extracted launch, "
        "HTTP UI/API, project save/open and restart persistence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
