from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(r"\d+\.\d+\.\d+", sys.argv[1]):
        raise SystemExit("Usage: set_build_version.py MAJOR.MINOR.PATCH")
    version = sys.argv[1]
    Path("app/version.py").write_text(
        '"""Single source for the installed application version."""\n\n'
        f'APP_VERSION = "{version}"\n',
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
