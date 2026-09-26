# PR11 rollout verification: current-head rerun
import json, os, time, math, pathlib, re
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1:8000/index.html"
OUT=pathlib.Path("qa-output"); OUT.mkdir(exist_ok=True)

# Catch the recurring $() vs $() selector-list regression before launching browsers.
source=pathlib.Path("index.html").read_text(encoding="utf-8")
bad_selector_lists=[]
for n,line in enumerate(source.splitlines(),1):
    if re.search(r'(?<!\$)\$\([^)]*\)\.forEach',line):
        bad_selector_lists.append((n,line.strip()))
if bad_selector_lists:
    raise SystemExit("Single-element selector used with .forEach(): "+repr(bad_selector_lists))
if "$$(" in source:
    raise SystemExit("Accidental triple-dollar selector found in index.html")

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

def tappable_index(page,sel):
    loc=page.locator(sel); t=box(page,"#tutorial"); vp=page.viewport_size
    for i in range(loc.count()):
        b=loc.nth(i).bounding_box()
        if not b: continue
        if b["y"] < 0 or b["y"]+b["height"] > vp["height"]: continue
        if b["x"] < 0 or b["x"]+b["width"] > vp["width"]: continue
        if not intersects(b,t): return i
    return -1

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
      river: document.querySelectorAll('#v14Terrain path[stroke="#263f42"]').length,
      terrainFields: document.querySelectorAll('#v14Terrain rect[fill="#b19d63"]').length,
      legacySettlementDecor: document.querySelectorAll('#map .terrainLayer .terrain').length
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
    if errors:
        raise RuntimeError(name+": startup browser errors: "+" | ".join(errors))
    result={"profile":name,"viewport":viewport,"initial":world(page),"stages":{},"errors":errors}

    # Stage 0
    music=page.locator("#v13Music")
    music_exists=music.count()>0
    result["stages"]["0"]={"map":map_counts(page),"tutorial":page.locator("#tutorial").inner_text(),
      "tutorialBox":box(page,"#tutorial"),"panelBox":box(page,"#panel"),
      "legendHidden":page.locator("#legend").evaluate("e=>e.classList.contains('hidden')"),
      "musicExists":music_exists,
      "musicHidden":music.first.evaluate("e=>e.classList.contains('hidden')") if music_exists else False,
      "timeControlsDisabled":page.locator(".time button").evaluate_all("els=>els.length>0&&els.every(e=>e.disabled)"),
      "otherTabsDisabled":page.locator("nav .tab:not([data-tab='settlement'])").evaluate_all("els=>els.length>0&&els.every(e=>e.disabled)"),
      "loadNewDisabled":page.locator("#load,#newGame").evaluate_all("els=>els.length===2&&els.every(e=>e.disabled)")}
    snap(page,f"{name}-00-day0.png")
    click_real(page,"#introNext")

    # Stage 1: on mobile, use the same Build shortcut the tutorial tells the player to use.
    if is_mobile: click_real(page,'[data-mobile-jump="buildingsCard"]')
    result["stages"]["1"]={"stage":stage(page),"farmsVisible":page.locator('[data-build="farms"]').first.is_visible(),
      "farmsCovered":covered(page,'[data-build="farms"]'),"farmsInPanelView":in_panel_view(page,'[data-build="farms"]'),
      "buildShortcutVisible":page.locator('[data-mobile-jump="buildingsCard"]').is_visible() if is_mobile else True,"effectText":page.locator('.building').filter(has_text="Farms").first.inner_text()}
    snap(page,f"{name}-01-farms.png")
    click_real(page,'[data-build="farms"]')
    autosave_stage2=page.evaluate("JSON.parse(localStorage.getItem('crownfall-autosave')).onboarding.stage")
    result["stages"]["2_autosave"]=autosave_stage2

    # Stage 2: use Recruit on mobile, then verify Militia is actually in the panel viewport.
    if is_mobile: click_real(page,'[data-mobile-jump="garrisonCard"]')
    result["stages"]["2"]={"stage":stage(page),"militiaVisible":page.locator('[data-recruit="militia"][data-q="5"]').is_visible(),
      "militiaCovered":covered(page,'[data-recruit="militia"][data-q="5"]'),"militiaInPanelView":in_panel_view(page,'[data-recruit="militia"][data-q="5"]'),
      "recruitShortcutVisible":page.locator('[data-mobile-jump="garrisonCard"]').is_visible() if is_mobile else True,
      "raidersVisible":page.locator('[data-recruit="raiders"]').count()>0 and page.locator('[data-recruit="raiders"]').first.is_visible(),
      "cavalryVisible":page.locator('[data-recruit="cavalry"]').count()>0 and page.locator('[data-recruit="cavalry"]').first.is_visible()}
    snap(page,f"{name}-02-militia.png")
    click_real(page,'[data-recruit="militia"][data-q="5"]')
    autosave_stage3=page.evaluate("JSON.parse(localStorage.getItem('crownfall-autosave')).onboarding.stage")
    result["stages"]["3_autosave"]=autosave_stage3

    # Stage 3 local reveal: at least one labeled Independent must be actually tappable.
    page.wait_for_timeout(450)
    neutrals=page.locator("#map .settlement.neutral")
    tap_i=tappable_index(page,"#map .settlement.neutral")
    visible_neutral_labels=page.locator("#map .label-neutral").evaluate_all("els=>els.filter(e=>getComputedStyle(e).display!=='none').length")
    result["stages"]["3"]={"stage":stage(page),"map":map_counts(page),"neutralCount":neutrals.count(),
      "tappableNeutralIndex":tap_i,"visibleNeutralLabels":visible_neutral_labels}
    snap(page,f"{name}-03-neighbors.png")
    if tap_i < 0: raise RuntimeError(name+": no Independent neighbor is tappable without tutorial overlap")
    neutrals.nth(tap_i).click(timeout=3000); page.wait_for_timeout(220)

    # Stage 4: use Actions on mobile, then verify the contextual order buttons are in view.
    if is_mobile: click_real(page,'[data-mobile-jump="quickOrders"]')
    result["stages"]["4"]={"stage":stage(page),"raidVisible":page.locator('[data-prepare="raid"]').count()>0 and page.locator('[data-prepare="raid"]').first.is_visible(),
      "raidCovered":covered(page,'[data-prepare="raid"]'),"raidInPanelView":in_panel_view(page,'[data-prepare="raid"]'),
      "actionsShortcutVisible":page.locator('[data-mobile-jump="quickOrders"]').is_visible() if is_mobile else True,"panelText":visible_text(page)[:2500]}
    snap(page,f"{name}-04-orders.png")
    click_real(page,'[data-prepare="raid"]')

    # Stage 5 full reveal.
    page.wait_for_timeout(1300)
    panel=visible_text(page)
    result["stages"]["5"]={"stage":stage(page),"map":map_counts(page),
      "resourceLabels":{k:(k in panel) for k in ["Food","Wood","Iron","Influence"]},
      "river":river_audit(page),"tutorial":page.locator("#tutorial").inner_text()}
    snap(page,f"{name}-05-full-map.png")

    # Finish/start clock, confirm tutorial disappears and Day 1 is actually reached.
    click_real(page,"#introFinish")
    day_advanced=True
    try:
        page.wait_for_function("window.__CROWNFALL__.getWorld().day >= 1",timeout=8000)
    except:
        day_advanced=False
    result["finished"]={"world":world(page),"tutorialHidden":page.locator("#tutorial").evaluate("e=>e.classList.contains('hidden')"),
      "normalSpeedActive":page.locator('.time [data-speed="0.25"]').evaluate("e=>e.classList.contains('active')"),
      "dayAdvanced":day_advanced,
      "timeControlsEnabled":page.locator(".time button").evaluate_all("els=>els.length>0&&els.every(e=>!e.disabled)"),
      "otherTabsEnabled":page.locator("nav .tab:not([data-tab='settlement'])").evaluate_all("els=>els.length>0&&els.every(e=>!e.disabled)"),
      "loadNewEnabled":page.locator("#load,#newGame").evaluate_all("els=>els.length===2&&els.every(e=>!e.disabled)"),
      "autosaveCompleted":page.evaluate("(()=>{const w=JSON.parse(localStorage.getItem('crownfall-autosave'));return !!w.onboarding&&!w.onboarding.active&&w.onboarding.stage===6;})()"),
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

def returning_player_rollout_checks(browser):
    ctx=browser.new_context(viewport={"width":1200,"height":820})
    page=ctx.new_page()
    page.goto(BASE,wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    # Simulate a v1.4.7 browser: old tutorial seen, but no v1.4.8 First Hour marker.
    page.evaluate("""() => {
      localStorage.setItem('crownfall-tutorial-seen','1');
      localStorage.removeItem('crownfall-first-hour-complete');
      localStorage.removeItem('crownfall-first-hour-v148-seen');
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    page.wait_for_timeout(250)
    shown_once={
      "active":page.evaluate("!!window.__CROWNFALL__.getWorld().onboarding?.active"),
      "stage":stage(page),
      "skipText":page.locator("#introSkip").inner_text() if page.locator("#introSkip").count() else "",
      "loadDisabled":page.locator("#load").is_disabled(),
      "newGameDisabled":page.locator("#newGame").is_disabled()
    }
    # Skipping counts as having seen v1.4.8 First Hour.
    page.locator("#introSkip").click()
    page.wait_for_timeout(180)
    after_skip={
      "marker":page.evaluate("localStorage.getItem('crownfall-first-hour-v148-seen')"),
      "active":page.evaluate("!!window.__CROWNFALL__.getWorld().onboarding?.active")
    }
    page.reload(wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    page.wait_for_timeout(220)
    no_repeat={
      "active":page.evaluate("!!window.__CROWNFALL__.getWorld().onboarding?.active"),
      "tutorialHidden":page.locator("#tutorial").evaluate("e=>e.classList.contains('hidden')")
    }
    ctx.close()
    return {"shownOnce":shown_once,"afterSkip":after_skip,"noRepeat":no_repeat}

def persistence_checks(browser):
    ctx=browser.new_context(viewport={"width":1200,"height":820})
    page=ctx.new_page()
    page.goto(BASE,wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    page.wait_for_timeout(300)
    # Reach stage 2 and save manually.
    click_real(page,"#introNext")
    click_real(page,'[data-build="farms"]')
    page.locator("#save").click(); page.wait_for_timeout(120)
    saved_stage=page.evaluate("JSON.parse(localStorage.getItem('crownfall-save')).onboarding.stage")
    # Advance to stage 3, then load the stage-2 manual save.
    click_real(page,'[data-recruit="militia"][data-q="5"]')
    page.locator("#load").click(); page.wait_for_timeout(250)
    restored={
      "stage":stage(page),
      "tutorial":page.locator("#tutorial").inner_text(),
      "timeLocked":page.locator(".time button").evaluate_all("els=>els.every(e=>e.disabled)")
    }
    # Stage 4 depends on the inspected Independent target; that target must survive save/load.
    click_real(page,'[data-recruit="militia"][data-q="5"]')
    page.wait_for_timeout(180)
    neutral=page.locator("#map .settlement.neutral").first
    neutral.click(); page.wait_for_timeout(180)
    target_name=page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld();
      return w.settlements[w.onboarding.targetId]?.name || '';
    }""")
    page.locator("#save").click(); page.wait_for_timeout(100)
    page.locator("#map .settlement.playerRealm").first.click(); page.wait_for_timeout(100)
    page.locator("#load").click(); page.wait_for_timeout(220)
    target_restore={
      "stage":stage(page),
      "targetName":target_name,
      "panelHasTarget":target_name in page.locator("#panel").inner_text(),
      "raidVisible":page.locator('[data-prepare="raid"]').count()>0 and page.locator('[data-prepare="raid"]').first.is_visible()
    }
    # A stale stage-4 save without a target must safely return to the Neighbors lesson.
    page.evaluate("""() => {
      const w=JSON.parse(window.__CROWNFALL__.save());
      w.onboarding={active:true,stage:4};
      localStorage.setItem('crownfall-save',JSON.stringify(w));
      localStorage.removeItem('crownfall-first-hour-complete');
      localStorage.removeItem('crownfall-tutorial-seen');
    }""")
    page.locator("#load").click(); page.wait_for_timeout(220)
    stale_stage4={"stage":stage(page),"tutorial":page.locator("#tutorial").inner_text()}
    # A legacy v1 save without onboarding must still load and hide tutorial chrome.
    page.evaluate("""() => {
      const w=JSON.parse(window.__CROWNFALL__.save());
      delete w.onboarding;
      w.playerSteward.policy='balanced';
      localStorage.setItem('crownfall-save',JSON.stringify(w));
      localStorage.removeItem('crownfall-first-hour-complete');
      localStorage.removeItem('crownfall-tutorial-seen');
    }""")
    page.locator("#load").click(); page.wait_for_timeout(250)
    legacy={
      "hasOnboarding":page.evaluate("'onboarding' in window.__CROWNFALL__.getWorld()"),
      "tutorialHidden":page.locator("#tutorial").evaluate("e=>e.classList.contains('hidden')"),
      "timeUnlocked":page.locator(".time button").evaluate_all("els=>els.every(e=>!e.disabled)")
    }
    # A stale active tutorial save must be normalized if completion was already recorded.
    page.evaluate("""() => {
      const w=JSON.parse(window.__CROWNFALL__.save());
      w.onboarding={active:true,stage:2};
      localStorage.setItem('crownfall-save',JSON.stringify(w));
      localStorage.setItem('crownfall-first-hour-complete','1');
      localStorage.setItem('crownfall-tutorial-seen','1');
    }""")
    page.locator("#load").click(); page.wait_for_timeout(250)
    normalized={
      "active":page.evaluate("!!window.__CROWNFALL__.getWorld().onboarding?.active"),
      "stage":page.evaluate("window.__CROWNFALL__.getWorld().onboarding?.stage"),
      "tutorialHidden":page.locator("#tutorial").evaluate("e=>e.classList.contains('hidden')")
    }
    ctx.close()
    return {"savedStage":saved_stage,"restored":restored,"targetRestore":target_restore,"staleStage4":stale_stage4,"legacy":legacy,"normalized":normalized}

with sync_playwright() as p:
    allr=[]
    desktop=p.chromium.launch(headless=True)
    allr.append(profile(desktop,"desktop-chromium",{"width":1440,"height":900}))
    persistence=persistence_checks(desktop)
    rollout=returning_player_rollout_checks(desktop)
    desktop.close()

    mobile=p.webkit.launch(headless=True)
    allr.append(profile(mobile,"iphone-webkit",{"width":390,"height":844},True,True))
    mobile.close()

    payload={"profiles":allr,"persistence":persistence,"rollout":rollout}
    with open(OUT/"results.json","w") as fh: json.dump(payload,fh,indent=2)
    print(json.dumps(payload,indent=2))
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
        if not r["stages"]["0"].get("musicExists"): hard.append(r["profile"]+": music button was not created")
        elif not r["stages"]["0"].get("musicHidden"): hard.append(r["profile"]+": music button exposed during tutorial")
        if not r["stages"]["0"].get("timeControlsDisabled"): hard.append(r["profile"]+": time controls are usable during paused onboarding")
        if not r["stages"]["0"].get("otherTabsDisabled"): hard.append(r["profile"]+": advanced tabs are usable during onboarding")
        if not r["stages"]["0"].get("loadNewDisabled"): hard.append(r["profile"]+": Load/New Game can bypass one-time First Hour")
        if r["stages"]["0"].get("map",{}).get("terrainFields",0)>1: hard.append(r["profile"]+": hidden settlement fields leak into Day 0")
        if r["stages"]["0"].get("map",{}).get("legacySettlementDecor",0)>1: hard.append(r["profile"]+": hidden settlement terrain markers leak into Day 0")
        if r["stages"].get("2_autosave")!=2: hard.append(r["profile"]+": onboarding stage 2 was not autosaved")
        if r["stages"].get("3_autosave")!=3: hard.append(r["profile"]+": onboarding stage 3 was not autosaved")
        if not r["stages"]["1"].get("buildShortcutVisible"): hard.append(r["profile"]+": Build shortcut unavailable during Farms lesson")
        if not r["stages"]["2"].get("recruitShortcutVisible"): hard.append(r["profile"]+": Recruit shortcut unavailable during Militia lesson")
        if not r["stages"]["4"].get("actionsShortcutVisible"): hard.append(r["profile"]+": Actions shortcut unavailable during order lesson")
        if r["stages"]["3"].get("tappableNeutralIndex",-1) < 0: hard.append(r["profile"]+": no tappable Independent neighbor during local reveal")
        if r["profile"].startswith("iphone"):
            if r["stages"]["3"].get("visibleNeutralLabels",0) < 1: hard.append(r["profile"]+": Independent neighbor labels hidden during tutorial")
            if not r["stages"]["1"].get("farmsInPanelView"): hard.append(r["profile"]+": Build shortcut did not bring Farms into view")
            if not r["stages"]["2"].get("militiaInPanelView"): hard.append(r["profile"]+": Recruit shortcut did not bring Militia into view")
            if not r["stages"]["4"].get("raidInPanelView"): hard.append(r["profile"]+": Actions shortcut did not bring Raid into view")
        if r["stages"]["0"].get("map",{}).get("bridges",0)!=0: hard.append(r["profile"]+": hidden roads leaked bridge geometry on Day 0")
        geo=r["stages"]["5"].get("river",{})
        if geo.get("uncoveredClose",0): hard.append(r["profile"]+": river still visually crosses an uncleared settlement")
        if geo.get("bridgeCount")!=geo.get("visualCrossings"): hard.append(r["profile"]+": bridge count does not match visual river crossings")
        if not r["finished"].get("normalSpeedActive"): hard.append(r["profile"]+": Start the clock did not select normal speed")
        if not r["finished"].get("dayAdvanced"): hard.append(r["profile"]+": Start the clock did not advance to Day 1")
        if not r["finished"].get("timeControlsEnabled"): hard.append(r["profile"]+": time controls stayed locked after onboarding")
        if not r["finished"].get("otherTabsEnabled"): hard.append(r["profile"]+": advanced tabs stayed locked after onboarding")
        if not r["finished"].get("loadNewEnabled"): hard.append(r["profile"]+": Load/New Game stayed locked after onboarding")
        if not r["finished"].get("autosaveCompleted"): hard.append(r["profile"]+": completed onboarding was not autosaved")
    if persistence["savedStage"]!=2: hard.append("persistence: manual tutorial save did not preserve stage 2")
    if persistence["restored"]["stage"]!=2 or "GARRISON" not in persistence["restored"]["tutorial"] or not persistence["restored"]["timeLocked"]:
        hard.append("persistence: loading a mid-tutorial save did not restore the correct paused lesson")
    tr=persistence["targetRestore"]
    if tr["stage"]!=4 or not tr["panelHasTarget"] or not tr["raidVisible"]:
        hard.append("persistence: stage-4 inspected target was not restored after load")
    if persistence["staleStage4"]["stage"]!=3 or "NEIGHBORS" not in persistence["staleStage4"]["tutorial"]:
        hard.append("persistence: stale stage-4 save without target did not recover to Neighbors lesson")
    if persistence["legacy"]["hasOnboarding"] or not persistence["legacy"]["tutorialHidden"] or not persistence["legacy"]["timeUnlocked"]:
        hard.append("persistence: legacy v1 save compatibility failed")
    if persistence["normalized"]["active"] or persistence["normalized"]["stage"]!=6 or not persistence["normalized"]["tutorialHidden"]:
        hard.append("persistence: completed user can be trapped by stale active onboarding save")
    if not rollout["shownOnce"]["active"] or rollout["shownOnce"]["stage"]!=0:
        hard.append("rollout: v1.4.7 returning player did not receive v1.4.8 First Hour")
    if "Skip" not in rollout["shownOnce"]["skipText"]:
        hard.append("rollout: returning player was not offered a skip option")
    if not rollout["shownOnce"]["loadDisabled"] or not rollout["shownOnce"]["newGameDisabled"]:
        hard.append("rollout: returning player can bypass First Hour via Load/New Game")
    if rollout["afterSkip"]["marker"]!="1" or rollout["afterSkip"]["active"]:
        hard.append("rollout: skipping First Hour did not persist v1.4.8 completion")
    if rollout["noRepeat"]["active"] or not rollout["noRepeat"]["tutorialHidden"]:
        hard.append("rollout: v1.4.8 First Hour repeated after being skipped once")
    if hard:
        raise SystemExit("HARD QA FAILURES\n" + "\n".join(hard))
