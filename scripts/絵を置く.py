#!/usr/bin/env python3
"""作った絵を img/ に置き、参考の絵の縦横比に切りそろえ、ページの絵と 画像の置き場.md と説明（alt）を突き合わせる。
絵を作り直したら毎回これを回す。img/ に書くのはこの道具だけ（絵を作る係は _gen/ にだけ書く）。

使い方: python3 絵を置く.py <店のフォルダ>
決まり:
  - 置く絵の名前は 絵の一覧.tsv（店のフォルダの写し。無ければ空の型の物）の1列目。作った絵は <店>/_gen/<名前>.png
  - _gen/<名前>.png を img/<名前>.png に置く。縦÷横が、絵の一覧.tsv の「元の大きさ」（参考の絵）と 5% を超えて違えば、写真は真ん中で切り、札・ロゴ・アイコン・図・イラストは切らずに地を足して、参考の比に合わせる（引き伸ばさない）
  - index.html の宣言の段に動画（img/sengen.mp4）がある時は、_gen/sengen.mp4 を img/sengen.mp4 に置く
  - index.html が指すのに 絵の一覧.tsv に無い名前（共通の印 kyotsu-* を除く）は、_gen/<名前>.png があればそのまま置く（比は合わせない）
  - 置くのは、指紋が前に置いた時と違う絵だけ。指紋は「_gen/<名前> の中身＋絵の一覧.tsv のその行＋この道具の版（版 = …）」の sha256 で、
    img/.置いた指紋.json に、指紋と置いた絵の中身の sha256 を名前ごとに持つ。img/ の絵が置いた時と違う（手で書いた・消えた）時も置き直す
  - 地を抜く: 参考の絵の地が透明（絵の一覧.tsv の6列目が「透明…」）で、作った絵に透ける所が無ければ、四隅の色とつながった地を透明にする
確かめる物（落ちたら終了コード 1）:
  - 地と比（毎回、全部の絵に。置き直さなかった絵も img/ の絵で見る）:
      縦÷横が参考の絵の「元の大きさ」と 5% を超えて違わない
      地が「透明…」の絵: 透明の割合が、参考の絵（絵の一覧.tsv の5列目を PIL で開いて数える）の割合の 0.5倍以上 1.6倍以下
        （0.5倍未満は「抜け残り」、1.6倍超は「抜けすぎ」。どちらも差が15ポイント以上の時だけ落とす。構図の小さな違いで落とさないため。参考の絵が開けない時は比べない）。
        縁を一周見て、作った絵の地の色（_gen の絵の四隅の色）が縁の 30% 以上に残っていれば「抜け残り」
      地が「不透明」の絵: 透ける所が 3% 未満
  - 絵の一覧.tsv の名前が全部 _gen/ にある
  - index.html（HTML・CSS の url()・JS の setImg）が指す img/ の絵と動画が全部 img/ にある
  - 画像の置き場.md の表（列「名前」「主役」「文字」「見えるべき物」「合う」）に、置く絵の名前が全部1行ずつあり、表に知らない名前が無い
  - 主役が ロゴ・札 でない行に「見えるべき物」が書いてあり、「合う」が ○（references/写真の指示文.md「形・数・向き・姿勢を描かせる時」）
書く物: <店>/絵と説明の一覧.tsv（タブ区切り。絵ごとに 名前・段・種類・主役・文字・見えるべき物・ページの alt。照らし合わせと編集長が読む）
終了コード: 0 置けて全部合った ／ 1 足りない・合わない物がある ／ 2 index.html か 画像の置き場.md か 絵の一覧.tsv が無い・読めない
"""
import hashlib, json, os, re, shutil, sys
from PIL import Image

版 = "2026-11-14a"   # 置き方（地を抜く・比をそろえる・縮める）を変えたら上げる。上げると全部の絵を置き直す
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
空の型の絵 = os.path.join(HERE, "..", "kata", "絵の一覧.tsv")
ずれ = 0.05
指紋の名 = ".置いた指紋.json"


def 一覧を読む(店):
    p = os.path.join(店, "絵の一覧.tsv")
    if not os.path.exists(p): p = 空の型の絵
    行 = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8")]
    頭 = 行[0]
    return [dict(zip(頭, r)) | {"名前": r[0]} for r in 行[1:] if r and r[0].strip()]


def 置き場を読む(p):
    頭, 行 = None, []
    for l in open(p, encoding="utf-8"):
        if not l.startswith("|"): 頭 = None if 行 else 頭; continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if "名前" in c and "主役" in c: 頭 = c; continue
        if 頭 and not set("".join(c)) <= set("-: ") and len(c) == len(頭): 行.append(dict(zip(頭, c)))
    return 行


def 大きさ(s):
    m = re.search(r"(\d+)\s*[×x]\s*(\d+)", s or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def 比をそろえる(im, 元, 種類=""):
    """縦÷横が 元 と 5% を超えて違えば合わせる。写真は真ん中で切る。札・ロゴ・アイコン・図・イラストは切らずに、
    角の色（透明なら透明）で足して合わせる（字や印が切れないように。2026-11-14）。合わせたかどうかも返す"""
    w, h = im.size; W, H = 元
    r, R = h / w, H / W
    if abs(r / R - 1) <= ずれ: return im, False
    if 種類 in ("札", "ロゴ", "アイコン", "図", "イラスト"):
        im = im.convert("RGBA")
        nw, nh = (w, round(w * R)) if r < R else (round(h / R), h)
        地 = im.getpixel((0, 0))
        台 = Image.new("RGBA", (nw, nh), 地); 台.paste(im, ((nw - w) // 2, (nh - h) // 2)); return 台, True
    if r > R:   # 縦が長すぎる → 上下を切る
        nh = round(w * R); y = (h - nh) // 2; return im.crop((0, y, w, y + nh)), True
    nw = round(h / R); x = (w - nw) // 2; return im.crop((x, 0, x + nw, h)), True


def 透ける割合(im):
    if "A" not in im.getbands(): return 0.0
    a = im.getchannel("A").resize((100, 100)); d = list(a.getdata()); return sum(1 for v in d if v < 128) / len(d)


def 地を抜く(im):
    """四隅の色とつながった一色の地を透明にする（参考の絵が透明の地の時。白い地で作った絵の白い四角を無くす。2026-11-14）"""
    from PIL import ImageDraw
    im = im.convert("RGBA"); w, h = im.size
    印 = (255, 0, 254, 0)
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        if im.getpixel(xy)[3] == 0: continue
        ImageDraw.floodfill(im, xy, 印, thresh=42)
    return im


def 白に置く(im):
    台 = Image.new("RGB", im.size, (255, 255, 255)); 台.paste(im, mask=im.getchannel("A")); return 台


def 保存(im, out):
    if im.mode not in ("RGB", "RGBA"): im = im.convert("RGBA" if "A" in im.getbands() or im.mode == "P" else "RGB")
    im.save(out, "PNG")


def 中身の指紋(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else ""


def 置く指紋(src, 行):
    """_gen の絵の中身＋絵の一覧.tsv のその行＋道具の版"""
    h = hashlib.sha256(open(src, "rb").read()); h.update(b"\0" + 行.encode("utf-8") + b"\0" + 版.encode("utf-8"))
    return h.hexdigest()


def 置き直す(前, 名, 紋, out):
    """指紋が前に置いた時と違うか、img/ の絵が置いた時の中身と違えば置き直す"""
    p = 前.get(名) or {}
    return p.get("指紋") != 紋 or p.get("置いた絵") != 中身の指紋(out)


def 縁の地(im, 地の色, 幅=60):
    """縁を一周見て、見える（不透明の）点のうち地の色に近い点の割合（地を抜く時の 42 より少し広く見る。影・ぼかしの残りも数える）"""
    im = im.convert("RGBA"); w, h = im.size
    点 = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + [(0, y) for y in range(1, h - 1)] + [(w - 1, y) for y in range(1, h - 1)]
    残 = 0
    for xy in 点:
        c = im.getpixel(xy)
        if c[3] >= 128 and max(abs(c[i] - 地の色[i]) for i in range(3)) <= 幅: 残 += 1
    return 残 / len(点) if 点 else 0.0


def 隅の色(im):
    """四隅のうち見える点で、いちばん多い色（地の色）。四隅が全部透けていれば None"""
    im = im.convert("RGBA"); w, h = im.size
    c = [im.getpixel(xy)[:3] for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)) if im.getpixel(xy)[3] >= 128]
    if not c: return None
    return max(c, key=lambda x: sum(1 for y in c if max(abs(x[i] - y[i]) for i in range(3)) <= 42))


_参考の割合 = {}
def 参考の透明(ref):
    if ref in _参考の割合: return _参考の割合[ref]
    try:
        im = Image.open(os.path.join(SKILL, ref)); im.load()
        if im.mode in ("P", "LA", "L", "PA") or (im.mode == "RGB" and "transparency" in im.info): im = im.convert("RGBA")
        v = 透ける割合(im)
    except Exception:
        v = None
    _参考の割合[ref] = v
    return v


def 地と比を見る(名, r, out, 隅):
    """置いた img/ の絵の地と比を見る。落ちた理由の list を返す"""
    try: im = Image.open(out); im.load()
    except Exception as e: return [f"img/{名}.png が開けない（{e}）"]
    if im.mode in ("P", "LA", "PA"): im = im.convert("RGBA")
    bad = []
    元 = 大きさ(r.get("元の大きさ", ""))
    if 元:
        q, Q = im.size[1] / im.size[0], 元[1] / 元[0]
        if abs(q / Q - 1) > ずれ: bad.append(f"img/{名}.png の縦÷横 {q:.2f} が参考 {元[0]}x{元[1]}（{Q:.2f}）と 5% を超えて違う")
    地 = r.get("地", "")
    透 = 透ける割合(im)
    if 地.startswith("透明"):
        ref = r.get("参考の絵（絵を作る時に一緒に渡す）", "")
        R = 参考の透明(ref) if ref else None
        if R:
            if 透 > R * 1.6 and 透 - R >= 0.15: bad.append(f"img/{名}.png が抜けすぎ（透明の割合 {透:.0%}・参考 {R:.0%} の 1.6倍超で、差が15ポイント以上。商品の本体まで抜けているか、中身が参考より小さい。地を商品と違う一色にして、中身を参考と同じ大きさで作り直す）")
            elif 透 < R * 0.5 and R - 透 >= 0.15: bad.append(f"img/{名}.png が抜け残り（透明の割合 {透:.0%}・参考 {R:.0%} の 0.5倍未満。地が残っている。一色の地で作り直す）")
        if 隅 is not None:
            v = 縁の地(im, 隅)
            if v >= 0.3: bad.append(f"img/{名}.png が抜け残り（縁の {v:.0%} に地の色 rgb{隅} が残っている。一色の地で作り直す）")
    elif 地 == "不透明" and 透 >= 0.03:
        bad.append(f"img/{名}.png に透ける所が {透:.0%} ある（参考の絵は不透明の地）")
    return bad


def main(a):
    if len(a) < 2: print(__doc__); return 2
    店 = os.path.abspath(a[1]); gen = os.path.join(店, "_gen"); img = os.path.join(店, "img")
    html_p = os.path.join(店, "index.html"); 置き場 = os.path.join(店, "画像の置き場.md")
    for p in (html_p, 置き場):
        if not os.path.exists(p): print("無い:", p); return 2
    try: 一覧 = 一覧を読む(店)
    except Exception as e: print(f"絵の一覧.tsv が読めない（{e}）"); return 2
    if not 一覧: print("絵の一覧.tsv に名前が 0"); return 2
    行たち = 置き場を読む(置き場)
    if not 行たち: print("画像の置き場.md に「名前」「主役」の列を持つ表が無い（列: 名前｜主役｜文字｜見えるべき物｜合う）"); return 2
    os.makedirs(img, exist_ok=True)
    html = open(html_p, encoding="utf-8").read()
    名前たち = [r["名前"] for r in 一覧]
    置いた, 切った, 落ち = [], [], []
    指紋p = os.path.join(img, 指紋の名)
    try: 前 = json.load(open(指紋p, encoding="utf-8")) if os.path.exists(指紋p) else {}
    except Exception: 前 = {}
    今 = {}
    tsv = os.path.join(店, "絵の一覧.tsv") if os.path.exists(os.path.join(店, "絵の一覧.tsv")) else 空の型の絵
    生の行 = {l.split("\t")[0]: l.rstrip("\n") for l in open(tsv, encoding="utf-8")}
    def 置いた印(名, 紋, out): 今[名] = {"指紋": 紋, "置いた絵": 中身の指紋(out)}
    # 1 置く（絵の一覧.tsv の名前）。置くのは指紋が違う絵だけ。地と比の確かめは毎回全部の絵に
    for r in 一覧:
        名 = r["名前"]; src = os.path.join(gen, 名 + ".png"); out = os.path.join(img, 名 + ".png")
        if not os.path.exists(src): 落ち.append(f"_gen/{名}.png が無い（{r.get('段', '')}・{r.get('種類', '')}。参考の絵: {r.get('参考の絵（絵を作る時に一緒に渡す）', '')}）"); continue
        try: im = Image.open(src); im.load()
        except Exception as e: 落ち.append(f"_gen/{名}.png が開けない（{e}）"); continue
        if im.mode in ("P", "LA", "PA") or (im.mode in ("RGB", "L") and "transparency" in im.info): im = im.convert("RGBA")
        地 = r.get("地", "")
        隅 = 隅の色(im) if 地.startswith("透明") and 透ける割合(im) < 0.03 else None   # 抜く前の地の色（縁に残っていないかを見る）
        紋 = 置く指紋(src, 生の行.get(名, ""))
        if 置き直す(前, 名, 紋, out):
            元 = 大きさ(r.get("元の大きさ", ""))
            if 地.startswith("透明") and 透ける割合(im) < 0.03: im = 地を抜く(im)
            if 地.startswith("透明") and 透ける割合(im) < 0.03: 落ち.append(f"_gen/{名}.png の地が抜けない（参考の絵は透明の地。一色の地で作り直す）"); continue
            if 地 == "不透明" and 透ける割合(im) >= 0.03: im = 白に置く(im)
            if 元: im, 切 = 比をそろえる(im, 元, r.get("種類", ""))
            else: 切 = False
            if 元 and im.size[0] > max(元[0] * 2, 1200): im = im.resize((max(元[0] * 2, 1200), round(im.size[1] * max(元[0] * 2, 1200) / im.size[0])))
            保存(im, out); 置いた.append(名)
            if 切: 切った.append(f"{名}（参考 {元[0]}x{元[1]} の比に）")
        置いた印(名, 紋, out)
        落ち += 地と比を見る(名, r, out, 隅)
    # 2 宣言の動画
    if 'src="img/sengen.mp4"' in html:
        src = os.path.join(gen, "sengen.mp4"); out = os.path.join(img, "sengen.mp4")
        if not os.path.exists(src): 落ち.append("_gen/sengen.mp4 が無い（動画が無い店は、宣言の段の <video> を <img data-e=\"sengen-poster\" src=\"img/sengen-poster.png\" alt=\"…\"> に替える）")
        else:
            紋 = 置く指紋(src, "sengen.mp4")
            if 置き直す(前, "sengen.mp4", 紋, out): shutil.copyfile(src, out); 置いた.append("sengen.mp4")
            置いた印("sengen.mp4", 紋, out)
    # 3 ページが指す絵
    使う = set(re.findall(r"""(?:src|poster)=["']img/([^"'?#]+)""", html)) | set(re.findall(r"""url\(\s*["']?img/([^"')?#]+)""", html))
    if "setImg(" in html: 使う |= {f"set-{t.group(1)}.png" for t in re.finditer(r"\{\s*n\s*:\s*(\d+)", html)}
    表に無い = sorted({os.path.splitext(f)[0] for f in 使う if f.endswith(".png") and not f.startswith("kyotsu-")} - set(名前たち))
    for 名 in 表に無い:
        src = os.path.join(gen, 名 + ".png"); out = os.path.join(img, 名 + ".png")
        if not os.path.exists(src): continue
        紋 = 置く指紋(src, "")
        if 置き直す(前, 名, 紋, out): 保存(Image.open(src), out); 置いた.append(名 + "（絵の一覧.tsv に無い名前。比は合わせない）")
        置いた印(名, 紋, out)
    for f in sorted(使う):
        if not os.path.exists(os.path.join(img, f)): 落ち.append(f"ページが指す img/{f} が img/ に無い" + ("（絵の一覧.tsv に無い名前。_gen/ に作るか、空の型を直す）" if os.path.splitext(f)[0] in 表に無い else ""))
    json.dump(今, open(指紋p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 4 画像の置き場.md と突き合わせる
    置く名 = 名前たち + 表に無い
    書いた = {}
    for r in 行たち: 書いた.setdefault(r["名前"], r)
    for n in 置く名:
        if n not in 書いた: 落ち.append(f"画像の置き場.md に {n} の行が無い")
    for n in 書いた:
        if n not in 置く名: 落ち.append(f"画像の置き場.md の {n} は 絵の一覧.tsv にもページにも無い名前（名前を 絵の一覧.tsv の1列目に合わせる）")
    for n, r in 書いた.items():
        if n not in 置く名 or r.get("主役") in ("ロゴ", "札"): continue
        if not r.get("見えるべき物") or r.get("見えるべき物") == "—":
            落ち.append(f"{n}: 「見えるべき物」が無い（写真の指示文「形・数・向き・姿勢を描かせる時」の②を書く）"); continue
        if not r.get("合う", "").startswith("○"): 落ち.append(f"{n}: 「合う」が ○ でない（絵を見て、見えるべき物が写っているかを ○× で書く。× は作り直す）")
    # 5 絵と説明の一覧
    alt = {}
    for t in re.findall(r"<img\b[^>]*>", html):
        e = re.search(r'data-e="([^"]+)"', t) or re.search(r'src="img/([^".]+)\.png"', t); al = re.search(r'alt="([^"]*)"', t)
        if e: alt.setdefault(e.group(1), al.group(1) if al else "")
    段 = {r["名前"]: r for r in 一覧}
    L = ["\t".join(["名前", "段", "種類", "主役", "文字", "見えるべき物", "ページの alt"])]
    for n in 置く名:
        r = 書いた.get(n, {}); t = 段.get(n, {})
        L.append("\t".join([n, t.get("段", ""), t.get("種類", "（絵の一覧.tsv に無い）"), r.get("主役", "（行が無い）"), r.get("文字", ""), r.get("見えるべき物", ""), alt.get(n, "（JS で出す絵）")]))
    open(os.path.join(店, "絵と説明の一覧.tsv"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"置いた {len(置いた)}（指紋が違った絵だけ）・比を切りそろえた {len(切った)}・絵の一覧 {len(名前たち)}・ページが指す絵 {len(使う)}")
    for x in 切った: print("  切った: " + x)
    for x in 落ち: print("- " + x)
    if not 落ち: print("通った（_gen の絵が全部あり、地と比が参考に合い、ページの絵が全部 img/ にあり、画像の置き場.md と名前が合う）")
    return 0 if not 落ち else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
