#!/usr/bin/env python3
"""Рисует пиксельные спрайты для модуля 6 (Pygame Zero) и упаковывает их в zip.

Результат: site/assets/sprites/*.png и site/assets/sprites.zip (внутри папка images/).
Запуск:  python3 make_sprites.py
"""
import struct
import zipfile
import zlib
from pathlib import Path

OUT = Path(__file__).parent / "site" / "assets" / "sprites"
SCALE = 4

PALETTE = {
    ".": None,
    "k": (20, 20, 20), "w": (250, 250, 250), "g": (90, 200, 90), "G": (40, 130, 60),
    "y": (255, 215, 60), "o": (230, 140, 40), "r": (220, 60, 60), "R": (150, 30, 40),
    "b": (80, 140, 230), "B": (40, 70, 160), "s": (240, 200, 160), "p": (170, 90, 200),
}

SPRITES = {
    "hero": [
        "....kkkkkk....",
        "...kbbbbbbk...",
        "..kbbbbbbbbk..",
        "..kssssssssk..",
        "..kskwsskwsk..",
        "..kssssssssk..",
        "...kssrrssk...",
        "....kkkkkk....",
        "..kBBBBBBBBk..",
        ".ksBBBBBBBBsk.",
        ".ksBBByyBBBsk.",
        "..kBBBBBBBBk..",
        "...kBBkkBBk...",
        "...kkk..kkk...",
    ],
    "coin": [
        "....kkkk....",
        "..kkyyyykk..",
        ".kyyyyyyyyk.",
        ".kyyowyyyyk.",
        "kyyywyyyoyyk",
        "kyyywyyyoyyk",
        "kyyyyyyyoyyk",
        "kyyyyyyyoyyk",
        ".kyyyyyooyk.",
        ".kyyyyyyyyk.",
        "..kkyyyykk..",
        "....kkkk....",
    ],
    "enemy": [
        "....kkkkkk....",
        "..kkRRRRRRkk..",
        ".kRrrrrrrrrRk.",
        "kRrrrrrrrrrrRk",
        "kRrwwkrrwwkrRk",
        "kRrwwkrrwwkrRk",
        "kRrrrrrrrrrrRk",
        "kRrrkkkkkkrrRk",
        "kRrkwkwkwkkrRk",
        "kRrrrrrrrrrrRk",
        ".kRrrRkkRrrRk.",
        "..kkkk..kkkk..",
    ],
    "star": [
        "......kk......",
        ".....kyyk.....",
        ".....kyyk.....",
        "....kyyyyk....",
        "kkkkkyyyykkkkk",
        "kyyyyyyyyyyyyk",
        ".kyyyyyyyyyyk.",
        "..kyyyyyyyyk..",
        "...kyyyyyyk...",
        "...kyyyyyyk...",
        "..kyyykkyyyk..",
        "..kyykk.kyyk..",
        ".kykk....kkyk.",
        ".kk........kk.",
    ],
    "heart": [
        ".kkk...kkk.",
        "krrrk.krrrk",
        "krwrrkrrrrk",
        "krrrrrrrrrk",
        "krrrrrrrrrk",
        ".krrrrrrrk.",
        "..krrrrrk..",
        "...krrrk...",
        "....krk....",
        ".....k.....",
    ],
    "rock": [
        "....kkkkk.....",
        "..kkoooookk...",
        ".koooooooooKk.".replace("K", "k"),
        "koooookoooooko".replace("ko", "ko"),
        "kooookoooooook",
        "koooooooookook",
        "kooooooooooook",
        ".koooooookoook",
        "..kkoooooooook",
        "....kkkkkkkkk.",
    ],
}


def png(pixels):
    h, w = len(pixels), len(pixels[0])
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def render(art):
    width = max(len(r) for r in art)
    rows = []
    for line in art:
        line = line.ljust(width, ".")
        row = []
        for ch in line:
            c = PALETTE.get(ch)
            px = (0, 0, 0, 0) if c is None else (*c, 255)
            row.extend([px] * SCALE)
        for _ in range(SCALE):
            rows.append(row)
    return png(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT.parent / "sprites.zip", "w") as z:
        for name, art in SPRITES.items():
            data = render(art)
            (OUT / f"{name}.png").write_bytes(data)
            z.writestr(f"images/{name}.png", data)
    print("Спрайты:", ", ".join(SPRITES))


if __name__ == "__main__":
    main()
