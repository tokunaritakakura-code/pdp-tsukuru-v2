(function(){
'use strict';
/* ===== 変えるならここ（店ごとに埋める） ===== */
var HANDLE = '〔商品のハンドル〕';        // 商品のハンドル（手順3c で決める。英小文字とハイフン。Shopify の商品とテンプレートをこの名前で作る）
var VMAP = {}, AVAIL = {};            // セットの数 → 型番の ID（Shopify の商品データで上書き）
var OPT_NAME = '〔選ぶ物の名前〕';       // 客が選ぶ物の名前（例: サイズ）。設計の 4「色・サイズの案内」と同じ
var OPTS = ['〔選ぶ物〕','〔選ぶ物〕','〔選ぶ物〕'];  // 選ぶ物。数は商品の選ぶ物の数だけ。無い商品は [] にして、HTML の「選ぶ所ここから〜ここまで」を消す
var OPT_SUB = {};                     // 選ぶ物ごとの小さい説明（例 {'S':'60×40cm'}）。無ければ {}
var OPT_IMG = {};                     // 色を選ばせる時だけ、選ぶ物ごとの色の札の絵（例 {'黒':'img/iro-1.png'}）。無ければ {}
var TIERS = [                         // 並びは画面の上から。いちばん大きいセットが真ん中で、最初から選ばれている
  {n:1, price:Number('〔1個の値段〕'), fuda:'〔1個のセットの札〕', kind:'starter'},
  {n:3, price:Number('〔3個の値段〕'), fuda:'いちばん人気', kind:''},
  {n:2, price:Number('〔2個の値段〕'), fuda:'〔2個のセットの札〕', kind:'bestvalue'}
];
var DAYS = 1095;                      // 1日あたりは3年で割る
var UNIT = '〔数え方〕';               // セットの数え方（個・本・枚）
/* ===== ここまで ===== */
function setName(n){ return n===1 ? '1'+UNIT : n+UNIT+'セット'; }
function setImg(n){ return 'img/set-'+n+'.png'; }
var yen = function(v){ return '¥' + Number(v).toLocaleString('ja-JP'); };
var st = {picked:true, opt:(OPTS.length ? OPTS[0] : null), n:3};   // 選ぶ物は1つめを最初から選んでおく（参考も最初から選んである）
var $ = function(s){ return document.querySelector(s); };
var $$ = function(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); };
var root = (window.Shopify && Shopify.routes && Shopify.routes.root) || '/';

/* 商品データが読めない・型番の対応表が空の時は、<html> に data-kata-err の印を付ける（往復とカート.mjs がカートを数える前に見る） */
function kataErr(m, e){ console.error('型の動き: ' + m + '（HANDLE=' + HANDLE + '・数え方=' + UNIT + '）', e || ''); document.documentElement.setAttribute('data-kata-err', '商品データが読めない'); }
fetch(root + 'products/' + HANDLE + '.js', {cache:'no-store'}).then(function(r){ if(!r.ok) throw Error('products/' + HANDLE + '.js が ' + r.status); return r.json(); }).then(function(p){
  (p.variants || []).forEach(function(v){
    var m=null, o='';
    [v.option1,v.option2,v.option3,v.title].map(String).forEach(function(x){ var r=x.match(new RegExp('(\\d+)'+UNIT)); if(r&&!m) m=r; if(OPTS.indexOf(x)>=0) o=x; });
    if(m){ VMAP[(OPTS.length?o+'|':'')+m[1]]=v.id; AVAIL[v.id]=v.available; }
  });
  if(!Object.keys(VMAP).length) kataErr('型番の対応表が空（型番の名前に「<数>' + UNIT + '」が無い）');
  render();
}).catch(function(e){ kataErr('商品データが読めない', e); });

/* 選ぶ所: OPTS が空の店は HTML ごと無い */
var vEl = document.getElementById('wdVariant'), sizesEl = null;
if (vEl && OPTS.length) {
  var asImg = OPTS.some(function(o){ return OPT_IMG[o]; }), kind = asImg ? 'color' : 'size';
  vEl.innerHTML = '<div class="wd-variant__row"><p class="wd-variant__label">'+OPT_NAME+' <b id="sizeCur">未選択</b></p><div class="wd-variant__opts wd-variant__opts--'+kind+'" id="sizes">'
    + OPTS.map(function(o){ return '<button type="button" class="wd-opt wd-opt--'+kind+'" data-opt="'+o+'">'+(OPT_IMG[o] ? '<img src="'+OPT_IMG[o]+'" alt=""><span>'+o+'</span>' : '<strong>'+o+'</strong>'+(OPT_SUB[o]?'<span>'+OPT_SUB[o]+'</span>':''))+'</button>'; }).join('') + '</div></div>';
  sizesEl = document.getElementById('sizes');
  sizesEl.addEventListener('click', function(e){ var b=e.target.closest('[data-opt]'); if(!b) return; st.opt=b.dataset.opt; err(''); render(); });
}
function needOpt(){ return OPTS.length>0 && !st.opt; }
function optKey(n){ return (OPTS.length ? st.opt+'|' : '') + n; }

function tierHTML(t, i){
  var per = Math.round(t.price/t.n), on = st.n===t.n;
  return '<div class="butOption_row butOption'+(i+1)+' tier'+(on?' active is-selected':'')+'" data-n="'+t.n+'" data-price="'+t.price+'">'
    + '<p class="most_popular'+(t.kind?' '+t.kind:'')+'">'+t.fuda+'</p>'
    + '<div class="buybox_left"><div class="packageOpt"><input type="radio" name="buyopt"'+(on?' checked':'')+'><span></span></div>'
    + '<div class="buy-mid"><p class="prod-qty">'+setName(t.n)+'</p>'
    + '<div class="wdp-price"><div class="wdp-price-top"><span class="wdp-label">1'+UNIT+'あたり</span></div><div class="wdp-price-main"><strong>'+yen(per)+'</strong><span>／'+UNIT+'</span></div></div>'
    + '<p class="pkg_quantity_text">合計 '+yen(t.price)+'</p></div></div>'
    + '<div class="buy_prodbx"><img src="'+setImg(t.n)+'" alt="" class="pakge_product"></div></div>';
}
var tiersEl = document.getElementById('tiers');
tiersEl.addEventListener('click', function(e){ var t=e.target.closest('.tier'); if(t){ st.n=+t.dataset.n; st.picked=true; err(''); render(); } });

function current(){ if(needOpt()) return null; var id=VMAP[optKey(st.n)]; return id?{id:id,available:AVAIL[id]!==false}:null; }
var busy=false;
function render(){
  var t = TIERS.filter(function(x){return x.n===st.n;})[0];
  $$('[data-opt]').forEach(function(b){ b.classList.toggle('is-on', b.dataset.opt===st.opt); });
  var cur=document.getElementById('sizeCur'); if(cur) cur.textContent = st.opt || '未選択';
  tiersEl.innerHTML = TIERS.map(tierHTML).join('');
  var bp=$('[data-btnprice]'); if(bp && !busy) bp.textContent = yen(t.price)+'（1日あたり約'+Math.max(1,Math.round(t.price/DAYS))+'円）';
}
function err(m){ var e=document.getElementById('buyErr'); if(!e) return; e.textContent=m||''; e.hidden=!m; }
function shake(el){ el.scrollIntoView({behavior:'smooth',block:'center'}); el.classList.remove('kata-shake'); void el.offsetWidth; el.classList.add('kata-shake'); }
function askOpt(){ shake(sizesEl); }
function needSet(){ shake(tiersEl); }

/* ===== カート（Shopify の /cart.js を直接読む） ===== */
var busy=false,checkoutNav=false,ADD_TIMEOUT=12000,replaceKey=null;
function withTimeout(promise,ms,msg){return new Promise(function(res,rej){var t=setTimeout(function(){rej(Error(msg||'timeout'));},ms);promise.then(function(v){clearTimeout(t);res(v);},function(e){clearTimeout(t);rej(e);});});}
function setLoading(on){var a=$('#atc');a.classList.toggle('busy',on);a.style.pointerEvents=on?'none':'';}
async function api(path,body){var r=await withTimeout(fetch(root+path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{cache:'no-store'}),ADD_TIMEOUT,'timeout');var j;try{j=await r.json();}catch(_){throw Error('〔札〕');}if(!r.ok)throw Error(j.description||j.message||'カートを更新できませんでした。');return j;}

var kc=$('#kc'),kcOv=$('#kcOv'),lastCart=null;
function openCart(){kcOv.hidden=false;kc.classList.add('open');kc.setAttribute('aria-hidden','false');document.documentElement.style.overflow='hidden';}
function closeCart(){kc.classList.remove('open');kc.setAttribute('aria-hidden','true');kcOv.hidden=true;document.documentElement.style.overflow='';}
kcOv.addEventListener('click',closeCart);
kc.addEventListener('click',function(e){ if(e.target.closest('[data-kc-close]')) closeCart(); });
document.addEventListener('keydown',function(e){ if(e.key==='Escape'&&kc.classList.contains('open')) closeCart(); });
/* ヘッダーのカートの印を押したら、このカートを開く */
document.addEventListener('click',function(e){var a=e.target.closest('#cart-icon-bubble,a[href="/cart"],.header__icon--cart');if(!a||a.closest('#kpdp'))return;e.preventDefault();e.stopImmediatePropagation();openCart();refreshCart();},true);

function setsOf(item){var m=String(item.variant_title||'').match(new RegExp('(\\d+)'+UNIT));return m?+m[1]:0;}
function renderCart(cart){
  lastCart=cart;
  var items=cart.items||[];
  $('#kcCount').textContent=cart.item_count;
  var pieces=0,wasTotal=0,biggest=0;
  $('#kcEmpty').hidden=items.length>0; $('#kcPowers').hidden=!items.length; kc.querySelector('.kc-quote').hidden=!items.length;
  $('#kcItems').innerHTML=items.map(function(it){
    var n=setsOf(it), t=TIERS.filter(function(x){return x.n===n;})[0];
    var unitWas=(t&&t.was)?t.was*100:it.original_price;
    wasTotal+=unitWas*it.quantity; pieces+=(n||1)*it.quantity; if(n>biggest)biggest=n;
    var title=n?'〔札〕'+setName(n):it.product_title;
    var off=unitWas>it.original_price?Math.floor((1-it.original_price/unitWas)*100):0;
    return '<div class="kc-item"><img src="'+setImg(n||1)+'" alt=""><div><h5>'+title+'</h5><div class="v">'+(st.opt||'')+(it.quantity>1?' × '+it.quantity:'')+'</div>'
      +(n?'<button type="button" class="chg" data-chg="'+it.key+'">変更する</button>':'<span class="qty"><button type="button" data-q="'+it.key+'" data-d="-1">−</button><span>'+it.quantity+'</span><button type="button" data-q="'+it.key+'" data-d="1">＋</button></span>')
      +'</div><div class="r">'+'<b>'+yen(it.original_line_price/100)+'</b>'
      +'<button type="button" class="del" data-del="'+it.key+'" aria-label="削除"><svg viewBox="0 0 24 24"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/></svg></button></div></div>';
  }).join('');
  /* 帯：選んだセットで言葉を変える */
  var b=$('#kcBanner');
  if(!items.length){b.textContent='〔帯の言葉〕';}
  else if(biggest===2){b.textContent='〔帯の言葉〕';}
  else if(biggest===3){b.textContent='〔帯の言葉〕';}
  else {b.textContent='〔帯の言葉〕';}
  var disc=cart.total_discount||0;
  $('#kcDisc').hidden=!disc; $('#kcDisc').innerHTML='<span>割引</span><span>−'+yen(disc/100)+'</span>';
  $('#kcTotal').textContent=yen(cart.total_price/100);
  $('#kcWas').textContent=wasTotal>cart.total_price?yen(wasTotal/100):'';
  $('#kcDay').hidden=!pieces; $('#kcDay').textContent='1日 約'+Math.max(1,Math.round(cart.total_price/100/DAYS))+'円';
  $('#kcPay').style.display=items.length?'':'none';
}
window.__kcRender=function(c){openCart();renderCart(c);};
async function refreshCart(){ try{ var cart=await api('cart.js'); renderCart(cart); return cart; }catch(e){} }
function syncBubble(){ fetch(root+'products/'+HANDLE+'?sections=cart-icon-bubble',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){var el=document.getElementById('cart-icon-bubble'); if(el&&j['cart-icon-bubble']){var d=document.createElement('div'); d.innerHTML=j['cart-icon-bubble']; var n=d.querySelector('#cart-icon-bubble')||d.firstElementChild; if(n) el.innerHTML=n.innerHTML;}}).catch(function(){}); }
async function afterChange(cart){ renderCart(cart); syncBubble(); }
kc.addEventListener('click',async function(e){
  var t=e.target.closest('[data-del],[data-q],[data-chg]'); if(!t) return;
  try{
    if(t.dataset.del){ afterChange(await api('cart/change.js',{id:t.dataset.del,quantity:0})); return; }
    if(t.dataset.q){ var it=lastCart.items.filter(function(x){return x.key===t.dataset.q;})[0]; afterChange(await api('cart/change.js',{id:t.dataset.q,quantity:Math.max(0,it.quantity+Number(t.dataset.d))})); return; }
    if(t.dataset.chg){ /* 変更する：選び直してもらい、次に入れた時にこの行と入れ替える */
      var it2=lastCart.items.filter(function(x){return x.key===t.dataset.chg;})[0];
      replaceKey=it2.key; st.n=setsOf(it2)||st.n; st.picked=true;
      render(); closeCart(); $('#tiers').scrollIntoView({behavior:'smooth',block:'center'});
      return;
    }
  }catch(err){ alert(err.message||'カートを更新できませんでした。'); refreshCart(); }
});

async function addToCart(direct){
  if(busy)return;
  if(!st.picked && !direct){ needSet(); return; }
  if(needOpt()){ askOpt(); return; }
  var v=current();
  if(!v){err('ただいま準備中です。少し待ってから、もう一度お試しください。');return;}
  if(!v.available){err('このセットは在庫切れです。別のセットをお選びください。');return;}
  busy=true;setLoading(true,direct);err('');
  var navigating=false;
  try{
    if(!direct){ openCart(); $('#kcItems').innerHTML='<div class="kc-loading">カートに追加しています…</div>'; }
    await api('cart/add.js',{items:[{id:v.id,quantity:1}]});
    if(replaceKey){ try{ await api('cart/change.js',{id:replaceKey,quantity:0}); }catch(_){} replaceKey=null; }
    if(direct){ navigating=true;checkoutNav=true;location.assign(root+'checkout');return; }
    await afterChange(await api('cart.js'));
  }catch(e){ err((e&&e.message)||'カートに追加できませんでした。少し待ってから、もう一度お試しください。'); refreshCart(); }
  finally{if(!navigating){busy=false;setLoading(false);render();}}
}
window.addEventListener('pageshow',function(e){if(e.persisted&&(checkoutNav||!busy)){busy=false;checkoutNav=false;setLoading(false);render();}});
$('#atc').addEventListener('click',function(e){e.preventDefault();addToCart(false);});

/* 比べるスライダー */
var ba=document.getElementById('ba'); if(ba){ var inp=ba.querySelector('input'); inp.addEventListener('input',function(){ ba.style.setProperty('--x',inp.value+'%'); }); }
/* 段ごとのボタン → 買う所へ */
$$('a.btn_scorall').forEach(function(a){ a.addEventListener('click',function(e){ e.preventDefault(); tiersEl.scrollIntoView({behavior:'smooth',block:'center'}); }); });
render();
})();
