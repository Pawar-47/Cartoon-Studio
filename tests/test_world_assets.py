from __future__ import annotations

import hashlib

import pytest

from app import world_assets


def test_catalog_is_curated_and_cc0():
    assets = world_assets.list_world_assets()
    assert len(assets) == 28
    assert {item["category"] for item in assets} == {
        "road", "street", "building", "nature", "vehicle", "furniture"
    }
    assert all(item["license"] == "CC0-1.0" for item in assets)


def test_catalog_filters_by_query_and_category():
    roads = world_assets.list_world_assets("cross", "road")
    assert [item["id"] for item in roads] == ["road-crossroad"]
    assert world_assets.list_world_assets("sedan", "vehicle")[0]["id"] == "car-sedan"


def test_git_blob_hash_uses_git_object_format():
    data = b"Cartoon Studio world asset"
    expected = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert world_assets._git_blob_sha1(data) == expected


def test_install_rejects_unknown_asset(tmp_path):
    with pytest.raises(KeyError):
        world_assets.install_world_asset(tmp_path, "../outside")


def test_install_download_verifies_size_hash_and_glb_header(tmp_path, monkeypatch):
    asset_id = "road-straight"
    data = b"glTF" + b"verified-test-payload"
    spec = world_assets.ASSETS[asset_id]
    original = dict(spec)
    spec["size"] = len(data)
    spec["git_blob_sha1"] = world_assets._git_blob_sha1(data)
    monkeypatch.setattr(world_assets, "_download_asset", lambda _asset_id, _size: data)
    try:
        result = world_assets.install_world_asset(tmp_path, asset_id)
        target = tmp_path / result["relative_path"]
        assert target.read_bytes() == data
        assert result["cached"] is False
        cached = world_assets.install_world_asset(tmp_path, asset_id)
        assert cached["cached"] is True
    finally:
        spec.clear()
        spec.update(original)
