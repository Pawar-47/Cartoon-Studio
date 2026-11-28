import json
import re
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "engine" / "ffmpeg_runtime.json"
DATED_RELEASE_PATTERN = re.compile(
    r"/releases/download/autobuild-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}/"
)


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_ffmpeg_download_is_pinned_to_a_dated_release():
    manifest = _manifest()
    assert DATED_RELEASE_PATTERN.search(manifest["download_url"]), (
        "Pin the FFmpeg archive to a dated release; the moving 'latest' tag "
        "changes its bytes and breaks the hash check on every upstream rebuild."
    )
    assert manifest["release_tag"] in manifest["download_url"]
    assert manifest["release_tag"] in manifest["checksums_url"]


def test_ffmpeg_archive_is_hash_pinned():
    manifest = _manifest()
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["archive_sha256"])
    assert manifest["archive_name"] in manifest["download_url"]
    assert manifest["binary_name"] == "ffmpeg.exe"


def test_ffmpeg_manifest_keeps_gpl_encoders_out():
    manifest = _manifest()
    assert {"aac", "mov_text"} <= set(manifest["required_encoders"])
    allowed = set(manifest["allowed_video_encoders"])
    assert not allowed & set(manifest["forbidden_video_encoders"])
