#!/usr/bin/env python3
"""Export the original ISSD (USA) roster tables to an auditable JSON catalog.

The game does not store squad data as text.  This decoder reads the exact
tables used by the cartridge: 36 squads × 20 players, seven packed attribute
bytes per player, and one formation record per squad.  It deliberately keeps
the raw bytes alongside decoded values, so the web port can reproduce the
cartridge rules instead of relying on hand-entered data.

Usage:
  python tools/extract_issd_catalog.py \
      "International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc" \
      docs/issd-rom-catalog.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_MD5 = "345ddedcd63412b9373dabb67c11fc05"
ROM_NAME_BASE = 0x03818E
ROM_ATTR_BASE = 0x050000
ROM_FORMATION_PTRS = 0x05EF48
ROM_FORMATION_BANK = 0x0B
ROM_KIT_PTRS_HOME = 0x01027A
ROM_KIT_PTRS_AWAY = 0x0102D0
ROM_KIT_BANK = 0x09
ROM_KIT_STRIDE = 34
TEAMS = 36
PLAYERS_PER_TEAM = 20
NAME_BYTES = 8
ATTR_BYTES = 7

TEAM_NAMES = (
    "Italy", "Holland", "England", "Norway", "Spain", "Ireland",
    "Portugal", "Denmark", "Germany", "France", "Belgium", "Sweden",
    "Romania", "Bulgaria", "Russia", "Swiss", "Greece", "Croatia",
    "Austria", "Wales", "Scotland", "N.Ireland", "Czech Rep.", "Poland",
    "Japan", "S.Korea", "Turkey", "Nigeria", "Cameroon", "Morocco",
    "Brazil", "Argentina", "Columbia", "Mexico", "U.S.A", "Uruguay",
)
FORMATION_LABELS = (
    "4-5-1", "4-4-2", "4-3-3", "4-2-4", "3-5-2", "3-4-3", "3-3-4",
    "3-2-5", "2-5-3", "2-4-4", "2-3-5", "5-4-1", "5-3-2", "5-2-3",
    "1-5-4", "1-4-5",
)
POSITION_NAMES = {1: "GK", 2: "DF", 3: "DF/MF", 4: "MF", 5: "MF/FW", 6: "FW"}
CHARSET = {0x00: " ", 0x54: "."}
CHARSET.update({0x68 + index: chr(ord("A") + index) for index in range(26)})
CHARSET.update({0x82 + index: chr(ord("a") + index) for index in range(26)})


def strip_copier_header(data: bytes) -> bytes:
    return data[512:] if len(data) % 1024 == 512 else data


def decode_name(raw: bytes) -> str:
    return "".join(CHARSET.get(value, "?") for value in raw).rstrip()


def decode_rating(nibble: int) -> int:
    """Map the cartridge's 4-bit level to the midpoint of its 0–99 band."""
    nibble = max(2, min(9, nibble))
    band = [rating for rating in range(100)
            if 2 + ((rating * 7 + 49) // 99) == nibble]
    return (band[0] + band[-1]) // 2


def read_word(data: bytes, offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8)


def bgr555_to_hex(value: int) -> str:
    red = (value & 31) * 255 // 31
    green = ((value >> 5) & 31) * 255 // 31
    blue = ((value >> 10) & 31) * 255 // 31
    return f"#{red:02X}{green:02X}{blue:02X}"


def read_kit(data: bytes, team_id: int, away: bool) -> dict | None:
    table = ROM_KIT_PTRS_AWAY if away else ROM_KIT_PTRS_HOME
    pointer = read_word(data, table + team_id * 2)
    if pointer < 0x8000:
        return None
    offset = ROM_KIT_BANK * 0x8000 + (pointer - 0x8000) + 2
    if offset + ROM_KIT_STRIDE > len(data):
        return None
    def colours(slot: int, count: int) -> list[str]:
        return [bgr555_to_hex(read_word(data, offset + (slot + shade) * 2)) for shade in range(count)]
    return {
        "source_offset": f"0x{offset:06X}",
        # The complete 16-colour OBJ palette belongs to the same kit record.
        # Index zero is transparent in an OBJ tile; the remaining entries
        # include skin/hair shades, kit shades and shared accent colours.
        "sprite_palette": [bgr555_to_hex(read_word(data, offset + index * 2)) for index in range(16)],
        "shirt": colours(7, 3),
        "shorts": colours(10, 3),
        "socks": colours(13, 2),
    }


def read_formation(data: bytes, team_id: int) -> dict:
    pointer = read_word(data, ROM_FORMATION_PTRS + team_id * 2)
    offset = ROM_FORMATION_BANK * 0x8000 + (pointer - 0x8000)
    raw = data[offset:offset + 31]
    label = raw[0]
    positions = []
    for slot in range(10):
        positions.append({
            "slot": slot + 1,
            "depth": int.from_bytes(raw[1 + slot * 2:2 + slot * 2], "little", signed=True),
            "width": int.from_bytes(raw[2 + slot * 2:3 + slot * 2], "little", signed=True),
            "role_code": raw[21 + slot],
        })
    return {
        "label_code": label,
        "label": FORMATION_LABELS[label] if label < len(FORMATION_LABELS) else None,
        "raw_hex": raw.hex(),
        "outfield_slots": positions,
    }


def read_player(data: bytes, team_id: int, player_id: int) -> dict:
    index = team_id * PLAYERS_PER_TEAM + player_id
    name_offset = ROM_NAME_BASE + index * NAME_BYTES
    attr_offset = ROM_ATTR_BASE + index * ATTR_BYTES
    raw_name = data[name_offset:name_offset + NAME_BYTES]
    raw = data[attr_offset:attr_offset + ATTR_BYTES]
    position_code = raw[4] >> 4
    return {
        "slot": player_id,
        "name": decode_name(raw_name),
        "shirt_number": player_id + 1,
        "position_code": position_code,
        "position": POSITION_NAMES.get(position_code, f"raw-{position_code}"),
        "appearance": {"skin_tone": raw[6] >> 4, "hair_style": raw[6] & 0x0F},
        "attributes": {
            "acceleration": decode_rating(raw[0] >> 4), "speed": decode_rating(raw[0] & 0x0F),
            "shooting": decode_rating(raw[1] >> 4), "technique": decode_rating(raw[1] & 0x0F),
            "balance": decode_rating(raw[2] >> 4), "intelligence": decode_rating(raw[2] & 0x0F),
            "dribbling": decode_rating(raw[3] >> 4), "jumping": decode_rating(raw[3] & 0x0F),
            "stamina": decode_rating(raw[4] & 0x0F),
        },
        "raw": {"name_hex": raw_name.hex(), "attributes_hex": raw.hex()},
    }


def extract(data: bytes) -> dict:
    teams = []
    for team_id, team_name in enumerate(TEAM_NAMES):
        teams.append({
            "id": team_id,
            "name": team_name,
            "kit": {"home": read_kit(data, team_id, False), "away": read_kit(data, team_id, True)},
            "formation": read_formation(data, team_id),
            "players": [read_player(data, team_id, player_id) for player_id in range(PLAYERS_PER_TEAM)],
        })
    return teams


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.rom.read_bytes()
    data = strip_copier_header(source)
    digest = hashlib.md5(data).hexdigest()
    if digest != EXPECTED_MD5:
        raise SystemExit(f"ROM MD5 {digest} does not match the supported USA revision ({EXPECTED_MD5}).")
    if len(data) <= ROM_ATTR_BASE + TEAMS * PLAYERS_PER_TEAM * ATTR_BYTES:
        raise SystemExit("ROM ends before the ISSD roster tables.")
    first_name = decode_name(data[ROM_NAME_BASE:ROM_NAME_BASE + NAME_BYTES])
    if not first_name or "?" in first_name:
        raise SystemExit("The expected player-name table could not be decoded.")
    catalog = {
        "schema_version": 1,
        "source": {
            "game": "International Superstar Soccer Deluxe (USA)",
            "rom_md5": digest,
            "rom_sha256": hashlib.sha256(data).hexdigest(),
            "roster_layout": {"teams": TEAMS, "players_per_team": PLAYERS_PER_TEAM,
                              "name_table_offset": f"0x{ROM_NAME_BASE:06X}",
                              "attribute_table_offset": f"0x{ROM_ATTR_BASE:06X}"},
        },
        "teams": extract(data),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}: {len(catalog['teams'])} teams, "
          f"{sum(len(team['players']) for team in catalog['teams'])} players")


if __name__ == "__main__":
    main()
