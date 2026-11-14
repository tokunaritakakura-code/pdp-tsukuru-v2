#!/usr/bin/env python3
"""空の型を作り直す（2/2）: 型を作る.mjs の中身に、ワンドライの CSS・足す CSS・カート・動きを付けて kata/ に組む。
  python3 scripts/空の型を作る/型を組む.py   → kata/index.html・kata/img/kyotsu-*・kata/絵の一覧.tsv
終了コード 0 組めた／1 入力が無い・印が切れている。
"""
import re, os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
REF = os.path.join(ROOT, 'references', '参考_ワンドライ', 'index.html'); KATA = os.path.join(ROOT, 'kata'); OUT = os.path.join(HERE, '_out')
rd = lambda p: open(p, encoding='utf-8').read()
for p in (REF, os.path.join(OUT, 'main.html'), os.path.join(OUT, '絵.json')):
    if not os.path.exists(p): print('入力が無い:', p, file=sys.stderr); sys.exit(1)
base = rd(REF); main = rd(os.path.join(OUT, 'main.html')); man = json.load(open(os.path.join(OUT, '絵.json'), encoding='utf-8'))
head = base[:base.find('</head>')]
head = re.sub(r'<title>.*?</title>', '<title>〔ページの題〕</title>', head, count=1, flags=re.S)
if 'noindex' not in head: head = head.replace('</title>', '</title>\n<meta name="robots" content="noindex">', 1)
head = re.sub(r'@font-face\s*\{[^}]*(?:mynovapaw|wandryshop)[^}]*\}', '', head)   # 書体は Google Fonts の Poppins と Noto Sans JP だけにする
bodytag = re.search(r'<body[^>]*>', base).group(0)
os.makedirs(os.path.join(KATA, 'img'), exist_ok=True)
# 共通の印（星・✓・×・開閉）と CSS の背景は、参考の img/ から kata/img/kyotsu-* に写して持つ
import shutil
REFIMG = os.path.join(os.path.dirname(REF), 'img')
def motsu(f):
    if 'hero_prod_point' in f: f = [x for x in os.listdir(REFIMG) if x.startswith('s7_list_check')][0]   # 足あとの行頭の印は ✓ に替える
    stem = re.sub(r'_[0-9a-f]{8}-[0-9a-f-]{20,}', '', f); local = 'img/kyotsu-' + stem
    srcp = os.path.join(REFIMG, f)
    if not os.path.exists(srcp): print('参考の絵が無い:', srcp, file=sys.stderr); sys.exit(1)
    shutil.copyfile(srcp, os.path.join(KATA, local)); return local
head = re.sub(r'url\((["\']?)img/([^"\')]+)\1\)', lambda m: 'url(' + motsu(m.group(2)) + ')', head)
def e_nashi(m):
    tag = m.group(0)
    if 'data-e=' in tag: return tag
    return re.sub(r'src="img/([^"]+)"', lambda k: 'src="' + motsu(k.group(1)) + '"', tag)
main = re.sub(r'<img\b[^>]*>', e_nashi, main)
html = (head + '\n<style data-from="kata">\n' + rd(os.path.join(HERE, '足す.css')) + '</style>\n</head>' + bodytag
        + '\n<main id="MainContent" class="content-for-layout focus-none" role="main" tabindex="-1">\n' + main + '\n</main>\n'
        + '<!-- ============ カート ============ -->\n' + rd(os.path.join(HERE, 'カート.html'))
        + '\n<script>' + rd(os.path.join(HERE, '結線.js')) + '</script>\n<script>\n' + rd(os.path.join(HERE, '型の動き.js')) + '\n</script>\n</body></html>\n')
marks = re.findall(r'<!-- ============ (.+?) ============ -->', html)
if len(marks) != 17: print('段の印が17個でない:', len(marks), marks, file=sys.stderr); sys.exit(1)
open(os.path.join(KATA, 'index.html'), 'w', encoding='utf-8').write(html)
KREF = 'references/参考_ここちドライの商品ページ/img/'
KGAL = ['gal2-v6.webp', 'gal6-v6.webp', 'gal19-v6.webp', 'how-v5.webp', 'gal5-v6.webp', 'gal3-v6.webp', 'kokochi-new-perf-4-cotton.webp']   # ここちドライの横送り 2〜8枚目
from PIL import Image
def ji(ref):
    """参考の絵の地: 透明／透明（白い線）／不透明"""
    try:
        im = Image.open(os.path.join(ROOT, ref)).convert('RGBA'); im.thumbnail((200, 200)); px = list(im.getdata())
    except Exception: return '不透明'
    sukeru = [p for p in px if p[3] < 128]
    if len(sukeru) / len(px) < 0.03: return '不透明'
    mieru = [p for p in px if p[3] >= 128]
    shiro = sum(1 for p in mieru if min(p[:3]) > 225)
    return '透明（白い線）' if mieru and shiro / len(mieru) > 0.8 else '透明'
rows = ['名前\t段\t種類\t元の大きさ\t参考の絵（絵を作る時に一緒に渡す）\t地']
for m in man['man']:
    ref = 'references/参考_ワンドライ/' + m['src'].split('?')[0]
    k = re.match(r'yoko-(\d+)$', m['name'])
    if k and int(k.group(1)) >= 2: ref = KREF + KGAL[int(k.group(1)) - 2]   # 横送りの2枚目からはここちドライ
    rows.append(f"{m['name']}\t{m['dan']}\t{m['kind']}\t{m['w']}x{m['h']}\t{ref}\t{ji(ref)}")
for n, dan in (('sengen-poster', '2. 宣言'), ('kurabe-mae', '4. 比べる'), ('kurabe-uchi', '4. 比べる')):
    rows.append(f"{n}\t{dan}\t写真\t1200x1200\t{KREF + ('kokochi-new-hero-e-m.webp' if n == 'sengen-poster' else 'kokochi-new-ba-1-before.webp' if n == 'kurabe-mae' else 'kokochi-new-ba-1-after.webp')}\t不透明")
for n in (1, 2, 3): rows.append(f"set-{n}\t1. 最初の画面\t写真\t252x326\treferences/参考_ワンドライ/img/pakge_{n}_pad.webp\t透明")
open(os.path.join(KATA, '絵の一覧.tsv'), 'w', encoding='utf-8').write('\n'.join(rows) + '\n')
print('組めた: kata/index.html', os.path.getsize(os.path.join(KATA, 'index.html')), '字 / 札', html.count('〔'), '/ 絵の名前', len(rows) - 1, '/ 段', len(marks))
