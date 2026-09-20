#!/usr/bin/env python3
"""Pixel-art banner compositor: pixel-snap an AI scene + pixel-font wordmark.

Pipeline: source art -> BOX downscale to a low-res pixel grid -> palette quantize
-> pixel-font text drawn ON that same grid -> NEAREST upscale. Single pixel unit,
so the result is authentic pixel art rather than 'AI pixel-style'.
"""
import sys
from PIL import Image, ImageDraw, ImageEnhance

LOW_W, LOW_H = 400, 134      # low-res pixel grid
PX = 3                        # upscale factor -> 1200 x 402
OUT_W, OUT_H = LOW_W * PX, LOW_H * PX

# ---------- palette ----------
CREAM = (255, 241, 220)
GOLD = (255, 176, 32)
AMBER = (255, 209, 102)
RED = (255, 46, 76)
DEEPRED = (176, 15, 50)
GLOWRED = (120, 10, 40)
OXBLOOD = (26, 4, 16)
RIM = (255, 214, 150)          # warm rim light on the silhouette edge

G = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    'N': ["10001", "11001", "11001", "10101", "10011", "10011", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def text_w(s, cell, gap=1):
    return len(s) * (5 + gap) * cell - gap * cell


def glyph_rects(s, x, y, cell, gap=1):
    """Yield (x0,y0,x1,y1) rects for a string on the low-res grid."""
    cx = x
    for ch in s:
        if ch == ' ':
            cx += (5 + gap) * cell
            continue
        for r, row in enumerate(G[ch]):
            c = 0
            while c < 5:
                if row[c] == '1':
                    st = c
                    while c < 5 and row[c] == '1':
                        c += 1
                    yield (cx + st * cell, y + r * cell, cx + c * cell, y + (r + 1) * cell)
                else:
                    c += 1
        cx += (5 + gap) * cell


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def draw_text(img, s, x, y, cell, colors, gap=1):
    """colors: list of stops sampled left->right across the string."""
    total = text_w(s, cell, gap)
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in glyph_rects(s, x, y, cell, gap):
        mid = (x0 - x + (x1 - x0) / 2) / max(total, 1)
        n = len(colors) - 1
        seg = min(int(mid * n), n - 1)
        col = lerp(colors[seg], colors[seg + 1], (mid * n) - seg)
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=col)


def draw_text_v(img, s, x, y, cell, rows_colors, outline=None, gap=1):
    """Vertical band shading per glyph row + optional 1-cell outline."""
    d = ImageDraw.Draw(img)
    rects = list(glyph_rects(s, x, y, cell, gap))
    if outline:
        for off in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            dx, dy = off[0] * cell, off[1] * cell
            for (x0, y0, x1, y1) in rects:
                d.rectangle([x0 + dx, y0 + dy, x1 + dx - 1, y1 + dy - 1], fill=outline)
    n = len(rows_colors) - 1
    for (x0, y0, x1, y1) in rects:
        row = (y0 - y) // cell
        t = min(row / 6.0, 1.0)
        seg = min(int(t * n), n - 1)
        col = lerp(rows_colors[seg], rows_colors[seg + 1], t * n - seg)
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=col)


def blocky_glow(img, s, x, y, cell, color, radius_cells, gap=1, step=2):
    """Pixel-art glow: glyph rects dilated by N cells, snapped to blocky steps."""
    d = ImageDraw.Draw(img)
    r = radius_cells * cell
    for (x0, y0, x1, y1) in glyph_rects(s, x, y, cell, gap):
        bx0 = (x0 - r) // step * step
        by0 = (y0 - r) // step * step
        bx1 = -(-(x1 + r) // step) * step
        by1 = -(-(y1 + r) // step) * step
        d.rectangle([bx0, by0, bx1 - 1, by1 - 1], fill=color)


def build(src, out, wordmark="BAYZO", subtitle="PROFIT HUNTER", colors=36,
          dither=True, levels=26, scrim=True, red_bias=True, rim=True, rim_zone=0.45):
    art = Image.open(src).convert("RGB")

    # 1. pixel-snap: area-average down to the low-res grid
    art = art.resize((LOW_W, LOW_H), Image.BOX)

    # 2. punch the colour (user wants "mencolok & terang") + pull orange back to red
    art = ImageEnhance.Color(art).enhance(1.5)
    art = ImageEnhance.Contrast(art).enhance(1.2)
    art = ImageEnhance.Brightness(art).enhance(1.1)
    if red_bias:
        art = art.point(lambda v: v)  # no-op keeps PIL from lazy-sharing
        px = art.load()
        for yy in range(LOW_H):
            for xx in range(LOW_W):
                r, g, b = px[xx, yy]
                px[xx, yy] = (min(255, int(r * 1.04)), int(g * 0.88), int(b * 1.02))
    # posterize FIRST so smooth AI glows become hard bands (kills the "AI veneer")
    art = Image.eval(art, lambda v: (v // levels) * levels + levels // 2)

    # 3. unify into a tight retro palette
    art = art.quantize(colors=colors, method=Image.MEDIANCUT,
                       dither=Image.FLOYDSTEINBERG if dither else Image.NONE).convert("RGB")

    # 3b. RIM LIGHT the hunter so the silhouette reads against the sky
    if rim:
        px = art.load()
        add = []
        for yy in range(LOW_H):
            for xx in range(1, int(LOW_W * rim_zone)):
                r, g, b = px[xx, yy]
                if (r * 299 + g * 587 + b * 114) / 1000 > 62:
                    continue
                for dx, dy in ((1, 0), (1, -1), (1, 1), (0, -1)):
                    nx, ny = xx + dx, yy + dy
                    if 0 <= nx < LOW_W and 0 <= ny < LOW_H:
                        nr, ng, nb = px[nx, ny]
                        if (nr * 299 + ng * 587 + nb * 114) / 1000 > 105:
                            add.append((xx, yy))
                            break
        for (xx, yy) in add:
            px[xx, yy] = RIM

    # 4. BLOCKY scrim on the right so the wordmark reads (stepped, never smooth)
    if scrim:
        for x in range(LOW_W):
            t = max(0.0, min(1.0, (x - LOW_W * 0.42) / (LOW_W * 0.30)))
            if t <= 0:
                continue
            f = round((1.0 - 0.78 * t) * 5) / 5.0          # 5 hard steps
            for y in range(LOW_H):
                r, g, b = art.getpixel((x, y))
                art.putpixel((x, y), (int(r * f + OXBLOOD[0] * (1 - f)),
                                      int(g * f + OXBLOOD[1] * (1 - f)),
                                      int(b * f + OXBLOOD[2] * (1 - f))))

    # 5. wordmark: blocky glow -> dark outline -> vertical sunset banding
    w_cell = 5
    w_gap = 2
    w_width = text_w(wordmark, w_cell, w_gap)
    w_x = 300 - w_width // 2
    w_y = 32
    blocky_glow(art, wordmark, w_x, w_y, w_cell, GLOWRED, 3, step=2, gap=w_gap)
    draw_text_v(art, wordmark, w_x, w_y, w_cell,
                [CREAM, AMBER, GOLD, RED, DEEPRED], outline=OXBLOOD, gap=w_gap)

    # 6. subtitle + rule
    s_cell = 2
    s_gap = 2
    s_width = text_w(subtitle, s_cell, s_gap)
    s_x = 300 - s_width // 2
    s_y = w_y + 7 * w_cell + 12
    blocky_glow(art, subtitle, s_x, s_y, s_cell, GLOWRED, 2, step=2, gap=s_gap)
    draw_text_v(art, subtitle, s_x, s_y, s_cell, [CREAM, GOLD], outline=OXBLOOD, gap=s_gap)

    rd = ImageDraw.Draw(art)
    ry = s_y + 7 * s_cell + 7
    rd.rectangle([s_x - 4, ry, s_x + s_width + 3, ry + 1], fill=RED)
    mid = (s_width - 14) // 2
    rd.rectangle([s_x + mid, ry - 2, s_x + mid + 13, ry + 3], fill=GOLD)

    # 7. pixel-grade upscale
    big = art.resize((OUT_W, OUT_H), Image.NEAREST)
    big = big.crop((0, 1, OUT_W, OUT_H - 1)).resize((OUT_W, OUT_H), Image.NEAREST)
    big.save(out)
    return out


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/v1.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/banner_final.png"
    build(src, out)
    print("wrote", out)
