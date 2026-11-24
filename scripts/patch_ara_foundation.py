from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected one occurrence, found {count}: {old!r}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def replace_all(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count < 1:
        raise RuntimeError(f"{relative}: expected at least one occurrence: {old!r}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def append_once(relative: str, marker: str, addition: str) -> None:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    if marker in source:
        return
    path.write_text(source.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")


def main() -> None:
    # Extend Ara's existing multi-scene film editor from five to seven one-minute scenes.
    replace_once(
        "src/studio/film.ts",
        "export const MAX_SCENES = 5;",
        "export const MAX_SCENES = 7;",
    )
    replace_once(
        "src/studio/film.ts",
        "/** Largest film file, in characters: five full scenes. */",
        "/** Largest film file, in characters: seven full scenes. */",
    )
    replace_once(
        "src/studio/film.ts",
        "export const MAX_FILM_SIZE = 500_000;",
        "export const MAX_FILM_SIZE = 700_000;",
    )
    replace_all("src/studio/film.ts", "up to five scenes", "up to seven scenes")
    replace_all(
        "src/studio/film.ts",
        "Choose a film smaller than 500 KB.",
        "Choose a film smaller than 700 KB.",
    )

    # Reuse the shared file-size constant in the Studio import path.
    replace_once(
        "src/studio/main.ts",
        "import { MAX_SCENES, filmDuration, filmJson, historyEntry, parseFilm, readHistoryEntry, sceneLabel, shareFilmSettings, fadeLevel } from './film';",
        "import { MAX_FILM_SIZE, MAX_SCENES, filmDuration, filmJson, historyEntry, parseFilm, readHistoryEntry, sceneLabel, shareFilmSettings, fadeLevel } from './film';",
    )
    replace_once("src/studio/main.ts", "source.size>500_000", "source.size>MAX_FILM_SIZE")
    replace_all(
        "src/studio/main.ts",
        "Use JSON smaller than 500 KB.",
        "Use JSON smaller than 700 KB.",
    )
    replace_all("src/studio/assist.ts", "500 KB", "700 KB")
    replace_all("src/play/studio-film.ts", "500 KB", "700 KB")

    # Update the upstream film parser tests to assert the expanded limits.
    replace_once(
        "scripts/studio-film-check.ts",
        "import { FADE, MAX_SCENES, fadeLevel, filmDuration, filmJson, historyEntry, parseFilm, readHistoryEntry, sceneAt, sceneLabel, sceneStarts, shareFilmSettings } from '../src/studio/film';",
        "import { FADE, MAX_FILM_SIZE, MAX_SCENES, fadeLevel, filmDuration, filmJson, historyEntry, parseFilm, readHistoryEntry, sceneAt, sceneLabel, sceneStarts, shareFilmSettings } from '../src/studio/film';",
    )
    replace_all("scripts/studio-film-check.ts", "one to 5 scenes", "one to 7 scenes")
    replace_once(
        "scripts/studio-film-check.ts",
        "assert.throws(() => parseFilm('x'.repeat(500_001)), /500 KB/);",
        "assert.throws(() => parseFilm('x'.repeat(MAX_FILM_SIZE + 1)), /700 KB/);",
    )
    replace_all(
        "scripts/studio-film-check.ts",
        "Film limits: five scenes",
        "Film limits: seven scenes",
    )

    # Keep user-facing upstream documentation consistent with the patched editor.
    replace_all("README.md", "up to five scenes", "up to seven scenes")
    replace_all("docs/README.md", "up to five scenes", "up to seven scenes")
    replace_all("docs/studio.md", "five scenes", "seven scenes")
    replace_all("docs/mcp.md", "up to five scenes", "up to seven scenes")

    # Compact the inspector at 1366x768 and other short desktop viewports.
    append_once(
        "src/studio/style.css",
        "Cartoon Studio compact inspector patch",
        """
/* Cartoon Studio compact inspector patch: keep the format and title-card controls visible on short desktop screens. */
@media (min-width: 1101px) and (max-height: 800px) {
  .inspector-section { padding: 4px 0; }
  .inspector .section-heading { margin-bottom: 4px; }
  .inspector label, .inspector .field-label { margin: 3px 0 2px; }
  .inspector input, .inspector select { min-height: 25px; padding: 4px 6px; }
  .inspector .cast-heading { margin: 7px 0 4px; }
  .inspector .cast-roster { gap: 3px; }
  .inspector .cast-member { padding: 3px 5px; }
  .inspector .cast-actions { margin: 3px 0; }
  .inspector .cast-status { margin: 2px 0 4px; }
  .inspector #action-note { max-height: 16px; margin: 3px 0; }
  .inspector .beat-tools { margin-top: 4px; }
  .inspector .coordinate-row { margin-top: 3px; }
  .inspector .camera-reset { margin: 2px 0; }
  .inspector .aspect-options { margin-top: 2px; }
  .inspector #blocking-hint { max-height: 16px; overflow: hidden; margin: 2px 0; }
  .caption-setting { margin-top: 3px; padding-bottom: 4px; }
}
""",
    )
    print("Applied Cartoon Studio Ara foundation patches: seven-scene films, 700 KB project JSON, compact 1366x768 inspector.")


if __name__ == "__main__":
    main()
