"""Render quality profiles for the four presets the master brief requires.

Preview, Low Hardware, Balanced and High Quality change render cost only: frame
rate and resolution. Every preset renders the same video, audio and subtitle
streams, so a lower preset can never silently remove a required feature.

The profile is stored in the project document as ``settings.quality_preset`` and
read by the episode render route; nothing else decides the render size.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityProfile:
    """One render preset: cost and the two numbers that define it."""

    name: str
    label: str
    fps: int
    width: int
    height: int
    note: str


QUALITY_PROFILES = {
    "preview": QualityProfile(
        name="preview",
        label="Preview",
        fps=15,
        width=640,
        height=360,
        note="Fastest draft on the target laptop: 15 fps at 640x360.",
    ),
    "low_hardware": QualityProfile(
        name="low_hardware",
        label="Low Hardware",
        fps=24,
        width=854,
        height=480,
        note="Native frame rate at SD resolution for the Intel HD 5500 target.",
    ),
    "balanced": QualityProfile(
        name="balanced",
        label="Balanced",
        fps=24,
        width=1280,
        height=720,
        note="Native frame rate at 720p; the default for a saved episode.",
    ),
    "high_quality": QualityProfile(
        name="high_quality",
        label="High Quality",
        fps=30,
        width=1920,
        height=1080,
        note="30 fps at 1080p; slowest preset, for final delivery.",
    ),
}
DEFAULT_QUALITY_PRESET = "balanced"
QUALITY_PRESET_NAMES = tuple(QUALITY_PROFILES)


def resolve_quality_profile(name: str | None) -> QualityProfile:
    """Return the profile for a preset name, falling back to the default."""
    if name and name in QUALITY_PROFILES:
        return QUALITY_PROFILES[name]
    return QUALITY_PROFILES[DEFAULT_QUALITY_PRESET]


def quality_summary() -> list[dict[str, object]]:
    """Return the preset table for the settings API and UI."""
    return [
        {
            "name": profile.name,
            "label": profile.label,
            "fps": profile.fps,
            "width": profile.width,
            "height": profile.height,
            "note": profile.note,
            "default": profile.name == DEFAULT_QUALITY_PRESET,
        }
        for profile in QUALITY_PROFILES.values()
    ]
