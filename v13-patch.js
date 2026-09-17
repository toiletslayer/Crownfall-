(()=>{
  if(window.__CROWNFALL_V13_PATCH__) return;
  window.__CROWNFALL_V13_PATCH__=true;

  const HOUSE_NAMES=['House Calder','House Vale','House Harker','House Fenner','House Morcant','House Bellamy'];
  const LEGACY_NAMES=['The Alder Crown','Bluewater Compact','Red Banner League','Green March','Violet Court','Amber Pact'];

  const style=document.createElement('style');
  style.id='crownfall-v13-style';
  style.textContent=`
    #mapWrap{
      background:
        radial-gradient(circle at 18% 16%,rgba(244,226,171,.13),transparent 16%),
        radial-gradient(circle at 78% 22%,rgba(192,221,173,.18),transparent 20%),
        radial-gradient(circle at 31% 78%,rgba(112,138,88,.19),transparent 18%),
        linear-gradient(180deg,#71865d 0%,#657852 22%,#566845 48%,#4d5f3f 74%,#455739 100%)!important;
      box-shadow:inset 0 0 90px #142014,inset 0 0 0 1px rgba(252,240,198,.05)!important;
    }
    #mapWrap::before{content:'';position:absolute;inset:0;pointer-events:none;z-index:0;opacity:.22;background:
      radial-gradient(circle at 20% 35%,rgba(255,244,198,.08) 0 2px,transparent 3px) 0 0/34px 34px,
      radial-gradient(circle at 70% 65%,rgba(26,40,20,.09) 0 1.5px,transparent 2.5px) 0 0/26px 26px,
      linear-gradient(125deg,transparent 0 46%,rgba(255,248,220,.04) 50%,transparent 54%) 0 0/18px 18px;
    }
    #v13Terrain{position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden}
    #roads{z-index:1;overflow:visible!important}#map{z-index:2}#legend,.mapNotice{z-index:12!important}
    .road{stroke:#d7bd82!important;stroke-width:.7!important;opacity:.9!important;stroke-linecap:round!important;stroke-dasharray:2.5 1.7!important;filter:drop-shadow(0 1px 1px rgba(55,37,20,.75)) drop-shadow(0 0 1px rgba(82,54,28,.5))}
    .road-player{stroke:#f6dfa3!important;stroke-width:.85!important;opacity:1!important;filter:drop-shadow(0 1px 1px rgba(61,38,17,.9)) drop-shadow(0 0 2px rgba(246,223,163,.35))}
    .v13-patch{position:absolute;border-radius:999px;filter:blur(9px);opacity:.65;mix-blend-mode:soft-light}
    .v13-patch.fertile{background:radial-gradient(circle,#a0ba70 0%,rgba(159,185,109,.55) 45%,transparent 74%)}
    .v13-patch.earth{background:radial-gradient(circle,#8a7352 0%,rgba(138,115,82,.38) 38%,transparent 72%)}
    .v13-patch.scrub{background:radial-gradient(circle,#80915a 0%,rgba(128,145,90,.42) 40%,transparent 72%)}
    .v13-ridge{position:absolute;width:80px;height:19px;border-radius:999px;background:linear-gradient(90deg,transparent,rgba(75,59,37,.45),rgba(135,112,76,.38),transparent);filter:blur(1px);opacity:.56}
    .v13-trees{position:absolute;display:flex;gap:2px;opacity:.58;filter:drop-shadow(0 1px 0 rgba(0,0,0,.18))}
    .v13-tree{width:12px;height:14px;background:linear-gradient(180deg,#294c2f,#1e3422);clip-path:polygon(50% 0,100% 70%,75% 70%,75% 100%,25% 100%,25% 70%,0 70%);border-radius:1px}
    .v13-lake{position:absolute;width:75px;height:43px;border-radius:58% 42% 61% 39%/47% 55% 45% 53%;background:radial-gradient(circle at 38% 36%,rgba(217,238,234,.56),rgba(118,159,170,.46) 55%,rgba(64,97,104,.31) 78%,transparent 80%);opacity:.56}
    .v13-river{position:absolute;inset:0;width:100%;height:100%}.v13-river path{fill:none;stroke:rgba(176,208,203,.42);stroke-width:16;stroke-linecap:round;filter:blur(2px)}.v13-river .core{stroke:rgba(210,234,228,.5);stroke-width:7;filter:none}
    .v13-compass{position:absolute;right:14px;top:14px;width:72px;height:72px;opacity:.18;color:#f7ebc6}.v13-compass svg{width:100%;height:100%}
    .settlement{width:50px!important;height:54px!important}.settlementArt{filter:drop-shadow(0 4px 3px #0008)!important}.label{font-size:11px!important;transform:translate(-50%,21px)!important;font-weight:600;letter-spacing:.02em}
    .army{width:23px!important;height:23px!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;transform:translate(-50%,-50%)!important;overflow:visible!important}
    .army svg{width:100%;height:100%;display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.72))}.army .v13-pole{stroke:#402f1e;stroke-width:1.5}.army .v13-cloth{fill:var(--flag);stroke:#21170f;stroke-width:.8}.army .v13-badge{fill:rgba(255,248,223,.92)}
    footer{gap:6px!important;flex-wrap:wrap}#v13Music{min-width:100px}
    @media(max-width:900px){.v13-compass{width:54px;height:54px;right:10px;top:10px;opacity:.14}.road{stroke-width:.62!important}.road-player{stroke-width:.75!important}.army{width:21px!important;height:21px!important}}
  `;
  document.head.appendChild(style);

  function hashSeed(input='crownfall'){
    let h=2166136261>>>0;for(const c of String(input)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;
  }
  function rngFrom(seed){let s=hashSeed(seed)||1;return()=>{s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}

  let terrainSeed='';
  function buildTerrain(){
    const wrap=document.querySelector('#mapWrap');if(!wrap||!window.__CROWNFALL__)return;
    const world=window.__CROWNFALL__.getWorld?.();if(!world)return;
    const key=String(world.seed||'crownfall');if(key===terrainSeed&&document.querySelector('#v13Terrain'))return;
    terrainSeed=key;document.querySelector('#v13Terrain')?.remove();
    const layer=document.createElement('div');layer.id='v13Terrain';
    const rng=rngFrom(key+'-v13-terrain');
    for(let i=0;i<14;i++){
      const d=document.createElement('div');d.className='v13-patch '+(i%3===0?'fertile':i%3===1?'earth':'scrub');
      d.style.left=(6+rng()*88)+'%';d.style.top=(8+rng()*82)+'%';d.style.width=(9+rng()*15)+'%';d.style.height=(7+rng()*12)+'%';layer.appendChild(d);
    }
    for(let i=0;i<9;i++){
      const d=document.createElement('div');d.className='v13-ridge';d.style.left=(6+rng()*86)+'%';d.style.top=(8+rng()*82)+'%';d.style.transform=`rotate(${-32+rng()*64}deg)`;layer.appendChild(d);
    }
    for(let i=0;i<11;i++){
      const d=document.createElement('div');d.className='v13-trees';d.style.left=(5+rng()*90)+'%';d.style.top=(8+rng()*82)+'%';const n=2+Math.floor(rng()*4);for(let j=0;j<n;j++){const t=document.createElement('span');t.className='v13-tree';d.appendChild(t);}layer.appendChild(d);
    }
    for(let i=0;i<3;i++){
      const d=document.createElement('div');d.className='v13-lake';d.style.left=(10+rng()*75)+'%';d.style.top=(14+rng()*62)+'%';d.style.transform=`rotate(${-20+rng()*40}deg)`;layer.appendChild(d);
    }
    const a=[12+rng()*18,-8+rng()*8,30+rng()*18,20+rng()*16,58+rng()*18,46+rng()*18,66+rng()*18,74+rng()*14,82+rng()*12,102+rng()*6];
    layer.insertAdjacentHTML('beforeend',`<svg class="v13-river" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M ${a[0]} ${a[1]} C ${a[2]} ${a[3]}, ${a[4]} ${a[5]}, ${a[6]} ${a[7]} S ${a[8]} ${a[9]}, ${a[8]} ${a[9]}"/><path class="core" d="M ${a[0]} ${a[1]} C ${a[2]} ${a[3]}, ${a[4]} ${a[5]}, ${a[6]} ${a[7]} S ${a[8]} ${a[9]}, ${a[8]} ${a[9]}"/></svg><div class="v13-compass"><svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" stroke-width="2"/><path d="M50 10 L57 43 L90 50 L57 57 L50 90 L43 57 L10 50 L43 43 Z" fill="none" stroke="currentColor" stroke-width="2"/><text x="50" y="24" text-anchor="middle" font-size="16" fill="currentColor">N</text></svg></div>`);
    wrap.insertBefore(layer,wrap.firstChild);
  }

  function renameWorld(){
    const api=window.__CROWNFALL__;if(!api?.getWorld)return false;const w=api.getWorld();if(!w?.factions)return false;
    let changed=false;
    w.factions.forEach((f,i)=>{if(HOUSE_NAMES[i]&&f.name!==HOUSE_NAMES[i]){f.name=HOUSE_NAMES[i];changed=true;}});
    if(Array.isArray(w.events))for(const e of w.events){if(!e?.text)continue;for(let i=0;i<LEGACY_NAMES.length;i++){if(e.text.includes(LEGACY_NAMES[i])){e.text=e.text.split(LEGACY_NAMES[i]).join(HOUSE_NAMES[i]);changed=true;}}}
    if(changed)api.refresh?.();
    return true;
  }

  function flagSvg(color){return `<svg viewBox="0 0 24 24" aria-hidden="true" style="--flag:${color}"><path class="v13-pole" d="M6 3v18"/><path class="v13-cloth" d="M7 4c4-1.6 6.5 2 10 .5v8.2c-3.2 1.2-5.9-1.8-10-.3z"/><circle class="v13-badge" cx="10.6" cy="8.6" r="1.15"/></svg>`;}
  function decorateArmies(){
    document.querySelectorAll('#map .army').forEach(el=>{
      const raw=el.style.backgroundColor||el.style.background||'#d8c796';
      if(el.dataset.v13Flag===raw)return;
      el.dataset.v13Flag=raw;el.style.setProperty('--flag',raw);el.innerHTML=flagSvg(raw);
    });
  }

  let audioCtx=null,master=null,musicTimer=null,musicStep=0,musicOn=false;
  const pattern=[0,3,7,10,7,3,12,10];
  const freq=s=>220*Math.pow(2,s/12);
  function ensureAudio(){if(audioCtx)return audioCtx;const C=window.AudioContext||window.webkitAudioContext;if(!C)return null;audioCtx=new C();master=audioCtx.createGain();master.gain.value=.045;master.connect(audioCtx.destination);return audioCtx;}
  function tone(f,t,d=1.55,type='triangle',vol=.14){if(!audioCtx||!master)return;const o=audioCtx.createOscillator(),g=audioCtx.createGain();o.type=type;o.frequency.setValueAtTime(f,t);g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(vol,t+.08);g.gain.exponentialRampToValueAtTime(vol*.5,t+.48);g.gain.exponentialRampToValueAtTime(.0001,t+d);o.connect(g);g.connect(master);o.start(t);o.stop(t+d+.05);}
  function bar(){if(!musicOn||!audioCtx)return;const t=audioCtx.currentTime+.03;for(let i=0;i<4;i++){const r=pattern[(musicStep+i)%pattern.length],at=t+i*1.9;tone(freq(r),at,1.7,'triangle',.14);tone(freq(r+12),at+.44,1.05,'sine',.055);if((musicStep+i)%2===0)tone(freq(r-12),at,.95,'sawtooth',.035);}musicStep=(musicStep+4)%pattern.length;}
  function updateMusicButton(){const b=document.querySelector('#v13Music');if(b)b.textContent=`Music: ${musicOn?'ON':'OFF'}`;}
  async function toggleMusic(){const c=ensureAudio();if(!c)return;musicOn=!musicOn;updateMusicButton();if(musicOn){await c.resume();bar();clearInterval(musicTimer);musicTimer=setInterval(bar,7600);}else{clearInterval(musicTimer);musicTimer=null;if(c.state==='running')c.suspend();}}
  function ensureMusicButton(){
    const footer=document.querySelector('footer');if(!footer||document.querySelector('#v13Music'))return;
    const b=document.createElement('button');b.id='v13Music';b.type='button';b.textContent='Music: OFF';b.title='Toggle the original ambient soundtrack';b.addEventListener('click',toggleMusic);
    const threat=document.querySelector('#threatPause');footer.insertBefore(b,threat||document.querySelector('#status')||null);
  }

  const observer=new MutationObserver(()=>{decorateArmies();ensureMusicButton();});
  function boot(){
    if(!window.__CROWNFALL__||!document.querySelector('#map')){setTimeout(boot,80);return;}
    renameWorld();buildTerrain();decorateArmies();ensureMusicButton();
    const map=document.querySelector('#map');observer.observe(map,{childList:true,subtree:true});
    setInterval(()=>{const before=terrainSeed;renameWorld();buildTerrain();decorateArmies();if(before!==terrainSeed)window.__CROWNFALL__?.refresh?.();},500);
    document.addEventListener('visibilitychange',()=>{if(!audioCtx||!musicOn)return;if(document.hidden&&audioCtx.state==='running')audioCtx.suspend();else if(!document.hidden&&audioCtx.state==='suspended')audioCtx.resume();});
  }
  boot();
})();
