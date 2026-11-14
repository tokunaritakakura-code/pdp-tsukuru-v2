#!/usr/bin/env python3
"""Shopify に置く前に、index.html の中の img/ を指す所を全部、Files に上げた絵の CDN の URL に替える（references/Shopifyに置く.md の手順3）。
使い方: python3 CDNに替える.py <店のフォルダ> <対応表.json>
  対応表.json: {"yoko-1.png": "https://cdn.shopify.com/…/yoko-1.png", …}（img/ の中のファイル名 → CDN の URL。img/ の全部のファイルが要る）
やる事: <店>/index.html を <店>/_shopify/index.html に写し、src・poster・CSS の url()・末尾のスクリプトの setImg（'img/set-'+n+'.png'）を替える。
        替えた後に 'img/' が1つでも残れば落とす（残った所を言う）。元の index.html は変えない。
終了コード: 0 全部替えた／1 対応表に無い絵がある・img/ が残った／2 入力が無い
"""
import json, os, re, sys


def main(a):
    if len(a) < 3: print(__doc__); return 2
    店, 表p = os.path.abspath(a[1]), a[2]
    src = os.path.join(店, "index.html")
    if not os.path.exists(src) or not os.path.exists(表p): print("無い:", src if not os.path.exists(src) else 表p); return 2
    try: 表 = json.load(open(表p, encoding="utf-8"))
    except Exception as e: print(f"対応表が読めない（{e}）"); return 2
    h = open(src, encoding="utf-8").read()
    無い = sorted({m for m in re.findall(r"""img/([A-Za-z0-9_.\-]+\.(?:png|jpe?g|webp|gif|svg|mp4))""", h) if m not in 表})
    for n in re.findall(r"\{\s*n\s*:\s*(\d+)", h):
        if f"set-{n}.png" not in 表: 無い.append(f"set-{n}.png")
    if 無い: print("対応表に無い絵:", "・".join(sorted(set(無い)))); return 1
    for f in sorted(表, key=len, reverse=True): h = h.replace("img/" + f, 表[f])
    sets = {n: 表[f"set-{n}.png"] for n in sorted(set(re.findall(r"\{\s*n\s*:\s*(\d+)", h)))}
    h, k = re.subn(r"function setImg\(n\)\{[^}]*\}", "function setImg(n){ return " + json.dumps(sets, ensure_ascii=False) + "[n]; }", h, count=1)
    if k != 1: print("setImg が見つからない（空の型の末尾のスクリプトが変わった）"); return 1
    残り = [h[max(0, m.start() - 40):m.end() + 30].replace("\n", " ") for m in re.finditer(r"""(?<![A-Za-z0-9_/.\-])img/""", h)]
    if 残り:
        print(f"img/ が {len(残り)} か所残った:"); [print("  …" + x + "…") for x in 残り[:10]]; return 1
    os.makedirs(os.path.join(店, "_shopify"), exist_ok=True)
    open(os.path.join(店, "_shopify", "index.html"), "w", encoding="utf-8").write(h)
    print(f"替えた: _shopify/index.html（絵 {len(表)} 個・img/ の残り 0）"); return 0


if __name__ == "__main__": sys.exit(main(sys.argv))
