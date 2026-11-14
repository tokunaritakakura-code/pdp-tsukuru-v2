#!/usr/bin/env python3
"""店の指紋（index.html と img/ の直下の画像と動画）を1つの手順で出す。店の検査を回す.py・審査を回す.py が使い、
参考と並べる.mjs は同じ手順を JS で書いている（2026-11-14。3つの道具で指紋がずれないように1つにした）。

手順: sha256 に index.html の中身を入れ、img/ の直下のファイルのうち拡張子が png・jpg・jpeg・webp・gif・svg・mp4 の物
（`.` で始まるファイルは除く）を、名前の UTF-8 のバイト順に、1件ごとに「\\0<名前>\\0」と中身を入れる。頭12字を指紋にする。

使い方: python3 店の指紋.py <店のフォルダ>   → 指紋を1行出す（終了コード 0。index.html が無ければ 2）
"""
import hashlib, os, sys

拡張子 = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".mp4")


def 店の指紋(店):
    h = hashlib.sha256(open(os.path.join(店, "index.html"), "rb").read())
    絵 = os.path.join(店, "img")
    名たち = [f for f in os.listdir(絵) if not f.startswith(".") and os.path.splitext(f)[1].lower() in 拡張子
             and os.path.isfile(os.path.join(絵, f))] if os.path.isdir(絵) else []
    for f in sorted(名たち, key=lambda x: x.encode("utf-8")):
        h.update(b"\0" + f.encode("utf-8") + b"\0")
        h.update(open(os.path.join(絵, f), "rb").read())
    return h.hexdigest()[:12]


if __name__ == "__main__":
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    if not os.path.exists(os.path.join(sys.argv[1], "index.html")): print("index.html が無い:", sys.argv[1]); sys.exit(2)
    print(店の指紋(sys.argv[1]))
