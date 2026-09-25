import json, os, time, math, pathlib
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1:8000/index.html"
OUT=pathlib.Path("qa-output"); OUT.mkdir(exist_ok=True)

def box(page,sel):
    loc=page.locator(sel)
    if loc.count()==0: return None
    try: return loc.first.bounding_box()
    except: return None

def intersects(a,b):
    if not a or not b: return False
    return not (a["x"]+a["width"]<=b["x"] or b["x"]+b["width"]<=a["x"] or a["y"]+a["height"]<=b["y"] or b["y"]+b["height"]<=a["y"])

def covered(page,sel):
    b=box(page,sel); t=box(page,"#tutorial")
    return intersects(b,t)

def in_panel_view(page,sel):
    b=box(page,sel); p=box(page,"#panel")
    if not b or not p: return False
    return b["y"] >= p["y"]-1 and b["y"]+b["height"] <= p["y"]+p["height"]+1

def snap(page,name):
    page.screenshot(path=str(OUT/name),full_page=True)

def stage(page):
    return page.evaluate("window.__CROWNFALL__.getWorld().onboarding?.stage ?? 99")

def world(page):
    return page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld();
      return {day:w.day, stage:w.onboarding?.stage ?? 99, active:!!w.onboarding?.active,
        steward:w.playerSteward?.policy, settlements:w.settlements.length, roads:w.roads.length};
    }""")

def map_counts(page):
    return page.evaluate("""() => ({
      settlements: document.querySelectorAll('#map .settlement').length,
      labels: document.querySelectorAll('#map .label').length,
      roads: document.querySelectorAll('#roads .road').length,
      bridges: document.querySelectorAll('#v14Terrain rect[fill="#b59a6a"]').length,
      dryCrossings: document.querySelectorAll('#v14Terrain ellipse[fill="#60704d"]').length,
      river: document.querySelectorAll('#v14Terrain path[stroke="#263f42"]').length
    })""")

def visible_text(page):
    return page.locator("#panel").inner_text()

def river_audit(page):
    return page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld();
      const p=document.querySelector('#v14Terrain path[stroke="#263f42"]');
      if(!p) return {river:false};
      const len=p.getTotalLength(), pts=[];
      for(let i=0;i<=600;i++){const q=p.getPointAtLength(len*i/600);pts.push({x:q.x,y:q.y});}
      const ds=w.settlements.map(s=>{
        let m=999; for(const q of pts)m=Math.min(m,Math.hypot(s.x-q.x,s.y-q.y));
        return {id:s.id,name:s.name,d:m};
      });
      const close=ds.filter(x=>x.d<4);
      const dry=[...document.querySelectorAll('#v14Terrain ellipse[fill="#60704d"]')].map(e=>({x:+e.getAttribute('cx'),y:+e.getAttribute('cy')}));
      const cross=(a,b,c,d)=>{
        const den=(a.x-b.x)*(c.y-d.y)-(a.y-b.y)*(c.x-d.x);if(Math.abs(den)<1e-8)return null;
        const n1=a.x*b.y-a.y*b.x,n2=c.x*d.y-c.y*d.x,x=(n1*(c.x-d.x)-(a.x-b.x)*n2)/den,y=(n1*(c.y-d.y)-(a.y-b.y)*n2)/den;
        const within=(v,p,q)=>v>=Math.min(p,q)-1e-5&&v<=Math.max(p,q)+1e-5;
        return within(x,a.x,b.x)&&within(y,a.y,b.y)&&within(x,c.x,d.x)&&within(y,c.y,d.y)?{x,y}:null;
      };
      const hits=[];
      for(const [ai,bi] of w.roads){const A=w.settlements[ai],B=w.settlements[bi];for(let j=0;j<pts.length-1;j++){const h=cross(A,B,pts[j],pts[j+1]);if(!h)continue;if(!hits.some(x=>Math.hypot(x.x-h.x,x.y-h.y)<2.2))hits.push(h);break;}}
      return {river:true,closest:Math.min(...ds.map(x=>x.d)),closeCount:close.length,
        uncoveredClose:close.filter(c=>!dry.some(d=>Math.hypot(w.settlements[c.id].x-d.x,w.settlements[c.id].y-d.y)<.2)).length,
        visualCrossings:hits.length,
        bridgeCount:document.querySelectorAll('#v14Terrain rect[fill="#b59a6a"]').length,
        dryCount:dry.length};
    }""")

def click_real(page,sel):
    page.locator(sel).first.click(timeout=3000)
    page.wait_for_timeout(220)

def profile(browser,name,viewport,is_mobile=False,has_touch=False):
    ctx=browser.new_context(viewport=viewport,is_mobile=is_mobile,has_touch=has_touch,device_scale_factor=3 if is_mobile else 1)
    page=ctx.new_page()
    errors=[]
    page.on("pageerror",lambda e: errors.append("pageerror:"+str(e)))
    page.on("console",lambda m: errors.append("console:"+m.text) if m.type=="error" else None)
    page.goto(BASE,wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    page.wait_for_timeout(1300)
    result={"profile":name,"viewport":viewport,"initial":world(page),"stages":{},"errors":errors}

    # Stage 0
    result["stages"]["0"]={"map":map_counts(page),"tutorial":page.locator("#tutorial").inner_text(),
      "tutorialBox":box(page,"#tutorial"),"panelBox":box(page,"#panel"),
      "legendHidden":page.locator("#legend").evaluate("e=>e.classList.contains('hidden')"),
      "musicHidden":page.locator("#v13Music").evaluate("e=>e.classList.contains('hidden')")}
    snap(page,f"{name}-00-day0.png")
    click_real(page,"#introNext")

    # Stage 1: required Farms button should be usable, not covered.
    result["stages"]["1"]={"stage":stage(page),"farmsVisible":page.locator('[data-build="farms"]').first.is_visible(),
      "farmsCovered":covered(page,'[data-build="farms"]'),"farmsInPanelView":in_panel_view(page,'[data-build="farms"]'),"effectText":page.locator('.building').filter(has_text="Farms").first.inner_text()}
    snap(page,f"{name}-01-farms.png")
    click_real(page,'[data-build="farms"]')

    # Stage 2: recruit Militia.
    result["stages"]["2"]={"stage":stage(page),"militiaVisible":page.locator('[data-recruit="militia"][data-q="5"]').is_visible(),
      "militiaCovered":covered(page,'[data-recruit="militia"][data-q="5"]'),"militiaInPanelView":in_panel_view(page,'[data-recruit="militia"][data-q="5"]'),
      "raidersVisible":page.locator('[data-recruit="raiders"]').count()>0 and page.locator('[data-recruit="raiders"]').first.is_visible(),
      "cavalryVisible":page.locator('[data-recruit="cavalry"]').count()>0 and page.locator('[data-recruit="cavalry"]').first.is_visible()}
    snap(page,f"{name}-02-militia.png")
    click_real(page,'[data-recruit="militia"][data-q="5"]')

    # Stage 3 local reveal.
    page.wait_for_timeout(200)
    neutrals=page.locator("#map .settlement.neutral")
    result["stages"]["3"]={"stage":stage(page),"map":map_counts(page),"neutralCount":neutrals.count(),
      "firstNeutralCovered":covered(page,"#map .settlement.neutral")}
    snap(page,f"{name}-03-neighbors.png")
    if neutrals.count(): click_real(page,"#map .settlement.neutral")

    # Stage 4 inspect/prepare.
    result["stages"]["4"]={"stage":stage(page),"raidVisible":page.locator('[data-prepare="raid"]').count()>0 and page.locator('[data-prepare="raid"]').first.is_visible(),
      "raidCovered":covered(page,'[data-prepare="raid"]'),"raidInPanelView":in_panel_view(page,'[data-prepare="raid"]'),"panelText":visible_text(page)[:2500]}
    snap(page,f"{name}-04-orders.png")
    click_real(page,'[data-prepare="raid"]')

    # Stage 5 full reveal.
    page.wait_for_timeout(1300)
    panel=visible_text(page)
    result["stages"]["5"]={"stage":stage(page),"map":map_counts(page),
      "resourceLabels":{k:(k in panel) for k in ["Food","Wood","Iron","Influence"]},
      "river":river_audit(page),"tutorial":page.locator("#tutorial").inner_text()}
    snap(page,f"{name}-05-full-map.png")

    # Finish/start clock, confirm tutorial disappears and day can advance.
    click_real(page,"#introFinish")
    page.wait_for_timeout(4300)
    result["finished"]={"world":world(page),"tutorialHidden":page.locator("#tutorial").evaluate("e=>e.classList.contains('hidden')"),
      "map":map_counts(page)}
    snap(page,f"{name}-06-running.png")
    if name.startswith("desktop"):
        samples=[]
        for i in range(10):
            page.once("dialog",lambda d:d.accept())
            page.locator("#newGame").click()
            page.wait_for_timeout(1350)
            samples.append(river_audit(page))
        result["bridgeSample"]=samples
    ctx.close()
    return result

with sync_playwright() as p:
    allr=[]
    desktop=p.chromium.launch(headless=True)
    allr.append(profile(desktop,"desktop-chromium",{"width":1440,"height":900}))
    desktop.close()

    mobile=p.webkit.launch(headless=True)
    allr.append(profile(mobile,"iphone-webkit",{"width":390,"height":844},True,True))
    mobile.close()

    with open(OUT/"results.json","w") as fh: json.dump(allr,fh,indent=2)
    print(json.dumps(allr,indent=2))
    hard=[]
    for r in allr:
        if r.get("errors"): hard.append(r["profile"]+": browser errors: "+" | ".join(r["errors"]))
        expected={"0":0,"1":1,"2":2,"3":3,"4":4,"5":5}
        for k,v in expected.items():
            got = r["initial"]["stage"] if k=="0" else r["stages"].get(k,{}).get("stage")
            if got is not None and got!=v: hard.append(f'{r["profile"]}: stage {k} expected {v}, got {got}')
        if r["stages"].get("5",{}).get("map",{}).get("settlements")!=48:
            hard.append(r["profile"]+": full map did not reveal 48 settlements")
        if not r["stages"]["0"].get("legendHidden"): hard.append(r["profile"]+": legend exposed during staged reveal")
        if not r["stages"]["0"].get("musicHidden"): hard.append(r["profile"]+": music button exposed during tutorial")
        for key,label in [("farmsInPanelView","Farms"),("militiaInPanelView","Militia")]:
            if not r["stages"][key=="farmsInPanelView" and "1" or "2"].get(key): hard.append(r["profile"]+f": {label} action not brought into visible panel")
        if not r["stages"]["4"].get("raidInPanelView"): hard.append(r["profile"]+": Raid action not brought into visible panel")
        geo=r["stages"]["5"].get("river",{})
        if geo.get("uncoveredClose",0): hard.append(r["profile"]+": river still visually crosses an uncleared settlement")
        if geo.get("bridgeCount")!=geo.get("visualCrossings"): hard.append(r["profile"]+": bridge count does not match visual river crossings")
        if r["finished"]["world"].get("day",0)<1: hard.append(r["profile"]+": Start the clock did not advance the day")
    if hard:
        raise SystemExit("HARD QA FAILURES\n" + "\n".join(hard))
