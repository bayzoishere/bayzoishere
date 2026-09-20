#!/usr/bin/env python3
"""Batch pixel-art banner scene generator via inferhub image models."""
import base64, io, json, os, sys, threading, urllib.request
import yaml
from PIL import Image

d = yaml.safe_load(open(os.path.expanduser("~/.hermes/config.yaml")))
P = [x for x in d["custom_providers"] if x["name"] == "Api.inferhub.dev"][0]
BASE, KEY = P["base_url"].rstrip("/"), P["api_key"]

PROMPT = (
    "Ultra-wide 3:1 cinematic pixel art banner, authentic 16-bit, hard chunky visible pixels, "
    "no anti-aliasing, no blur, no smooth gradients. "
    "COMPOSITION: dark crimson night. At x=28% of the width, a HUGE blocky pixelated synthwave "
    "half-sun sitting on the horizon, built from stacked horizontal scanline slabs going gold -> "
    "amber -> orange -> crimson top to bottom, with a red glow halo and a bright red horizon line. "
    "Below the horizon, a dark crimson perspective GRID floor with thin red lines converging to a "
    "vanishing point under the sun. Far LEFT: a small pixel-art HUNTER, pointed hood, black void "
    "face, long tattered cloak, long rifle held diagonally across the body, standing on the grid, "
    "lit by a strong bright red rim light on the sun side plus a thin gold outline so the silhouette "
    "reads clearly, casting a hard black shadow on the grid. "
    "RIGHT HALF (from 55% to 100% of the width) must be DELIBERATELY DARK AND NEARLY EMPTY: flat "
    "deep oxblood #1A0410 night sky, only four or five faint tiny pixel stars, NO sun, NO clouds, "
    "NO coins, NO grid, NO mountains, so a large title can be placed there. "
    "Add a few small gold pixel coins and four-point sparkle stars only on the LEFT half, plus one "
    "or two tiny pixel birds. "
    "PALETTE: #160310 #330A18 #B00F32 #FF2E4C #FFB020 #FFD166 #FFF1DC. Vivid, punchy, high contrast. "
    "NO text, NO letters, NO words, NO logo, NO watermark, NO signature."
)

JOBS = [
    ("cb/gpt-image-2", {"size": "1536x512"}, "/tmp/v1.png"),
    ("cb/gpt-image-2", {"size": "1536x512"}, "/tmp/v2.png"),
    ("cb/gemini-3.1-flash-image", {"size": "1536x512"}, "/tmp/v3.png"),
    ("cb/gemini-3.1-flash-image", {}, "/tmp/v4.png"),
]


def go(model, extra, out):
    try:
        p = {"model": model, "modalities": ["image", "text"],
             "messages": [{"role": "user", "content": PROMPT}]}
        p.update(extra)
        req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(p).encode(),
                                     headers={"Authorization": f"Bearer {KEY}",
                                              "Content-Type": "application/json"})
        r = json.load(urllib.request.urlopen(req, timeout=560))
        c = r["choices"][0]["message"].get("content")
        url = [q for q in (c if isinstance(c, list) else [])
               if isinstance(q, dict) and q.get("type") == "image_url"][0]["image_url"]["url"]
        raw = base64.b64decode(url.split(",", 1)[1])
        open(out, "wb").write(raw)
        print(f"[{model}] OK {Image.open(io.BytesIO(raw)).size} -> {out}", flush=True)
    except Exception as e:
        det = ""
        try: det = e.read().decode()[:150]
        except Exception: pass
        print(f"[{model}] FAIL {e} {det}", flush=True)


ts = [threading.Thread(target=go, args=j) for j in JOBS]
for t in ts: t.start()
for t in ts: t.join()
