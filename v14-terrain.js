
(()=>{
  if(window.__CROWNFALL_V14_TERRAIN__) return;
  window.__CROWNFALL_V14_TERRAIN__=true;

  const style=document.createElement('style');
  style.id='crownfall-v14-terrain-style';
  style.textContent=
    '#v13Terrain{display:none!important}'+
    '#v14Terrain{position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden}'+
    '#v14Terrain svg{width:100%;height:100%;display:block}'+
    '#mapWrap{background:radial-gradient(ellipse at 20% 14%,rgba(213,196,137,.13),transparent 20%),radial-gradient(ellipse at 75% 78%,rgba(39,67,38,.24),transparent 26%),linear-gradient(150deg,#71835d 0%,#667951 22%,#5a6c48 48%,#526241 72%,#48583b 100%)!important;box-shadow:inset 0 0 95px rgba(17,28,16,.78),inset 0 0 0 1px rgba(244,228,183,.08)!important}'+
    '#mapWrap::after{content:"";position:absolute;inset:0;z-index:0;pointer-events:none;opacity:.2;mix-blend-mode:soft-light;background-image:repeating-linear-gradient(17deg,rgba(255,246,214,.022) 0 1px,transparent 1px 8px),repeating-linear-gradient(101deg,rgba(31,43,24,.024) 0 1px,transparent 1px 11px)}'+
    '#roads{z-index:2!important}.road{stroke:#c9ae79!important;stroke-width:.72!important;opacity:.92!important;stroke-dasharray:1.5 1.05!important;filter:drop-shadow(0 1.2px .5px #3d2c1d) drop-shadow(0 0 1px #5c442b)}'+
    '.road-player{stroke:#ecd296!important;stroke-width:.88!important;filter:drop-shadow(0 1.3px .6px #3c2817) drop-shadow(0 0 1.5px rgba(255,225,153,.42))}';
  document.head.appendChild(style);

  function hashSeed(input){
    let h=2166136261>>>0;
    String(input||'crownfall').split('').forEach(function(c){h^=c.charCodeAt(0);h=Math.imul(h,16777619);});
    return h>>>0;
  }
  function rngFrom(seed){
    let s=hashSeed(seed)||1;
    return function(){s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};
  }

  let terrainKey='';
  function makeTerrain(w){
    const rng=rngFrom((w.seed||'crownfall')+'-v14-land');
    let s='<svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">';
    s+='<defs><linearGradient id="v14river" x1="0" x2="1"><stop offset="0" stop-color="#607c77" stop-opacity=".42"/><stop offset=".45" stop-color="#a8c8c2" stop-opacity=".68"/><stop offset="1" stop-color="#668783" stop-opacity=".44"/></linearGradient><filter id="v14soft"><feGaussianBlur stdDeviation=".55"/></filter></defs>';

    for(let i=0;i<18;i++){
      const x=(rng()*92+4).toFixed(1),y=(rng()*90+5).toFixed(1),rx=(5+rng()*11).toFixed(1),ry=(3+rng()*8).toFixed(1);
      const colors=['#8a8d59','#93845a','#58734b','#70865a'];
      s+='<ellipse cx="'+x+'" cy="'+y+'" rx="'+rx+'" ry="'+ry+'" fill="'+colors[i%colors.length]+'" opacity="'+(.09+rng()*.11).toFixed(2)+'" transform="rotate('+(-30+rng()*60).toFixed(0)+' '+x+' '+y+')"/>';
    }

    const r=[8+rng()*17,-5,25+rng()*14,18+rng()*15,48+rng()*14,38+rng()*18,63+rng()*15,66+rng()*16,83+rng()*12,105];
    const river='M '+r[0]+' '+r[1]+' C '+r[2]+' '+r[3]+', '+r[4]+' '+r[5]+', '+r[6]+' '+r[7]+' S '+r[8]+' '+r[9]+', '+r[8]+' '+r[9];
    s+='<path d="'+river+'" fill="none" stroke="#304d4b" stroke-opacity=".26" stroke-width="10" filter="url(#v14soft)"/><path d="'+river+'" fill="none" stroke="url(#v14river)" stroke-width="6.5"/><path d="'+river+'" fill="none" stroke="#d0e4dd" stroke-opacity=".22" stroke-width="1.1"/>';

    for(let i=0;i<12;i++){
      const x=5+rng()*88,y=8+rng()*80,w=5+rng()*9,h=2+rng()*4,rot=-30+rng()*60;
      s+='<g transform="translate('+x.toFixed(1)+' '+y.toFixed(1)+') rotate('+rot.toFixed(0)+')" opacity=".34"><path d="M '+(-w).toFixed(1)+' 1 Q 0 '+(-h).toFixed(1)+' '+w.toFixed(1)+' 1" fill="none" stroke="#4d4532" stroke-width=".6"/><path d="M '+(-w*.72).toFixed(1)+' 1 Q 0 '+(-h*.64).toFixed(1)+' '+(w*.72).toFixed(1)+' 1" fill="none" stroke="#817556" stroke-width=".42"/></g>';
    }

    for(let c=0;c<14;c++){
      const cx=4+rng()*92,cy=7+rng()*84,n=5+Math.floor(rng()*7);
      s+='<g opacity="'+(.38+rng()*.2).toFixed(2)+'">';
      for(let j=0;j<n;j++){
        const x=cx+(rng()-.5)*7,y=cy+(rng()-.5)*5,rr=.75+rng()*1.15;
        s+='<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+rr.toFixed(2)+'" fill="'+(j%2?'#26482c':'#315437')+'" stroke="#1b3420" stroke-width=".18"/><rect x="'+(x-.12).toFixed(1)+'" y="'+(y+rr*.55).toFixed(1)+'" width=".24" height="'+(.7+rr*.3).toFixed(2)+'" fill="#59452f"/>';
      }
      s+='</g>';
    }

    (w.settlements||[]).forEach(function(st,i){
      if(i%3!==0)return;
      const local=rngFrom((w.seed||'x')+'-field-'+st.id);
      const x=Math.max(3,Math.min(92,st.x+(local()>.5?3.6:-7.4))),y=Math.max(4,Math.min(92,st.y+(local()-.5)*5.2));
      const rot=(-28+local()*56).toFixed(0),ww=(4+local()*3).toFixed(1),hh=(2+local()*2).toFixed(1);
      s+='<g transform="translate('+x.toFixed(1)+' '+y.toFixed(1)+') rotate('+rot+')" opacity=".37"><rect x="0" y="0" width="'+ww+'" height="'+hh+'" rx=".3" fill="#b19d63" stroke="#6a603f" stroke-width=".2"/>';
      for(let k=1;k<5;k++){const yy=(Number(hh)*k/5).toFixed(2);s+='<path d="M .2 '+yy+' H '+(Number(ww)-.2).toFixed(1)+'" stroke="#796d42" stroke-width=".16"/>';}
      s+='</g>';
    });

    for(let i=0;i<4;i++){
      const x=8+rng()*80,y=10+rng()*74,rx=2.3+rng()*3.2,ry=1.4+rng()*2.3;
      s+='<ellipse cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" rx="'+rx.toFixed(1)+'" ry="'+ry.toFixed(1)+'" fill="#83a7a1" opacity=".25" stroke="#bdd4c9" stroke-opacity=".2" stroke-width=".3" transform="rotate('+(-20+rng()*40).toFixed(0)+' '+x.toFixed(1)+' '+y.toFixed(1)+')"/>';
    }

    s+='<g transform="translate(91 10)" opacity=".18" stroke="#f1e2bb" fill="none"><circle r="5.4" stroke-width=".35"/><path d="M0 -5 L.9 -1 L5 0 L.9 1 L0 5 L-.9 1 L-5 0 L-.9 -1 Z" stroke-width=".38"/><text x="0" y="-6.2" text-anchor="middle" fill="#f1e2bb" stroke="none" font-size="2.2" font-family="Georgia">N</text></g>';
    return s+'</svg>';
  }

  function build(){
    const api=window.__CROWNFALL__,wrap=document.querySelector('#mapWrap');
    if(!api || !api.getWorld || !wrap)return;
    const w=api.getWorld(); if(!w)return;
    const key=String(w.seed||'crownfall');
    if(key===terrainKey && document.querySelector('#v14Terrain'))return;
    terrainKey=key;
    const old=document.querySelector('#v14Terrain'); if(old)old.remove();
    const layer=document.createElement('div');layer.id='v14Terrain';layer.innerHTML=makeTerrain(w);
    wrap.insertBefore(layer,wrap.firstChild);
  }

  function boot(){
    if(!window.__CROWNFALL__ || !document.querySelector('#mapWrap')){setTimeout(boot,80);return;}
    build();setInterval(build,1200);
  }
  boot();
})();
