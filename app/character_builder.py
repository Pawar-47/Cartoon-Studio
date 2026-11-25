from __future__ import annotations

import hashlib
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

SOURCE_REPOSITORY = "LuanDucate/Ducz.CharacterCreator"
SOURCE_COMMIT = "fcd215b58eec5c9ed97d0ba5f696d0e7dc085e08"
SOURCE_BASE_URL = (
    "https://raw.githubusercontent.com/"
    f"{SOURCE_REPOSITORY}/{SOURCE_COMMIT}/public/models"
)
LICENSE_ID = "CC0-1.0"
LICENSE_NAME = "Creative Commons Zero 1.0 Universal"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
PACK_LICENSE_URLS = {
    "Male": "https://quaternius.com/packs/ultimatemodularcharacters.html",
    "Female": "https://quaternius.com/packs/ultimatemodularwomen.html",
}
SLOTS = ("head", "body", "legs", "feet")
ANIMATIONS = (
    "Idle", "Idle_Neutral", "Walk", "Run", "Run_Back", "Run_Left", "Run_Right",
    "Wave", "Interact", "Roll", "Punch_Left", "Punch_Right", "Kick_Left",
    "Kick_Right", "Sword_Slash", "Idle_Sword", "Gun_Shoot", "Run_Shoot",
    "Idle_Gun", "Idle_Gun_Pointing", "Idle_Gun_Shoot", "HitRecieve",
    "HitRecieve_2", "Death",
)


class CharacterLibraryError(RuntimeError):
    """A pinned character-library asset could not be safely obtained."""


class UnknownCharacterModel(ValueError):
    """A requested model is not part of the pinned CC0 catalog."""


@dataclass(frozen=True, slots=True)
class CharacterModelSpec:
    pack: str
    outfit: str
    size_bytes: int
    git_blob_sha1: str

    @property
    def relative_path(self) -> str:
        return f"public/models/{self.pack}/{self.outfit}.glb"

    @property
    def url(self) -> str:
        return f"{SOURCE_BASE_URL}/{self.pack}/{self.outfit}.glb"

    @property
    def model_id(self) -> str:
        return f"{self.pack}/{self.outfit}"


_MODEL_ROWS = (
    ("Female", "Adventurer", 1718128, "ed43d9f8d2dfb0d069eb93df749e9e1cce170842"),
    ("Female", "Casual", 1668252, "a67f4495d64d9d6f5e08d85ba024815d88a5b195"),
    ("Female", "Formal", 1631212, "139c03afede432acdd613ce44207dd23f1b63c4d"),
    ("Female", "Medieval", 1718712, "24014629857e71a8f5f1c9e12f904150818844e4"),
    ("Female", "Punk", 1615296, "2f8be0a22a56ab69ff116a855a5cf11f4fd4da6d"),
    ("Female", "SciFi", 1795840, "69c04735122f1d8c01f1d9ca269bf1bc37e5033a"),
    ("Female", "Soldier", 1830932, "c4eb59f40d879af5286042cd80c4da9d18b7fa6b"),
    ("Female", "Suit", 1675460, "3e808f9b15f5957e42e36e1cce8bd226a1cd748d"),
    ("Female", "Witch", 1722828, "ca15370f97dfa7fddd9107dcb13954385455a848"),
    ("Female", "Worker", 1638260, "ce4590b0ab050494dcd0a24e9abf07bebaf70533"),
    ("Male", "Adventurer", 2069132, "1ccdfeb9bffd94cb0f401ce83eac46f5e949ec02"),
    ("Male", "Beach", 1691780, "e27009d1ee23c231da8e52576d6696bec25b6ed7"),
    ("Male", "Casual_2", 1611824, "dde65b2952f58b05392a139c1bad297e401d9f1d"),
    ("Male", "Casual_Hoodie", 1646632, "bdae92bff1aef0bf58b6bee99a3ea22a53cfd1c1"),
    ("Male", "Farmer", 1565656, "4a95d9a351269649a585aaabf067c51537d8cdf6"),
    ("Male", "King", 2159552, "c2eba9d3a9e29861396ab466a7ed87fef781532a"),
    ("Male", "Punk", 1568720, "863b2e2f2400ac5f86e7ea43c0c04c03c9fa448f"),
    ("Male", "Spacesuit", 2104016, "2371de241dcc51846813c632d3f557cffb2d29c6"),
    ("Male", "Suit", 1803052, "6291a81754ea87664b19e6c27a68c003b1618f1d"),
    ("Male", "Swat", 1844496, "628dfb1ddb4548a3bb347e2081c614c0e015b216"),
    ("Male", "Worker", 1541248, "3979f271e62242b046bfd3c07d6962064c699eff"),
)
MODEL_SPECS = {
    (pack, outfit): CharacterModelSpec(pack, outfit, size, blob_sha)
    for pack, outfit, size, blob_sha in _MODEL_ROWS
}
_DOWNLOAD_LOCK = threading.Lock()
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_DOWNLOAD_TIMEOUT_SECONDS = 45


def get_model_spec(pack: str, outfit: str) -> CharacterModelSpec:
    try:
        return MODEL_SPECS[(pack, outfit)]
    except KeyError as error:
        raise UnknownCharacterModel(
            "That model is not in the pinned CC0 library."
        ) from error


def get_character_catalog() -> dict[str, Any]:
    pack_labels = {
        "Male": "Ultimate Modular Men Pack",
        "Female": "Ultimate Modular Women Pack",
    }
    outfits = [
        {
            "id": spec.model_id,
            "pack": spec.pack,
            "name": spec.outfit,
            "label": f"{pack_labels[spec.pack]} · {spec.outfit.replace('_', ' ')}",
            "asset_url": f"/api/character-builder/models/{spec.pack}/{spec.outfit}",
            "size_bytes": spec.size_bytes,
            "git_blob_sha1": spec.git_blob_sha1,
        }
        for spec in MODEL_SPECS.values()
    ]
    return {
        "version": 1,
        "source": {
            "repository": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT,
            "license": LICENSE_ID,
            "license_name": LICENSE_NAME,
            "license_url": LICENSE_URL,
            "pack_license_urls": dict(PACK_LICENSE_URLS),
            "code_reused": False,
        },
        "slots": list(SLOTS),
        "outfits": outfits,
        "animations": list(ANIMATIONS),
        "rig_expectations": {
            "bone_count": 62,
            "animation_count": len(ANIMATIONS),
        },
    }


def _git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(b"blob " + str(size).encode("ascii") + bytes((0,)))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_DOWNLOAD_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model_file(path: Path, spec: CharacterModelSpec) -> bool:
    try:
        return (
            path.is_file()
            and path.stat().st_size == spec.size_bytes
            and _git_blob_sha1(path) == spec.git_blob_sha1
        )
    except OSError:
        return False


def download_model_asset(
    spec: CharacterModelSpec,
    destination: Path,
    opener: Callable[..., Any] | None = None,
) -> Path:
    destination = Path(destination)
    temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    open_url = opener or urlopen
    request = Request(
        spec.url,
        headers={"User-Agent": "CartoonStudio-CharacterLibrary/1.0"},
    )
    total = 0
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open_url(request, timeout=_DOWNLOAD_TIMEOUT_SECONDS) as response:
            with temporary.open("wb") as handle:
                while True:
                    chunk = response.read(_DOWNLOAD_CHUNK_BYTES)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > spec.size_bytes:
                        raise CharacterLibraryError(
                            f"Pinned model {spec.model_id} exceeded its expected size."
                        )
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        if total != spec.size_bytes:
            raise CharacterLibraryError(
                f"Pinned model {spec.model_id} has an unexpected file size."
            )
        if _git_blob_sha1(temporary) != spec.git_blob_sha1:
            raise CharacterLibraryError(
                f"Pinned model {spec.model_id} failed its Git blob integrity check."
            )
        os.replace(temporary, destination)
        return destination
    except CharacterLibraryError:
        raise
    except Exception as error:
        raise CharacterLibraryError(
            f"Could not download pinned model {spec.model_id}."
        ) from error
    finally:
        temporary.unlink(missing_ok=True)


def ensure_model_asset(cache_root: Path, pack: str, outfit: str) -> Path:
    spec = get_model_spec(pack, outfit)
    root = Path(cache_root).expanduser().resolve()
    destination = (root / "quaternius" / pack / f"{outfit}.glb").resolve()
    if root not in destination.parents:
        raise UnknownCharacterModel("The requested model cache path is invalid.")
    with _DOWNLOAD_LOCK:
        if verify_model_file(destination, spec):
            return destination
        destination.unlink(missing_ok=True)
        return download_model_asset(spec, destination)
