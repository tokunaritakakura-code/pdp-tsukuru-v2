// 横送りの写真を全枚往復できるか、セットを1つずつカートに入れて個数と金額が表示どおりかを数える（references/dame-list.md の G の2つ）。
//
// 使い方: node 往復とカート.mjs <URL> [--カートなし]
//   往復: 390px で開き、小さい写し（.hero_thumb_slider の8枚）を順に押して、大きい写真（.hero_image_slider）がその枚だけ見えているかを全枚で見る（行きと帰り）
//   カート: 非公開テーマのプレビュー URL で回す（カートは Shopify の /cart.js でしか動かない）。ローカルの index.html は --カートなし
//          カートを数える前に <html> の data-kata-err（型の動き.js が付ける「商品データが読めない」の印）を見て、あれば終了コード 1
//          選ぶ物があれば1つ目を選び、セット（#tiers の .tier）を1つずつ選んで #atc を押し、カートの合計（#kcTotal）が変わるまで最大20秒待ち、
//          合計がそのセットの値段（その .tier の data-price）と同じか、品数（/cart.js の型番の名前の数×個数の合計）がそのセットの数（data-n）と同じかを見る。見たらカートを空にする
// 終了コード: 0 全部合った / 1 どれかが合わない・商品データが読めない / 2 引数が足りない / 3 ページが取れない / 4 実行環境が壊れている
// process.exit はブラウザを閉じた後に呼ぶ
const { 引く, EXE } = await import(new URL('./lib.mjs', import.meta.url));

const 引数 = process.argv.slice(2);
const URL_ = 引数.find(a => !a.startsWith('--'));
const カートなし = 引数.includes('--カートなし');
if (!URL_) { console.error('使い方: node 往復とカート.mjs <URL> [--カートなし]'); process.exit(2); }

const chromium = 引く();
let browser;
try { browser = await chromium.launch({ executablePath: EXE, headless: true }); } catch (e) { console.error('環境が壊れている: Chromium を起動できない / ' + e.message); process.exit(4); }
const 落ち = [];
let 終わり = 0;
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  let 開けた = true;
  try { await page.goto(URL_, { waitUntil: 'load', timeout: 90000 }); } catch (e) { console.error('ページが取れない:', e.message); 終わり = 3; 開けた = false; }
  if (開けた) {
  await page.waitForTimeout(800);

  // 往復: 小さい写し（.hero_thumb_slider .slick-slide）を 1→最後→1 の順に押し、大きい写真（.hero_image_slider .slick-slide）がその枚だけ見えているか
  const 枚 = await page.$$eval('.hero_thumb_slider .slick-slide', xs => xs.length).catch(() => 0);
  const 大枚 = await page.$$eval('.hero_image_slider .slick-slide', xs => xs.length).catch(() => 0);
  if (!枚) 落ち.push('往復: .hero_thumb_slider に小さい写しが無い（空の型の作りが変わっている）');
  if (枚 !== 大枚) 落ち.push(`往復: 小さい写し ${枚} 枚と大きい写真 ${大枚} 枚の数が違う`);
  const 順 = [...Array(枚).keys()]; const 行き帰り = [...順, ...順.slice(0, -1).reverse()];
  for (const i of 行き帰り) {
    await page.evaluate(i => { const t = document.querySelectorAll('.hero_thumb_slider .slick-slide')[i]; t && t.click(); }, i);
    await page.waitForTimeout(400);
    const 見え = await page.$$eval('.hero_image_slider .slick-slide', ss => ss.map(s => { const r = s.getBoundingClientRect(); const st = getComputedStyle(s); const im = s.querySelector('img'); return st.display !== 'none' && st.visibility !== 'hidden' && r.width > 0 && r.height > 0 && !!im && im.naturalWidth > 0 && s.classList.contains('slick-current'); }));
    const 見えた = 見え.map((v, k) => v ? k : -1).filter(k => k >= 0);
    if (見えた.length !== 1 || 見えた[0] !== i) { 落ち.push(`往復: ${i + 1}枚目の小さい写しを押したのに、大きい写真で見えているのが ${見えた.length ? 見えた.map(k => k + 1).join('・') + '枚目' : '0枚'}（絵が無いか、替わっていない）`); break; }
  }
  console.log(`往復: ${枚}枚を行き帰り ${行き帰り.length}回押した`);

  // カート: セットごとに入れて、合計がそのセットの値段と同じか・品数がセットの数と同じか
  if (!カートなし) {
    await page.waitForTimeout(1500);   // 商品データ（/products/<HANDLE>.js）を読み終わるのを待つ
    const 印 = await page.evaluate(() => document.documentElement.getAttribute('data-kata-err'));
    if (印) {
      落ち.push(`カート: ${印}（HANDLE・型番の名前を見る。型番の名前に「<数><数え方>」が要る）`);
    } else {
      const セット = await page.$$eval('#tiers .tier', xs => xs.map(x => x.dataset.n));
      if (!セット.length) 落ち.push('カート: #tiers にセットが無い');
      for (const n of セット) {
        await page.evaluate(() => { const o = document.querySelector('#sizes [data-opt]'); if (o && !o.classList.contains('is-on')) o.click(); });
        await page.evaluate(n => document.querySelector(`#tiers .tier[data-n="${n}"]`).click(), n);
        await page.waitForTimeout(400);
        const 値段 = await page.$eval(`#tiers .tier[data-n="${n}"]`, e => String(e.dataset.price).replace(/[^\d]/g, ''));
        const 前 = await page.$eval('#kcTotal', e => e.textContent).catch(() => '');
        await page.evaluate(() => document.querySelector('#atc').click());
        // 合計の表示が変わるまで最大20秒待つ（変わらなければその時の表示で比べる）
        await page.waitForFunction(前 => { const e = document.querySelector('#kcTotal'); return e && e.textContent !== 前; }, 前, { timeout: 20000 }).catch(() => {});
        await page.waitForTimeout(300);
        const 合計 = await page.$eval('#kcTotal', e => e.textContent.replace(/[^\d]/g, '')).catch(() => '');
        // 品数: カートの中身（/cart.js）の、型番の名前の数（「3個セット」の 3）×個数の合計
        const 品数 = await page.evaluate(async () => { try { const c = await (await fetch('/cart.js', { cache: 'no-store' })).json(); return String((c.items || []).reduce((a, it) => a + (Number((String(it.variant_title || '').match(/(\d+)/) || [])[1]) || 0) * it.quantity, 0)); } catch (e) { return ''; } });
        const 誤り = await page.$eval('#buyErr', e => e.hidden ? '' : e.textContent.trim()).catch(() => '');
        console.log(`カート: ${n}個のセット 値段 ${値段} → 合計 ${合計}（品数 ${品数}）${誤り ? ' 表示: ' + 誤り : ''}`);
        if (!合計 || 合計 !== 値段) 落ち.push(`カート: ${n}個のセットの合計 ${合計 || '取れない'} が値段 ${値段} と違う${誤り ? '（' + 誤り + '）' : ''}`);
        if (品数 !== String(n)) 落ち.push(`カート: ${n}個のセットを入れたのに品数が ${品数 || '取れない'}`);
        // 空にする
        await page.evaluate(async () => { await fetch('/cart/clear.js', { method: 'POST' }); });
        await page.waitForTimeout(800);
      }
    }
  }
  }
} catch (e) {
  console.error('環境が壊れている: ' + e.message); 終わり = 4;
} finally {
  await browser.close();
}
if (終わり) process.exit(終わり);
if (落ち.length) { console.log(`落ちた ${落ち.length}件`); 落ち.forEach(x => console.log(' - ' + x)); process.exit(1); }
console.log('通った');
