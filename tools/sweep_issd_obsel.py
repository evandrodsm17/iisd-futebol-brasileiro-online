"""Create a contact sheet over all SNES OBJSEL values for one captured frame."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "docs" / "issd-objsel-contact.png"
    source = root / "docs" / "issd-runtime-oam.hex"
    vram = root / "docs" / "issd-runtime-vram.bin"
    cgram = root / "docs" / "issd-runtime-cgram.hex"
    renderer = root / "tools" / "render_issd_oam_composite.py"
    thumb_width, thumb_height = 256, 112
    sheet = Image.new("RGB", (thumb_width * 8, (thumb_height + 16) * 8), "black")
    with tempfile.TemporaryDirectory() as temporary:
        for obsel in range(64):
            frame = Path(temporary) / f"{obsel:02x}.png"
            subprocess.run([sys.executable, str(renderer), str(source), str(vram), str(cgram), str(frame), "--obsel", hex(obsel)], check=True)
            image = Image.open(frame).convert("RGB").resize((thumb_width, thumb_height), Image.Resampling.NEAREST)
            x, y = (obsel % 8) * thumb_width, (obsel // 8) * (thumb_height + 16)
            sheet.paste(image, (x, y + 16))
            ImageDraw.Draw(sheet).text((x + 4, y + 2), f"OBJSEL ${obsel:02X}", fill="white")
    sheet.save(output)


if __name__ == "__main__":
    main()
