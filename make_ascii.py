"""Gera o retrato em ASCII a partir de uma foto (roda uma vez, localmente)."""
import sys

from PIL import Image, ImageEnhance, ImageOps

RAMP = " .'`^,:;Il!i><~+_-?][}{1)(|tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def to_ascii(path: str, box: tuple[int, int, int, int], cols: int, rows: int, gamma: float) -> list[str]:
    image = Image.open(path).convert("L").crop(box)
    image = ImageOps.autocontrast(image, cutoff=2)
    image = ImageEnhance.Contrast(image).enhance(1.6)
    image = image.resize((cols, rows), Image.LANCZOS)
    lines = []
    for y in range(rows):
        line = []
        for x in range(cols):
            darkness = 1 - image.getpixel((x, y)) / 255
            darkness = darkness ** gamma
            line.append(RAMP[int(darkness * (len(RAMP) - 1))])
        lines.append("".join(line).rstrip())
    return lines


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    art = to_ascii(src, box=(120, 30, 500, 470), cols=42, rows=25, gamma=1.15)
    with open(out, "w") as handle:
        handle.write("\n".join(art) + "\n")
    print("\n".join(art))
