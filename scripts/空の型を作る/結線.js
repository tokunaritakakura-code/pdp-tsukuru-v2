
/* ===== ワンドライ日本語版 結線（本家JSは除去済みのため自前で実装） ===== */
(function(){
  "use strict";
  var on=function(el,ev,fn){ if(el) el.addEventListener(ev,fn); };
  var all=function(sel,root){ return [].slice.call((root||document).querySelectorAll(sel)); };

  /* 2) ヒーロー内のミニFAQ */
  all('.hero_question_row').forEach(function(row){
    var head=row.querySelector('.hero_question_heading'), body=row.querySelector('.hero_question_content');
    if(!head||!body) return;
    body.style.display='none'; head.classList.remove('hero_question_heading_open');
    on(head,'click',function(){
      var open=(body.style.display!=='none');
      body.style.display= open ? 'none' : 'block';
      head.classList.toggle('hero_question_heading_open', !open);
    });
  });

  /* 3) よくある質問 */
  all('.faq_slide_row').forEach(function(row, i){
    var head=row.querySelector('.acdn_heading'), body=row.querySelector('.acdn_content');
    if(!head||!body) return;
    var open=(i===0);
    body.style.display= open ? 'block' : 'none';
    head.classList.toggle('accordion_open', open);
    on(head,'click',function(){
      var isOpen=(body.style.display!=='none');
      body.style.display= isOpen ? 'none' : 'block';
      head.classList.toggle('accordion_open', !isOpen);
    });
  });

  /* 4) ヒーローのメイン画像＋サムネイル */
  (function(){
    var main=document.querySelector('.hero_image_slider'), thumbs=document.querySelector('.hero_thumb_slider');
    if(!main) return;
    var ms=all('.slick-slide', main), ts=thumbs?all('.slick-slide',thumbs):[];
    function show(i){
      if(i<0||i>=ms.length) return;
      ms.forEach(function(s,k){ s.classList.toggle('slick-current', k===i); s.classList.toggle('slick-active', k===i); });
      ts.forEach(function(s,k){ s.classList.toggle('is-active', k===i); });
      if(ts[i] && thumbs){
        var list=thumbs.querySelector('.slick-list');
        if(list) list.scrollTo({left: ts[i].offsetLeft - ts[0].offsetLeft - list.clientWidth/2 + ts[i].offsetWidth/2, behavior:'smooth'});
      }
    }
    ts.forEach(function(s,i){ on(s,'click',function(){ show(i); }); });
    if(thumbs){
      var list=thumbs.querySelector('.slick-list');
      all('.slick-prev', thumbs).forEach(function(b){ on(b,'click',function(e){ e.preventDefault(); list.scrollBy({left:-list.clientWidth*0.8, behavior:'smooth'}); }); });
      all('.slick-next', thumbs).forEach(function(b){ on(b,'click',function(e){ e.preventDefault(); list.scrollBy({left: list.clientWidth*0.8, behavior:'smooth'}); }); });
    }
    show(0);
  })();

  /* 5) レビューのカルーセル */
  all('.petOwner_review_slider').forEach(function(sl){
    var list=sl.querySelector('.slick-list'), slides=all('.slick-slide', sl), dots=all('.slick-dots li', sl);
    if(!list||!slides.length) return;
    list.scrollLeft=0;
    function go(i){ var s=slides[Math.max(0,Math.min(i,slides.length-1))];
      if(s) list.scrollTo({left:s.offsetLeft-slides[0].offsetLeft, behavior:'smooth'}); }
    dots.forEach(function(li,i){ on(li,'click',function(){ go(i); }); });
    all('.slick-prev', sl).forEach(function(b){ on(b,'click',function(e){ e.preventDefault(); list.scrollBy({left:-list.clientWidth*0.9, behavior:'smooth'}); }); });
    all('.slick-next', sl).forEach(function(b){ on(b,'click',function(e){ e.preventDefault(); list.scrollBy({left: list.clientWidth*0.9, behavior:'smooth'}); }); });
    on(list,'scroll',function(){
      var idx=0, best=1e9;
      slides.forEach(function(s,i){ var d=Math.abs(s.offsetLeft-slides[0].offsetLeft-list.scrollLeft); if(d<best){best=d;idx=i;} });
      dots.forEach(function(li,i){ li.classList.toggle('slick-active', i===idx); });
    });
  });

  })();
