import shutil
import subprocess
from pathlib import Path

import pytest


def test_character_expression_presets_node_suite():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; expression preset tests run in CI.")
    test_file = Path(__file__).with_name("test_character_expression_presets.mjs")
    result = subprocess.run(
        [node, "--test", str(test_file)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
