from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.audio import VOICE_CATALOG

SUPPORTED_VOICE_IDS = tuple(VOICE_CATALOG)

# A scene names either a catalog backdrop or a location owned by the episode's
# saved world. The ``world:`` prefix keeps the two vocabularies apart, so a typo
# can never silently resolve to a different place, and a world's own locations
# never collide with the catalog's identifiers.
WORLD_LOCATION_PREFIX = "world:"
WORLD_LOCATION_PATTERN = r"^world:[a-z][a-z0-9_-]{0,39}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


LOCATION_CATALOG = {
    "portrait": "The portrait",
    "runway": "After hours",
    "black-box": "Black box",
    "cyclorama": "White cyclorama",
    "art-gallery": "Art gallery",
    "photo-loft": "Photo loft",
    "office": "Executive office",
    "open-office": "Open-plan office",
    "boardroom": "Boardroom",
    "newsroom": "Newsroom",
    "recording-studio": "Recording studio",
    "classroom": "Classroom",
    "laboratory": "Laboratory",
    "coworking": "Co-working lounge",
    "bedroom": "Morning bedroom",
    "bedroom-night": "Bedroom at night",
    "living-room": "Living room",
    "kitchen": "Kitchen",
    "dining-room": "Dining room",
    "apartment-loft": "City loft",
    "home-library": "Home library",
    "veranda": "Veranda",
    "beach": "Palm beach",
    "sunset-beach": "Sunset beach",
    "resort-pool": "Resort pool",
    "infinity-pool": "Infinity pool",
    "hotel-lobby": "Hotel lobby",
    "rooftop-bar": "Rooftop bar",
    "spa": "Garden spa",
    "wedding-garden": "Wedding garden",
    "restaurant-terrace": "Restaurant terrace",
    "yacht-deck": "Yacht deck",
    "street-cafe": "Street café",
    "alley": "Neon alley",
    "subway": "Subway platform",
    "parking-garage": "Parking garage",
    "diner": "Roadside diner",
    "warehouse": "Warehouse",
    "city-rooftop": "City rooftop",
    "airport-lounge": "Airport lounge",
    "train-platform": "Railway platform",
    "boutique": "Fashion boutique",
    "courtyard": "Golden hour",
    "urban-park": "City park",
    "forest-trail": "Forest trail",
    "campsite": "Lakeside campsite",
    "desert-outpost": "Desert outpost",
    "mountain-lake": "Mountain lake",
    "sports-court": "Basketball court",
    "harbour": "Harbour promenade",
    "hospital-room": "Hospital room",
    "police-station": "Police station",
    "interrogation-room": "Police interrogation room",
    "highway": "Highway",
    "military-base": "Military base",
    "prison-cell": "Prison cell",
    "prison-yard": "Prison yard",
    "public-restroom": "Public restroom",
    "private-bathroom": "Private bathroom / toilet",
    "neon-street": "Neon-lit street",
    "back-alley": "Alley",
    "football-stadium": "Football stadium",
    "fine-dining": "Fancy-dining restaurant room",
    "night-club": "Night club",
    "elevator": "Elevator",
    "church": "Church",
    "train-carriage": "Train carriage",
    "city-bus": "City bus",
    "private-jet": "Private jet",
    "airliner-cabin": "Airliner cabin",
    "gym": "Gym",
}
EXPRESSION_IDS = (
    "neutral",
    "happy",
    "laughing",
    "angry",
    "sad",
    "crying",
    "surprised",
    "afraid",
    "determined",
)
ExpressionId = Literal[
    "neutral",
    "happy",
    "laughing",
    "angry",
    "sad",
    "crying",
    "surprised",
    "afraid",
    "determined",
]


class CharacterSpec(StrictModel):
    id: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=80)
    personality: str = Field(default="", max_length=500)
    voice_profile: str = Field(default="", max_length=80)
    asset_id: str | None = Field(default=None, max_length=36, pattern=r"^[0-9a-fA-F-]{36}$")
    resting_expression: ExpressionId = "neutral"
    relationships: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("voice_profile")
    @classmethod
    def validate_voice_profile(cls, value: str) -> str:
        """Reject a voice now, not after the scenes have already been generated."""
        if value and value not in SUPPORTED_VOICE_IDS:
            supported = ", ".join(SUPPORTED_VOICE_IDS)
            raise ValueError(
                f"Unsupported voice_profile {value!r}; use one of: {supported}, "
                "or leave it blank to use the default voice."
            )
        return value


class DialogueLine(StrictModel):
    character_id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=1200)
    # The planned subtitle text in the requested subtitle_mode. Urdu mode uses
    # ``text``; roman_urdu and english modes require this field.
    subtitle_text: str = Field(default="", max_length=300)
    emotion: ExpressionId = "neutral"
    delivery: str = Field(default="natural", max_length=80)
    start_seconds: float = Field(ge=0, le=60)
    duration_seconds: float = Field(gt=0, le=45)


AVAILABLE_ACTION_IDS = [
    "idle",
    "crouch",
    "walk",
    "run",
    "walk_back",
    "strafe_left",
    "strafe_right",
    "run_slide",
    "stumble_recover",
    "talk",
    "talk_gestures",
    "wave",
    "cheer",
    "laugh",
    "clap",
    "point",
    "thumbs_up",
    "bow",
    "dance_groove",
    "dance_bounce",
    "phone_call",
    "texting",
    "take_picture",
    "lean_wall",
    "look_around",
    "sweep",
    "fall",
    "jump_start",
    "jump_air",
    "jump_land",
    "jump_running",
    "punch",
    "hit",
    "pick_up",
    "use_press",
    "open_door",
    "push",
    "put_down",
    "drive_car",
    "sit_passenger",
    "ride_bicycle",
    "ride_motorcycle",
]


class ActionCue(StrictModel):
    character_id: str = Field(min_length=1, max_length=40)
    action_id: str = Field(min_length=1, max_length=80)
    expression: ExpressionId = "neutral"
    target: str = Field(default="", max_length=120)
    start_seconds: float = Field(ge=0, le=60)
    duration_seconds: float = Field(gt=0, le=12)

    @field_validator("action_id")
    @classmethod
    def validate_action_id(cls, value: str) -> str:
        if value not in AVAILABLE_ACTION_IDS:
            raise ValueError("Action ID is not in the production animation catalog.")
        return value


class CameraCue(StrictModel):
    shot: Literal["wide", "medium", "close"]
    movement: Literal["locked", "orbit", "dolly"] = "locked"
    target: str = Field(default="all", max_length=40)
    start_seconds: float = Field(ge=0, le=60)
    duration_seconds: float = Field(gt=0, le=60)


class SoundCue(StrictModel):
    kind: Literal["music", "effect", "ambience"]
    description: str = Field(min_length=1, max_length=240)
    start_seconds: float = Field(ge=0, le=60)
    duration_seconds: float = Field(gt=0, le=60)
    volume: float = Field(default=0.5, ge=0, le=1)


class ScenePlan(StrictModel):
    id: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_-]*$")
    title: str = Field(min_length=1, max_length=100)
    location_id: str = Field(min_length=1, max_length=80)
    environment_description: str = Field(default="", max_length=1200)
    lighting: str = Field(default="", max_length=300)
    transition_to_next: Literal["cut", "fade"] = "cut"
    duration_seconds: int = Field(ge=30, le=60)
    character_ids: list[str] = Field(min_length=1, max_length=5)
    props: list[str] = Field(default_factory=list, max_length=30)
    dialogue: list[DialogueLine] = Field(default_factory=list, max_length=60)
    actions: list[ActionCue] = Field(default_factory=list, max_length=80)
    camera: list[CameraCue] = Field(default_factory=list, max_length=12)
    audio: list[SoundCue] = Field(default_factory=list, max_length=40)

    @field_validator("location_id")
    @classmethod
    def validate_location_id(cls, value: str) -> str:
        """Accept a catalog backdrop or a location the episode's world owns.

        A saved world owns reusable locations, so a scene names one as
        ``world:<location-id>``. The project-scoped save checks that the
        reference exists in the selected world; anything that is neither a
        catalog ID nor a world reference is refused here.
        """
        if value in LOCATION_CATALOG:
            return value
        if re.fullmatch(WORLD_LOCATION_PATTERN, value):
            return value
        raise ValueError(
            "Location ID must be a production scene catalog ID or a saved world "
            "location written as world:<location-id>."
        )


class EpisodePlan(StrictModel):
    title: str = Field(min_length=1, max_length=100)
    synopsis: str = Field(min_length=1, max_length=1500)
    ending: str = Field(default="", max_length=1500)
    language: Literal["ur"] = "ur"
    target_duration_seconds: int = Field(default=360, ge=300, le=420)
    world_id: str | None = Field(default=None, max_length=64)
    characters: list[CharacterSpec] = Field(min_length=1, max_length=5)
    scenes: list[ScenePlan] = Field(min_length=5, max_length=7)
    subtitle_mode: Literal["urdu", "roman_urdu", "english", "none"] = "urdu"

    @model_validator(mode="after")
    def validate_subtitle_text(self) -> EpisodePlan:
        """Require the planned subtitle line before production, not at render time."""
        if self.subtitle_mode in ("roman_urdu", "english"):
            missing = [
                f"{scene.id}:{index}"
                for scene in self.scenes
                for index, line in enumerate(scene.dialogue, start=1)
                if not line.subtitle_text.strip()
            ]
            if missing:
                raise ValueError(
                    f"subtitle_mode {self.subtitle_mode!r} requires subtitle_text on "
                    f"every dialogue line; missing at {', '.join(missing[:5])}."
                )
        return self

    @model_validator(mode="after")
    def validate_episode_timeline(self) -> EpisodePlan:
        character_ids = [character.id for character in self.characters]
        if len(character_ids) != len(set(character_ids)):
            raise ValueError("Character IDs must be unique.")

        scene_ids = [scene.id for scene in self.scenes]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique.")

        total_duration = sum(scene.duration_seconds for scene in self.scenes)
        if not 300 <= total_duration <= 420:
            raise ValueError("Total episode duration must be between 300 and 420 seconds.")
        if abs(total_duration - self.target_duration_seconds) > 30:
            raise ValueError(
                "Total scene duration must be within 30 seconds of target_duration_seconds."
            )

        known_characters = set(character_ids)
        for scene in self.scenes:
            scene_characters = set(scene.character_ids)
            if len(scene_characters) != len(scene.character_ids):
                raise ValueError(f"Scene {scene.id} contains duplicate character IDs.")
            if not scene_characters.issubset(known_characters):
                raise ValueError(f"Scene {scene.id} references an unknown character.")
            for line in scene.dialogue:
                if line.character_id != "narrator" and line.character_id not in scene_characters:
                    raise ValueError(
                        f"Scene {scene.id} dialogue references a character not in the scene."
                    )
                if line.start_seconds + line.duration_seconds > scene.duration_seconds:
                    raise ValueError(f"Scene {scene.id} has dialogue outside its duration.")
            action_counts: dict[str, int] = {}
            for action in scene.actions:
                if action.character_id not in scene_characters:
                    raise ValueError(
                        f"Scene {scene.id} action references a character not in the scene."
                    )
                action_counts[action.character_id] = action_counts.get(action.character_id, 0) + 1
                if action_counts[action.character_id] > 16:
                    raise ValueError(
                        f"Scene {scene.id} exceeds 16 animation beats for one character."
                    )
                if action.start_seconds + action.duration_seconds > scene.duration_seconds:
                    raise ValueError(f"Scene {scene.id} has an action outside its duration.")
            for cue in scene.camera:
                if cue.target != "all" and cue.target not in scene_characters:
                    raise ValueError(
                        f"Scene {scene.id} camera cue targets a character not in the scene."
                    )
                if cue.start_seconds + cue.duration_seconds > scene.duration_seconds:
                    raise ValueError(f"Scene {scene.id} has a camera cue outside its duration.")
            for cue in scene.audio:
                if cue.start_seconds + cue.duration_seconds > scene.duration_seconds:
                    raise ValueError(f"Scene {scene.id} has an audio cue outside its duration.")
        return self


class WorldLocationRef(StrictModel):
    """One saved location of the episode's world, as offered to the prompt."""

    id: str = Field(min_length=1, max_length=40, pattern=r"^[a-z][a-z0-9_-]*$")
    label: str = Field(min_length=1, max_length=80)


class StoryPromptRequest(StrictModel):
    idea: str = Field(min_length=5, max_length=2000)
    language: Literal["ur"] = "ur"
    target_duration_seconds: int = Field(default=360, ge=300, le=420)
    tone: Literal["comedy", "adventure", "family", "mystery", "educational"] = "comedy"
    audience: Literal["family", "children", "general"] = "family"
    character_names: list[str] = Field(default_factory=list, max_length=5)
    continuity_notes: str = Field(default="", max_length=2000)
    world_context: str = Field(default="", max_length=3000)
    world_id: str | None = Field(default=None, max_length=64)
    world_locations: list[WorldLocationRef] = Field(default_factory=list, max_length=24)


def build_story_prompt(request: StoryPromptRequest) -> str:
    language_rule = (
        "Write all dialogue in natural Pakistani Urdu using Urdu script. "
        "Do not use Hindi or machine-translated phrasing. English dialogue is not "
        "supported by the bundled voice pack, so never switch the episode language."
    )
    schema = json.dumps(EpisodePlan.model_json_schema(), ensure_ascii=False, indent=2)
    characters = ", ".join(request.character_names) or "Create an original small recurring cast."
    action_ids = ", ".join(AVAILABLE_ACTION_IDS)
    location_catalog = "\n".join(
        f"- {location_id}: {name}" for location_id, name in LOCATION_CATALOG.items()
    )
    if request.world_locations:
        saved_locations = "\n".join(
            f"- {WORLD_LOCATION_PREFIX}{item.id}: {item.label}"
            for item in request.world_locations
        )
        location_rule = (
            "This episode is set in a saved world, so write every scene's location_id as\n"
            "  world:<location-id> using one of the saved world locations listed below.\n"
            "  Use a location catalog ID only for a scene that happens outside that world."
        )
    else:
        saved_locations = "None supplied; this episode is not bound to saved world locations."
        location_rule = (
            "Use only exact location_id values from the production location catalog below."
        )
    expression_ids = ", ".join(EXPRESSION_IDS)
    continuity = request.continuity_notes or (
        "Preserve established character identities and relationships."
    )
    world_context = request.world_context or (
        "No saved world selected; choose a suitable catalog location."
    )
    return f"""You are the story and scene director for an original 3D cartoon series.
Create one complete, production-ready episode plan. Do not copy existing copyrighted
characters, shows, stories, dialogue, names, branding or designs.

STORY IDEA:
{request.idea}

LANGUAGE:
{request.language}. {language_rule}

TARGET DURATION:
{request.target_duration_seconds} seconds ({request.target_duration_seconds // 60} minutes).

TONE: {request.tone}
AUDIENCE: {request.audience}
PREFERRED RECURRING CHARACTERS: {characters}
CONTINUITY NOTES: {continuity}
ESTABLISHED WORLD: {world_context}
WORLD ID: {request.world_id or "null"}

PRODUCTION RULES:
- Copy the exact WORLD ID above into the episode-level world_id field.
  Use null only when no world ID is supplied.
- Produce 5 to 7 scenes, each 30 to 60 seconds.
- Total scene duration must be 300 to 420 seconds and within 30 seconds of the target.
- Use no more than 5 characters and keep their IDs stable throughout the episode.
- Define character relationships and keep them consistent across the episode.
- Each action cue is one animation clip of up to 12 seconds.
  Split longer actions into multiple cues.
- Every scene needs a reusable location_id, character_ids, actions, expressions,
  camera, lighting, props, audio and transition plan.
- Dialogue must be natural, character-specific and timed within the scene.
- Set subtitle_mode to urdu, roman_urdu, english or none.
  urdu writes the dialogue text itself; roman_urdu and english require a
  subtitle_text on every dialogue line; none writes no subtitle entries.
- Set each character voice_profile to one of these Pakistani Urdu voices:
  ur_PK-fasih-medium (male) or ur_PK-aegis_female-medium (female).
- Include clear physical comedy and visual actions where appropriate.
  Do not rely only on dialogue.
- Use action_id values that can later map to the reusable animation library.
- Use only wide, medium or close shots and locked, orbit or dolly camera movement.
- Use only cut or fade scene transitions.
LOCATION RULES:
{location_rule}
- Use only these exact expression IDs: {expression_ids}.
- Use only the exact action IDs listed below; never invent clip IDs.

VALID SAVED WORLD LOCATIONS:
{saved_locations}

VALID LOCATION CATALOG (generic backdrops):
{location_catalog}

VALID EXPRESSION IDS:
{expression_ids}

VALID ACTION IDS:
{action_ids}
- Provide an ending that resolves the episode story.
- Keep every dialogue, action, camera and audio cue inside its scene duration.
- Use narrator as character_id only when narration is needed.
- Return valid JSON only. No Markdown fences, preamble or explanation.
- Match this JSON Schema exactly; do not add undocumented properties.

JSON SCHEMA:
{schema}
"""
