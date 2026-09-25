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
      for(let i=0;i<=500;i++){const q=p.getPointAtLength(len*i/500);pts.push([q.x,q.y]);}
      const ds=w.settlements.map(s=>{
        let m=999; for(const q of pts)m=Math.min(m,Math.hypot(s.x-q[0],s.y-q[1]));
        return {id:s.id,name:s.name,d:m};
      });
      const close=ds.filter(x=>x.d<4);
      const dry=[...document.querySelectorAll('#v14Terrain ellipse[fill="#60704d"]')].map(e=>({x:+e.getAttribute('cx'),y:+e.getAttribute('cy')}));
      return {river:true,closest:Math.min(...ds.map(x=>x.d)),closeCount:close.length,
        uncoveredClose:close.filter(c=>!dry.some(d=>Math.hypot(w.settlements[c.id].x-d.x,w.settlements[c.id].y-d.y)<.2)).length,
        bridgeCount:document.querySelectorAll('#v14Terrain rect[fill="#b59a6a"]').length,
        dryCount:dry.length};
    }""")

def click_js(page,sel):
    page.evaluate("(s)=>document.querySelector(s)?.click()",sel)
    page.wait_for_timeout(150)

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
      "tutorialBox":box(page,"#tutorial"),"panelBox":box(page,"#panel")}
    snap(page,f"{name}-00-day0.png")
    click_js(page,"#introNext")

    # Stage 1: required Farms button should be usable, not covered.
    result["stages"]["1"]={"stage":stage(page),"farmsVisible":page.locator('[data-build="farms"]').first.is_visible(),
      "farmsCovered":covered(page,'[data-build="farms"]'),"effectText":page.locator('.building').filter(has_text="Farms").first.inner_text()}
    snap(page,f"{name}-01-farms.png")
    click_js(page,'[data-build="farms"]')

    # Stage 2: recruit Militia.
    result["stages"]["2"]={"stage":stage(page),"militiaVisible":page.locator('[data-recruit="militia"][data-q="5"]').is_visible(),
      "militiaCovered":covered(page,'[data-recruit="militia"][data-q="5"]'),
      "raidersVisible":page.locator('[data-recruit="raiders"]').count()>0 and page.locator('[data-recruit="raiders"]').first.is_visible(),
      "cavalryVisible":page.locator('[data-recruit="cavalry"]').count()>0 and page.locator('[data-recruit="cavalry"]').first.is_visible()}
    snap(page,f"{name}-02-militia.png")
    click_js(page,'[data-recruit="militia"][data-q="5"]')

    # Stage 3 local reveal.
    page.wait_for_timeout(200)
    neutrals=page.locator("#map .settlement.neutral")
    result["stages"]["3"]={"stage":stage(page),"map":map_counts(page),"neutralCount":neutrals.count(),
      "firstNeutralCovered":covered(page,"#map .settlement.neutral")}
    snap(page,f"{name}-03-neighbors.png")
    if neutrals.count(): click_js(page,"#map .settlement.neutral")

    # Stage 4 inspect/prepare.
    result["stages"]["4"]={"stage":stage(page),"raidVisible":page.locator('[data-prepare="raid"]').count()>0 and page.locator('[data-prepare="raid"]').first.is_visible(),
      "raidCovered":covered(page,'[data-prepare="raid"]'),"panelText":visible_text(page)[:2500]}
    snap(page,f"{name}-04-orders.png")
    click_js(page,'[data-prepare="raid"]')

    # Stage 5 full reveal.
    page.wait_for_timeout(1300)
    panel=visible_text(page)
    result["stages"]["5"]={"stage":stage(page),"map":map_counts(page),
      "resourceLabels":{k:(k in panel) for k in ["Food","Wood","Iron","Influence"]},
      "river":river_audit(page),"tutorial":page.locator("#tutorial").inner_text()}
    snap(page,f"{name}-05-full-map.png")

    # Finish/start clock, confirm tutorial disappears and day can advance.
    click_js(page,"#introFinish")
    page.wait_for_timeout(1250)
    result["finished"]={"world":world(page),"tutorialHidden":page.locator("#tutorial").evaluate("e=>e.classList.contains('hidden')"),
      "map":map_counts(page)}
    snap(page,f"{name}-06-running.png")
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
