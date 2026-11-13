#!/usr/bin/env python3
"""生成商店图标（1024 / 512 / 256），纯标准库实现，不依赖 Pillow。

设计：深墨蓝圆角方底（品牌 --deep #0E2438）+ 橙色四角星（--accent #F2653A）
+ 右上角金点（--gold #E8B44A）。星形用超椭圆式四尖公式，边缘按像素覆盖率抗锯齿。

用法：python qa/store-assets/make_icons.py
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "icon"

BG_TOP = (0x14, 0x31, 0x4A)   # #14314A
BG_BOT = (0x0A, 0x18, 0x26)   # #0A1826
ACCENT = (0xF2, 0x65, 0x3A)   # #F2653A
GOLD = (0xE8, 0xB4, 0x4A)     # #E8B44A

K_SPARK = 0.55   # 四尖星形状指数（越小越胖）


def _clamp01(v: float) -> float:
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _mix(a, b, t: float):
    t = _clamp01(t)
    return (a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _round_rect_sdf(x: float, y: float, hx: float, hy: float, r: float) -> float:
    dx = abs(x) - (hx - r)
    dy = abs(y) - (hy - r)
    ox = dx if dx > 0 else 0.0
    oy = dy if dy > 0 else 0.0
    outside = (ox * ox + oy * oy) ** 0.5
    inside = min(max(dx, dy), 0.0)
    return outside + inside - r


def _spark_sdf(x: float, y: float, radius: float) -> float:
    """四尖星（超椭圆 |px|^k + |py|^k = 1），返回近似像素距离，内部为负。"""
    px = abs(x) / radius
    py = abs(y) / radius
    f = (px ** K_SPARK + py ** K_SPARK) ** (1.0 / K_SPARK) - 1.0
    return f * radius


def _coverage(sdf: float, aa: float = 0.9) -> float:
    return _clamp01(0.5 - sdf / aa)


def render(size: int) -> bytes:
    pad = size * 0.045
    hx = hy = size / 2.0 - pad
    radius = size * 0.225

    spark_c = (size * 0.500, size * 0.505)
    spark_r = size * 0.285
    dot_c = (size * 0.748, size * 0.248)
    dot_r = size * 0.092
    glow_r = size * 0.34

    rows = []
    for yy in range(size):
        row = bytearray()
        cy = yy + 0.5 - size / 2.0
        for xx in range(size):
            cx = xx + 0.5 - size / 2.0
            bg = _coverage(_round_rect_sdf(cx, cy, hx, hy, radius))
            if bg <= 0.0:
                row += b"\x00\x00\x00\x00"
                continue
            t = (yy + 0.5) / size
            col = _mix(BG_TOP, BG_BOT, t * t * 0.55 + t * 0.45)

            # 主星周围的暖光
            ddx = xx + 0.5 - spark_c[0]
            ddy = yy + 0.5 - spark_c[1]
            d2 = ddx * ddx + ddy * ddy
            glow = 0.16 * (2.718281828 ** (-d2 / (glow_r * glow_r)))
            col = _mix(col, ACCENT, glow)

            spark = _coverage(_spark_sdf(xx + 0.5 - spark_c[0], yy + 0.5 - spark_c[1], spark_r), 0.8)
            if spark > 0.0:
                col = _mix(col, ACCENT, spark)

            dot = _coverage(_spark_sdf(xx + 0.5 - dot_c[0], yy + 0.5 - dot_c[1], dot_r), 0.8)
            if dot > 0.0:
                col = _mix(col, GOLD, dot)

            row += bytes((int(col[0] + 0.5), int(col[1] + 0.5), int(col[2] + 0.5),
                          int(bg * 255 + 0.5)))
        rows.append(bytes(row))

    raw = b"".join(b"\x00" + r for r in rows)
    return _png(size, size, raw)


def _chunk(tag: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def _png(w: int, h: int, raw: bytes) -> bytes:
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 8bit RGBA
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b""))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for size in (1024, 512, 256):
        path = OUT_DIR / ("icon-%d.png" % size)
        path.write_bytes(render(size))
        print("写出 %-28s %7d bytes  %dx%d" % (path.relative_to(OUT_DIR.parent.parent.parent),
                                               path.stat().st_size, size, size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
