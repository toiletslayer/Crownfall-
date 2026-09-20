
(()=>{
  if(window.__CROWNFALL_V14_VILLAGES__) return;
  window.__CROWNFALL_V14_VILLAGES__=true;

  const style=document.createElement('style');
  style.id='crownfall-v14-village-style';
  style.textContent=
    '.settlement{width:60px!important;height:59px!important;overflow:visible!important}'+
    '.settlement .settlementArt{width:60px!important;height:59px!important;overflow:visible!important;filter:drop-shadow(0 4px 2px rgba(16,16,10,.58))!important}'+
    '.settlement.selected .settlementArt{filter:drop-shadow(0 0 5px #fff1af) drop-shadow(0 4px 2px rgba(16,16,10,.7))!important}'+
    '.settlement.capital::after{top:-12px!important;font-size:15px!important}'+
    '.v14-ground{fill:rgba(41,48,31,.22)}.v14-field{fill:#a79a62;stroke:#605b3c;stroke-width:.45;opacity:.86}.v14-furrow{stroke:#71693f;stroke-width:.48;opacity:.75}.v14-road{fill:#957954;opacity:.78}'+
    '.v14-stone{fill:#b6ab8e;stroke:#4a4235;stroke-width:.8}.v14-stone-dark{fill:#8f8977;stroke:#443d32;stroke-width:.8}.v14-timber{fill:#866144;stroke:#3c291c;stroke-width:.75}.v14-plaster{fill:#c7bea1;stroke:#4a4031;stroke-width:.72}'+
    '.v14-roof{fill:#69463a;stroke:#34251f;stroke-width:.78}.v14-roof2{fill:#62584a;stroke:#302a24;stroke-width:.78}.v14-window{fill:#e8ca78;stroke:#5c4827;stroke-width:.28}'+
    '.v14-tree-trunk{fill:#5f4831}.v14-tree-a{fill:#29482d;stroke:#182d1c;stroke-width:.45}.v14-tree-b{fill:#345436;stroke:#1c321f;stroke-width:.45}.v14-rock{fill:#847e6c;stroke:#4a473e;stroke-width:.55}'+
    '.v14-wall{fill:#aaa18a;stroke:#4a4335;stroke-width:.7}.v14-banner-pole{stroke:#403020;stroke-width:.75}.v14-banner{fill:var(--realm);stroke:#2a2118;stroke-width:.45}'+
    '.label{font-size:10px!important;transform:translate(-50%,24px)!important;text-shadow:0 1px 3px #000,0 0 4px #000!important}'+
    '@media(max-width:900px){.settlement{width:58px!important;height:57px!important}.settlement .settlementArt{width:58px!important;height:57px!important}.label{font-size:7.5px!important;max-width:76px!important;transform:translate(-50%,24px)!important}}'+
    '@media(max-width:390px){.settlement{width:54px!important;height:53px!important}.settlement .settlementArt{width:54px!important;height:53px!important}}';
  document.head.appendChild(style);

  function hashSeed(input){
    let h=2166136261>>>0;
    String(input||'village').split('').forEach(function(c){h^=c.charCodeAt(0);h=Math.imul(h,16777619);});
    return h>>>0;
  }
  function rngFrom(seed){
    let s=hashSeed(seed)||1;
    return function(){s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
  }

  function tree(x,y,scale,alt){
    return '<g transform="translate('+x+' '+y+') scale('+scale+')"><rect class="v14-tree-trunk" x="-.45" y="1.8" width=".9" height="2.2" rx=".2"/><path class="'+(alt?'v14-tree-b':'v14-tree-a')+'" d="M0 -4 L3 1.5 L1.5 1.5 L2.3 3 L-2.3 3 L-1.5 1.5 L-3 1.5 Z"/></g>';
  }
  function house(x,y,w,h,alt){
    return '<g><rect class="v14-plaster" x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" rx=".7"/><path class="'+(alt?'v14-roof2':'v14-roof')+'" d="M '+(x-1)+' '+y+' L '+(x+w/2)+' '+(y-h*.55)+' L '+(x+w+1)+' '+y+' Z"/><rect class="v14-timber" x="'+(x+w*.42)+'" y="'+(y+h*.52)+'" width="'+Math.max(1,w*.18)+'" height="'+(h*.48)+'"/><rect class="v14-window" x="'+(x+w*.17)+'" y="'+(y+h*.3)+'" width="'+Math.max(.8,w*.14)+'" height="'+Math.max(.8,h*.17)+'"/></g>';
  }

  function village(st,color){
    const b=st.buildings||{},rng=rngFrom('village-'+st.id+'-'+(st.name||''));
    const keep=b.keep||1,farms=b.farms||1,lumber=b.lumber||1,mine=b.mine||1,barracks=b.barracks||1,walls=b.walls||0,hall=b.hall||0;
    const roofAlt=rng()>.5;
    let h='<svg class="settlementArt v14Village" viewBox="0 0 72 64" aria-hidden="true" style="--realm:'+color+'"><ellipse class="v14-ground" cx="36" cy="53" rx="30" ry="8"/><ellipse cx="36" cy="55" rx="25" ry="4.7" fill="#172016" opacity=".3"/>';
    h+='<path class="v14-road" d="M34 62 C35 54 34 49 38 43 C41 38 45 33 49 27 L53 22 L57 19 L59 17 L56 16 L51 19 L47 23 C43 27 39 32 36 37 C33 42 31 49 30 62 Z"/>';

    if(farms>=1){
      const strips=Math.min(4,1+Math.floor(farms/2));
      h+='<g transform="translate(4 37) rotate(-8)"><rect class="v14-field" x="0" y="0" width="18" height="10" rx="1"/>';
      for(let i=1;i<=strips+1;i++)h+='<path class="v14-furrow" d="M1 '+(i*10/(strips+2))+' H17"/>';
      h+='</g>';
    }
    if(lumber>=1){
      h+=tree(60,39,1.15,false)+tree(65,43,.9,true);
      if(lumber>=4)h+=tree(57,45,.78,true);
    }
    if(mine>=2)h+='<g transform="translate(6 29)"><path class="v14-rock" d="M0 7 L4 1 L9 4 L12 10 L3 11 Z"/><path class="v14-rock" d="M8 9 L13 3 L18 8 L16 13 L9 13 Z"/><path d="M5 10 L11 5" stroke="#40372e" stroke-width="1"/></g>';

    h+=house(18,32,10,13,roofAlt)+house(45,35,9,11,!roofAlt);
    if(keep>=2)h+=house(30,29,11,15,!roofAlt);
    if(barracks>=2)h+='<g><rect class="v14-timber" x="49" y="26" width="12" height="7" rx=".6"/><path class="v14-roof2" d="M47 26 L55 21 L63 26 Z"/><path d="M51 30h8" stroke="#d5c8a4" stroke-width=".7"/></g>';

    const kh=16+Math.min(8,keep*1.6),ky=37-kh;
    h+='<g><rect class="v14-stone" x="31" y="'+ky.toFixed(1)+'" width="13" height="'+kh.toFixed(1)+'" rx=".8"/><rect class="v14-stone-dark" x="34.5" y="'+(ky+kh-6).toFixed(1)+'" width="5" height="6"/><path class="v14-roof2" d="M29 '+ky.toFixed(1)+' L37.5 '+(ky-7).toFixed(1)+' L46 '+ky.toFixed(1)+' Z"/>';
    if(keep>=4)h+='<rect class="v14-stone" x="41" y="'+(ky+3).toFixed(1)+'" width="6" height="'+(kh-3).toFixed(1)+'"/><path class="v14-roof2" d="M40 '+(ky+3)+' L44 '+(ky-1)+' L48 '+(ky+3)+' Z"/>';
    h+='</g>';

    if(hall>=1||st.capital)h+='<g><path class="v14-banner-pole" d="M38 '+(ky-6)+' V'+(ky+5)+'"/><path class="v14-banner" d="M38 '+(ky-5)+' h8 l-2 3 h-6z"/></g>';
    h+='<rect class="v14-window" x="34" y="'+(ky+5).toFixed(1)+'" width="2.1" height="2.5"/><rect class="v14-window" x="39" y="'+(ky+5).toFixed(1)+'" width="2.1" height="2.5"/>';

    if(walls>=1){
      h+='<g opacity="'+(walls>=4?'.98':'.88')+'"><path class="v14-wall" fill-rule="evenodd" d="M12 48 Q13 20 36 14 Q60 18 62 48 L57 52 Q55 27 36 22 Q18 26 17 52 Z"/>';
      [[15,42],[55,42],[20,24],[49,24]].forEach(function(t){h+='<rect class="v14-wall" x="'+t[0]+'" y="'+t[1]+'" width="5" height="8" rx=".5"/>';});
      h+='</g>';
    }
    return h+'</svg>';
  }

  function decorate(){
    const api=window.__CROWNFALL__;
    if(!api || !api.getWorld)return;
    const w=api.getWorld(); if(!w)return;
    document.querySelectorAll('#map .settlement').forEach(function(el){
      const id=Number(el.dataset.id),st=w.settlements && w.settlements[id];
      if(!st)return;
      const sig=[st.owner,st.capital].concat(Object.values(st.buildings||{})).join(':');
      if(el.dataset.v14Village===sig)return;
      el.dataset.v14Village=sig;
      const color=st.owner==null?'#aaa58d':((w.factions[st.owner]&&w.factions[st.owner].color)||'#aaa58d');
      el.innerHTML=village(st,color);
    });
  }

  let queued=false;
  function schedule(){if(queued)return;queued=true;requestAnimationFrame(function(){queued=false;decorate();});}
  function boot(){
    if(!window.__CROWNFALL__ || !document.querySelector('#map')){setTimeout(boot,80);return;}
    decorate();
    new MutationObserver(schedule).observe(document.querySelector('#map'),{childList:true,subtree:true});
    setInterval(schedule,950);
  }
  boot();
})();
