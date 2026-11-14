// 空の型を作り直す（1/2）: 参考のワンドライの写し（references/参考_ワンドライ/index.html）から、
// 段を16個に並べ、文字を〔元の文〕の札に、絵に名前（data-e）を付けた中身を作る。
//   node scripts/空の型を作る/型を作る.mjs   → scripts/空の型を作る/_out/main.html・絵.json
// 続けて python3 scripts/空の型を作る/型を組む.py で kata/ に組む。空の型を直す時だけ使う（店を作る回は使わない）。
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { 引く, EXE } from '../lib.mjs';
const HERE = path.dirname(fileURLToPath(import.meta.url));
const REF = path.join(HERE, '..', '..', 'references', '参考_ワンドライ', 'index.html');
const OUT = path.join(HERE, '_out'); fs.mkdirSync(OUT, { recursive: true });
const b = await 引く().launch({ executablePath: EXE, headless: true });
const ctx = await b.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
const p = await ctx.newPage();
await p.goto(pathToFileURL(REF).href, { waitUntil: 'load', timeout: 60000 });
const CTA = `<div class="clearall"></div><div class="button_box"><div class="button_width"><a href="#buy" class="common_button btn_scorall pulse"><p class="btn_cart_text">〔本日限定価格で注文する〕</p></a><div class="wd-purchase-assurance"><span>〔90日間返金保証〕</span><span>〔全国送料無料・2〜5営業日でお届け〕</span></div></div></div>`;
const SENGEN = `<div class="shopify-section kata-sec" data-dan="2. 宣言"><div class="section_3 kata-sengen"><div class="container"><p class="common_sub_heading color_sky">〔宣言の上の小さい言葉〕</p><p class="common_heading">〔もう◯◯いらない、の宣言の1文〕</p><div class="section3_image_box kata-video"><video src="img/sengen.mp4" poster="img/sengen-poster.png" data-e="sengen-poster" playsinline muted loop controls preload="none"></video></div><p class="common_paragraph">〔宣言を受ける2〜3文〕</p><ul class="hero_prod_point kata-anshin"><li><strong>〔安心1〕</strong> － 〔ひと言〕</li><li><strong>〔安心2〕</strong> － 〔ひと言〕</li><li><strong>〔安心3〕</strong> － 〔ひと言〕</li><li><strong>〔安心4〕</strong> － 〔ひと言〕</li><li><strong>〔安心5〕</strong> － 〔ひと言〕</li></ul>${CTA}</div></div></div>`;
const KURABE = `<div class="shopify-section kata-sec" data-dan="4. 比べる"><div class="section_4 kata-kurabe"><div class="container"><p class="common_sub_heading color_sky">〔比べるの上の小さい言葉〕</p><p class="common_heading">〔今の物とうちの違いを言う見出し〕</p><div class="kata-ba" id="ba"><img class="bef" src="img/kurabe-mae.png" data-e="kurabe-mae" alt="〔今の物を使っている所の説明〕"><img class="aft" src="img/kurabe-uchi.png" data-e="kurabe-uchi" alt="〔うちの商品を使っている所の説明〕"><div class="ln"><span class="knob"><i>◀</i><i>▶</i></span></div><span class="l">〔今の物の名〕</span><span class="r">〔うちの商品の名〕</span><input type="range" min="0" max="100" value="50" aria-label="左右に動かして比べる"></div><p class="kata-bahint">〔左右に動かして比べる、のひと言〕</p><p class="common_paragraph">〔違いを言う1〜2文〕</p>${CTA}</div></div></div>`;
const SHIME = `<div class="shopify-section kata-sec" data-dan="16. 締め"><div class="section_10 kata-shime"><div class="container"><p class="common_sub_heading color_sky">〔締めの上の小さい言葉〕</p><p class="common_heading">〔最後の一押しの1文〕</p><p class="common_paragraph">〔背中を押す2文〕</p>${CTA}</div></div></div>`;

const res = await p.evaluate(({ CTA, SENGEN, KURABE, SHIME }) => {
  const main = document.querySelector('main');
  const S = id => main.querySelector(`[id$="__${id}"]`);
  const log = [];
  // 段の名前
  const DAN = { section1_product_info_a4WC7i: '1. 最初の画面', horizontal_ticker_Wy3gzM: '3. 流れる帯', section2_BMaPHf: '5. 効かなかった理由', section3_KwkmjW: '6. とは・仕組み', section_4_UNH3dT: '7. 使い方', section_5_RNAzkY: '8. 特長', section6_6fmGek: '9. 費用の比べ', section7_iEz6EN: '10. 暮らし', section8_TnhJeQ: '11. 専門家', section9_Fgmw6C: '12. くらべる表', section10_D3gEnm: '13. 保証', section11_yzUh9K: '14. 人の声', section12_m4qzGA: '15. よくある質問' };
  [...main.children].forEach(c => { const k = (c.id || '').split('__')[1]; if (DAN[k]) { c.dataset.dan = DAN[k]; c.removeAttribute('id'); c.className = 'shopify-section kata-sec'; } else c.remove(); });
  // 犬の飾りを消す
  let n = 0; main.querySelectorAll('img').forEach(im => { if (/dog|paw/i.test(im.className)) { im.remove(); n++; } }); log.push('犬の飾り ' + n);
  // 最初の画面
  const hero = main.querySelector('[data-dan="1. 最初の画面"]');
  ['.hero_image_slider', '.hero_thumb_slider'].forEach(sel => { const sl = hero.querySelectorAll(sel + ' .slick-slide'); sl.forEach((s, i) => { if (i >= 8) s.remove(); }); });
  hero.querySelectorAll('#wdSub,.wd-order-proof,#btnRegular,.wdp-free').forEach(e => e.remove());
  main.querySelectorAll('.button_shipp').forEach(e => e.remove());
  const variant = hero.querySelector('#wdVariant'); variant.innerHTML = '';
  variant.before(document.createComment(' 選ぶ所ここから（OPTS が空の店は、ここからここまでを消す） ')); variant.after(document.createComment(' 選ぶ所ここまで '));
  const rows = [...hero.querySelectorAll('.butOption_row')]; const tiers = document.createElement('div'); tiers.id = 'tiers'; rows[0].before(tiers); rows.forEach(r => r.remove());
  const err = document.createElement('p'); err.id = 'buyErr'; err.hidden = true; err.className = 'kata-err'; tiers.after(err);
  // 段の間に残ったコメント（Package 1 など）を消す
  const walker = document.createTreeWalker(main, NodeFilter.SHOW_COMMENT); const cm = []; while (walker.nextNode()) cm.push(walker.currentNode); cm.forEach(c => { if (!/選ぶ所/.test(c.data)) c.remove(); });
  const det = hero.querySelector('.hero_prod_details'); if (det) det.id = 'buy';
  const atc = hero.querySelector('a.common_button.atc'); atc.id = 'atc'; atc.setAttribute('href', '#buy'); atc.querySelectorAll('input').forEach(e => e.remove());
  const off = hero.querySelector('#btnOffer'); off.textContent = ''; off.setAttribute('data-btnprice', '');
  main.querySelectorAll('a.btn_scorall').forEach(a => a.setAttribute('href', '#buy'));
  // 足す段
  const at = name => main.querySelector(`[data-dan="${name}"]`);
  at('1. 最初の画面').insertAdjacentHTML('afterend', SENGEN);
  at('3. 流れる帯').insertAdjacentHTML('afterend', KURABE);
  at('15. よくある質問').insertAdjacentHTML('afterend', SHIME);
  // 絵: 名前を付ける
  const KYOTSU = /star_|compare_check|compare_cross|s7_list_check|petOwner_icon/;
  const RULE = [[/hero_slide_img|hero_thumb_slider_img/, 'yoko', '写真'], [/wd-shelter__img/, 'shirushi', '札'], [/hero_qstn_icon/, 'faq-icon', 'アイコン'], [/secure_scroll_icon/, 'obi-icon', 'アイコン'], [/sec2_col_img/, 'mae', 'イラスト'], [/sec2_indu_box_top_imgbx/, 'gyokai-icon', 'アイコン'], [/section3_image_quote/, 'towa-quote', '札'], [/section3_image/, 'towa', '写真'], [/sec3_prod_m/, 'towa-tate', '写真'], [/sec3cont_row_icon/, 'shikumi-icon', 'アイコン'], [/sec4_col_image/, 'tsukaikata', '写真'], [/__sp__/, 'tsukaikata-sp', '写真'], [/feature-seals/, 'tokucho-shirushi', '札'], [/sec5_col_image/, 'tokucho', '写真'], [/wallet_col_logo|comp_logo/, 'logo', 'ロゴ'], [/s6_wallet_col_prod/, 'hiyou', '写真'], [/s7-slider-img/, 'kurashi', '写真'], [/sec8_women/, 'senmonka', '専門家'], [/vet_seal/, 'senmonka-shirushi', '札'], [/comp_list_icon/, 'hikaku-icon', 'アイコン'], [/comp_prod/, 'hikaku', '写真'], [/money_back_seal/, 'hosho-fuda', '札'], [/petOwner_review_image/, 'koe', '写真'], [/review_img/, 'koe-matome', '札']];
  const seen = {}; const count = {}; const man = []; const kyotsu = new Set();
  main.querySelectorAll('img').forEach(im => {
    const src = im.getAttribute('src') || ''; if (im.dataset.e) return; const file = src.split('?')[0].split('/').pop();
    if (KYOTSU.test(file)) { kyotsu.add(src); return; }
    const key = (im.className || '') + ' ' + (im.parentElement.className || '');
    let r = RULE.find(x => x[0].test(im.className || '')) || RULE.find(x => x[0].test(key)); const dan = im.closest('[data-dan]').dataset.dan;
    if (!r) { log.push('名前の無い絵: ' + dan + ' ' + key.slice(0, 40) + ' ' + file); return; }
    let stem = file.replace(/_m(?=[._])|_m_[0-9a-f-]+|_[0-9a-f]{8}-[0-9a-f-]{20,}/g, '').replace(/\.(webp|png|jpe?g)$/, '').replace(/-mob$/, '').replace(/^wdprev-/, '');
    if (r[1] === 'tsukaikata' && /_m(?=[._])/.test(file)) r = RULE.find(x => x[1] === 'tsukaikata-sp');   // スマホ用の縦長の絵は別の名前にする（PC 用は横長）
    const k = r[1] + '|' + stem;
    if (!seen[k]) { count[r[1]] = (count[r[1]] || 0) + 1; seen[k] = r[1] + '-' + count[r[1]]; const q = im.getBoundingClientRect(); man.push({ name: seen[k], dan, kind: r[2], w: im.naturalWidth, h: im.naturalHeight, src }); }
    im.dataset.e = seen[k]; if (r[2] === '写真' || r[2] === '専門家' || r[2] === 'イラスト') im.setAttribute('alt', '〔絵の説明〕'); else im.setAttribute('alt', '');
  });
  // 1つしか無い名前は番号を外す
  const single = Object.keys(count).filter(k => count[k] === 1);
  single.forEach(k => { main.querySelectorAll(`img[data-e="${k}-1"]`).forEach(im => im.dataset.e = k); man.forEach(m => { if (m.name === k + '-1') m.name = k; }); });
  // 絵の行き先は、作った絵の名前（img/<名前>.png）。店を作る回は img タグを触らない
  main.querySelectorAll('img[data-e]').forEach(im => { im.setAttribute('src', 'img/' + im.dataset.e + '.png'); im.removeAttribute('srcset'); im.removeAttribute('sizes'); im.removeAttribute('loading'); });
  // 参考の店だけの印（data-wandry-*）は消す（画面に出ないが、店に参考の店の名前が残る）
  main.querySelectorAll('*').forEach(e => { [...e.attributes].forEach(at => { if (/^data-wandry/.test(at.name)) e.removeAttribute(at.name); }); });
  // 文字を札に
  const tw = document.createTreeWalker(main, NodeFilter.SHOW_TEXT); const tx = []; while (tw.nextNode()) tx.push(tw.currentNode);
  let slots = 0; tx.forEach(t => { const v = t.data.replace(/\s+/g, ' ').trim(); if (!v) return; const pe = t.parentElement; if (pe.closest('script,style,svg,#tiers,#wdVariant')) return; if (/〔/.test(v)) return; if (/^[－・｜／\/|:：、。+＋×\-\s]+$/.test(v)) return; t.data = t.data.replace(v.length === t.data.trim().length ? t.data.trim() : t.data.trim(), '〔' + v + '〕'); slots++; });
  log.push('札 ' + slots);
  // 段の印
  [...main.children].forEach(c => { c.before(document.createComment(' ============ ' + c.dataset.dan + ' ============ ')); c.before(document.createTextNode('\n')); });
  return { html: main.innerHTML, man, kyotsu: [...kyotsu], log, order: [...main.children].map(c => c.dataset.dan) };
}, { CTA, SENGEN, KURABE, SHIME });
await b.close();
console.log(res.log.join('\n')); console.log('段', res.order.join(' / ')); console.log('絵の名前', res.man.length, '共通', res.kyotsu.length);
fs.writeFileSync(path.join(OUT, 'main.html'), res.html); fs.writeFileSync(path.join(OUT, '絵.json'), JSON.stringify({ man: res.man, kyotsu: res.kyotsu }, null, 1));
