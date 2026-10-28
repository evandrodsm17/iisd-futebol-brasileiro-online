"""Guard the validated Canvas-direction -> ROM-locomotion-sheet conversion."""

from pathlib import Path
import re


EXPECTED = [6, 7, 0, 1, 2, 3, 4, 5]


def main() -> None:
    game = Path(__file__).parents[1] / "dist" / "game.js"
    source = game.read_text(encoding="utf-8")
    match = re.search(r"const romSheetIndexByScreenDirection = \[([^]]+)\];", source)
    if not match:
        raise SystemExit("missing explicit browser direction conversion")
    actual = [int(value.strip()) for value in match.group(1).split(",")]
    if actual != EXPECTED:
        raise SystemExit(f"unexpected browser direction conversion: {actual!r}")
    print("browser direction conversion: OK")


if __name__ == "__main__":
    main()
