#!/usr/bin/env python3
"""Animated pixel-art banner: procedural synthwave scene + wordmark, N-frame loop.

Why procedural instead of animating the AI still: the AI grid is baked into the
pixels, so any scrolling drawn on top doubles up. Here every layer is generated
per frame on the SAME low-res grid, so the motion is authentic pixel motion.

Every animated value is sin/cos of (i/N) or a modulo of N, so frame N == frame 0
and no two frames are identical.

Two invariants learned the hard way:
  * indices 0..13 are a strictly increasing brightness ramp. 14/15/16/17 sit
    outside it and are only ever written explicitly. Computed brightness always
    goes through putr() which clamps to 13 -- index arithmetic that overflows
    lands on the near-black slot and punches holes in bright areas.
  * the sprite is rasterised into a mask first, then composited with a
    guaranteed 1px outline. Drawing a dark figure straight onto a dark floor by
    hand gives an invisible silhouette (and a scanning rim-light pass is fragile).
"""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel_banner import glyph_rects, text_w  # bitmap font

LOW_W, LOW_H = 400, 134
PX = 3
OUT_W, OUT_H = LOW_W * PX, LOW_H * PX
TAU = 2 * math.pi

VPX, VPY = 118, 80          # vanishing point = sun base = horizon
SUN_R = 32
N = 32
DUR = 80
PANEL_X = 0.42 * LOW_W
RAMP_MAX = 13

PAL = [
    (26, 5, 16), (44, 7, 22), (68, 9, 30), (98, 11, 38),        # 0-3  dark maroons
    (132, 13, 45), (176, 15, 50), (206, 20, 57), (255, 46, 76),  # 4-7  reds
    (255, 86, 96), (255, 120, 70), (255, 150, 40), (255, 176, 32),  # 8-11 hot -> gold
    (255, 209, 102), (255, 241, 220),                            # 12-13 amber, cream
    (10, 2, 7), (250, 252, 255),                                 # 14 black, 15 white
    (72, 12, 80), (116, 20, 116),                                # 16-17 dusk violets
]
PAL_FLAT = [c for k in range(256) for c in PAL[k % len(PAL)]]
PAL_IMG = Image.new("P", (1, 1))
PAL_IMG.putpalette(PAL_FLAT)


def new_canvas():
    """A P-mode canvas carrying OUR palette.

    Image.new("P", ...) starts life with PIL's default identity GRAYSCALE
    palette, so px[x, y] = 11 would paint mid-grey rather than PAL[11] -- and
    every later convert("RGB") flattens the art to near-black. The palette has
    to be attached before a single pixel is written.
    """
    im = Image.new("P", (LOW_W, LOW_H), 0)
    im.putpalette(PAL_FLAT)
    return im

OXBLOOD, CREAM, GOLD, AMBER = PAL[0], PAL[13], PAL[11], PAL[12]
RED, HOTRED = PAL[7], PAL[8]
CLOAK, CLOAK_MID, FACE = 14, 2, 1
AMBER_IDX = 12


def put(px, x, y, idx):
    """Explicit colour write (0..17). Never feed it index arithmetic."""
    if 0 <= x < LOW_W and 0 <= y < LOW_H:
        px[x, y] = 0 if idx < 0 else (17 if idx > 17 else idx)


def putr(px, x, y, v):
    """Computed brightness: clamped into the safe part of the ramp."""
    if 0 <= x < LOW_W and 0 <= y < LOW_H:
        px[x, y] = max(0, min(RAMP_MAX, v))


def line(px, x0, y0, x1, y1, idx):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        put(px, x0, y0, idx)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def rect(px, x0, y0, x1, y1, idx):
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            put(px, xx, yy, idx)


def ramp(v, stops):
    v = max(0.0, min(1.0, v))
    n = len(stops) - 1
    seg = min(int(v * n), n - 1)
    lo, hi = stops[seg], stops[seg + 1]
    return int(round(lo + (hi - lo) * (v * n - seg)))


def draw_sky(px, i, sun_dy):
    breath = 1.0 + 0.5 * math.sin(TAU * i / N)
    dy = 1 - 2 * ((i // 8) % 2)                     # glow wall creeps up/down
    for y in range(VPY):
        t = y / float(VPY)
        violet = 16 if t < 0.055 else (17 if t < 0.11 else None)
        base = ramp((t - 0.11) / 0.89, [3, 4, 5, 6, 7])
        for x in range(LOW_W):
            d = math.hypot((x - VPX) * 0.9, (y - (VPY - sun_dy)) * (1.0 + 0.15 * dy))
            g = (1.0 - d / (SUN_R * 3.0)) ** 1.7 if d < SUN_R * 3.0 else 0.0
            if violet is not None and g < 0.5:
                put(px, x, y, violet)               # dusk violet lives off-ramp
            else:
                putr(px, x, y, base + int(g * 5 * breath))


def draw_sun(px, i, sun_dy):
    base_y = VPY - sun_dy
    breath = (0, 0, 1, 1, 2, 2, 1, 0)[(i * 3) % 8]
    slab = 2 * int((i / float(N)) * 8)              # 8 x 1px drifts per loop
    for y in range(base_y - SUN_R, base_y):
        row = y - (base_y - SUN_R)
        t = row / float(SUN_R - 1)
        for x in range(VPX - SUN_R, VPX + SUN_R + 1):
            if (x - VPX) ** 2 + (y - base_y) ** 2 > SUN_R * SUN_R:
                continue
            idx = ramp(t, [12, 11, 11, 10, 9, 8])   # amber crown -> hot red base
            if t > 0.16 and ((row + slab) // 2) % 2 == 0:
                idx -= 3                             # thin retro slits (2 on / 2 off)
            putr(px, x, y, idx + breath)
    for x in range(VPX - SUN_R + 4, VPX + SUN_R - 3):     # crisp crown highlight
        for y in range(base_y - SUN_R, base_y - SUN_R + 2):
            if (x - VPX) ** 2 + (y - base_y) ** 2 <= SUN_R * SUN_R:
                putr(px, x, y, 12)
    ph = (i / float(N) * 2) % 1.0                        # halo: 2 breaths per loop
    ring = SUN_R + 2 + int(abs(2.0 * ((2.0 * i / N) % 1.0) - 1.0) * 13)
    for y in range(max(0, base_y - ring - 1), base_y):
        for x in range(VPX - ring - 1, VPX + ring + 2):
            d = math.hypot(x - VPX, y - base_y)
            if SUN_R < d <= ring:
                putr(px, x, y, max(1, 6 - int(ph * 4)))


def draw_grid(px, i):
    ph = i / float(N)
    for y in range(VPY + 1, LOW_H):                 # floor base
        t = (y - VPY) / float(LOW_H - VPY)
        base = ramp(t, [6, 5, 4, 3, 2, 1])
        for x in range(LOW_W):
            putr(px, x, y, base)
    for x in range(LOW_W):                          # hot horizon seam
        g = ramp(max(0.0, 1.0 - abs(x - VPX) / 200.0), [4, 6, 8, 9])
        putr(px, x, VPY, g)
        putr(px, x, VPY + 1, g - 2)
        putr(px, x, VPY + 2, g - 4)
    NH = 7                                          # rungs rush toward the viewer
    for k in range(NH + 1):
        t = (k + ph) / float(NH)
        if not (0.0 < t < 1.0):
            continue
        y = VPY + 3 + int((LOW_H - VPY - 4) * (t ** 2.1))
        idx = ramp(1.0 - t, [5, 7, 9, 10])
        th = 1 if t < 0.5 else 2
        for x in range(LOW_W):
            for k2 in range(th):
                putr(px, x, y + k2, idx)
    for m in range(-9, 10):                         # fan + light pulse running out
        xb = VPX + m * 17
        u = (m * 0.13 + ph * 2) % 1.0
        idx = 9 if u < 0.16 else (7 if u < 0.32 else 5)
        dx, dy = abs(xb - VPX), abs(LOW_H - VPY)
        sx = 1 if VPX < xb else -1
        err = dx - dy
        x, y = VPX, VPY
        while y <= LOW_H - 1:
            if y > VPY + 3:
                putr(px, x, y, idx)
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += 1


STARS = [(40, 10, 0), (76, 26, 2), (26, 38, 4), (152, 14, 1), (188, 24, 3),
         (206, 40, 5), (62, 48, 3), (178, 52, 0), (98, 16, 5), (134, 40, 2),
         (14, 22, 2), (160, 34, 4), (52, 30, 1), (200, 12, 4)]


def draw_stars(px, i):
    for j, (sx, sy, p) in enumerate(STARS):
        ph = (i + p * 4) % 8
        if ph < 4:
            put(px, sx, sy, 12 if j % 3 else 13)
            if ph == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(px, sx + dx, sy + dy, 4)
        else:
            putr(px, sx, sy, 5)


def draw_birds(px, i):
    span = 150.0
    for j in range(3):
        bx = int(58 + (j * 52 + (i / float(N)) * span * 2) % span)
        by = 18 + j * 11 + int(2 * math.sin(TAU * (i / float(N)) + j))
        if (i // 2 + j) % 2 == 0:
            line(px, bx, by + 1, bx + 2, by, 5)
            line(px, bx + 2, by, bx + 4, by + 1, 5)
        else:
            line(px, bx, by, bx + 2, by + 1, 5)
            line(px, bx + 2, by + 1, bx + 4, by, 5)


EMBERS = [(46, 120, 44), (88, 128, 58), (152, 124, 50), (198, 130, 42),
          (28, 114, 36), (120, 118, 60), (170, 126, 46), (214, 122, 40)]


def draw_embers(px, i):
    p = i / float(N)
    if p < 0.06 or p > 0.94:
        return
    for j, (ex0, ey0, travel) in enumerate(EMBERS):
        ex = ex0 + int(3 * math.sin(TAU * (p + j * 0.14)))
        ey = ey0 - int(travel * p)
        putr(px, ex, ey, 11 if (j % 2 and p > 0.5) else 9)
        if j % 3 == 0:
            putr(px, ex, ey + 1, 4)


def draw_hunter(px, i, fx=60, fy=120):
    """Masked sprite -> guaranteed 1px outline, so the figure always reads.

    Feet at fy, ~40px tall, cowl + rifle + cloak with sway. Drawn into a mask
    first and composited, because a dark figure hand-drawn onto a dark floor
    has no readable silhouette.
    """
    sway = int(round(1.4 * math.sin(TAU * i / N)))
    m = Image.new("P", (LOW_W, LOW_H), 0)
    mp = m.load()

    def mr(x0, y0, x1, y1, v):
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if 0 <= xx < LOW_W and 0 <= yy < LOW_H:
                    mp[xx, yy] = v

    def ml(x0, y0, x1, y1, v):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if 0 <= x0 < LOW_W and 0 <= y0 < LOW_H:
                mp[x0, y0] = v
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    top = fy - 48
    for k, y in enumerate(range(top, top + 17)):          # tall pointed cowl
        hw = 1 + int(k * 0.46)
        mr(fx + 2 - hw, y, fx + 2 + hw, y, 1 if k > 6 else 2)
    mr(fx - 3, fy - 38, fx + 6, fy - 27, 1)               # cowl opening: dark void
    mr(fx - 10, fy - 27, fx + 14, fy - 23, 2)             # shoulders
    for y in range(fy - 22, fy - 3):                      # cloak, widening down
        t = (y - (fy - 22)) / 19.0
        hw = 9 + int(t * 8)
        off = sway if y > fy - 12 else 0
        mr(fx + 2 - hw + off, y, fx + 3 + hw, y, 1)
    mr(fx + 1, fy - 22, fx + 5, fy - 4, 2)                # inner cloak highlight
    ml(fx - 8 + sway, fy - 2, fx - 16 + sway, fy + 1, 1)  # hem sweeps out left
    mr(fx - 8 + sway, fy - 2, fx - 3 + sway, fy + 2, 1)
    mr(fx + 8 + sway, fy - 2, fx + 13 + sway, fy + 2, 1)
    mr(fx - 7, fy + 3, fx - 3, fy + 9, 1)                 # legs
    mr(fx + 9, fy + 3, fx + 13, fy + 9, 1)
    mr(fx - 10, fy + 10, fx - 2, fy + 11, 2)              # boots
    mr(fx + 8, fy + 10, fx + 15, fy + 11, 2)
    ml(fx - 14, fy - 16, fx + 26, fy - 36, 2)             # rifle: stock -> barrel
    ml(fx - 13, fy - 15, fx + 27, fy - 35, 2)
    mr(fx - 17, fy - 18, fx - 11, fy - 13, 2)             # wooden stock
    mr(fx + 6, fy - 27, fx + 11, fy - 26, 2)              # scope block
    ml(fx + 4, fy - 24, fx + 9, fy - 24, 3)               # receiver glint
    ml(fx + 23, fy - 34, fx + 27, fy - 36, 3)             # muzzle glint
    mr(fx, fy - 35, fx, fy - 35, 3)                       # two amber eyes
    mr(fx + 3, fy - 35, fx + 3, fy - 35, 3)

    RIM = 13
    for y in range(top - 1, fy + 13):                     # outline pass
        for x in range(fx - 26, fx + 32):
            if mp[x, y]:
                continue
            if any(mp[x + a, y + b] for a in (-1, 0, 1) for b in (-1, 0, 1)):
                put(px, x, y, RIM if x >= fx + 2 else (AMBER_IDX if y > fy + 8 else 0))
    for y in range(top, fy + 12):                         # body fill
        for x in range(fx - 26, fx + 32):
            v = mp[x, y]
            if v:
                put(px, x, y, CLOAK if v == 1 else (CLOAK_MID if v == 2 else AMBER_IDX))


def draw_scanline(px, i):
    y = int((i / float(N)) * LOW_H * 2) % LOW_H
    for x in range(LOW_W):
        if px[x, y] < RAMP_MAX:
            putr(px, x, y, px[x, y] + 1)


def blink(px, i):
    on = math.sin(TAU * i / N) > 0.35
    rect(px, 205, 120, 209, 124, 8 if on else 3)


def draw_panel(px):
    for x in range(LOW_W):
        t = max(0.0, min(1.0, (x - PANEL_X) / (LOW_W * 0.30)))
        if t <= 0:
            continue
        f = round((1.0 - 0.84 * t) * 5) / 5.0
        for y in range(LOW_H):
            r, g, b = PAL[px[x, y] % 18]
            nr, ng, nb = (int(c * f + o * (1 - f)) for c, o in
                          ((r, OXBLOOD[0]), (g, OXBLOOD[1]), (b, OXBLOOD[2])))
            best, bd = 0, 1e9
            for k, c in enumerate(PAL[:14]):
                dd = (c[0] - nr) ** 2 + (c[1] - ng) ** 2 + (c[2] - nb) ** 2
                if dd < bd:
                    bd, best = dd, k
            px[x, y] = best


def _snap(col):
    if col in PAL:
        return PAL.index(col)
    best, bd = 0, 1e9
    for k, c in enumerate(PAL[:18]):
        dd = sum((c[i] - col[i]) ** 2 for i in range(3))
        if dd < bd:
            bd, best = dd, k
    return best


def draw_text_shimmer(img, s, x, y, cell, rows, outline, gap, shimmer_x, plate=None):
    d = ImageDraw.Draw(img)
    rects = list(glyph_rects(s, x, y, cell, gap))
    if plate:
        d.rectangle([x - cell, y - cell, x + text_w(s, cell, gap) + cell - 1,
                     y + 7 * cell + cell - 1], fill=plate)
    if outline is not None:
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1)):
            for (x0, y0, x1, y1) in rects:
                d.rectangle([x0 + ox * cell, y0 + oy * cell,
                             x1 + ox * cell - 1, y1 + oy * cell - 1], fill=outline)
    n = len(rows) - 1
    for (x0, y0, x1, y1) in rects:
        row = (y0 - y) // cell
        t = min(row / 6.0, 1.0)
        seg = min(int(t * n), n - 1)
        lo, hi = rows[seg], rows[seg + 1]
        col = tuple(int(round(lo[k] + (hi[k] - lo[k]) * (t * n - seg))) for k in range(3))
        if abs((x0 + x1) / 2.0 - shimmer_x) < 15:
            col = PAL[15] if row < 3 else CREAM
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=_snap(col))


def frame(i):
    img = new_canvas()
    px = img.load()
    sun_dy = int(round(1.5 + 1.5 * math.sin(TAU * i / N)))
    draw_sky(px, i, sun_dy)
    draw_sun(px, i, sun_dy)
    draw_grid(px, i)
    draw_stars(px, i)
    draw_birds(px, i)
    draw_embers(px, i)
    draw_hunter(px, i)
    draw_scanline(px, i)
    draw_panel(px)

    w_cell, w_gap = 5, 3
    w_width = text_w("BAYZO", w_cell, w_gap)
    w_x = 284 - w_width // 2
    w_y = 30
    sh = (w_x - 45) + (i / float(N)) * (w_width + 130)
    draw_text_shimmer(img, "BAYZO", w_x, w_y, w_cell,
                      [CREAM, AMBER, GOLD, RED, PAL[5]], OXBLOOD, w_gap, sh)

    s_cell, s_gap = 2, 2
    s_width = text_w("PROFIT HUNTER", s_cell, s_gap)
    s_x = 284 - s_width // 2
    s_y = w_y + 7 * w_cell + 14
    draw_text_shimmer(img, "PROFIT HUNTER", s_x, s_y, s_cell,
                      [CREAM, AMBER], None, s_gap, sh, plate=OXBLOOD)

    d = ImageDraw.Draw(img)
    ry = s_y + 7 * s_cell + 6
    d.rectangle([s_x - 5, ry, s_x + s_width + 4, ry + 1], fill=RED)
    mid = (s_width - 13) // 2
    d.rectangle([s_x + mid, ry - 2, s_x + mid + 12, ry + 3], fill=GOLD)
    blink(px, i)

    rgb = img.convert("RGB").resize((OUT_W, OUT_H), Image.NEAREST)
    return rgb.quantize(palette=PAL_IMG, dither=Image.NONE), rgb


def build(out_gif, out_preview=None, n=N, preview_only=False):
    frames_p, frames_rgb = [], []
    for i in range(n):
        p, rgb = frame(i)
        frames_p.append(p)
        frames_rgb.append(rgb)
    if out_preview:
        picks = list(range(0, n, max(1, n // 8)))[:8]
        sw, shh = OUT_W // 2, OUT_H // 2
        sheet = Image.new("RGB", (sw, shh * len(picks)), (0, 0, 0))
        for k, idxx in enumerate(picks):
            sheet.paste(frames_rgb[idxx].resize((sw, shh), Image.NEAREST), (0, k * shh))
        sheet.save(out_preview)
    if not preview_only:
        diffs = []
        for a, b in zip(frames_rgb, frames_rgb[1:] + frames_rgb[:1]):
            pa, pb = a.convert("L").load(), b.convert("L").load()
            s = 0
            for yy in range(0, OUT_H, 9):
                for xx in range(0, OUT_W, 9):
                    s += abs(pa[xx, yy] - pb[xx, yy])
            diffs.append(s)
        frames_p[0].save(out_gif, save_all=True, append_images=frames_p[1:],
                         duration=DUR, loop=0, optimize=True, disposal=2)
        print("frame deltas: min=%d max=%d avg=%d" % (min(diffs), max(diffs),
                                                      sum(diffs) // len(diffs)))
    return out_gif


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/banner.gif"
    prev = sys.argv[2] if len(sys.argv) > 2 else "/tmp/banner_strip.png"
    build(out, prev)
    print("wrote", out, os.path.getsize(out), "bytes ;", prev)
