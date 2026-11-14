#!/usr/bin/env python3
"""店のページ（index.html）を空の型と比べ、本人に出す前に機械で落とす（2026-10-18 本人「数える物は文ではなく道具に」）。
2026-11-13 空の型をワンドライの実物の HTML・CSS から作り直したのに合わせ、箱を作り直した（古い F2・F3・F5・F7〜F10 は消した）。

使い方: python3 店の仕上がり検査.py <店のフォルダ>
終了コード: 0 全部通った / 1 落ちた所がある（箱ごとに1行。落ちた中身をその下に出す） / 2 読めなかった

箱（店を作る回に替えてよいのは、札の中の文字・絵・末尾のスクリプトの「変えるならここ」の値だけ）:
  F1 骨組み: <style> の中身が全部、空の型（kata/index.html）と1字も違わない。
     <main> の前（<html> の頭から <main> の前まで。<head> の <link>・<meta>・<style> のタグ、<body> のタグ）が、タグと属性の値まで空の型と同じ
     （変えてよいのは <title> の中身だけ）。
     <main> からカートの終わりまでの骨組み（タグ・属性の名前・class と、style・id・href・src・data-e・poster の値）が空の型と同じで、
     タグの間の文字は、空の型で〔…〕だった所のほかは空の型と同じ（空白は数えない。変えてよいのは札だった文字と alt の値だけ）。
     末尾の2つの <script> は、「変えるならここ」から「ここまで」の間と、空の型で〔…〕だった文字以外が空の型と同じ。
     許す違い: OPTS が空の店で「選ぶ所ここから」〜「ここまで」が無い／宣言の段の <video> を、動画が無い時に同じ場所の
     <img data-e="sengen-poster" src="img/sengen-poster.png" alt="…"> に替える（属性はこの3つだけ。alt は無くてもよい。
     違う時は、どの属性が余分・不足かを言う）
  F4 ボタン: .btn_cart_text の文字が全部同じ1つの言葉で、「カートに入れる」「購入する」でない
  F6 届く日数: 「営業日」が出るのは、ボタンの下の行（.wd-purchase-assurance）と FAQ の答え（.hero_question_content・.acdn_content）の中だけ
  F11 見出し: .hero_title の文字に「？」「?」が無く、行（span と、span の外の文字の塊）ごとに12字以内
  F12 名残: 〔 と 〕が 0・画面の文のダッシュ（— ― – の3つ）0・打ち消し線（中身のある <del>・<s>）と「OFF」0・
      ワンドライの言葉（ワンドライ・WANDRY・愛犬・フェロモン・獣医・ペット・犬）0・noindex がある・作業場に 決めた値.md がある・
      TIERS の値段が全部、半角数字だけ（^[0-9]+$）で 0 より大きい
      （画面の文 = 本文の文字・alt/title/aria-label/placeholder の値・スクリプトの '…' と "…" の文字）
  F13 選ぶ所: 設計の 4「色・サイズの案内」（店の印.json の値）が「無し」なら #wdVariant と選ぶ所のコメントが無く OPTS が空。
      「<名前>: A・B・C」なら #wdVariant があり、OPT_NAME と OPTS が同じ名前・同じ数・同じ中身
  T2 値段の見せ方: TIERS が3つで、n:3 があり、いちばん大きい n の fuda が「いちばん人気」
  D2 細長い画像: img/ の絵の縦÷横が 0.4未満・2.5超の物が 0。アイコン・札・ロゴ・kyotsu-* は数えない。
      参考の絵（絵の一覧.tsv の元の大きさ）がもう細長い物も数えない（絵を置く.py が参考の比に切りそろえるので、参考どおりの比になる）
"""
import json, os, re, sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
KATA = os.path.join(HERE, "..", "kata", "index.html")
空の型の絵 = os.path.join(HERE, "..", "kata", "絵の一覧.tsv")
VOID = {"img", "br", "hr", "input", "meta", "link", "source", "wbr", "area", "base", "col", "embed", "track", "param"}
ワンドライの言葉 = ("ワンドライ", "WANDRY", "愛犬", "フェロモン", "獣医", "ペット", "犬")
変える頭, 変える尻 = "/* ===== 変えるならここ", "/* ===== ここまで ===== */"


class 要素:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, attrs, parent, []

    def cls(self): return self.attrs.get("class", "").split()

    def 文字(self): return "".join(k if isinstance(k, str) else k.文字() for k in self.kids)

    def 祖先(self):
        n = self
        while n is not None: yield n; n = n.parent

    def 全部(self):
        for k in self.kids:
            if isinstance(k, 要素): yield k; yield from k.全部()


比べる属性 = ("style", "id", "href", "src", "data-e", "poster")
宣言の絵の属性 = {"data-e", "src", "alt"}


def 字をならす(d): return re.sub(r"\s+", "", d or "")


class 木(HTMLParser):
    """本文の木（script・style の中身は木に入れない）と、骨組みの並び（main からカートの終わりまで）と、<main> の前の並びを作る"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.根 = 要素("#root", {}, None); self.今 = self.根
        self.字 = []          # (文字, 親の要素)
        self.骨 = []          # 骨組みの札: ('s', tag, 属性の名前, class, 比べる属性の値, 前の文字) ／ ('e', tag, 前の文字) ／ ('c', 印の文, 前の文字) ／ ('終', 前の文字)
        self.頭 = []          # <main> の前: ('s', tag, 属性と値) ／ ('e', tag) ／ ('t', 文字) ／ ('c', 文) ／ ('d', 宣言)
        self.骨を取る = False; self.骨が済んだ = False; self.頭を取る = True; self.中身を飛ばす = 0; self.題の中 = False
        self.待つ字 = []; self.絵の問題 = []

    def _骨(self, *t):
        self.骨.append(t + (字をならす("".join(self.待つ字)),)); self.待つ字 = []

    def _開く(self, tag, attrs, 閉じる):
        a = {k: (v or "") for k, v in attrs}
        if tag == "main" and not self.骨が済んだ: self.骨を取る = True; self.頭を取る = False
        if tag == "script" and self.骨を取る and not self.中身を飛ばす:   # カートの後の script で骨組みは終わり
            self._骨("終"); self.骨を取る = False; self.骨が済んだ = True
        if self.頭を取る:
            self.頭.append(("s", tag, tuple(sorted(a.items()))))
            if tag == "title": self.題の中 = True
        if self.骨を取る and tag not in ("script", "style"):
            if tag == "img" and a.get("data-e") == "sengen-poster":
                余分 = sorted(set(a) - 宣言の絵の属性); 不足 = sorted({"data-e", "src"} - set(a))
                if not 余分 and not 不足 and a.get("src") == "img/sengen-poster.png":
                    self._骨("s", "img", "SENGEN-POSTER", "", ())
                else:
                    self.絵の問題.append("宣言の段の <img data-e=\"sengen-poster\"> の属性が違う（使えるのは data-e・src・alt の3つ）: "
                                      + "・".join(([f"余分 {'・'.join(余分)}"] if 余分 else []) + ([f"不足 {'・'.join(不足)}"] if 不足 else [])
                                                 + ([f"src が {a.get('src')}（img/sengen-poster.png にする）"] if a.get("src") and a.get("src") != "img/sengen-poster.png" else [])))
                    self._骨("s", tag, tuple(sorted(a)), a.get("class", ""), tuple((k, a[k]) for k in 比べる属性 if k in a))
            else:
                self._骨("s", tag, tuple(sorted(a)), a.get("class", ""), tuple((k, a[k]) for k in 比べる属性 if k in a))
        if tag in ("script", "style"): self.中身を飛ばす += 1
        e = 要素(tag, a, self.今); self.今.kids.append(e)
        if tag not in VOID and not 閉じる: self.今 = e

    def handle_starttag(self, tag, attrs): self._開く(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._開く(tag, attrs, True)
        if tag in ("script", "style"): self.中身を飛ばす -= 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.中身を飛ばす: self.中身を飛ばす -= 1
        if self.頭を取る:
            self.頭.append(("e", tag))
            if tag == "title": self.題の中 = False
        if self.骨を取る and tag not in ("script", "style") and tag not in VOID: self._骨("e", tag)
        n = self.今
        while n is not None and n.tag != tag: n = n.parent
        if n is not None and n.parent is not None: self.今 = n.parent

    def handle_comment(self, d):
        if self.頭を取る: self.頭.append(("c", d.strip()))
        if self.骨を取る and ("============" in d or "選ぶ所" in d): self._骨("c", d.strip())

    def handle_decl(self, d):
        if self.頭を取る: self.頭.append(("d", d.strip().lower()))

    def handle_data(self, d):
        if self.中身を飛ばす: return
        if self.頭を取る and not self.題の中 and d.strip(): self.頭.append(("t", 字をならす(d)))
        if self.骨を取る: self.待つ字.append(d)
        self.今.kids.append(d)
        if d.strip(): self.字.append((d, self.今))


def 読む(s):
    t = 木(); t.feed(s); t.close(); return t


def スクリプト(s): return re.findall(r"<script\b[^>]*>(.*?)</script>", s, re.S)


def 変えるならここ(js):
    a, b = js.find(変える頭), js.find(変える尻)
    return (js[:a], js[a:b], js[b:]) if a >= 0 and b > a else None


def 札を許す(kata_seg, 店_seg):
    """空の型の部分 kata_seg の〔…〕だけを、店で別の文字に替えてよい。合えば None、違えば最初に違う所の行を返す"""
    片 = re.split(r"〔[^〕]*〕", kata_seg)
    if re.fullmatch(r"[^'\"\n]*?".join(map(re.escape, 片)), 店_seg, re.S): return None
    for i, (x, y) in enumerate(zip(kata_seg.splitlines(), 店_seg.splitlines())):
        if not re.fullmatch(r"[^'\"\n]*?".join(map(re.escape, re.split(r"〔[^〕]*〕", x))), y): return f"{i + 1}行目: 空の型 {x.strip()[:60]} ／ 店 {y.strip()[:60]}"
    return f"行の数が違う（空の型 {len(kata_seg.splitlines())} ／ 店 {len(店_seg.splitlines())}）"


def 骨の説明(t):
    if t[0] == "終": return "（カートの終わり）"
    if t[0] == "c": return f"<!-- {t[1][:30]} -->"
    if t[0] == "e": return f"</{t[1]}>"
    if t[2] == "SENGEN-POSTER": return '<img data-e="sengen-poster" src="img/sengen-poster.png" alt="…">'
    他 = [x for x in t[2] if x != "class"]
    値 = " ".join(f'{k}="{v[:50]}"' for k, v in t[4] if k != "class")
    return f"<{t[1]}" + (f' class="{t[3]}"' if t[3] else "") + (f" {値}" if 値 else "") + (f" 属性 {','.join(他)}" if 他 else "") + ">"


def 頭の説明(t):
    if t[0] == "s": return f"<{t[1]}" + "".join(f' {k}="{v[:70]}"' for k, v in t[2]) + ">"
    if t[0] == "e": return f"</{t[1]}>"
    if t[0] == "t": return f"文字「{t[1][:40]}」"
    if t[0] == "d": return f"<!{t[1]}>"
    return f"<!-- {t[1][:30]} -->"


def 字が合う(k, x):
    """空の型の文字 k（空白を除いた物）の〔…〕だけを、店で別の文字に替えてよい"""
    if "〔" not in k: return k == x
    return re.fullmatch(r"[\s\S]*?".join(map(re.escape, re.split(r"〔[^〕]*〕", k))), x) is not None


def 骨が合う(x, y):
    return len(x) == len(y) and all(a[:-1] == b[:-1] and 字が合う(b[-1], a[-1]) for a, b in zip(x, y))


def 選ぶ所を除く(骨k):
    a = next((i for i, t in enumerate(骨k) if t[0] == "c" and "選ぶ所ここから" in t[1]), None)
    b = next((i for i, t in enumerate(骨k) if t[0] == "c" and "選ぶ所ここまで" in t[1]), None)
    if a is None or b is None or b + 1 >= len(骨k): return 骨k
    次 = 骨k[b + 1]
    return 骨k[:a] + [次[:-1] + (骨k[a][-1] + 次[-1],)] + 骨k[b + 2:]   # 消した所の前後の文字はつながる


def F1(s, k, ts, tk):
    bad = []
    st_s = re.findall(r"<style\b[^>]*>.*?</style>", s, re.S); st_k = re.findall(r"<style\b[^>]*>.*?</style>", k, re.S)
    if len(st_s) != len(st_k): bad.append(f"<style> の数が {len(st_s)}（空の型は {len(st_k)}）")
    else:
        for i, (x, y) in enumerate(zip(st_s, st_k)):
            if x != y:
                j = next(n for n in range(min(len(x), len(y)) + 1) if n >= min(len(x), len(y)) or x[n] != y[n])
                bad.append(f"{i + 1}個目の <style>（{re.match(r'<style[^>]*>', y).group(0)[:60]}）が空の型と違う: 空の型 「{y[max(0, j - 20):j + 20]}」 ／ 店 「{x[max(0, j - 20):j + 20]}」"); break
    # <main> の前（<head> と <body> のタグ。変えてよいのは <title> の中身だけ）
    if ts.頭 != tk.頭:
        x, y = ts.頭, tk.頭
        j = next((n for n in range(min(len(x), len(y))) if x[n] != y[n]), min(len(x), len(y)))
        bad.append(f"<main> の前（<head> と <body> のタグ）が空の型と違う（{j + 1} 個目: 空の型 {頭の説明(y[j]) if j < len(y) else '（終わり）'} ／ 店 {頭の説明(x[j]) if j < len(x) else '（終わり）'}。変えてよいのは <title> の中身だけ）")
    # 骨組み
    bad += ts.絵の問題
    骨k = list(tk.骨)
    if not any(t[0] == "c" and "選ぶ所ここから" in t[1] for t in ts.骨): 骨k = 選ぶ所を除く(骨k)
    候補 = [骨k]
    v = next((i for i, t in enumerate(骨k) if t[0] == "s" and t[1] == "video"), None)
    if v is not None and v + 1 < len(骨k) and 骨k[v + 1][:2] == ("e", "video"):
        候補.append(骨k[:v] + [("s", "img", "SENGEN-POSTER", "", (), 骨k[v][-1])] + 骨k[v + 2:])
    if not any(骨が合う(ts.骨, c) for c in 候補):
        x = ts.骨; y = 候補[-1] if any(t[0] == "s" and t[2] == "SENGEN-POSTER" for t in x) else 候補[0]
        j = next((n for n in range(min(len(x), len(y))) if not (x[n][:-1] == y[n][:-1] and 字が合う(y[n][-1], x[n][-1]))), min(len(x), len(y)))
        段 = next((t[1] for t in reversed(x[:j + 1]) if t[0] == "c" and "====" in t[1]), "?").strip("= ").strip()
        if j < len(x) and j < len(y) and x[j][:-1] == y[j][:-1]:
            bad.append(f"<main> の中の文字が空の型と違う（段「{段}」の {j + 1} 個目の札 {骨の説明(y[j])} の前: 空の型 「{y[j][-1][:60]}」 ／ 店 「{x[j][-1][:60]}」。変えてよいのは〔…〕だった文字と alt の値だけ）")
        else:
            bad.append(f"<main> の中の骨組みが空の型と違う（段「{段}」の {j + 1} 個目の札: 空の型 {骨の説明(y[j]) if j < len(y) else '（終わり）'} ／ 店 {骨の説明(x[j]) if j < len(x) else '（終わり）'}）")
    # 末尾の script
    sc_s, sc_k = スクリプト(s), スクリプト(k)
    if len(sc_s) != len(sc_k): bad.append(f"<script> の数が {len(sc_s)}（空の型は {len(sc_k)}）")
    else:
        for i, (x, y) in enumerate(zip(sc_s, sc_k)):
            ky, kx = 変えるならここ(y), 変えるならここ(x)
            if ky:
                if not kx: bad.append(f"{i + 1}個目の <script> に「変えるならここ」〜「ここまで」の印が無い"); continue
                for 名, a, b in (("「変えるならここ」より前", ky[0], kx[0]), ("「ここまで」より後", ky[2], kx[2])):
                    r = 札を許す(a, b)
                    if r: bad.append(f"{i + 1}個目の <script> の{名}が空の型と違う（{r}）")
            else:
                r = 札を許す(y, x)
                if r: bad.append(f"{i + 1}個目の <script> が空の型と違う（{r}）")
    return bad, f"<style> {len(st_k)}個・<main> の前 {len(tk.頭)}札・骨組み {len(tk.骨)}札・<script> {len(sc_k)}つ"


def 画面の文(t, s):
    out = [d for d, _ in t.字]
    for e in t.根.全部():
        for k in ("alt", "title", "aria-label", "placeholder"):
            if e.attrs.get(k): out.append(e.attrs[k])
    for js in スクリプト(s):
        js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        一重 = r"'((?:[^'\\\n]|\\.)*)'"
        out += re.findall(一重, js)
        out += re.findall(r'"((?:[^"\\\n]|\\.)*)"', re.sub(一重, "''", js))   # 二重引用符の文字も（一重の中の " は数えない）
    return "\n".join(out)


def F4(t):
    字 = [re.sub(r"\s+", "", e.文字()) for e in t.根.全部() if "btn_cart_text" in e.cls()]
    bad = []
    if not 字: bad.append(".btn_cart_text が無い")
    elif len(set(字)) > 1: bad.append(f"ボタンの言葉が {len(set(字))} 種（全部同じ1つの言葉にする）: " + " ／ ".join(f"{w}×{字.count(w)}" for w in sorted(set(字), key=字.count, reverse=True)[:4]))
    elif 字[0] in ("カートに入れる", "購入する") or re.fullmatch(r"(カートに入れる|購入する)[。！!]?", 字[0]): bad.append(f"ボタンの言葉が「{字[0]}」（読み手の望む結果の文にする）")
    return bad, f"ボタン {len(字)} 個が「{字[0] if 字 else ''}」"


def F6(t, s):
    bad = []
    場所 = ("wd-purchase-assurance", "hero_question_content", "acdn_content")
    n = 0
    for d, p in t.字:
        if "営業日" not in d: continue
        n += 1
        if not any(c in a.cls() for a in p.祖先() for c in 場所): bad.append(f"「営業日」がボタンの下の行と FAQ の答えの外にある: {d.strip()[:40]}")
    for js in スクリプト(s):
        h = 変えるならここ(js)
        if h and "営業日" in h[1]: bad.append("「営業日」が末尾のスクリプトの「変えるならここ」の値にある（セットの札などに届く日数を書かない）")
    return bad, f"「営業日」{n} か所"


def F11(t):
    h = [e for e in t.根.全部() if "hero_title" in e.cls()]
    if not h: return [".hero_title が無い"], ""
    bad, 行 = [], []
    for k in h[0].kids:
        w = (k if isinstance(k, str) else ("" if k.tag == "br" else k.文字()))
        w = re.sub(r"\s", "", w)
        if w: 行.append(w)
    全 = "".join(行)
    if re.search(r"[？?]", 全): bad.append(f"見出しが問いの文（？）: {全[:30]}")
    for w in 行:
        if len(w) > 12: bad.append(f"見出しの行が {len(w)} 字（12字以内）: {w[:30]}")
    return bad, f"{len(行)} 行・いちばん長い行 {max(map(len, 行)) if 行 else 0} 字"


def TIERS(s):
    m = re.search(r"var TIERS\s*=\s*\[(.*?)\];", s, re.S)
    if not m: return None
    out = []
    for x in re.finditer(r"\{\s*n\s*:\s*(\d+)\s*,\s*price\s*:\s*(.*?)\s*,\s*fuda\s*:\s*'([^']*)'", m.group(1)):
        p = re.sub(r"^Number\(\s*['\"]?|['\"]?\s*\)$", "", x.group(2).strip())
        v = int(p) if re.fullmatch(r"[0-9]+", p) else None   # 半角数字だけ（全角・小数・式は認めない）
        out.append({"n": int(x.group(1)), "price": v, "price_src": x.group(2), "fuda": x.group(3)})
    return out


def F12(t, s, 店):
    bad = []
    札 = re.findall(r"〔[^〕]{0,20}〕?", s)
    n札 = s.count("〔") + s.count("〕")
    if n札: bad.append(f"〔 と 〕が {n札} 個残っている（例: {'・'.join(sorted(set(札))[:5])}）")
    文 = 画面の文(t, s)
    ダッシュ = ("—", "―", "–")
    n = sum(文.count(c) for c in ダッシュ)
    if n: bad.append(f"画面の文にダッシュ（— ― –）が {n} 個ある（読点か句点で言い直す）: " + "／".join(sorted({l.strip()[:30] for l in 文.splitlines() if any(c in l for c in ダッシュ)})[:3]))
    消し = [m.group(0)[:40] for m in re.finditer(r"<(del|s)\b[^>]*>(.*?)</\1>", s, re.S | re.I) if re.sub(r"<[^>]+>|\s", "", m.group(2))]
    if 消し: bad.append(f"打ち消し線が {len(消し)} か所（値段は割引なし）: {消し[0]}")
    if "OFF" in 文: bad.append(f"「OFF」が {文.count('OFF')} か所ある")
    出た = {w: 文.count(w) for w in ワンドライの言葉 if w in 文}
    if "WANDRY" not in 出た and re.search(r"wandry", 文, re.I): 出た["WANDRY"] = len(re.findall(r"wandry", 文, re.I))
    if 出た: bad.append("ワンドライの言葉が残っている: " + "・".join(f"{w}×{n}" for w, n in 出た.items()) + "（例: " + "／".join(sorted({l.strip()[:30] for l in 文.splitlines() if any(w in l for w in 出た)})[:3]) + "）")
    if "noindex" not in s: bad.append("noindex が無い")
    if not os.path.exists(os.path.join(店, "決めた値.md")): bad.append("決めた値.md が無い（Claude が決めた数字・人・声を書く）")
    ts = TIERS(s)
    if not ts: bad.append("TIERS が読めない（var TIERS = [{n:…, price:…, fuda:'…', kind:'…'}, …]）")
    else:
        for x in ts:
            if x["price"] is None: bad.append(f"TIERS の {x['n']} のセットの値段が半角数字だけでない: {x['price_src'][:30]}")
            elif x["price"] <= 0: bad.append(f"TIERS の {x['n']} のセットの値段が 0 より大きくない: {x['price_src'][:30]}")
    return bad, "札・ダッシュ・打ち消し線・OFF・ワンドライの言葉 0、noindex・決めた値.md あり、値段 " + ("・".join(f"{int(x['price'])}" for x in ts if x["price"]) if ts else "")


def 案内の値(店):
    try:
        印 = json.load(open(os.path.join(店, "店の印.json"), encoding="utf-8"))
        v = 印["値"].get("色・サイズの案内", "").strip()
        if v: return v
        p = 印.get("設計", "")
    except Exception:
        p = ""
    for q in (p, os.path.join(店, "移植表_店の設計.md")):
        if q and os.path.exists(q):
            m = re.search(r"^\|\s*色・サイズの案内\s*\|([^|]*)\|", open(q, encoding="utf-8").read(), re.M)
            if m and m.group(1).strip(): return m.group(1).strip()
    return ""


def F13(s, 店):
    値 = 案内の値(店)
    if not 値: return ["設計の 4「色・サイズの案内」の値が無い（店の印.json か 店の設計.md に書く）"], ""
    m = re.search(r"var OPTS\s*=\s*\[(.*?)\];", s, re.S); 出す = re.findall(r"'([^']*)'", m.group(1)) if m else []
    mn = re.search(r"var OPT_NAME\s*=\s*'([^']*)'", s); 名 = mn.group(1) if mn else ""
    ある = 'id="wdVariant"' in s; 印 = "選ぶ所ここから" in s or "選ぶ所ここまで" in s
    bad = []
    if 値.startswith("無し"):
        if ある or 印: bad.append("選ぶ物が無い商品なのに、選ぶ所（#wdVariant か「選ぶ所ここから〜ここまで」のコメント）が残っている（ここからここまでを消す）")
        if 出す: bad.append(f"選ぶ物が無い商品なのに OPTS が {len(出す)} 個ある（[] にする）")
        return bad, "選ぶ物なし"
    mm = re.match(r"\s*([^:：]+?)\s*[:：]\s*([^（(]+)", 値)
    if not mm: return [f"設計の「色・サイズの案内」が「無し」か「<名前>: A・B・C」の形でない: {値[:40]}"], ""
    要る名 = mm.group(1).strip(); 要る = [x.strip() for x in re.split(r"[・、,]", mm.group(2)) if x.strip()]
    if not ある: bad.append(f"選ぶ物が {len(要る)} 個ある商品なのに、選ぶ所（#wdVariant）が無い")
    if 名 != 要る名: bad.append(f"OPT_NAME が設計と違う（設計 {要る名} ／ ページ {名}）")
    if 出す != 要る: bad.append(f"OPTS が設計と合わない（設計 {len(要る)} 個: {'・'.join(要る)} ／ ページ {len(出す)} 個: {'・'.join(出す)}）")
    return bad, f"{要る名}: {'・'.join(要る)}"


def T2(s):
    ts = TIERS(s)
    if not ts: return ["TIERS が読めない"], ""
    bad = []
    if len(ts) != 3: bad.append(f"TIERS が {len(ts)} つ（3つにする）")
    if not any(x["n"] == 3 for x in ts): bad.append("TIERS に n:3 が無い（いちばん大きいセットは 3）")
    if ts:
        大 = max(ts, key=lambda x: x["n"])
        if 大["fuda"] != "いちばん人気": bad.append(f"いちばん大きいセット（{大['n']}）の札が「{大['fuda']}」（「いちばん人気」にする）")
    return bad, "セット " + "・".join(str(x["n"]) for x in ts) + "、いちばん大きいセットが「いちばん人気」"


def D2(店):
    try: from PIL import Image
    except Exception: return ["PIL が無い（pip install pillow）"], ""
    p = os.path.join(店, "絵の一覧.tsv")
    if not os.path.exists(p): p = 空の型の絵
    行 = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8")][1:]
    種類 = {r[0]: r for r in 行 if r and r[0]}
    bad, 見た, 外した = [], 0, 0
    img = os.path.join(店, "img")
    for f in sorted(os.listdir(img)) if os.path.isdir(img) else []:
        名, ext = os.path.splitext(f)
        if f.startswith("kyotsu-") or ext.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif"): continue
        r = 種類.get(名)
        if r and len(r) > 2 and r[2] in ("アイコン", "札", "ロゴ"): continue
        try: w, h = Image.open(os.path.join(img, f)).size
        except Exception: continue
        q = h / w if w else 0
        if 0.4 <= q <= 2.5: 見た += 1; continue
        m = re.search(r"(\d+)x(\d+)", r[3]) if r and len(r) > 3 else None
        if m and not 0.4 <= int(m.group(2)) / int(m.group(1)) <= 2.5: 外した += 1; continue
        bad.append(f"細長い画像 {f}（縦÷横 {q:.2f}。0.4〜2.5 にする）")
    return bad, f"{見た} 枚を見た（参考がもう細長いので数えなかった {外した} 枚）"


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    店 = argv[1] if os.path.isdir(argv[1]) else os.path.dirname(os.path.abspath(argv[1]))
    try:
        s = open(os.path.join(店, "index.html"), encoding="utf-8").read()
        k = open(KATA, encoding="utf-8").read()
    except Exception as e:
        print(f"読めなかった: {e}"); return 2
    ts, tk = 読む(s), 読む(k)
    箱 = [("F1 骨組み", F1(s, k, ts, tk)), ("F4 ボタン", F4(ts)), ("F6 届く日数", F6(ts, s)), ("F11 見出し", F11(ts)),
          ("F12 名残", F12(ts, s, 店)), ("F13 選ぶ所", F13(s, 店)), ("T2 値段の見せ方", T2(s)), ("D2 細長い画像", D2(店))]
    落ちた = 0
    for 名, (bad, 説明) in 箱:
        if bad:
            落ちた += 1; print(f"× {名}: 落ちた {len(bad)} 件")
            for x in bad: print("  - " + x)
        else:
            print(f"○ {名}: 通った（{説明}）")
    print("通った" if not 落ちた else f"落ちた箱 {落ちた}")
    return 1 if 落ちた else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
