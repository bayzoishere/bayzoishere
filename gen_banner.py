#!/usr/bin/env python3
"""Generate the bayzoishere profile banner + footer (crimson/gold pixel-art sunset)."""
import math, os, random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

W, H = 1200, 320
HORIZON = 226

# ---------- palette ----------
BG_TOP, BG_MID, BG_BOT = "#160310", "#330A18", "#0B0208"
RED      = "#FF2E4C"
RED_DEEP = "#B00F32"
RIM      = "#FF6A5A"
GOLD     = "#FFB020"
AMBER    = "#FFD166"
CREAM    = "#FFF1DC"

def rect(x, y, w, h, fill, extra=""):
    x, y, w, h = round(x, 1), round(y, 1), round(w, 1), round(h, 1)
    if w <= 0 or h <= 0:
        return ""
    a = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
    if extra:
        a += " " + extra
    return a + "/>"

# ---------- 5x7 pixel font ----------
G = {
 'A': ["01110","10001","10001","11111","10001","10001","10001"],
 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'I': ["11111","00100","00100","00100","00100","00100","11111"],
 'N': ["10001","11001","11001","10101","10011","10011","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"],
 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"],
 'Z': ["11111","00001","00010","00100","01000","10000","11111"],
}

def text_w(s, scale, gap=1):
    return len(s) * (5 + gap) * scale - gap * scale

def text(s, x, y, scale, fill, gap=1):
    out, cx = [], x
    for ch in s:
        if ch == ' ':
            cx += (5 + gap) * scale
            continue
        for r, row in enumerate(G[ch]):
            c = 0
            while c < 5:
                if row[c] != '0':
                    st = c
                    while c < 5 and row[c] != '0':
                        c += 1
                    out.append(rect(cx + st * scale, y + r * scale, (c - st) * scale, scale, fill))
                else:
                    c += 1
        cx += (5 + gap) * scale
    return "".join(out)

# ---------- sprites ----------
SPRITE = [
 "......1111......",
 "....11222211....",
 "...1122222211...",
 "..112222222211..",
 ".11223333332211.",
 ".11223333332211.",
 ".11222222222211.",
 "..112222222211..",
 "..112222222211..",
 ".11222222222211.",
 "1122222222222211",
 "1122222222222211",
 "1122222222222211",
 "1122555555552211",
 "1122222222222211",
 "1122222222222211",
 "1122222222222211",
 ".11222222222211.",
 "..112222222211..",
 "..1122....2211..",
 "..1122....2211..",
 "..1122....2211..",
 "..5555....5555..",
 ".55555....55555.",
]

def add_rim(art, rows):
    """Sunset rim-light on the right edge (sun sits to the right of the sprite)."""
    out = []
    for i, row in enumerate(art):
        if i in rows:
            j = row.rfind('2')
            if j != -1:
                row = row[:j] + '4' + row[j+1:]
        out.append(row)
    return out

SPRITE = add_rim(SPRITE, set(range(2, 19)))
SPRITE_FILL = {"1": "#1A0310", "2": "#8A1235", "4": RIM, "3": RED, "5": GOLD}

COIN = [
 "..1111..",
 ".155551.",
 "15666551",
 "15644551",
 "15644551",
 "15666551",
 ".155551.",
 "..1111..",
]
COIN_FILL = {"1": "#5A3A00", "5": GOLD, "6": AMBER, "4": RED_DEEP}

SPARK = ["..3..", ".333.", "33333", ".333.", "..3.."]

BIRD = ["1.....1", ".1...1.", "..1.1.."]

def blit(art, fills, x, y, scale, extra="", glow_chars=""):
    out = []
    for r, row in enumerate(art):
        c = 0
        while c < len(row):
            ch = row[c]
            if ch == '.':
                c += 1
                continue
            st = c
            while c < len(row) and row[c] == ch:
                c += 1
            ex = extra
            if glow_chars and ch in glow_chars:
                ex = (extra + ' filter="url(#glow)"').strip()
            out.append(rect(x + st * scale, y + r * scale, (c - st) * scale, scale, fills[ch], ex))
    return "".join(out)

# ---------- sun ----------
def sun(cx, cy, R, P):
    rows = []
    n = int(R // P)
    for i in range(-n, n + 1):
        y = cy + i * P
        if y >= HORIZON:
            continue
        d = abs(i * P - P / 2)
        if d >= R:
            continue
        half = math.sqrt(R * R - d * d)
        if i > 0 and i % 2 == 1:
            continue  # retro slit bands
        h_ = min(P, HORIZON - y)
        rows.append(rect(cx - half, y, half * 2, h_, "url(#sunGrad)"))
    return "".join(rows)

# ---------- floor ----------
def grid():
    out, vp = [], 418
    for xb in range(-1300, 2200, 100):
        out.append(f'<polygon points="{vp},{HORIZON} {xb},{H} {xb+11},{H}" fill="{RED}" opacity="0.20"/>')
    yy, step = HORIZON, 3
    while yy < H:
        out.append(rect(0, yy, W, 2, RED, 'opacity="0.15"'))
        step += 2.2
        yy += step
    return "".join(out)

def sprite_shadow(x, y, wpx, scale):
    out = []
    for i, w in enumerate([wpx, wpx - 2, wpx - 5, wpx - 9]):
        if w <= 0:
            continue
        out.append(rect(x + (wpx - w) / 2 * scale, y + i * scale, w * scale, scale, "#000000", 'opacity="0.30"'))
    return "".join(out)

def corners():
    out, L, T, pad = [], 30, 4, 16
    for (cx, cy) in [(pad, pad), (W - pad - L, pad), (pad, H - pad - L), (W - pad - L, H - pad - L)]:
        out.append(rect(cx, cy, L, T, CREAM, 'opacity="0.8"'))
        out.append(rect(cx, cy, T, L, CREAM, 'opacity="0.8"'))
    return "".join(out)

# ---------- banner ----------
def banner():
    sun_cx, sun_cy, sun_R, P = 418, 186, 92, 5

    wm_scale, wm_gap = 13, 1
    wm_w = text_w("BAYZO", wm_scale, wm_gap)
    wm_x, wm_y = 900 - wm_w / 2, 56
    wm_h = 7 * wm_scale

    ph_scale, ph_gap = 5, 1
    ph_w = text_w("PROFIT HUNTER", ph_scale, ph_gap)
    ph_x, ph_y = 900 - ph_w / 2, 168
    ph_h = 7 * ph_scale

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="bayzoishere - profit hunter">']
    s.append('<defs>')
    s.append(f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="{BG_TOP}"/><stop offset="0.60" stop-color="{BG_MID}"/><stop offset="1" stop-color="{BG_BOT}"/></linearGradient>')
    s.append(f'<linearGradient id="sunGrad" x1="0" y1="{sun_cy - sun_R}" x2="0" y2="{HORIZON}" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="{AMBER}"/><stop offset="0.40" stop-color="#FF8A2B"/>'
             f'<stop offset="0.76" stop-color="{RED}"/><stop offset="1" stop-color="{RED_DEEP}"/></linearGradient>')
    s.append(f'<linearGradient id="wmGrad" x1="{wm_x}" y1="{wm_y}" x2="{wm_x + wm_w}" y2="{wm_y + wm_h}" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="#FF7A62"/><stop offset="0.45" stop-color="{RED}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>')
    s.append(f'<linearGradient id="phGrad" x1="{ph_x}" y1="0" x2="{ph_x + ph_w}" y2="0" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="{GOLD}"/><stop offset="0.5" stop-color="{CREAM}"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>')
    s.append(f'<radialGradient id="sunGlow" cx="0.5" cy="0.5" r="0.5">'
             f'<stop stop-color="{RED}" stop-opacity="0.45"/><stop offset="0.55" stop-color="{RED_DEEP}" stop-opacity="0.14"/>'
             f'<stop offset="1" stop-color="{RED_DEEP}" stop-opacity="0"/></radialGradient>')
    s.append(f'<linearGradient id="hz" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="{RED}" stop-opacity="0"/><stop offset="0.30" stop-color="{GOLD}" stop-opacity="0.85"/>'
             f'<stop offset="0.58" stop-color="{RED}" stop-opacity="0.7"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>')
    s.append(f'<linearGradient id="floor" x1="0" y1="{HORIZON}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="#20060F"/><stop offset="1" stop-color="#080104"/></linearGradient>')
    s.append('<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#000000"/></pattern>')
    s.append('<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
             '<feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    s.append('<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="16"/></filter>')
    s.append('</defs>')

    s.append(rect(0, 0, W, H, "url(#bg)"))

    # starfield
    random.seed(11)
    for _ in range(70):
        sx, sy = random.randint(8, W - 8), random.randint(6, HORIZON - 60)
        if 300 < sx < 540 and sy > 90:      # keep the sun's halo clean
            continue
        r = random.choice([1, 1, 2, 2, 3])
        col = random.choice([CREAM, AMBER, RED, "#8A2A48"])
        s.append(rect(sx, sy, r, r, col, f'opacity="{round(random.uniform(0.2, 0.8), 2)}"'))

    # sun
    s.append(f'<circle cx="{sun_cx}" cy="{sun_cy - 30}" r="215" fill="url(#sunGlow)"/>')
    s.append(f'<ellipse cx="{sun_cx}" cy="{HORIZON - 6}" rx="290" ry="86" fill="{RED}" opacity="0.32" filter="url(#soft)"/>')
    s.append(sun(sun_cx, sun_cy, sun_R, P))
    s.append(rect(0, HORIZON - 1, W, 4, "url(#hz)"))

    # floor
    s.append(rect(0, HORIZON, W, H - HORIZON, "url(#floor)"))
    s.append(grid())

    # birds
    for (bx, by, sc, dur) in [(706, 34, 2, 9), (762, 22, 1.6, 11), (654, 48, 1.5, 13)]:
        s.append(f'<g opacity="0.55"><animateTransform attributeName="transform" type="translate" '
                 f'values="0,0;34,-6;0,0" dur="{dur}s" repeatCount="indefinite"/>'
                 + blit(BIRD, {"1": RIM}, bx, by, sc) + '</g>')

    # hunter sprite
    sp_scale = 6.5
    sp_x, sp_w = 150, 16 * sp_scale
    sp_y = HORIZON + 4 - len(SPRITE) * sp_scale
    s.append(sprite_shadow(sp_x + 6, HORIZON + 2, 12, sp_scale))
    s.append(blit(SPRITE, SPRITE_FILL, sp_x, sp_y, sp_scale, glow_chars="3"))

    # coins
    def coin(cx, cy, scale, dur, phase):
        return (f'<g><animateTransform attributeName="transform" type="translate" '
                f'values="0,{phase};0,{phase - 7};0,{phase}" dur="{dur}s" repeatCount="indefinite"/>'
                + blit(COIN, COIN_FILL, cx, cy, scale, extra='filter="url(#glow)"') + '</g>')
    s.append(coin(252, 74, 4, 4.2, 0))
    s.append(coin(556, 122, 3, 5.1, -3))
    s.append(coin(1096, 240, 3.5, 4.7, -5))
    s.append(coin(660, 254, 2.5, 5.6, -2))

    # sparkles
    def spark(cx, cy, scale, dur):
        return (f'<g><animateTransform attributeName="transform" type="translate" '
                f'values="0,0;0,-5;0,0" dur="{dur}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.25;1;0.25" dur="{dur}s" repeatCount="indefinite"/>'
                + blit(SPARK, {"3": AMBER}, cx, cy, scale) + '</g>')
    s.append(spark(336, 56, 3, 2.6))
    s.append(spark(658, 84, 2, 3.4))
    s.append(spark(1122, 40, 2.5, 3.0))
    s.append(spark(112, 148, 2, 2.2))
    s.append(spark(872, 252, 2, 2.9))

    # wordmark
    s.append(f'<g filter="url(#glow)">{text("BAYZO", wm_x, wm_y, wm_scale, "url(#wmGrad)", gap=wm_gap)}</g>')
    s.append(text("PROFIT HUNTER", ph_x, ph_y, ph_scale, "url(#phGrad)", gap=ph_gap))

    # centered pixel divider under the kicker
    s.append(rect(900 - 70, ph_y + ph_h + 14, 140, 3, RED, 'opacity="0.8"'))
    s.append(rect(900 - 22, ph_y + ph_h + 14, 44, 3, AMBER))

    # frame + CRT overlay
    s.append(corners())
    s.append(rect(0, 0, W, H, "url(#scan)", 'opacity="0.09"'))
    s.append(f'<rect x="0" y="-60" width="{W}" height="60" fill="{RED}" opacity="0.10">'
             f'<animate attributeName="y" from="-60" to="{H}" dur="6s" repeatCount="indefinite"/></rect>')
    s.append('</svg>')
    return "".join(s)

# ---------- footer ----------
def footer():
    Wf, Hf = 1200, 78
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wf}" height="{Hf}" viewBox="0 0 {Wf} {Hf}" role="img" aria-label="bayzoishere">']
    s.append('<defs>'
             f'<linearGradient id="fl" x1="0" y1="0" x2="{Wf}" y2="0" gradientUnits="userSpaceOnUse">'
             f'<stop stop-color="{RED_DEEP}" stop-opacity="0"/><stop offset="0.5" stop-color="{GOLD}"/>'
             f'<stop offset="1" stop-color="{RED_DEEP}" stop-opacity="0"/></linearGradient>'
             '<mask id="fm"><rect width="1200" height="78" fill="black"/>'
             '<rect x="-200" y="14" width="200" height="3" fill="white">'
             '<animate attributeName="x" from="-200" to="1200" dur="5s" repeatCount="indefinite"/></rect></mask>'
             '</defs>')
    s.append(f'<path d="M0 18 H{Wf}" stroke="url(#fl)" stroke-width="1.5"/>')
    s.append(f'<rect x="0" y="16" width="{Wf}" height="3" fill="{CREAM}" mask="url(#fm)"/>')
    lab, sc, gap = "BAYZOISHERE", 3, 1
    tw = text_w(lab, sc, gap)
    x, y, cx = (Wf - tw) / 2, 44, (Wf - tw) / 2
    out = []
    for ch in lab:
        out.append(text(ch, cx, y, sc, RED if cx >= x + tw * 0.55 else "#8A2640", gap=gap))
        cx += (5 + gap) * sc
    s.append("".join(out))
    s.append('</svg>')
    return "".join(s)

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "banner.svg"), "w").write(banner())
open(os.path.join(OUT, "footer.svg"), "w").write(footer())
print("wrote banner.svg + footer.svg")
