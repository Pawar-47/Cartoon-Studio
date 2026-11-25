import shutil
import subprocess
from pathlib import Path

import pytest


def test_animation_clip_resolver_node_suite():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable; browser helper tests run in CI.")
    test_files = [
        Path(__file__).with_name("test_animation_clip_resolver.mjs"),
        Path(__file__).with_name("test_browser_retarget_clip.mjs"),
    ]
    result = subprocess.run(
        [node, "--test", *(str(path) for path in test_files)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
