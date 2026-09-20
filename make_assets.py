#!/usr/bin/env python3
"""Build the final GitHub profile assets: assets/banner.png + assets/footer.png."""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pixel_banner as pb

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
SCENE = os.environ.get("SCENE", "/tmp/v2.png")


def build_footer(path, low_w=600, low_h=45, px=2, word_a="BAYZOIS", word_b="HERE"):
    """Slim pixel-art footer: flat oxblood field, hard rules, deliberate embers."""
    low = Image.new("RGB", (low_w, low_h), pb.OXBLOOD)
    d = ImageDraw.Draw(low)

    # deliberate pixel texture: diagonal ember dust on both ends (mirrored)
    for i in range(26):
        x = 14 + (i * 5) % 96
        y = 4 + (i * 11) % (low_h - 8)
        col = pb.DEEPRED if i % 3 else pb.RED
        d.rectangle([x, y, x + 1, y + 1], fill=col)
        d.rectangle([low_w - 2 - x, y, low_w - 1 - x, y + 1], fill=col)
    # hairline rules top/bottom
    d.rectangle([0, 0, low_w - 1, 0], fill=pb.DEEPRED)
    d.rectangle([0, low_h - 1, low_w - 1, low_h - 1], fill=pb.DEEPRED)

    cell, gap = 6, 2
    wa = pb.text_w(word_a, cell, gap)
    wb = pb.text_w(word_b, cell, gap)
    sep = cell * 2
    x = (low_w - (wa + sep + wb)) // 2
    y = (low_h - 7 * cell) // 2

    pb.blocky_glow(low, word_a, x, y, cell, pb.GLOWRED, 2, gap=gap, step=2)
    pb.blocky_glow(low, word_b, x + wa + sep, y, cell, pb.GLOWRED, 2, gap=gap, step=2)
    pb.draw_text_v(low, word_a, x, y, cell, [pb.CREAM, pb.AMBER, pb.GOLD, pb.DEEPRED],
                   outline=pb.OXBLOOD, gap=gap)
    pb.draw_text_v(low, word_b, x + wa + sep, y, cell, [pb.CREAM, pb.RED, pb.DEEPRED],
                   outline=pb.OXBLOOD, gap=gap)

    # rule under the lockup
    ry = y + 7 * cell + 7
    ux0, ux1 = x, x + wa + sep + wb - 1
    d.rectangle([ux0, ry, ux1, ry + 1], fill=pb.RED)
    mid = ux0 + (ux1 - ux0 - 15) // 2
    d.rectangle([mid, ry - 2, mid + 14, ry + 3], fill=pb.GOLD)

    low.resize((low_w * px, low_h * px), Image.NEAREST).save(path)
    return path


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    b = pb.build(SCENE, os.path.join(ASSETS, "banner.png"),
                 colors=14, dither=False, levels=34)
    f = build_footer(os.path.join(ASSETS, "footer.png"))
    print("banner:", b, Image.open(b).size)
    print("footer:", f, Image.open(f).size)
