from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
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
        return response.status, json.loads(response.read())


def start_application(
    executable: Path,
    data_dir: Path,
    port: int,
    expected_version: str,
) -> subprocess.Popen:
    environment = os.environ.copy()
    environment["CARTOON_STUDIO_DATA"] = str(data_dir)
    environment["CARTOON_STUDIO_PORT"] = str(port)
    environment["CARTOON_STUDIO_NO_BROWSER"] = "1"
    process = subprocess.Popen(
        [str(executable)],
        cwd=executable.parent,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    for _ in range(120):
        if process.poll() is not None:
            raise AssertionError(
                f"Installed app exited during startup (code {process.returncode})."
            )
        try:
            status, health = request(base, "/api/health")
            if status == 200 and health.get("status") == "ok":
                if health.get("version") != expected_version:
                    raise AssertionError(
                        f"Expected app version {expected_version}, got {health.get('version')}."
                    )
                return process
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    process.terminate()
    process.wait(timeout=8)
    raise AssertionError("Installed app did not become healthy within 30 seconds.")


def stop_application(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def install(installer: Path, install_dir: Path) -> None:
    subprocess.run(
        [str(installer), "/S", f"/D={install_dir}"],
        check=True,
        timeout=180,
    )


def uninstall(install_dir: Path) -> None:
    uninstaller = install_dir / "Uninstall.exe"
    if not uninstaller.is_file():
        raise AssertionError("Installed uninstaller is missing.")
    debug_path = Path(os.environ["TEMP"]) / "CartoonStudio-uninstall-debug.txt"
    if debug_path.exists():
        debug_path.unlink()
    subprocess.run([str(uninstaller), "/S"], check=True, timeout=180)
    if (install_dir / "CartoonStudio.exe").exists():
        registry = subprocess.run(
            ["reg", "query", r"HKCU\Software\CartoonStudio", "/v", "InstallDir"],
            check=False,
            capture_output=True,
            text=True,
        )
        debug_text = (
            debug_path.read_text(encoding="utf-8", errors="replace")
            if debug_path.exists()
            else "No uninstaller debug file."
        )
        raise AssertionError(
            "Uninstaller left the main executable in place.\n"
            + debug_text
            + "\nRegistry:\n"
            + registry.stdout
            + registry.stderr
        )

def main() -> int:
    if len(os.sys.argv) != 3:
        raise SystemExit("Usage: smoke_windows_installer.py <v1-installer> <v2-installer>")

    v1_installer = Path(os.sys.argv[1]).resolve()
    v2_installer = Path(os.sys.argv[2]).resolve()
    if not v1_installer.is_file() or not v2_installer.is_file():
        raise SystemExit("Both versioned installer files must exist.")

    with tempfile.TemporaryDirectory(prefix="cartoon-studio-installer-") as temporary:
        root = Path(temporary)
        install_dir = root / "CartoonStudio"
        data_dir = root / "persistent-user-data"
        data_dir.mkdir()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        start_menu = (
            Path(os.environ["APPDATA"])
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Cartoon Studio"
            / "Cartoon Studio.lnk"
        )
        desktop_shortcut = (
            Path(os.environ["USERPROFILE"]) / "Desktop" / "Cartoon Studio.lnk"
        )

        install(v1_installer, install_dir)
        executable = install_dir / "CartoonStudio.exe"
        assert executable.is_file()
        assert start_menu.is_file()
        assert desktop_shortcut.is_file()

        process = start_application(executable, data_dir, port, "0.1.0")
        try:
            status, created = request(
                f"http://127.0.0.1:{port}",
                "/api/projects",
                "POST",
                {
                    "name": "Installer Upgrade Preservation",
                    "description": "Created before upgrade",
                },
            )
            assert status == 201
            project_id = created["id"]
        finally:
            stop_application(process)

        project_file = data_dir / "projects" / project_id / "project.json"
        assert project_file.is_file()

        # Install v2 over v1. The previous uninstaller removes only program files.
        install(v2_installer, install_dir)
        executable = install_dir / "CartoonStudio.exe"
        assert executable.is_file()
        process = start_application(executable, data_dir, port, "0.1.1")
        try:
            status, projects = request(f"http://127.0.0.1:{port}", "/api/projects")
            assert status == 200
            assert any(project["id"] == project_id for project in projects)
        finally:
            stop_application(process)

        uninstall(install_dir)
        assert not executable.exists()
        assert project_file.is_file(), "Uninstall deleted the user's project data."
        assert not start_menu.exists()
        assert not desktop_shortcut.exists()

        # Reinstall after uninstall and confirm the same project remains readable.
        install(v2_installer, install_dir)
        executable = install_dir / "CartoonStudio.exe"
        process = start_application(executable, data_dir, port, "0.1.1")
        try:
            status, projects = request(f"http://127.0.0.1:{port}", "/api/projects")
            assert status == 200
            assert any(project["id"] == project_id for project in projects)
        finally:
            stop_application(process)

        uninstall(install_dir)
        assert project_file.is_file(), "Final uninstall deleted the user's project data."

    print(
        "Windows installer smoke test passed: clean install, shortcuts, v1-to-v2 upgrade, "
        "project preservation, uninstall and reinstall."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
