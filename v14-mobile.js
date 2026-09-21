
(()=>{
  if(window.__CROWNFALL_V14_MOBILE__) return;
  window.__CROWNFALL_V14_MOBILE__=true;

  const style=document.createElement('style');
  style.id='crownfall-v14-mobile-style';
  style.textContent=
    '@media(max-width:900px){'+
    '#app{min-height:100dvh!important}'+
    'main{grid-template-rows:minmax(240px,47%) minmax(0,53%)!important;transition:grid-template-rows .18s ease}'+
    'body.v14-panel-focus main{grid-template-rows:minmax(155px,25%) minmax(0,75%)!important}'+
    'body.v14-panel-focus #mapWrap{min-height:155px!important}'+
    'aside,#panel{min-height:0!important}'+
    '#panel{padding-bottom:10px!important}'+
    'footer{flex-wrap:nowrap!important;overflow-x:auto!important;overflow-y:hidden!important;min-height:48px!important}'+
    'footer button{min-height:39px!important}'+
    '.mobileSettlementNav{grid-template-columns:repeat(5,minmax(0,1fr))!important}'+
    '.mobileSettlementNav button{font-size:9px!important;padding:6px 2px!important;min-height:38px!important}'+
    '.label-foreign:not(.capitalLabel):not(.label-selected),.label-neutral:not(.label-selected){display:none!important}'+
    '.capitalLabel{display:block!important;font-size:8px!important;font-weight:700!important;color:#f5ead1!important}'+
    '#legend{left:6px!important;right:6px!important;bottom:6px!important;max-width:none!important;width:auto!important;max-height:44px!important;display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;overflow-y:hidden!important;white-space:nowrap!important;padding:5px 7px!important;gap:8px!important;font-size:8px!important;backdrop-filter:blur(4px)}'+
    '#legend .legendItem{flex:0 0 auto!important}#legend .legendItem small{font-size:7px!important}'+'#mapWrap>#v13Music{position:absolute!important;right:8px!important;top:76px!important;z-index:24!important;min-width:78px!important;min-height:38px!important;padding:6px 8px!important;font-size:10px!important;background:#20251aee!important;border:1px solid #c6a64f!important;box-shadow:0 3px 12px #0008!important;backdrop-filter:blur(4px)}'+'#mapWrap>#v13Music.v14-music-on{background:#d3b45b!important;color:#17180f!important;border-color:#f0d98a!important}'+
    '.building,.unitRow{padding:9px 0!important}.building .desc{display:block!important;font-size:10px!important;line-height:1.25!important}'+
    '.building>button{min-width:88px!important;min-height:42px!important;font-size:12px!important}'+
    '.recruitActions{min-width:158px!important}.recruitActions button{min-height:39px!important}'+
    '}'+
    '@media(max-width:900px) and (orientation:landscape){'+
    'main{grid-template-columns:minmax(0,1.15fr) minmax(330px,.85fr)!important;grid-template-rows:1fr!important}'+
    'body.v14-panel-focus main{grid-template-columns:minmax(0,.75fr) minmax(390px,1.25fr)!important;grid-template-rows:1fr!important}'+
    '}';
  document.head.appendChild(style);


  function placeMusic(){
    const b=document.querySelector('#v13Music');
    const map=document.querySelector('#mapWrap');
    const footer=document.querySelector('footer');
    if(!b||!map||!footer)return;
    const mobile=window.matchMedia('(max-width:900px)').matches;
    if(mobile){
      if(b.parentElement!==map)map.appendChild(b);
      b.classList.toggle('v14-music-on',/ON/i.test(b.textContent||''));
      b.title=/ON/i.test(b.textContent||'')?'Mute soundtrack':'Play soundtrack';
    }else{
      if(b.parentElement!==footer){
        const threat=document.querySelector('#threatPause');
        footer.insertBefore(b,threat||document.querySelector('#status')||null);
      }
      b.classList.remove('v14-music-on');
    }
  }

  function labels(){
    document.querySelectorAll('#map .label').forEach(function(label){
      const prev=label.previousElementSibling;
      if(prev && prev.classList && prev.classList.contains('settlement') && prev.classList.contains('capital')) label.classList.add('capitalLabel');
      else label.classList.remove('capitalLabel');
    });
  }

  function notice(){
    const api=window.__CROWNFALL__,n=document.querySelector('#mapNotice');
    if(!api || !api.getWorld || !n || n.classList.contains('threat')) return;
    const w=api.getWorld(),m=n.textContent.match(/Day\s+(\d+)/i);
    if(m && Number.isFinite(w.day) && w.day-Number(m[1])>6) n.classList.add('hidden');
  }

  function workspace(){
    document.querySelectorAll('.mobileSettlementNav').forEach(function(nav){
      if(nav.querySelector('.v14-map-button')) return;
      const b=document.createElement('button');
      b.type='button'; b.className='v14-map-button'; b.textContent='Map'; b.title='Give the map more room';
      b.addEventListener('click',function(){
        document.body.classList.remove('v14-panel-focus');
        const map=document.querySelector('#mapWrap'); if(map) map.scrollIntoView({block:'start'});
      });
      nav.appendChild(b);
      nav.querySelectorAll('[data-mobile-jump]').forEach(function(btn){
        btn.addEventListener('click',function(){
          if(btn.dataset.mobileJump!=='resourcesCard') document.body.classList.add('v14-panel-focus');
        });
      });
    });
  }

  function tabs(){
    document.querySelectorAll('nav .tab').forEach(function(tab){
      if(tab.dataset.v14Bound) return;
      tab.dataset.v14Bound='1';
      tab.addEventListener('click',function(){
        if(tab.dataset.tab!=='settlement') document.body.classList.add('v14-panel-focus');
      });
    });
  }

  let queued=false;
  function run(){queued=false;placeMusic();labels();notice();workspace();tabs();}
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(run);}

  function boot(){
    if(!window.__CROWNFALL__ || !document.querySelector('#map')){setTimeout(boot,80);return;}
    run();
    const observer=new MutationObserver(schedule);
    const map=document.querySelector('#map'),panel=document.querySelector('#panel');
    observer.observe(map,{childList:true,subtree:true});
    observer.observe(panel,{childList:true,subtree:true});
    setInterval(schedule,1000);
  }
  boot();
})();
