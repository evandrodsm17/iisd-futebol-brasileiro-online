"""Render a small, browser-friendly ISS Deluxe player sprite sheet.

The input files are the 4bpp SNES player frames extracted from a locally owned
USA ROM with the companion extraction script.  This utility never distributes
or modifies the ROM; it converts the extracted tile planes into PNG assets.
"""

import argparse
import json
from pathlib import Path

from PIL import Image


TILE = 8
# A player frame consists of twelve 8×8 SNES tiles.  The ROM's body upload is
# a three-column by four-row silhouette (not the 4×3 contact sheet used by the
# first prototype renderer).
FRAME_COLUMNS = 3
FRAME_ROWS = 4
SCALE = 2


def decode_tile(data: bytes, tile_index: int, palette: list[tuple[int, int, int, int]]):
    """Decode a SNES 4bpp planar tile into a transparent RGBA image."""
    start = tile_index * 32
    tile = Image.new("RGBA", (TILE, TILE))
    pixels = tile.load()
    for y in range(TILE):
        lo, hi = data[start + y * 2], data[start + y * 2 + 1]
        lo2, hi2 = data[start + 16 + y * 2], data[start + 16 + y * 2 + 1]
        for x in range(TILE):
            bit = 7 - x
            color = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1) | (((lo2 >> bit) & 1) << 2) | (((hi2 >> bit) & 1) << 3)
            pixels[x, y] = palette[color]
    return tile


def render_frame(source: Path, palette: list[tuple[int, int, int, int]]):
    data = source.read_bytes()
    expected = FRAME_COLUMNS * FRAME_ROWS
    if len(data) < expected * 32:
        raise ValueError(f"{source.name} has fewer than {expected} SNES tiles")
    frame = Image.new("RGBA", (FRAME_COLUMNS * TILE, FRAME_ROWS * TILE))
    for index in range(expected):
        frame.alpha_composite(decode_tile(data, index, palette), ((index % FRAME_COLUMNS) * TILE, (index // FRAME_COLUMNS) * TILE))
    return frame


def make_palette(jersey: tuple[int, int, int]):
    # Index zero is transparent. Remaining entries map skin, hair, kit and shading.
    r, g, b = jersey
    shadow = (max(r - 56, 0), max(g - 56, 0), max(b - 56, 0), 255)
    return [
        (0, 0, 0, 0), (250, 205, 158, 255), (191, 125, 88, 255), (54, 37, 31, 255),
        (r, g, b, 255), shadow, (239, 239, 224, 255), (32, 49, 61, 255),
        (244, 231, 190, 255), (115, 76, 54, 255), (31, 36, 44, 255), (148, 161, 169, 255),
        (119, 163, 83, 255), (220, 78, 64, 255), (255, 255, 255, 255), (16, 22, 29, 255),
    ]


def make_sheet(source_dir: Path, destination: Path, palette: list[tuple[int, int, int, int]], direction: str):
    frames = sorted(source_dir.glob(f"GFX_Sprite_Player_{direction}_Running*.bin"), key=lambda p: int(p.stem.rsplit("Running", 1)[1]))
    if not frames:
        raise FileNotFoundError("No extracted Player_Down_Running frames were found")
    rendered = [render_frame(frame, palette) for frame in frames]
    width, height = rendered[0].size
    sheet = Image.new("RGBA", (width * len(rendered), height))
    for i, frame in enumerate(rendered):
        sheet.alpha_composite(frame, (i * width, 0))
    sheet = sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.Resampling.NEAREST)
    destination.mkdir(parents=True, exist_ok=True)
    sheet.save(destination / f"issd-player-{direction.lower()}.png")


def palette_from_kit(kit: dict) -> list[tuple[int, int, int, int]]:
    """Use the actual 16-colour OBJ palette extracted from a kit record."""
    values = kit.get("sprite_palette")
    if not isinstance(values, list) or len(values) != 16:
        raise ValueError("catalog kit is missing its 16-colour sprite palette")
    palette = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
            raise ValueError("catalog contains an invalid sprite-palette colour")
        rgb = tuple(bytes.fromhex(value[1:]))
        palette.append((*rgb, 0 if index == 0 else 255))
    return palette


def render_catalog(source: Path, catalog_path: Path, destination: Path) -> None:
    """Render the shared running tiles once per original team kit.

    The tile artwork remains the ROM's 4bpp running body.  Only the matching
    ROM palette changes, so a selected team has its real home/change strip
    rather than the prototype's fixed blue/red recolour.
    """
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    teams = catalog.get("teams")
    if not isinstance(teams, list) or len(teams) != 36:
        raise ValueError("catalog must contain the 36 cartridge teams")
    directions = ("Up", "DiagonalUp", "Side", "DiagonalDown", "Down")
    for team in teams:
        team_id = team.get("id")
        if not isinstance(team_id, int):
            raise ValueError("catalog team is missing an integer ID")
        for kit_name in ("home", "away"):
            kit = team.get("kit", {}).get(kit_name)
            if not isinstance(kit, dict):
                raise ValueError(f"team {team_id} is missing {kit_name} kit data")
            output = destination / "teams" / f"{team_id:02d}" / kit_name
            actual_palette = palette_from_kit(kit)
            for direction in directions:
                make_sheet(source, output, actual_palette, direction)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="directory containing extracted running-frame bins")
    parser.add_argument("output", type=Path)
    parser.add_argument("--catalog", type=Path, help="render all ROM team home/change palettes")
    args = parser.parse_args()
    source, output = args.source, args.output
    if args.catalog:
        render_catalog(source, args.catalog, output)
        raise SystemExit(0)
    directions = ("Up", "DiagonalUp", "Side", "DiagonalDown", "Down")
    for team, jersey in (("blue", (39, 135, 212)), ("red", (217, 75, 63))):
        team_output = output / team
        for direction in directions:
            make_sheet(source, team_output, make_palette(jersey), direction)
