"""Stable mapping from episode ``action_id`` values to licensed animation clips.

The production scene builder uses a procedural pose for every action in the
brief's catalog. A real clip library is optional: when a clip pack has been
acquired and its manifest is present, the worker can play a clip and cross-fade
to the next one. This module is the single source of truth for the mapping and
for the shape of that manifest, so the browser, the adapter and the worker
cannot disagree about what a clip name means.

No third-party clip file is bundled by this repository. The acquisition script
``scripts/fetch_animation_clips.py`` records the exact source, licence and hash
of any pack the owner chooses to install; this module never downloads anything.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.story import AVAILABLE_ACTION_IDS

# The pack page <https://quaternius.com/packs/universalanimationlibrary.html>
# and its itch.io listing both state CC0 for the Universal Animation Library.
# QAL packs are deliberately excluded: QAL v1.0 forbids redistributing the
# assets themselves, so they cannot be shipped inside this application.
LICENSE = "CC0-1.0"
LICENSE_SOURCE = "https://quaternius.com/packs/universalanimationlibrary.html"
MANIFEST_FILENAME = "animation_clips.json"
MANIFEST_VERSION = 1

# Each action has one canonical clip name. Several actions may share a clip
# when the brief asks for a direction or intensity variant of one motion; the
# worker then mirrors or times the same source rather than inventing a name.
ACTION_CLIP_NAMES: dict[str, str] = {
    "idle": "Idle",
    "crouch": "Crouch",
    "walk": "Walk",
    "run": "Run",
    "walk_back": "Walk",
    "strafe_left": "Walk",
    "strafe_right": "Walk",
    "run_slide": "Slide",
    "stumble_recover": "Recover",
    "talk": "Talking",
    "talk_gestures": "TalkingGestures",
    "wave": "Wave",
    "cheer": "Cheering",
    "laugh": "Laughing",
    "clap": "Clapping",
    "point": "Pointing",
    "thumbs_up": "ThumbsUp",
    "bow": "Bow",
    "dance_groove": "Dance",
    "dance_bounce": "Dance",
    "phone_call": "PhoneCall",
    "texting": "Texting",
    "take_picture": "TakePicture",
    "lean_wall": "Lean",
    "look_around": "LookAround",
    "sweep": "Sweeping",
    "fall": "Falling",
    "jump_start": "JumpStart",
    "jump_air": "JumpAir",
    "jump_land": "JumpLand",
    "jump_running": "JumpRunning",
    "punch": "Punch",
    "hit": "Hit",
    "pick_up": "PickUp",
    "use_press": "PressButton",
    "open_door": "OpenDoor",
    "push": "Push",
    "put_down": "PutDown",
    "drive_car": "Driving",
    "sit_passenger": "Sitting",
    "ride_bicycle": "Cycling",
    "ride_motorcycle": "Motorcycling",
    "turn": "Turn",
    "sit": "Sit",
    "stand": "Stand",
    "cry": "Crying",
    "smile": "Smiling",
    "anger": "Angry",
    "surprise": "Surprised",
    "fear": "Afraid",
    "confusion": "Confused",
    "thinking": "Thinking",
    "blink": "Blink",
    "gestures": "Gestures",
    "fighting": "Fight",
    "throwing": "Throw",
    "interact": "Interact",
}


def clip_name_for_action(action_id: str) -> str | None:
    """Return the canonical clip name, or None when the action is unknown."""
    return ACTION_CLIP_NAMES.get(str(action_id))


def normalize_clip_name(name: str) -> str:
    """Match clip names the way GLTFLoader/Godot expose them."""
    return "".join(
        character
        for character in str(name).strip().lower()
        if character.isalnum()
    )


def build_clip_manifest(
    clips: list[dict[str, object]],
    *,
    source_url: str,
    sha256: str,
    license_source: str = LICENSE_SOURCE,
) -> dict[str, object]:
    """Build a reviewed manifest from an inventoried CC0 pack.

    ``clips`` entries carry ``name`` and ``file``; every action mapping must
    resolve to exactly one inventoried clip. An ambiguous or missing name is a
    hard error: guessing would silently animate the wrong action.
    """
    if not source_url.startswith("https://"):
        raise ValueError("Clip source must use HTTPS.")
    if len(sha256) != 64 or any(character not in "0123456789abcdef" for character in sha256):
        raise ValueError("Clip archive SHA-256 must be 64 lowercase hex characters.")
    by_name: dict[str, dict[str, object]] = {}
    for clip in clips:
        name = str(clip.get("name", ""))
        file_name = str(clip.get("file", ""))
        if not name or not file_name or "/" in file_name or "\\" in file_name:
            raise ValueError("Every clip needs a name and a bare GLB file name.")
        normalized = normalize_clip_name(name)
        if normalized in by_name:
            raise ValueError(f"Duplicate clip name in the inventory: {name!r}")
        by_name[normalized] = clip
    actions: dict[str, str] = {}
    for action_id, clip_name in ACTION_CLIP_NAMES.items():
        normalized = normalize_clip_name(name)
        if normalized not in by_name:
            raise ValueError(
                f"The clip inventory is missing {clip_name!r}, needed for action {action_id!r}."
            )
        actions[action_id] = normalized
    return {
        "manifest_version": MANIFEST_VERSION,
        "license": LICENSE,
        "license_source": license_source,
        "source_url": source_url,
        "sha256": sha256,
        "clips": clips,
        "actions": actions,
        "clip_names": {
            str(clip["name"]): str(clip["name"])
            for clip in clips
        },
        "clip_file": str(clips[0]["file"]) if clips else "",
    }


def validate_clip_manifest(document: dict[str, object]) -> list[str]:
    """Return action IDs the manifest can play, refusing a malformed one."""
    if document.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError("Unsupported animation clip manifest version.")
    if document.get("license") != LICENSE:
        raise ValueError("Only a CC0 animation clip pack may be installed.")
    if len(str(document.get("sha256", ""))) != 64:
        raise ValueError("Animation clip archive hash is missing or invalid.")
    actions = document.get("actions", {})
    if not isinstance(actions, dict):
        raise ValueError("Animation clip manifest has no action map.")
    action_ids = [action_id for action_id in actions if action_id in AVAILABLE_ACTION_IDS]
    if not action_ids:
        raise ValueError("Animation clip manifest maps no supported action ID.")
    return sorted(action_ids)


def load_clip_manifest(path: Path) -> dict[str, object] | None:
    """Load a manifest, or return None when no optional pack is installed."""
    manifest_path = Path(path)
    if manifest_path.name != MANIFEST_FILENAME:
        manifest_path = manifest_path / MANIFEST_FILENAME
    if not manifest_path.is_file():
        return None
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("The animation clip manifest is not readable JSON.") from error
    if not isinstance(document, dict):
        raise ValueError("The animation clip manifest must be a JSON object.")
    validate_clip_manifest(document)
    return document
