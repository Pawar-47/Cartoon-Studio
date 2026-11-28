import subprocess

import pytest

from app.render import (
    GPL_ONLY_VIDEO_ENCODERS,
    RenderDependencyUnavailable,
    VIDEO_ENCODER_PREFERENCE,
    choose_video_encoder,
)


def _ffmpeg_with(monkeypatch, listing, tmp_path):
    executable = tmp_path / "ffmpeg.exe"
    executable.write_bytes(b"ffmpeg-test")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=listing, stderr="")

    monkeypatch.setattr("app.render.subprocess.run", fake_run)
    return executable


def _listing(*encoders):
    rows = []
    for encoder in encoders:
        kind = {"aac": "A", "mov_text": "S"}.get(encoder, "V")
        rows.append(f" {kind}..... {encoder:<12} test encoder")
    return "\n".join(rows) + "\n"


def test_prefers_openh264_then_vp9(monkeypatch, tmp_path):
    executable = _ffmpeg_with(
        monkeypatch, _listing("libvpx-vp9", "libopenh264", "aac", "mov_text"), tmp_path
    )
    assert choose_video_encoder(executable) == "libopenh264"


def test_falls_back_to_vp9_when_openh264_is_missing(monkeypatch, tmp_path):
    executable = _ffmpeg_with(
        monkeypatch, _listing("libvpx-vp9", "mpeg4", "aac", "mov_text"), tmp_path
    )
    assert choose_video_encoder(executable) == "libvpx-vp9"


def test_uses_native_mpeg4_as_the_last_resort(monkeypatch, tmp_path):
    executable = _ffmpeg_with(monkeypatch, _listing("mpeg4", "aac", "mov_text"), tmp_path)
    assert choose_video_encoder(executable) == "mpeg4"


def test_refuses_a_build_whose_only_video_encoder_is_gpl(monkeypatch, tmp_path):
    executable = _ffmpeg_with(
        monkeypatch, _listing("libx264", "aac", "mov_text"), tmp_path
    )
    with pytest.raises(RenderDependencyUnavailable, match="only GPL video encoders"):
        choose_video_encoder(executable)


def test_requires_aac_and_mov_text(monkeypatch, tmp_path):
    executable = _ffmpeg_with(monkeypatch, _listing("libvpx-vp9", "mov_text"), tmp_path)
    with pytest.raises(RenderDependencyUnavailable, match="Missing encoder: aac"):
        choose_video_encoder(executable)


def test_requires_some_safe_encoder(monkeypatch, tmp_path):
    executable = _ffmpeg_with(monkeypatch, _listing("aac", "mov_text"), tmp_path)
    with pytest.raises(RenderDependencyUnavailable, match="no redistribution-safe"):
        choose_video_encoder(executable)


def test_no_gpl_encoder_is_preferred() -> None:
    assert not set(VIDEO_ENCODER_PREFERENCE) & GPL_ONLY_VIDEO_ENCODERS


def test_bundled_ffmpeg_is_preferred_over_path(monkeypatch, tmp_path):
    from app import render

    bundle = tmp_path / "bundle"
    bundled = bundle / "engine" / "ffmpeg" / render.BUNDLED_FFMPEG_NAME
    bundled.parent.mkdir(parents=True)
    bundled.write_bytes(b"bundled")
    monkeypatch.setattr(render, "__file__", str(bundle / "app" / "render.py"))
    monkeypatch.setattr(
        render.shutil, "which", lambda _name: pytest.fail("PATH must not be consulted")
    )
    assert render._find_ffmpeg() == bundled.resolve()
