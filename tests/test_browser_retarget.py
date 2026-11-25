import shutil
import subprocess
from pathlib import Path

import pytest


def test_browser_retarget_node_suite():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; browser retarget tests run in CI.")
    test_file = Path(__file__).with_name("test_browser_retarget.mjs")
    result = subprocess.run(
        [node, "--test", str(test_file)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
