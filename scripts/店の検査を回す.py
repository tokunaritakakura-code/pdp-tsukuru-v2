#!/usr/bin/env python3
"""店の機械の検査を全部回し、店のフォルダに 検査の結果.md（店の指紋つき）を書く（最終確認 A2・A4・C1・C2・D1）。
審査の箱（scripts/審査を回す.py）が出す前にこれを呼ぶ。手で回してもよい。
検査の前に、店の印.json の「設計」が指す 店の設計.md を、店のフォルダの 移植表_店の設計.md に写す（審査役が読む写し）。

使い方: python3 店の検査を回す.py <店のフォルダ>
回す順: 設計の写し → 照らし合わせ（いちばん新しい 直し_<回>.md の回の審査が FAIL の時だけ。照らし合わせ_<回>.txt の1行目が「食い違い 0件」）
        → 設計の検査（店の印.json の「設計」が指す 店の設計.md を写した 移植表_店の設計.md と 店の印.json。印が読めない・設計のパスが無い時は終了コード 2）
        → 絵を置く.py（置く・突き合わせ） → 他社の計測タグ → 店の仕上がり検査
        → 面の数字（作業場に 広告の文字.txt がある時だけ。--広告 広告の文字.txt --店 index.html。店の設計.md の「1 来た人」の「どの記事から」に
          http で始まる URL があれば --記事 <URL> も足す。無ければ「対象外（広告の文字.txt が無い）」で通す）
        → lint（390・1440。scripts/lint.mjs。その場で http.server を立てる） → 横送りの往復（往復とカート.mjs --カートなし）
        → 並べて見た結果（作業場の 並べて見た_<回>.txt のいちばん新しい物の1行目が「安く見える所 0件」で、
          2行目の「指紋: <12字>」＝ 並べた絵/指紋.txt ＝ 今の店の指紋、の3つが同じ）
指紋: 店の指紋.py の 店の指紋（index.html と img/ の直下の画像と動画。参考と並べる.mjs・審査を回す.py と同じ値）
道具が時間切れ・起動できない（node が無い・例外）時は、その道具を終了コード 2 の行にして最後まで回す。
検査の結果.md: 道具ごとに、「落ちた」の行（落ち・×・「- 」で始まる行。lint は 判定 と 落ちた）を先に抜き出し、その後に出力の最後の25行。
終了コード: 0 全部0 ／ 1 どれかが落ちた（終了コード 1 の道具があり、回らなかった道具は無い） ／ 2 回らなかった道具がある・index.html が無い
  （標準出力の各行「<名前>: 終了コード <N>」で、1 は落ちた・2 以上は回らなかった）
"""
import functools, http.server, json, os, re, shutil, socket, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from 店の指紋 import 店の指紋   # noqa: E402

HONE = os.path.join(HERE, "lint.mjs")   # hone スキルの lint.mjs の写し（2026-10-19。GitHub だけで回るように）
計測タグ = ("gtag", "googletagmanager", "fbq", "klaviyo", "tiktok", "ttq", "clarity", "hotjar", "pintrk", "snaptr", "twq")


def 回す(名, cmd, timeout=600):
    """道具を1つ回す。時間切れ・起動の失敗・例外は終了コード 2 の行にして返す（止まらずに最後まで回す）"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (名, r.returncode, (r.stdout + r.stderr).strip())
    except subprocess.TimeoutExpired:
        return (名, 2, f"回らなかった: 時間切れ（{timeout}秒）: {' '.join(cmd[:2])}")
    except FileNotFoundError as e:
        return (名, 2, f"回らなかった: 起動できない（{cmd[0]} が無い）: {e}")
    except Exception as e:
        return (名, 2, f"回らなかった: {type(e).__name__}: {e}")


def 並べて見た結果(店, 指紋):
    """並べて見た_<回>.txt のいちばん新しい物: 1行目「安く見える所 0件」・2行目の指紋 ＝ 並べた絵/指紋.txt ＝ 今の指紋 の時だけ通す"""
    名 = "並べて見た結果"
    やる = "`node scripts/参考と並べる.mjs <店のフォルダ>` を回し、`references/並べて見る指示文.md` の指示文を Opus の Agent に渡す"
    回 = sorted((int(m.group(1)), f) for f in os.listdir(店) for m in [re.fullmatch(r"並べて見た_(\d+)\.txt", f)] if m)
    if not 回: return (名, 1, f"並べて見た_<回>.txt が無い。{やる}")
    f = 回[-1][1]; 行 = open(os.path.join(店, f), encoding="utf-8").read().splitlines() + ["", ""]
    m = re.fullmatch(r"指紋:\s*([0-9a-f]{12})", 行[1].strip())
    p = os.path.join(店, "並べた絵", "指紋.txt")
    並べた = open(p, encoding="utf-8").read().strip() if os.path.exists(p) else ""
    if not 並べた:
        return (名, 1, f"並べた絵/指紋.txt が無い（参考と並べる.mjs が最後まで書けていない）。{やる}")
    if 並べた != 指紋:
        return (名, 1, f"並べた絵/指紋.txt（{並べた}）が今の店の指紋（{指紋}）と違う。直した後の店でもう一度並べる。{やる}")
    if not m or m.group(1) != 指紋:
        return (名, 1, f"{f} の指紋（2行目: {行[1].strip() or '無い'}）が 並べた絵/指紋.txt と今の店の指紋（{指紋}）と違う。今の並べた絵でもう一度見比べる。{やる}")
    if 行[0].strip() != "安く見える所 0件":
        return (名, 1, f"{f} の1行目: {行[0].strip() or '空'}。挙がった所を直してから、もう一度 {やる}")
    return (名, 0, f"{f}: 安く見える所 0件（指紋 {指紋}。並べた絵/指紋.txt も同じ）")


def 記事のURL(設計):
    """店の設計.md の「1 来た人」の「どの記事から」の行に http で始まる URL があれば返す"""
    if not 設計 or not os.path.exists(設計): return ""
    t = open(設計, encoding="utf-8").read()
    m = re.search(r"^## 1 .*?$(.*?)(?=^## |\Z)", t, re.M | re.S)
    if not m: return ""
    for l in m.group(1).splitlines():
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if c and c[0].startswith("どの記事から"):
            for x in c[1:]:
                u = re.search(r"https?://[^\s|）)」]+", x)
                if u: return u.group(0)
    return ""


def 落ちた行(名, 出):
    """検査の結果.md に先に書く「落ちた」の行。lint は JSON の 判定 と 落ちた を必ず出す"""
    if 名.startswith("lint"):
        try:
            j = json.loads(出[出.index("{"):出.rindex("}") + 1])
            return [f"判定: {j.get('判定', '?')}", "落ちた: " + ("・".join(map(str, j.get("落ちた") or [])) or "なし")]
        except Exception:
            pass
    out, 続き = [], False
    for l in 出.splitlines():
        if "落ち" in l or l.lstrip().startswith(("×", "- ")): out.append(l); 続き = True
        elif 続き and l[:1].isspace() and l.strip(): out.append(l)   # 落ちた行の下の字下げした中身も
        else: 続き = False
    return out


def main(a):
    if len(a) < 2: print(__doc__); return 2
    店 = os.path.abspath(a[1]); html = os.path.join(店, "index.html")
    if not os.path.exists(html): print("index.html が無い:", 店); return 2
    結果 = []
    # 店の設計の写し: 店の印.json の「設計」が指す 店の設計.md を 移植表_店の設計.md に写す。読めない・無い時は古い写しで通さない
    元, 設計の理由 = "", ""
    try:
        元 = json.load(open(os.path.join(店, "店の印.json"), encoding="utf-8")).get("設計", "") or ""
        if not 元: 設計の理由 = "店の印.json に「設計」が無い（印を書く.py を回すと入る）"
        elif not os.path.exists(元): 設計の理由 = f"店の印.json の「設計」のパスが無い: {元}"
    except Exception as e:
        設計の理由 = f"店の印.json が読めない（{type(e).__name__}: {e}）"
    設計 = os.path.join(店, "移植表_店の設計.md")
    if not 設計の理由:
        try: shutil.copyfile(元, 設計)
        except Exception as e: 設計の理由 = f"店の設計.md を写せない（{e}）"
    # 出し直す前の照らし合わせ（references/照らし合わせの指示文.md）: いちばん新しい 直し_<回>.md の回の審査が FAIL なら、
    # 同じ番号の 照らし合わせ_<回>.txt が直しより新しく、1行目が「食い違い 0件」
    直し = sorted((int(m.group(1)), f) for f in os.listdir(店) for m in [re.fullmatch(r"直し_(\d+)\.md", f)] if m)
    def _FAIL(回):
        p = os.path.join(店, f"審査_{回}.md")
        return os.path.exists(p) and any(l.startswith("判定: FAIL") for l in open(p, encoding="utf-8"))
    if 直し and _FAIL(直し[-1][0]):
        回, f = 直し[-1]; 照 = os.path.join(店, f"照らし合わせ_{回}.txt")
        if not os.path.exists(照):
            結果.append(("照らし合わせ", 1, f"照らし合わせ_{回}.txt が無い（references/照らし合わせの指示文.md の指示文を別の AI に渡し、結果を書く）"))
        elif os.path.getmtime(照) < os.path.getmtime(os.path.join(店, f)):
            結果.append(("照らし合わせ", 1, f"照らし合わせ_{回}.txt が 直し_{回}.md より古い（直しを足したらもう一度照らす）"))
        else:
            頭 = open(照, encoding="utf-8").readline().strip()
            結果.append(("照らし合わせ", 0 if 頭 == "食い違い 0件" else 1, f"照らし合わせ_{回}.txt の1行目: {頭}"))
    if 設計の理由:
        結果.append(("設計の検査", 2, "回らなかった: " + 設計の理由))
    else:
        結果.append(回す("設計の検査", [sys.executable, os.path.join(HERE, "設計の検査.py"), 設計, 店]))
    結果.append(回す("絵を置く（ページの絵・画像の置き場・説明の突き合わせ）", [sys.executable, os.path.join(HERE, "絵を置く.py"), 店]))
    本文 = open(html, encoding="utf-8").read()
    # <style> の中は空の型のまま（F1）。ワンドライの CSS に klaviyo のクラス名の決まりがあるので、計測タグは <style> の外で探す
    本文 = re.sub(r"<style\b[^>]*>.*?</style>", "", 本文, flags=re.S).lower()
    タグ = [t for t in 計測タグ if re.search((r"(?<![a-z0-9])" + t) if len(t) <= 5 else t, 本文)]
    結果.append(("他社の計測タグ（C2）", 1 if タグ else 0, "落ちた: 残っている: " + "・".join(タグ) if タグ else "0（" + "・".join(計測タグ) + "）"))
    結果.append(回す("店の仕上がり検査", [sys.executable, os.path.join(HERE, "店の仕上がり検査.py"), 店]))
    広告 = os.path.join(店, "広告の文字.txt")
    if os.path.exists(広告):
        cmd = [sys.executable, os.path.join(HERE, "面の数字.py"), "--広告", 広告]
        u = 記事のURL(元 if not 設計の理由 else "")
        if u: cmd += ["--記事", u]
        結果.append(回す("面の数字（A4）", cmd + ["--店", html], timeout=900))
    else:
        結果.append(("面の数字（A4）", 0, "面の数字: 対象外（広告の文字.txt が無い）"))
    try:
        with socket.socket() as sk:
            sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
        class 静か(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *x, **k): pass
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(静か, directory=店))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    except Exception as e:
        srv = None
        for 名 in ("lint 390", "lint 1440", "横送りの往復（カートは非公開テーマのプレビューで回す）"):
            結果.append((名, 2, f"回らなかった: その場の http.server が立たない（{e}）"))
    if srv:
        try:
            for w in ("390", "1440"):
                if not os.path.exists(HONE):
                    結果.append((f"lint {w}", 2, f"回らなかった: hone スキルの lint.mjs が無い: {HONE}")); continue
                結果.append(回す(f"lint {w}", ["node", HONE, f"http://127.0.0.1:{port}/index.html", "--w", w]))
            結果.append(回す("横送りの往復（カートは非公開テーマのプレビューで回す）", ["node", os.path.join(HERE, "往復とカート.mjs"), f"http://127.0.0.1:{port}/index.html", "--カートなし"]))
        finally:
            srv.shutdown()
    今の指紋 = 店の指紋(店)   # 絵を置く.py が img/ に置いた後の指紋（絵だけ直した回も、並べて見直す）
    結果.append(並べて見た結果(店, 今の指紋))
    行 = ["# 機械の検査の結果（店の検査を回す.py が書いた。手で直さない）", "",
          "読む人: 編集長と、店を直す Claude。", "読む時: 審査の前。", "読まなくていい条件: なし。", "",
          f"- 店の指紋: `{今の指紋}`（index.html と img/ の直下の画像と動画。この指紋の店で回した結果。index.html か img/ を変えたら無効）",
          f"- 回した時刻: {time.strftime('%Y-%m-%d %H:%M')}", ""]
    for 名, 終, 出 in 結果:
        状 = "通った" if 終 == 0 else "落ちた" if 終 == 1 else "回らなかった"
        行 += [f"## {名}: 終了コード {終}（{状}）", ""]
        lint = 名.startswith("lint")
        落 = 落ちた行(名, 出) if 終 or lint else []
        if 落: 行 += ["lint の判定:" if lint else "落ちた行:", "", "```", "\n".join(落[:80]), "```", ""]
        行 += ["```", "\n".join(出.splitlines()[-25:]), "```", ""]
    open(os.path.join(店, "検査の結果.md"), "w", encoding="utf-8").write("\n".join(行))
    for 名, 終, _ in 結果: print(f"{名}: 終了コード {終}")
    if any(終 >= 2 for _, 終, _ in 結果): return 2
    return 1 if any(終 == 1 for _, 終, _ in 結果) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
