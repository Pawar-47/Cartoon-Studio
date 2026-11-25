from __future__ import annotations

import hashlib
import io
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app import main
from app.character_builder import (
    CharacterLibraryError,
    CharacterModelSpec,
    UnknownCharacterModel,
    download_model_asset,
    get_character_catalog,
    get_model_spec,
    verify_model_file,
)

client = TestClient(main.app)


def _git_blob_sha1(payload: bytes) -> str:
    header = b"blob " + str(len(payload)).encode("ascii") + bytes((0,))
    return hashlib.sha1(header + payload).hexdigest()


def test_character_builder_catalog_is_pinned_cc0_and_modular():
    catalog = get_character_catalog()

    assert catalog["version"] == 1
    assert catalog["source"]["license"] == "CC0-1.0"
    assert catalog["source"]["code_reused"] is False
    assert len(catalog["outfits"]) == 21
    assert catalog["slots"] == ["head", "body", "legs", "feet"]
    assert len(catalog["animations"]) == 24
    assert catalog["rig_expectations"] == {
        "bone_count": 62,
        "animation_count": 24,
    }


def test_character_builder_rejects_unlisted_models():
    with pytest.raises(UnknownCharacterModel):
        get_model_spec("../Male", "Adventurer")
    with pytest.raises(UnknownCharacterModel):
        get_model_spec("Male", "../../outside")


def test_character_model_download_verifies_git_blob_and_caches(tmp_path):
    payload = b"glTF-pinned-character-model"
    spec = CharacterModelSpec(
        pack="Test",
        outfit="Fixture",
        size_bytes=len(payload),
        git_blob_sha1=_git_blob_sha1(payload),
    )
    calls = []

    def opener(request, timeout):
        calls.append((request.full_url, timeout))
        return io.BytesIO(payload)

    destination = tmp_path / "cache" / "fixture.glb"
    downloaded = download_model_asset(spec, destination, opener=opener)

    assert downloaded == destination
    assert downloaded.read_bytes() == payload
    assert verify_model_file(downloaded, spec)
    assert calls and calls[0][0] == spec.url


def test_character_model_download_rejects_wrong_blob_hash(tmp_path):
    payload = b"glTF-tampered-character-model"
    spec = CharacterModelSpec(
        pack="Test",
        outfit="Fixture",
        size_bytes=len(payload),
        git_blob_sha1="0" * 40,
    )

    with pytest.raises(CharacterLibraryError, match="integrity check"):
        download_model_asset(
            spec,
            tmp_path / "fixture.glb",
            opener=lambda request, timeout: io.BytesIO(payload),
        )
    assert not (tmp_path / "fixture.glb").exists()


def test_character_builder_catalog_endpoint():
    response = client.get("/api/character-builder/catalog")

    assert response.status_code == 200
    assert len(response.json()["outfits"]) == 21
    assert response.json()["source"]["license"] == "CC0-1.0"


def test_character_builder_model_endpoint_serves_pinned_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    model_path = tmp_path / "cached" / "Adventurer.glb"
    model_path.parent.mkdir(parents=True)
    model_path.write_bytes(b"glTF-fixture")

    def fake_ensure(cache_root: Path, pack: str, outfit: str) -> Path:
        assert cache_root == tmp_path / "character-library"
        assert (pack, outfit) == ("Male", "Adventurer")
        return model_path

    monkeypatch.setattr(main, "ensure_model_asset", fake_ensure)
    response = client.get("/api/character-builder/models/Male/Adventurer")

    assert response.status_code == 200
    assert response.content == b"glTF-fixture"
    expected_etag = f'"{get_model_spec("Male", "Adventurer").git_blob_sha1}"'
    assert response.headers["etag"] == expected_etag


def test_character_builder_model_endpoint_rejects_unknown_outfit():
    response = client.get("/api/character-builder/models/Male/../../outside")

    assert response.status_code in {404, 405, 422}
