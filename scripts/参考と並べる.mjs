// 店の段ごとに、左に参考の同じ段・右に店の段を並べた PNG を書く（2026-11-13 本人「段ごとに参考と横に並べた画像を、作った本人でない Opus が見て安く見える所を挙げる」）。
//   node scripts/参考と並べる.mjs <店のフォルダ>
// 幅 390 で開く。書く物（<店>/並べた絵/ の中。前の PNG は消してから書く）:
//   <2桁の番号>_<段の名前>.png   16段それぞれ。1枚の高さは 2400px まで、超える段は続きを _2・_3 に分ける
//   00_横送り_<N>.png            最初の画面の横送りの写真 N 枚目（左に 絵の一覧.tsv の参考の絵、右に店の img/yoko-N.png）
//   一覧.md                       段・参考・ファイル名の表
//   指紋.txt                      並べた時の店の指紋（index.html と img/ の直下の画像と動画。手順は 店の指紋.py と同じ。sha256 の頭12字）
//   指紋.txt と 一覧.md は、PNG を全部書けた時だけ最後に書く。始めに古い 指紋.txt・一覧.md を消すので、途中で落ちた回は 指紋.txt が無い
// 参考: ワンドライに同じ段がある13段はワンドライ（references/参考_ワンドライ/index.html）のその段、
//       「2. 宣言」「4. 比べる」はここちドライ（references/参考_ここちドライの商品ページ/index.html）の「2. 言い切り」「3. 違い」の段、「16. 締め」は参考なしで店だけ。
// 終了コード: 0 書けた ／ 1 段が見つからない（店か参考に） ／ 2 入力が無い ／ 4 Chromium が起きない
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { 引く, EXE } from './lib.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SKILL = path.join(HERE, '..');
const REF_W = path.join(SKILL, 'references', '参考_ワンドライ', 'index.html');
const REF_K = path.join(SKILL, 'references', '参考_ここちドライの商品ページ', 'index.html');
const 店 = process.argv[2] && path.resolve(process.argv[2]);
const W = 390, 高さ = 2400, 頭 = 40, 片 = 高さ - 頭;

if (!店) { console.error('使い方: node scripts/参考と並べる.mjs <店のフォルダ>'); process.exit(2); }
const HTML = path.join(店, 'index.html');
for (const p of [HTML, REF_W, REF_K]) if (!fs.existsSync(p)) { console.error('入力が無い: ' + p); process.exit(2); }
// 始めに古い PNG・指紋.txt・一覧.md を消す（途中で落ちた回に古い指紋が残らないように）
const 指紋 = 店の指紋(店);   // 並べる前の店の指紋（並べている間に店を変えない）
const 出 = path.join(店, '並べた絵'); fs.mkdirSync(出, { recursive: true });
for (const f of fs.readdirSync(出)) if (f.endsWith('.png') || f === '指紋.txt' || f === '一覧.md') fs.unlinkSync(path.join(出, f));
const 一覧p = fs.existsSync(path.join(店, '絵の一覧.tsv')) ? path.join(店, '絵の一覧.tsv') : path.join(SKILL, 'kata', '絵の一覧.tsv');
const 一覧 = fs.readFileSync(一覧p, 'utf8').trim().split('\n').slice(1).map((l) => l.split('\t'));

// 段の並び（空の型の段の印と同じ16個。カートは並べない）と、参考の段の見つけ方
const WANDRY = { '1. 最初の画面': 'section1_product_info_a4WC7i', '3. 流れる帯': 'horizontal_ticker_Wy3gzM', '5. 効かなかった理由': 'section2_BMaPHf', '6. とは・仕組み': 'section3_KwkmjW', '7. 使い方': 'section_4_UNH3dT', '8. 特長': 'section_5_RNAzkY', '9. 費用の比べ': 'section6_6fmGek', '10. 暮らし': 'section7_iEz6EN', '11. 専門家': 'section8_TnhJeQ', '12. くらべる表': 'section9_Fgmw6C', '13. 保証': 'section10_D3gEnm', '14. 人の声': 'section11_yzUh9K', '15. よくある質問': 'section12_m4qzGA' };
const KOKOCHI = { '2. 宣言': '2. 言い切り', '4. 比べる': '3. 違い' };
const 段たち = [...fs.readFileSync(HTML, 'utf8').matchAll(/<!-- ============ (.+?) ============ -->/g)].map((m) => m[1]).filter((n) => n !== 'カート');
if (段たち.length !== 16) { console.error(`段が見つからない: 店の段の印が ${段たち.length} 個（16個のはず）`); process.exit(1); }

let browser;
try { browser = await 引く().launch({ executablePath: EXE, headless: true }); }
catch (e) { console.error('Chromium が起きない: ' + e.message + '（HONE_CHROMIUM で場所を渡す）'); process.exit(4); }

async function 開く(file) {
  const ctx = await browser.newContext({ viewport: { width: W, height: 844 }, deviceScaleFactor: 1, locale: 'ja-JP', isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  await page.goto(pathToFileURL(file).href, { waitUntil: 'load', timeout: 90000 });
  await page.evaluate(async () => {
    document.querySelectorAll('img').forEach((im) => { im.loading = 'eager'; const d = im.getAttribute('data-src'); if (d && !im.getAttribute('src')) im.src = d; });
    for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise((r) => setTimeout(r, 50)); }
    scrollTo(0, 0);
    document.querySelectorAll('.slick-list, [class*="slider"], [class*="track"]').forEach((e) => { e.scrollLeft = 0; });   // 横送りは左端にそろえてから撮る（回ごとに位置が違って、係の言う事が逆になった。2026-11-14）
    await Promise.all([...document.images].map((im) => im.complete ? 0 : new Promise((r) => { im.onload = im.onerror = r; setTimeout(r, 4000); })));
    // 画面を覆う飾り（ポップアップ・下に張り付く帯）は並べる絵から外す
    document.querySelectorAll('body *').forEach((el) => { const s = getComputedStyle(el); if (s.position === 'fixed') el.style.setProperty('display', 'none', 'important'); });
  });
  await page.waitForTimeout(500);
  return page;
}

// 段の場所（ページの上からの y と高さ）
async function 場所(page, how) {
  return page.evaluate((how) => {
    // 段の要素は中身が float で高さ0のことがある（ワンドライの CSS）。子孫まで含めた外枠で取る
    const 箱 = (els) => { const rs = els.flatMap((e) => [e, ...e.querySelectorAll('*')]).filter((e) => getComputedStyle(e).position !== 'fixed').map((e) => e.getBoundingClientRect()).filter((r) => r.height > 0 && r.width > 0); if (!rs.length) return null; const t = Math.min(...rs.map((r) => r.top)), b = Math.max(...rs.map((r) => r.bottom)); return { y: Math.round(t + scrollY), h: Math.round(b - t) }; };
    if (how.dan) { const e = document.querySelector(`main > [data-dan="${how.dan}"]`); return e ? 箱([e]) : null; }
    if (how.id) { const e = document.querySelector(`[id$="__${how.id}"]`); return e ? 箱([e]) : null; }
    // ここちドライ: 段の印のコメントから、次の段の印までの要素
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_COMMENT); let c = null;
    while (w.nextNode()) if (w.currentNode.data.includes('====') && w.currentNode.data.includes(how.mark)) { c = w.currentNode; break; }
    if (!c) return null;
    const els = []; for (let n = c.nextSibling; n; n = n.nextSibling) { if (n.nodeType === 8 && n.data.includes('====')) break; if (n.nodeType === 1) els.push(n); }
    return 箱(els);
  }, how);
}

async function 撮る(page, at) {
  const H = await page.evaluate(() => document.documentElement.scrollHeight);
  const 片たち = [];
  for (let y = at.y; y < at.y + at.h; y += 片) {
    const h = Math.min(片, at.y + at.h - y, H - y); if (h <= 0) break;
    片たち.push((await page.screenshot({ clip: { x: 0, y, width: W, height: h }, fullPage: true, scale: 'css' })).toString('base64'));
  }
  return 片たち;
}

const 台 = await (await browser.newContext({ viewport: { width: W * 2 + 12, height: 844 }, deviceScaleFactor: 1 })).newPage();
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
async function 並べて書く(左, 右, 左の名, 右の名, out) {
  const 列 = (src, 名) => `<div style="width:${W}px"><div style="height:${頭}px;line-height:${頭}px;font:bold 15px sans-serif;padding:0 8px;background:#222;color:#fff;overflow:hidden;white-space:nowrap">${esc(名)}</div>${src ? `<img src="${src}" style="display:block;width:${W}px">` : `<div style="height:200px;display:flex;align-items:center;justify-content:center;font:15px sans-serif;color:#888;background:#f2f2f2">（無し）</div>`}</div>`;
  await 台.setContent(`<html><body style="margin:0;background:#fff"><div id="x" style="display:flex;gap:12px;width:${W * 2 + 12}px;align-items:flex-start">${列(左, 左の名)}${列(右, 右の名)}</div></body></html>`);
  await 台.evaluate(() => Promise.all([...document.images].map((im) => im.complete ? 0 : new Promise((r) => { im.onload = im.onerror = r; }))));
  await (await 台.$('#x')).screenshot({ path: out });
}

// 店の指紋（店の指紋.py と同じ手順: index.html → img/ の直下の png・jpg・jpeg・webp・gif・svg・mp4（. で始まる物を除く）を名前の UTF-8 のバイト順に「\0名前\0」＋中身）
function 店の指紋(店) {
  const h = crypto.createHash('sha256').update(fs.readFileSync(path.join(店, 'index.html')));
  const 絵 = path.join(店, 'img');
  const 名たち = fs.existsSync(絵) ? fs.readdirSync(絵).filter((f) => !f.startsWith('.') && ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg', '.mp4'].includes(path.extname(f).toLowerCase()) && fs.statSync(path.join(絵, f)).isFile()) : [];
  名たち.sort((a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8')));
  for (const f of 名たち) { h.update(Buffer.concat([Buffer.from([0]), Buffer.from(f, 'utf8'), Buffer.from([0])])); h.update(fs.readFileSync(path.join(絵, f))); }
  return h.digest('hex').slice(0, 12);
}
const 行 = []; const 無い = [];
try {
  const [pw, pk, ps] = [await 開く(REF_W), await 開く(REF_K), await 開く(HTML)];
  for (const [i, 名] of 段たち.entries()) {
    const 番 = String(i + 1).padStart(2, '0'); const 短 = 名.replace(/^\d+\.\s*/, '');
    const 店の場所 = await 場所(ps, { dan: 名 });
    if (!店の場所) { 無い.push(`店の段「${名}」`); continue; }
    let 参の場所 = null, 参の名 = '参考なし', 参page = null;
    if (WANDRY[名]) { 参page = pw; 参の場所 = await 場所(pw, { id: WANDRY[名] }); 参の名 = `参考: ワンドライの同じ段`; if (!参の場所) { 無い.push(`ワンドライの段 ${WANDRY[名]}（${名}）`); continue; } }
    else if (KOKOCHI[名]) { 参page = pk; 参の場所 = await 場所(pk, { mark: KOKOCHI[名] }); 参の名 = `参考: ここちドライ「${KOKOCHI[名]}」`; if (!参の場所) { 無い.push(`ここちドライの段「${KOKOCHI[名]}」（${名}）`); continue; } }
    const 右 = await 撮る(ps, 店の場所); const 左 = 参page ? await 撮る(参page, 参の場所) : [];
    const n = Math.max(右.length, 左.length); const files = [];
    for (let k = 0; k < n; k++) {
      const f = `${番}_${短}${k ? '_' + (k + 1) : ''}.png`;
      await 並べて書く(左[k] && 'data:image/png;base64,' + 左[k], 右[k] && 'data:image/png;base64,' + 右[k], 参の名 + (n > 1 ? `（${k + 1}/${n}）` : ''), `店: ${名}` + (n > 1 ? `（${k + 1}/${n}）` : ''), path.join(出, f));
      files.push(f);
    }
    行.push([名, 参の名.replace(/^参考: /, ''), files.join('・')]);
  }
  // 横送りの写真を1枚ずつ
  const 横 = 一覧.filter((r) => /^yoko-\d+$/.test(r[0]));
  const dataURL = (p) => { if (!fs.existsSync(p)) return null; const ext = path.extname(p).slice(1).toLowerCase(); return `data:image/${ext === 'jpg' ? 'jpeg' : ext};base64,` + fs.readFileSync(p).toString('base64'); };
  for (const r of 横) {
    const N = r[0].split('-')[1]; const f = `00_横送り_${N}.png`;
    const 参 = path.join(SKILL, r[4] || ''); const う = path.join(店, 'img', r[0] + '.png');
    if (!fs.existsSync(う)) console.error(`店の img/${r[0]}.png が無い（右を空にした。絵を置く.py を先に回す）`);
    await 並べて書く(dataURL(参), dataURL(う), `参考: ${path.basename(参)}`, `店: img/${r[0]}.png`, path.join(出, f));
    行.push([`1. 最初の画面 横送り ${N} 枚目`, path.basename(参), f]);
  }
} catch (e) {
  await browser.close(); console.error('並べられなかった: ' + e.message); process.exit(2);
}
await browser.close();
if (無い.length) { console.error('段が見つからない: ' + 無い.join('・')); process.exit(1); }
if (店の指紋(店) !== 指紋) { console.error('並べている間に index.html か img/ が変わった。もう一度並べる'); process.exit(1); }
fs.writeFileSync(path.join(出, '一覧.md'), ['# 参考と並べた絵（参考と並べる.mjs が書いた。手で直さない）', '', `店の指紋（index.html と img/ の絵）: ${指紋}`, '', '| 段 | 参考（左） | ファイル（右が店） |', '|---|---|---|', ...行.map((r) => `| ${r.join(' | ')} |`), ''].join('\n'));
fs.writeFileSync(path.join(出, '指紋.txt'), 指紋 + '\n');   // いちばん最後に書く
console.log(`並べた: ${出}（段 ${段たち.length}・ファイル ${fs.readdirSync(出).filter((f) => f.endsWith('.png')).length}・指紋 ${指紋}）`);
