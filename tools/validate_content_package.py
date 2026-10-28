"""Validate a version-1 local content package for the future ISSD editor."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")


def fail(message: str) -> None:
    raise SystemExit(f"content package invalid: {message}")


def collection(payload: dict, name: str) -> list[dict]:
    value = payload.get(name)
    if not isinstance(value, list):
        fail(f"{name} must be an array")
    if not all(isinstance(entry, dict) for entry in value):
        fail(f"{name} entries must be objects")
    return value


def identifiers(entries: list[dict], name: str) -> set[str]:
    result = set()
    for entry in entries:
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            fail(f"{name} has invalid id")
        if identifier in result:
            fail(f"{name} repeats id {identifier}")
        result.add(identifier)
    return result


def relative_asset(path: object) -> bool:
    return isinstance(path, str) and bool(path) and not path.startswith(("/", "\\")) and ":" not in path and ".." not in Path(path).parts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--print-hash", action="store_true", help="include the canonical SHA-256 used by saves and multiplayer")
    args = parser.parse_args()
    payload = json.loads(args.package.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        fail("schema_version must be 1")
    if not isinstance(payload.get("package_id"), str) or not IDENTIFIER.fullmatch(payload["package_id"]):
        fail("package_id must be a stable identifier")
    if not isinstance(payload.get("revision"), int) or payload["revision"] < 1:
        fail("revision must be a positive integer")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict) or not all(isinstance(metadata.get(key), str) and metadata[key].strip() for key in ("name", "author", "license")):
        fail("metadata requires non-empty name, author and license")
    assets = payload.get("assets")
    if not isinstance(assets, list) or not all(relative_asset(asset) for asset in assets):
        fail("assets must contain only relative package paths")
    clubs = collection(payload, "clubs")
    players = collection(payload, "players")
    stadiums = collection(payload, "stadiums")
    competitions = collection(payload, "competitions")
    club_ids = identifiers(clubs, "clubs")
    identifiers(players, "players")
    identifiers(stadiums, "stadiums")
    identifiers(competitions, "competitions")
    for club in clubs:
        kits = club.get("kits")
        if not isinstance(kits, list) or not {"home", "away"} <= {kit.get("kind") for kit in kits if isinstance(kit, dict)}:
            fail(f"club {club['id']} requires home and away kits")
        for kit in kits:
            if not isinstance(kit, dict) or not isinstance(kit.get("id"), str) or kit.get("kind") not in {"home", "away", "third", "goalkeeper"}:
                fail(f"club {club['id']} has invalid kit")
            colours = kit.get("colours")
            if not isinstance(colours, dict) or not colours or not all(isinstance(value, str) and COLOUR.fullmatch(value) for value in colours.values()):
                fail(f"club {club['id']} kit {kit['id']} has invalid colours")
    for player in players:
        club_id = player.get("club_id")
        if club_id is not None and club_id not in club_ids:
            fail(f"player {player['id']} references unknown club {club_id}")
    result = {"status": "ok", "package_id": payload["package_id"], "revision": payload["revision"], "clubs": len(clubs), "players": len(players), "stadiums": len(stadiums), "competitions": len(competitions)}
    if args.print_hash:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        result["canonical_sha256"] = hashlib.sha256(canonical).hexdigest()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
