#!/usr/bin/env python3
"""Draw a clean Skaldr-branded BIOS/GRUB splash without external image tools."""
import math
from pathlib import Path
import struct
import sys
import zlib

WIDTH, HEIGHT = 640, 480
FONT = {
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    " ": ["00000"] * 7,
}


def chunk(name, payload):
    return (struct.pack(">I", len(payload)) + name + payload +
            struct.pack(">I", zlib.crc32(name + payload) & 0xffffffff))


def save_png(path, pixels):
    rows = b"".join(b"\x00" + bytes(row) for row in pixels)
    body = (chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + body)


def render():
    pixels = []
    for y in range(HEIGHT):
        row = bytearray()
        for x in range(WIDTH):
            dx, dy = (x - WIDTH / 2) / WIDTH, (y - HEIGHT / 2) / HEIGHT
            glimmer = max(0, 1 - math.sqrt(dx * dx + dy * dy) * 1.7)
            row.extend((int(5 + glimmer * 17),
                        int(12 + glimmer * 23),
                        int(26 + glimmer * 39)))
        pixels.append(row)

    def dot(x, y, color):
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            offset = 3 * x
            pixels[y][offset:offset + 3] = bytes(color)

    def line(a, b, color, thickness=2):
        steps = max(1, int(math.dist(a, b) * 2))
        for i in range(steps + 1):
            x = round(a[0] + (b[0] - a[0]) * i / steps)
            y = round(a[1] + (b[1] - a[1]) * i / steps)
            for tx in range(-thickness, thickness + 1):
                for ty in range(-thickness, thickness + 1):
                    if tx * tx + ty * ty <= thickness * thickness:
                        dot(x + tx, y + ty, color)

    center = (WIDTH // 2, 204)
    for t in range(5, 175):
        theta = math.radians(t + 180)
        x = int(center[0] + 175 * math.cos(theta))
        y = int(center[1] + 175 * math.sin(theta))
        dot(x, y, (13, 205, 235) if t < 85 else (165, 62, 244))
    for t in range(5, 175):
        theta = math.radians(t)
        x = int(center[0] + 175 * math.cos(theta))
        y = int(center[1] + 175 * math.sin(theta))
        dot(x, y, (13, 205, 235) if t > 85 else (165, 62, 244))
    # The raven mark is a lightweight scalable polyline inspired by Skaldr.
    feather = [(190, 265), (248, 190), (219, 213), (284, 149),
               (260, 166), (330, 120), (378, 148), (400, 166),
               (448, 184), (396, 179), (376, 201), (346, 229),
               (341, 195), (308, 246), (298, 207), (265, 276)]
    for p, q in zip(feather, feather[1:]):
        line(p, q, (208, 227, 245), 4)
    line((331, 156), (371, 169), (13, 225, 241), 4)

    label = "SKALDR OS"
    scale = 6
    length = len(label) * (5 + 1) * scale - scale
    x0 = (WIDTH - length) // 2
    y0 = 322
    for ci, glyph in enumerate(label):
        for y, row in enumerate(FONT[glyph]):
            for x, pixel in enumerate(row):
                if pixel == "1":
                    color = (217, 233, 252) if ci < 7 else (18, 217, 239)
                    for yy in range(scale):
                        for xx in range(scale):
                            dot(x0 + ci * 6 * scale + x * scale + xx,
                                y0 + y * scale + yy, color)
    line((188, 389), (284, 389), (8, 218, 237), 2)
    line((356, 389), (452, 389), (178, 64, 238), 2)
    return pixels


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: skaldr-make-boot-splash.py STAGED_ARCHISO")
    root = Path(sys.argv[1])
    pixels = render()
    for filename in ("grub/splash.png", "syslinux/splash.png",
                     "syslinux/splash1.png"):
        path = root / filename
        save_png(path, pixels)
        print("Created Skaldr boot artwork:", path)


if __name__ == "__main__":
    main()
