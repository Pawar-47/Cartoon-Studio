from __future__ import annotations

import logging
import os
import threading
import time
import webbrowser
from pathlib import Path

import uvicorn

from app.main import app
from app.storage import default_data_dir


def _data_directory() -> Path:
    override = os.environ.get("CARTOON_STUDIO_DATA", "").strip()
    return Path(override).expanduser() if override else default_data_dir()


def main() -> int:
    data_dir = _data_directory()
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "cartoon-studio.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        encoding="utf-8",
    )

    host = "127.0.0.1"
    port = int(os.environ.get("CARTOON_STUDIO_PORT", "8765"))
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=host,
            port=port,
            log_config=None,
            access_log=False,
            log_level="info",
        )
    )
    worker = threading.Thread(
        target=server.run,
        name="cartoon-studio-web-server",
        daemon=True,
    )
    worker.start()

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if server.started:
            break
        if not worker.is_alive():
            logging.error("The local web server stopped before startup completed.")
            return 1
        time.sleep(0.1)
    else:
        server.should_exit = True
        logging.error("The local web server did not become ready within 30 seconds.")
        return 1

    url = f"http://{host}:{port}"
    logging.info("Cartoon Studio is running at %s", url)
    if os.environ.get("CARTOON_STUDIO_NO_BROWSER") != "1":
        webbrowser.open(url)

    try:
        while worker.is_alive():
            worker.join(timeout=0.5)
    except KeyboardInterrupt:
        server.should_exit = True
        worker.join(timeout=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
