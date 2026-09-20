#!/usr/bin/env python3
"""Banner assets via inferhub: SVG codegen (Gemini/GPT) + pixel-art scene (image models)."""
import base64, json, os, re, sys, threading, urllib.request

CFG = os.path.expanduser("~/.hermes/config.yaml")
import yaml
d = yaml.safe_load(open(CFG))
P = [x for x in d["custom_providers"] if x["name"] == "Api.inferhub.dev"][0]
BASE, KEY = P["base_url"].rstrip("/"), P["api_key"]

BRIEF = r"""You are a senior SVG artist. Produce ONE self-contained animated pixel-art banner SVG for a GitHub profile README.

OWNER: GitHub user "bayzoishere" — on-chain automation / mint snipers / infra engineer from Indonesia. Tagline: PROFIT HUNTER.

CANVAS: width="1200" height="320" viewBox="0 0 1200 320".

ART DIRECTION — hand-crafted pixel art, not flat vector:
- Palette: deep crimson sky (#160310 -> #330A18), neon RED #FF2E4C (hero colour), deep red #B00F32, gold #FFB020, amber #FFD166, cream #FFF1DC. Bright, punchy, high contrast.
- Synthwave pixel sunset: a big blocky PIXELATED half-sun on the horizon at x~420 built from stacked horizontal slabs with retro slit bands cut through the lower half, gradient amber -> orange -> red downward, soft red glow halo behind it.
- Perspective grid floor below horizon y=226: thin red lines converging to a vanishing point under the sun + horizontal red lines crowding tighter toward the horizon.
- A small pixel-art HUNTER sprite on the left (x~150), ~16 px wide by 24 px tall at scale ~6.5, standing on the floor. It must be UNMISTAKABLY a hunter: pointed hood peak, dark face opening, long cloak/robe, holding a long pixel RIFLE or BOW diagonally across the body. Sunset rim-light (bright #FF6A5A) on the sun-facing right edge, plus a dark ground shadow so it is grounded.
- Pixel detail: floating gold coins (slow bob animation), 4-point sparkle stars (twinkle), a couple of tiny pixel birds, sparse varied-brightness pixel starfield.
- Optional: very low-opacity CRT scanline overlay, faint slow light sweep.

TYPOGRAPHY (critical):
- Wordmark "BAYZO" — huge pixel capitals drawn with <rect> only (5x7 cell grid, NO <text> element, NO external fonts). Centred at x=900. Gradient fill #FF7A62 -> #FF2E4C -> #FFB020 plus a soft red outer glow.
- Under it "PROFIT HUNTER" in smaller pixel capitals (cell scale 5, <rect> only), gradient gold -> cream -> gold, centred at x=900, with a short decorative pixel rule under it that is exactly as wide as the text and exactly centred.
- Everything must be crisp at 1x; the wordmark must never be overlapped by any other element.

FRAME: thin cream L-shaped corner brackets inset ~16px from each corner.

HARD TECHNICAL RULES:
- Output ONLY raw SVG markup. No markdown fences, no prose, no explanation.
- Valid XML; must render correctly in librsvg (rsvg-convert) AND Chrome. No <foreignObject>, no <style> blocks, no external refs, no <text>. SMIL <animate>/<animateTransform> allowed and encouraged.
- Every animated element must still look correct in a STATIC render.
- Gradients use gradientUnits="userSpaceOnUse" with explicit coordinates.
- Under ~60 KB. Nothing clipped at the canvas edges.

Return ONLY the SVG."""

SCENE = (
    "Extreme wide banner artwork, 3:1 aspect ratio, authentic 16-bit pixel art with hand-placed "
    "visible pixels and hard edges, no anti-aliasing. Synthwave retro sunset at night: deep oxblood "
    "crimson sky, neon red and hot magenta bands; a huge blocky pixelated half-sun on the horizon "
    "made of stacked horizontal slabs graduating amber to orange to deep red with a soft red glow "
    "halo; below the horizon a dark crimson perspective grid floor with thin red lines converging to "
    "a vanishing point under the sun. On the LEFT third stands a small pixel-art HUNTER: pointed hood, "
    "dark face opening, long cloak, holding a rifle diagonally across the body, lit by a bright red "
    "rim light from the sun, casting a hard dark shadow on the grid. Scattered gold pixel coins, "
    "small sparkle stars, a couple of tiny birds, sparse pixel stars, CRT scanline texture. "
    "Palette: #160310, #330A18, #FF2E4C, #B00F32, #FFB020, #FFD166, #FFF1DC. Vivid, punchy, "
    "high contrast. NO text, NO letters, NO words, NO watermark, NO signature, NO border."
)


def post(path, payload, timeout=600):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                headers={"Authorization": f"Bearer {KEY}",
                                         "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def svg_gen(model, out):
    try:
        r = post("/chat/completions", {"model": model, "max_tokens": 32000, "temperature": 0.9,
                                      "messages": [{"role": "user", "content": BRIEF}]})
        txt = r["choices"][0]["message"]["content"]
        m = re.search(r"<svg[\s\S]*?</svg>", txt)
        svg = m.group(0) if m else txt
        open(out, "w").write(svg)
        print(f"[SVG {model}] OK {len(svg)}B -> {out}", flush=True)
    except Exception as e:
        det = ""
        try: det = e.read().decode()[:200]
        except Exception: pass
        print(f"[SVG {model}] FAIL {e} {det}", flush=True)


def img_gen(model, out):
    try:
        r = post("/chat/completions", {"model": model, "modalities": ["image", "text"],
                                      "messages": [{"role": "user", "content": SCENE}]})
        msg = r["choices"][0]["message"]
        imgs = msg.get("images") or []
        if not imgs:
            c = msg.get("content")
            if isinstance(c, list):
                imgs = [p for p in c if isinstance(p, dict) and p.get("type") == "image_url"]
        if not imgs:
            print(f"[IMG {model}] no image: {str(msg.get('content'))[:160]}", flush=True)
            return
        url = imgs[0]["image_url"]["url"]
        open(out, "wb").write(base64.b64decode(url.split(",", 1)[1]))
        print(f"[IMG {model}] OK -> {out}", flush=True)
    except Exception as e:
        det = ""
        try: det = e.read().decode()[:200]
        except Exception: pass
        print(f"[IMG {model}] FAIL {e} {det}", flush=True)


jobs = [
    (svg_gen, "gemini-3.1-pro", "/tmp/gem.svg"),
    (svg_gen, "gpt-5.6-luna", "/tmp/gpt.svg"),
    (img_gen, "cb/gemini-3.1-flash-image", "/tmp/scene_a.png"),
    (img_gen, "cb/gpt-image-2", "/tmp/scene_b.png"),
]
ts = [threading.Thread(target=f, args=a) for f, *a in jobs]
for t in ts: t.start()
for t in ts: t.join()
