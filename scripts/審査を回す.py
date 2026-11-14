#!/usr/bin/env python3
"""店を編集長の審査に出し、店のフォルダに 審査_<回>.md を書く。部屋（team-room）も advertorial-automation も要らない。
pdp-tsukuru と Claude Code（`claude` コマンド）だけで回る（2026-10-19 本人「それぞれで作ったら良くない？」）。

使い方: python3 審査を回す.py <店のフォルダ> [--待つ分 40] [--モデル opus]
  `claude` コマンドが使えない時（契約・支払いで起動できない）: 作った本人でない Opus の Agent で代える。
    1) python3 審査を回す.py <店のフォルダ> --頼む文だけ   → 出す前の確かめを通し、審査_<回>_頼む文.txt を書いて終了コード 5
    2) その文をそのまま Agent（model: opus。読むだけ）に渡し、返事の全文を 審査_<回>_返事.txt に書く
    3) python3 審査を回す.py <店のフォルダ> --返事 審査_<回>_返事.txt   → 判定を読んで 審査_<回>.md を書く（終了コードは同じ）

出す前に道具が自分で確かめる物（通らなければ出さずに終了コード2）:
  - 前の回が FAIL なら、直し_<前の回>.md に「探した語」の行が指摘の件数以上ある（1か所だけ直して別の所と食い違うのを止める）
  - 前の回から index.html も img/ も変わっていなければ出し直さない
  - scripts/店の検査を回す.py が全部0（検査の結果.md を指紋つきで書く）。「検査が落ちた」（終了コード 1 の道具）と
    「検査が回らなかった」（終了コード 2 以上の道具）を分けて言う
判定の読み方: 審査役の返事の最後の {"decision" から括弧の対応を数えて JSON を切り出す。読めない時は元の文を 審査_<回>_全文.md に残し、
  「判定は出たが読めない」と言って終了コード 2
指紋: 店の指紋.py（index.html と img/ の直下の画像と動画の 12字。店の検査を回す.py・参考と並べる.mjs と同じ）
審査のしかた: 書いた本人でない Claude（既定 Opus）を `claude -p` で1つ起こし、references/ストア担当の審査.md の「## ストア担当の関門」「## 審査の決まり」と、並べて見る指示文.md の「数えない物」の表で
  店のフォルダの物を読ませる。読むだけで、店の物は書き換えさせない（Edit・Write・Bash・Agent を使わせない）。
回し方（SKILL.md の手順11。回数の上限は無い）:
  1. この道具を走らせる。PASS なら終了コード0で終わり
  2. FAIL なら終了コード1。審査_<回>.md を全部直し、直し_<回>.md に1行ずつ書く。直した所を書いた本人でない Opus に照らし合わせさせ（references/照らし合わせの指示文.md）、照らし合わせ_<回>.txt が「食い違い 0件」になったら 1 へ
終了コード: 0 PASS（指摘なし）／ 3 PASS だが書き方の指摘あり（審査_<回>.md を直して機械の検査を通す）／ 1 FAIL ／ 2 出せなかった
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from 店の指紋 import 店の指紋   # noqa: E402  店の検査を回す.py・参考と並べる.mjs と同じ指紋
PDP = os.path.dirname(HERE)
決まりの書類 = os.path.join(PDP, "references", "ストア担当の審査.md")


def 引数(argv, 名, 既定):
    return argv[argv.index(名) + 1] if 名 in argv and argv.index(名) + 1 < len(argv) else 既定


def 決まり():
    """ストア担当の審査.md の「## ストア担当の関門」と「## 審査の決まり」の2節（審査の決まりが関門を指すので両方渡す）"""
    t = open(決まりの書類, encoding="utf-8").read()
    節 = []
    for 名 in ("ストア担当の関門", "審査の決まり"):
        m = re.search(r"^## " + 名 + r"\s*$(.*?)(?=^## |\Z)", t, re.M | re.S)
        if m: 節.append(f"### {名}\n" + m.group(1).strip())
    # 見た目の行が指す「数えない物」の表も渡す（審査役がセールの帯・犬の飾りが無い事で落とさないように。2026-11-14）
    並 = os.path.join(os.path.dirname(決まりの書類), "並べて見る指示文.md")
    if os.path.exists(並):
        m = re.search(r"^## 数えない物.*?$(.*?)(?=^## |\Z)", open(並, encoding="utf-8").read(), re.M | re.S)
        if m: 節.append("### 数えない物（見た目で落とさない物）\n" + m.group(1).strip())
    return "\n\n".join(節)


def 同じ所(理由, 前の理由):
    """前の回の指摘と同じ箱（A2・F12 のような番号）か同じ書き出しの指摘に印を付ける。同じ所で2回落ちたら、直す前に手順か道具を直す"""
    def 箱(x): return set(re.findall(r"\b[A-FT]\d{1,2}\b", x))
    out = []
    for x in 理由:
        同じ = any((箱(x) & 箱(y)) or x[:20] == y[:20] for y in 前の理由)
        out.append(("【前の回も同じ所】" if 同じ else "") + x)
    return out


def 指紋(店):
    """店の指紋.py の指紋（index.html と img/ の直下の画像と動画）。絵だけを直した回も「直した」と数える"""
    return 店の指紋(店)


def 判定を切り出す(結果):
    """最後の {"decision" から括弧の対応を数えて JSON を1つ切り出す（文字列の中の括弧は数えない）。読めなければ None"""
    i = 結果.rfind('{"decision"')
    if i < 0:
        m = list(re.finditer(r'\{\s*"decision"', 結果))
        if not m: return None
        i = m[-1].start()
    深さ, 中, 逃 = 0, False, False
    for j in range(i, len(結果)):
        c = 結果[j]
        if 中:
            if 逃: 逃 = False
            elif c == "\\": 逃 = True
            elif c == '"': 中 = False
            continue
        if c == '"': 中 = True
        elif c == "{": 深さ += 1
        elif c == "}":
            深さ -= 1
            if 深さ == 0:
                try: return json.loads(結果[i:j + 1])
                except Exception: return None
    return None


class 読めない判定(Exception):
    def __init__(self, 全文): super().__init__("判定は出たが読めない"); self.全文 = 全文


def 前の回(店):
    回たち = sorted(int(m.group(1)) for f in os.listdir(店) for m in [re.fullmatch(r"審査_(\d+)\.md", f)] if m)
    if not 回たち:
        return 0, None, 0, None
    n = 回たち[-1]
    t = open(os.path.join(店, f"審査_{n}.md"), encoding="utf-8").read()
    判 = "FAIL" if re.search(r"^判定: FAIL", t, re.M) else "PASS"
    件 = len(re.findall(r"^\d+\. ", t, re.M))
    紋 = re.search(r"^指紋: (\w+)", t, re.M)
    return n, 判, 件, 紋.group(1) if 紋 else None


def 絵を並べる(店):
    """画像の置き場.md の絵を、番号つきで 16 枚ずつ並べた1枚（絵の一覧_<n>.jpg）にする。審査役は先にこれを全部見る"""
    md = os.path.join(店, "画像の置き場.md")
    if not os.path.exists(md):
        return []
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return []
    絵, 見た, 列 = [], set(), 0
    for l in open(md, encoding="utf-8"):
        if not l.startswith("|"):
            continue
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if "名前" in c: 列 = c.index("名前"); continue   # 頭の行で「名前」の列を決める（1列目が # の表でも読む。2026-11-14: 1列目を名前と決め打ちにして、一覧の絵が1枚も出来なかった）
        if 列 >= len(c): continue
        名 = c[列]; f = f"img/{名}.png"
        if not 名 or f in 見た or not os.path.exists(os.path.join(店, f)):
            continue
        見た.add(f); 絵.append((名, f))
    字 = None
    for f in ("~/Library/Fonts/NotoSansJP.ttf", "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        try:
            字 = ImageFont.truetype(os.path.expanduser(f), 20); break
        except Exception:
            pass
    字 = 字 or ImageFont.load_default()
    W, 列, 段 = 340, 4, 4
    out = []
    for k in range(0, len(絵), 列 * 段):
        組 = 絵[k:k + 列 * 段]
        sh = Image.new("RGB", (列 * W, ((len(組) + 列 - 1) // 列) * (W + 30)), "white"); d = ImageDraw.Draw(sh)
        for i, (番, f) in enumerate(組):
            im = Image.open(os.path.join(店, f)).convert("RGB"); im.thumbnail((W - 8, W - 8))
            x, y = (i % 列) * W, (i // 列) * (W + 30)
            sh.paste(im, (x + 4, y + 4)); d.text((x + 6, y + W), f"{番}"[:30], fill="black", font=字)
        名 = f"絵の一覧_{k // (列 * 段) + 1}.jpg"
        sh.save(os.path.join(店, 名), quality=82); out.append(名)
    return out


def 頼む文(店, 回, 一覧):
    # 照らし合わせは、前の回の審査が FAIL の時だけ見せる（PASS で書き方だけ直した回は照らし合わせを回さない）
    前p = os.path.join(店, f"審査_{回 - 1}.md")
    前がFAIL = os.path.exists(前p) and any(l.startswith("判定: FAIL") for l in open(前p, encoding="utf-8"))
    並べ = sorted((int(m.group(1)), f) for f in os.listdir(店) for m in [re.fullmatch(r"並べて見た_(\d+)\.txt", f)] if m)
    読む = ["index.html", "検査の結果.md"] + 一覧 + (["並べた絵/一覧.md（並べた絵/ の PNG。左が参考・右が店）"] if os.path.exists(os.path.join(店, "並べた絵", "一覧.md")) else []) + ([並べ[-1][1]] if 並べ else []) + sorted(f for f in os.listdir(店) if f.startswith("移植表") and f.endswith(".md")) + \
        [f for f in ("画像の置き場.md", "決めた値.md", "絵と説明の一覧.tsv", "報告.md", f"直し_{回 - 1}.md") + ((f"照らし合わせ_{回 - 1}.txt",) if 前がFAIL else ()) if os.path.exists(os.path.join(店, f))]
    return f"""あなたは編集長。店（商品ページ）を作った本人ではない。この店の {回} 回目の審査をする。
店のフォルダ（今いる所）: {店}
読む物（全部読む。絵は 絵の一覧_<n>.jpg を先に全部見て、気になった絵だけ img/ を1枚ずつ開く）: {"、".join(読む)}
スキルの置き場（決まりの書類が指す SKILL.md・references/ はここ）: {PDP}

## 審査の決まり
{決まり()}

## 答え方
店の物は1つも書き換えない。読んで照らすだけ。
最後に、次の形の JSON を1つだけ書いて終わる（前後に説明を書いてよいが、JSON は最後に1つ）:
{{"decision": "PASS" か "FAIL", "reasons": ["指摘1件を1文で。どの段・どの文や絵・何がどう違うか・何に合わせるか", ...]}}
FAIL: 最終確認 A〜E・T・F の箱に理由の無い × が1つでもある、数字・名前・場面が書類の間で食い違う、決まりに外れた絵や文がある時。
PASS で reasons が空: 直す所が無い。PASS で reasons あり: 合格だが書き方だけ直す所がある（再審査は要らない程度の物だけ）。"""


def 審査役(店, 文, 分, モデル):
    r = subprocess.run(
        ["claude", "-p", 文, "--model", モデル, "--output-format", "json", "--add-dir", PDP,
         "--allowedTools", "Read", "Glob", "Grep",
         "--disallowedTools", "Edit", "Write", "NotebookEdit", "Bash", "Agent", "WebFetch", "WebSearch"],
        cwd=店, capture_output=True, text=True, timeout=分 * 60)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[-600:])
    try: 結果 = json.loads(r.stdout).get("result", "")
    except Exception: 結果 = r.stdout
    d = 判定を切り出す(結果)
    if not isinstance(d, dict) or d.get("decision") not in ("PASS", "FAIL") or not isinstance(d.get("reasons", []), list):
        raise 読めない判定(結果)
    return d["decision"], [str(x) for x in d.get("reasons") or []], 結果


def 書く(店, 回, 判, 理由, 紋):
    頭 = ["読む人: この店を直す Claude。", "読む時: 直す前に全部。", "読まなくていい条件: なし。", "", f"指紋: {紋}", ""]
    探す = ("指摘1件ごとに、名前・数字・場面の語を `grep -n <語> index.html 移植表*.md 画像の置き場.md 決めた値.md` で全部探してそろえ、"
          f"直し_{回}.md の各行に「探した語: <語>／見つかった所: <数>／全部そろえた」を書く。")
    if 判 == "FAIL":
        行 = [f"# 編集長の審査 {回}回目"] + [""] + 頭 + [f"判定: FAIL（{len(理由)}件）。全部直してから、もう一度 `審査を回す.py` を走らせる。回数の上限は無い。", "", 探す, ""]
    else:
        行 = [f"# 編集長の審査 {回}回目（合格）"] + [""] + 頭 + [f"判定: PASS。" + (f"下の {len(理由)} 件は書き方の指摘。全部直し、機械の検査（`scripts/店の検査を回す.py`）だけ通す。再審査には出さない。" if 理由 else "直す所なし。"), ""] + ([探す, ""] if 理由 else [])
    前p = os.path.join(店, f"審査_{回 - 1}.md")
    前の理由 = [re.sub(r"^\d+\.\s*(【前の回も同じ所】)?", "", l).strip() for l in open(前p, encoding="utf-8") if re.match(r"^\d+\.\s", l)] if os.path.exists(前p) else []
    理由 = 同じ所(理由, 前の理由)
    if any(x.startswith("【前の回も同じ所】") for x in 理由):
        行 += ["【前の回も同じ所】の付いた指摘は、直す前に、その箱を作る手順に「やる事」を1行入れて止める検査か見本に結ぶ（SKILL.md「直しの入れ方」）。", ""]
    行 += [f"{i}. {x}" for i, x in enumerate(理由, 1)]
    open(os.path.join(店, f"審査_{回}.md"), "w", encoding="utf-8").write("\n".join(行) + "\n")


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    店 = os.path.abspath(argv[1]); 分 = int(引数(argv, "--待つ分", "40")); モデル = 引数(argv, "--モデル", "opus")
    if not os.path.exists(os.path.join(店, "index.html")):
        print("index.html が無い:", 店); return 2
    if not os.path.exists(決まりの書類):
        print("審査の決まりが無い:", 決まりの書類); return 2
    前, 前の判, 前の件, 前の紋 = 前の回(店)
    回 = 前 + 1; 紋 = 指紋(店)
    if 前 and 前の紋 == 紋:
        print(f"{前}回目から index.html も img/ も変わっていない。出し直さない（審査_{前}.md を直す）"); return 2
    if 前の判 == "FAIL":
        直し = os.path.join(店, f"直し_{前}.md")
        探した = sum(1 for l in open(直し, encoding="utf-8") if "探した語" in l) if os.path.exists(直し) else 0
        if 探した < 前の件:
            print(f"直し_{前}.md に「探した語」の行が {探した} 行（{前}回目の指摘は {前の件} 件）。指摘1件ごとに書いてから出す"); return 2
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "店の検査を回す.py"), 店], capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        print("検査が回らなかった: 店の検査を回す.py が60分で終わらない。審査には出さない"); return 2
    if r.returncode != 0:
        行 = [re.match(r"^(.*): 終了コード (\d+)$", l) for l in r.stdout.splitlines()]
        落 = [m.group(1) for m in 行 if m and m.group(2) == "1"]
        回らない = [m.group(1) for m in 行 if m and int(m.group(2)) >= 2]
        結果の場所 = os.path.join(店, '検査の結果.md')
        if 落: print(f"検査が落ちた（{'・'.join(落)}）。審査には出さない。{結果の場所} を見て直す")
        if 回らない: print(f"検査が回らなかった（{'・'.join(回らない)}）。審査には出さない。道具が動く形にしてから回す（{結果の場所}）")
        if not 落 and not 回らない: print(f"検査が回らなかった（終了コード {r.returncode}）: {(r.stdout + r.stderr).strip()[-300:]}")
        return 2
    一覧 = 絵を並べる(店)
    print(f"{回}回目を審査役（{モデル}）に出した。判定を待つ（最大 {分} 分）")
    文 = 頼む文(店, 回, 一覧); 返事 = 引数(argv, "--返事", "")
    if "--頼む文だけ" in argv:
        q = os.path.join(店, f"審査_{回}_頼む文.txt"); open(q, "w", encoding="utf-8").write(文 + "\n")
        print(f"頼む文を書いた: {q}。作った本人でない Opus の Agent（読むだけ）にこのまま渡し、返事の全文を 審査_{回}_返事.txt に書いてから --返事 で読ませる"); return 5
    try:
        if 返事:
            rp = 返事 if os.path.isabs(返事) else os.path.join(店, 返事)
            if not os.path.exists(rp): print("返事のファイルが無い:", rp); return 2
            全文 = open(rp, encoding="utf-8").read(); d = 判定を切り出す(全文)
            if not isinstance(d, dict) or d.get("decision") not in ("PASS", "FAIL") or not isinstance(d.get("reasons", []), list): raise 読めない判定(全文)
            判, 理由 = d["decision"], [str(x) for x in d.get("reasons") or []]
        else:
            判, 理由, 全文 = 審査役(店, 文, 分, モデル)
    except subprocess.TimeoutExpired:
        print(f"{分} 分の間に判定が出なかった。--待つ分 を延ばしてもう一度走らせる"); return 2
    except 読めない判定 as e:
        p = os.path.join(店, f"審査_{回}_全文.md")
        open(p, "w", encoding="utf-8").write(e.全文 + "\n")
        print(f"判定は出たが読めない（最後の {{\"decision\" … }} が JSON として読めない）。元の文: {p}"); return 2
    except Exception as e:
        print("審査役が判定を出せなかった:", e, "／ `claude` コマンドが起動できない時は --頼む文だけ と --返事 で、Opus の Agent に代える（頭の使い方）"); return 2
    open(os.path.join(店, f"審査_{回}_全文.md"), "w", encoding="utf-8").write(全文 + "\n")
    書く(店, 回, 判, 理由, 紋)
    if 判 == "FAIL":
        print(f"FAIL（{回}回目・{len(理由)}件）。{os.path.join(店, f'審査_{回}.md')} を直してから、もう一度走らせる"); return 1
    if 理由:
        print(f"PASS（{回}回目）。書き方の指摘 {len(理由)} 件を 審査_{回}.md に書いた。直して機械の検査を通すまで終わりではない"); return 3
    print(f"PASS（{回}回目）"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
