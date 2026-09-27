#!/usr/bin/env python3
"""Rotate cassette artwork for the GitHub profile README."""

from __future__ import annotations

import random
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "cassettes" / "source"
BLACKLIGHT_TARGET = ROOT / "assets" / "cassettes" / "current-blacklight.png"
MIDDLEMAN_TARGET = ROOT / "assets" / "cassettes" / "current-middleman.png"
SPOTIFY_TARGET = ROOT / "assets" / "cassettes" / "current-spotify.png"


def main() -> int:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(path for path in SOURCE_DIR.glob("*.png") if path.is_file())

    if len(images) < 2:
        print(
            "Need at least two PNG files in assets/cassettes/source/ "
            "to rotate cassette artwork. No files were changed."
        )
        return 0

    blacklight, middleman = random.sample(images, 2)
    spotify = random.choice(images)

    BLACKLIGHT_TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(blacklight, BLACKLIGHT_TARGET)
    shutil.copyfile(middleman, MIDDLEMAN_TARGET)
    shutil.copyfile(spotify, SPOTIFY_TARGET)

    print(f"Project Blacklight cassette: {blacklight.name}")
    print(f"Middle Man cassette: {middleman.name}")
    print(f"Spotify cassette: {spotify.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
