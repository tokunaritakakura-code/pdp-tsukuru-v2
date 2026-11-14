#!/usr/bin/env python3
"""絵を名前つきで1枚に並べる（参考の絵・作った絵をまとめて開いて確かめる時に使う。1枚ずつ開くより読む量が少ない）。
使い方: python3 並べ絵を作る.py <書き出す先.png> <絵1> <絵2> …（12枚まで。13枚目からは分けて叩く）
        1枚を 320px の幅にそろえ、4列で並べ、下にファイル名を書く。
終了コード: 0 書けた／1 開けない絵がある（開けた分だけで書く）／2 引数が足りない・絵が13枚以上
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont


def main(a):
    if len(a) < 3 or len(a) > 14: print(__doc__); return 2
    out, 絵 = a[1], a[2:]
    W, 列, 字 = 320, 4, 28
    try: f = ImageFont.truetype("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", 16)
    except Exception: f = ImageFont.load_default()
    片, 落 = [], []
    for p in 絵:
        try:
            im = Image.open(p).convert("RGBA"); 台 = Image.new("RGBA", im.size, (200, 200, 200, 255)); 台.alpha_composite(im)   # 透明は灰で見せる
            im = 台.convert("RGB"); im = im.resize((W, max(1, round(im.size[1] * W / im.size[0]))))
            if im.size[1] > 640: im = im.crop((0, 0, W, 640))
            片.append((os.path.basename(p), im))
        except Exception as e: 落.append(f"{p}（{e}）")
    if not 片: print("開けた絵が 0:", "・".join(落)); return 1
    行 = [片[i:i + 列] for i in range(0, len(片), 列)]
    高 = [max(im.size[1] for _, im in r) + 字 for r in 行]
    板 = Image.new("RGB", (W * 列 + 8 * (列 + 1), sum(高) + 8 * (len(行) + 1)), "white"); d = ImageDraw.Draw(板); y = 8
    for r, h in zip(行, 高):
        for i, (名, im) in enumerate(r):
            x = 8 + i * (W + 8); 板.paste(im, (x, y)); d.text((x, y + h - 字 + 4), 名[:34], fill="black", font=f)
        y += h + 8
    板.save(out)
    print(f"書いた: {out}（{len(片)} 枚）" + (f"／開けなかった: {'・'.join(落)}" if 落 else ""))
    return 1 if 落 else 0


if __name__ == "__main__": sys.exit(main(sys.argv))
