#!/usr/bin/env python3
"""Rotate cassette artwork for the GitHub profile README."""

from __future__ import annotations

import random
from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "cassettes" / "source"
BLACKLIGHT_TARGET = ROOT / "assets" / "cassettes" / "current-blacklight.png"
MIDDLEMAN_TARGET = ROOT / "assets" / "cassettes" / "current-middleman.png"
SPOTIFY_TARGET = ROOT / "assets" / "cassettes" / "current-spotify.png"
OUTPUT_SIZE = 72
SOURCE_PADDING = 1


def strip_uniform_frame(image: Image.Image) -> Image.Image:
    """Remove solid perimeter frames without touching the enclosed artwork."""
    while image.width > 2 and image.height > 2:
        pixels = image.load()
        perimeter = (
            [pixels[x, 0] for x in range(image.width)]
            + [pixels[x, image.height - 1] for x in range(image.width)]
            + [pixels[0, y] for y in range(1, image.height - 1)]
            + [pixels[image.width - 1, y] for y in range(1, image.height - 1)]
        )
        if len(set(perimeter)) != 1:
            break
        image = image.crop((1, 1, image.width - 1, image.height - 1))
    return image


def remove_edge_background(image: Image.Image) -> Image.Image:
    """Make only edge-connected row/column background colors transparent."""
    image = strip_uniform_frame(image.convert("RGBA"))
    pixels = image.load()
    width, height = image.size

    left_colors = [pixels[0, y][:3] for y in range(height)]
    right_colors = [pixels[width - 1, y][:3] for y in range(height)]
    top_colors = [pixels[x, 0][:3] for x in range(width)]
    bottom_colors = [pixels[x, height - 1][:3] for x in range(width)]

    def is_background_candidate(x: int, y: int) -> bool:
        red, green, blue, alpha = pixels[x, y]
        color = (red, green, blue)
        return alpha == 0 or color in (
            left_colors[y],
            right_colors[y],
            top_colors[x],
            bottom_colors[x],
        )

    queue: deque[tuple[int, int]] = deque()
    visited = bytearray(width * height)

    def enqueue(x: int, y: int) -> None:
        index = y * width + x
        if not visited[index] and is_background_candidate(x, y):
            visited[index] = 1
            queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    for index, is_background in enumerate(visited):
        if is_background:
            x = index % width
            y = index // width
            red, green, blue, _ = pixels[x, y]
            pixels[x, y] = (red, green, blue, 0)

    return image


def prepare_cassette(path: Path) -> Image.Image:
    """Crop cassette art, square-pad transparently, and scale pixel-perfectly."""
    with Image.open(path) as source:
        image = remove_edge_background(source)

    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"No cassette artwork found in {path}")

    left, top, right, bottom = bounds
    crop_box = (
        max(0, left - SOURCE_PADDING),
        max(0, top - SOURCE_PADDING),
        min(image.width, right + SOURCE_PADDING),
        min(image.height, bottom + SOURCE_PADDING),
    )
    cropped = image.crop(crop_box)

    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    offset = ((side - cropped.width) // 2, (side - cropped.height) // 2)
    square.alpha_composite(cropped, offset)
    return square.resize(
        (OUTPUT_SIZE, OUTPUT_SIZE),
        resample=Image.Resampling.NEAREST,
    )


def write_cassette(image: Image.Image, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG")


def main() -> int:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(path for path in SOURCE_DIR.glob("*.png") if path.is_file())

    if len(images) < 2:
        print(
            "Need at least two PNG files in assets/cassettes/source/ "
            "to rotate cassette artwork. No files were changed."
        )
        return 0

    processed = {path: prepare_cassette(path) for path in images}
    blacklight, middleman = random.sample(images, 2)
    spotify = random.choice(images)

    write_cassette(processed[blacklight], BLACKLIGHT_TARGET)
    write_cassette(processed[middleman], MIDDLEMAN_TARGET)
    write_cassette(processed[spotify], SPOTIFY_TARGET)

    print(f"Project Blacklight cassette: {blacklight.name}")
    print(f"Middle Man cassette: {middleman.name}")
    print(f"Spotify cassette: {spotify.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
