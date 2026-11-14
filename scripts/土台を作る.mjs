// 店の作業場の元（空の型）を写す。
//   node 土台を作る.mjs <出力フォルダ>
// 写す物: kata/index.html・kata/絵の一覧.tsv・kata/img/kyotsu-*（共通の印。作らない絵で、店にそのまま使う）
// 空の型は、ワンドライのプレミアム LP の HTML と CSS をそのまま写した物（作り方は scripts/空の型を作る/、説明は references/土台.md）。
// 文字は全部〔ワンドライの元の文〕の札、絵は全部 <img data-e="<名前>" src="img/<名前>.png">。店を作る回に替えるのは、
// 札の中の文字・絵（_gen/<名前>.png に作り、絵を置く.py が img/ に置く）・末尾のスクリプトの「変えるならここ」の値だけ。
// 埋めるまで 店の仕上がり検査.py の F12（札の残り）で落ちる。
// 終了コード: 0 写した ／ 1 引数が無い ／ 2 空の型が無い
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const KATA = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'kata');
const OUT = process.argv[2];
if (!OUT) { console.error('使い方: node 土台を作る.mjs <出力フォルダ>'); process.exit(1); }
for (const f of ['index.html', '絵の一覧.tsv']) {
  if (!fs.existsSync(path.join(KATA, f))) { console.error(`空の型が無い: ${path.join(KATA, f)}`); process.exit(2); }
}
fs.mkdirSync(path.join(OUT, 'img'), { recursive: true });
fs.copyFileSync(path.join(KATA, 'index.html'), path.join(OUT, 'index.html'));
fs.copyFileSync(path.join(KATA, '絵の一覧.tsv'), path.join(OUT, '絵の一覧.tsv'));
const 共通 = fs.readdirSync(path.join(KATA, 'img')).filter((f) => f.startsWith('kyotsu-'));
for (const f of 共通) fs.copyFileSync(path.join(KATA, 'img', f), path.join(OUT, 'img', f));
const 札 = (fs.readFileSync(path.join(OUT, 'index.html'), 'utf8').match(/〔/g) || []).length;
const 絵 = fs.readFileSync(path.join(OUT, '絵の一覧.tsv'), 'utf8').trim().split('\n').length - 1;
console.log(`空の型を写した: ${OUT}（札 ${札}・作る絵 ${絵}（絵の一覧.tsv）・共通の印 ${共通.length}）`);
