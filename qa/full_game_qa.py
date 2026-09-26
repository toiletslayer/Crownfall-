import json, pathlib, time
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1:8000/index.html"
OUT=pathlib.Path("qa-output-full"); OUT.mkdir(exist_ok=True)

def click(page,sel):
    loc=page.locator(sel)
    loc.wait_for(state="visible",timeout=5000)
    loc.click()

def skip_intro(page):
    if page.locator("#introSkip").count() and page.locator("#introSkip").is_visible():
        page.locator("#introSkip").click()
        page.wait_for_timeout(180)

def wval(page,expr):
    return page.evaluate("expr => eval(expr)",expr)

def desktop_journey(browser):
    ctx=browser.new_context(viewport={"width":1440,"height":900})
    page=ctx.new_page()
    errors=[]
    page.on("pageerror",lambda e: errors.append(str(e)))
    page.goto(BASE,wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    page.wait_for_timeout(500)
    skip_intro(page)
    if page.locator('.time [data-speed="0"]').count(): page.locator('.time [data-speed="0"]').click()
    result={"errors":errors}

    # Baseline UI / full map / help / music.
    result["baseline"]={
      "settlements":page.locator("#map .settlement").count(),
      "tabsEnabled":page.locator("nav .tab").evaluate_all("els=>els.every(e=>!e.disabled)"),
      "loadNewEnabled":page.locator("#load,#newGame").evaluate_all("els=>els.every(e=>!e.disabled)"),
      "musicVisible":page.locator("#v13Music").count()>0 and page.locator("#v13Music").is_visible()
    }
    click(page,"#help")
    result["help"]={"visible":not page.locator("#modal").evaluate("e=>e.classList.contains('hidden')"),
                    "text":page.locator("#modalContent").inner_text()}
    click(page,"#closeModal")
    if page.locator("#v13Music").count():
        before=page.locator("#v13Music").inner_text()
        page.locator("#v13Music").click();page.wait_for_timeout(150)
        after=page.locator("#v13Music").inner_text()
        result["musicToggle"]={"before":before,"after":after,"changed":before!=after}

    # Manual save, building upgrade, recruitment, then load exact manual snapshot.
    saved=json.loads(page.evaluate("window.__CROWNFALL__.save()"))
    click(page,"#save")
    cap=page.evaluate("window.__CROWNFALL__.getWorld().settlements.find(s=>s.owner===0).id")
    before_farms=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{cap}].buildings.farms")
    click(page,'[data-build="farms"]')
    after_farms=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{cap}].buildings.farms")
    before_mil=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{cap}].troops.militia")
    click(page,'[data-recruit="militia"][data-q="5"]')
    after_mil=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{cap}].troops.militia")
    click(page,"#load");page.wait_for_timeout(180)
    restored=json.loads(page.evaluate("window.__CROWNFALL__.save()"))
    result["buildRecruitSave"]={
      "farmIncrement":after_farms==before_farms+1,
      "militiaIncrement":after_mil==before_mil+5,
      "manualLoadExact":restored==saved
    }

    # Realm steward UI.
    click(page,'nav .tab[data-tab="realm"]')
    click(page,'[data-steward="military"]')
    military=page.evaluate("window.__CROWNFALL__.getWorld().playerSteward.policy")
    click(page,'[data-steward="off"]')
    off=page.evaluate("window.__CROWNFALL__.getWorld().playerSteward.policy")
    result["steward"]={"military":military,"off":off}

    # Diplomacy: envoys -> alliance; allied settlement must expose Reinforce, not hostile actions.
    click(page,'nav .tab[data-tab="diplomacy"]')
    f=1
    inf0=page.evaluate("window.__CROWNFALL__.getWorld().factions[0].influence")
    rel0=page.evaluate("window.__CROWNFALL__.getWorld().relations['0:1'].value")
    for _ in range(3):
        page.locator(f'[data-dip="improve"][data-f="{f}"]').click();page.wait_for_timeout(80)
    rel1=page.evaluate("window.__CROWNFALL__.getWorld().relations['0:1'].value")
    inf1=page.evaluate("window.__CROWNFALL__.getWorld().factions[0].influence")
    ally_btn=page.locator(f'[data-dip="alliance"][data-f="{f}"]')
    if ally_btn.count() and ally_btn.is_visible():
        ally_btn.click();page.wait_for_timeout(100)
    alliance=page.evaluate("window.__CROWNFALL__.getWorld().relations['0:1'].status")

    ally_sid=page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld();
      for(const el of document.querySelectorAll('#map .settlement')){
        const id=Number(el.dataset.id);
        if(w.settlements[id]?.owner===1)return id;
      }
      return null;
    }""")
    rendered_before_ally=page.locator("#map .settlement").count()
    if ally_sid is None:
        raise RuntimeError("No rendered House Vale settlement after alliance; rendered="+str(rendered_before_ally))
    page.locator(f'#map .settlement[data-id="{ally_sid}"]').click(timeout=5000);page.wait_for_timeout(100)
    allied_support="Allied Support" in page.locator("#panel").inner_text()
    hostile_on_ally=page.locator('[data-prepare="raid"],[data-prepare="annex"],[data-prepare="attack"]').count()
    reinf=page.locator('[data-prepare="reinforce"]')
    reinf.click();page.wait_for_timeout(100)
    mission_text=page.locator("#mission").inner_text()
    # Ensure origin can send a small reinforcement.
    page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld(),s=w.settlements.find(x=>x.owner===0);
      s.troops.militia=Math.max(s.troops.militia,20);
      window.__CROWNFALL__.refresh();
    }""")
    page.locator("#u_militia").fill("5")
    for k in ["spears","raiders","cavalry"]:
        if page.locator(f"#u_{k}").count(): page.locator(f"#u_{k}").fill("0")
    before_ally=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{ally_sid}].troops.militia")
    click(page,"#sendArmy");page.wait_for_timeout(100)
    army=page.evaluate("window.__CROWNFALL__.getWorld().armies.find(a=>a.owner===0&&a.mission==='reinforce')")
    if army:
        delta=max(1,army["arriveDay"]-page.evaluate("window.__CROWNFALL__.getWorld().day"))
        page.evaluate(f"window.__CROWNFALL__.advance({delta})");page.wait_for_timeout(120)
    after_ally=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{ally_sid}].troops.militia")
    result["alliance"]={
      "envoyRelationGain":rel1-rel0,
      "envoyInfluenceSpent":inf0-inf1,
      "status":alliance,
      "renderedSettlements":rendered_before_ally,
      "alliedSupport":allied_support,
      "hostileButtonsOnAlly":hostile_on_ally,
      "missionText":mission_text,
      "reinforcementArrived":after_ally>=before_ally+5
    }

    # Guaranteed UI raid against an Independent, then battle report via Chronicle.
    setup=page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld();
      const home=w.settlements.find(s=>s.owner===0);
      const edge=w.roads.find(([a,b])=>(a===home.id&&w.settlements[b].owner===null)||(b===home.id&&w.settlements[a].owner===null));
      let target=edge?w.settlements[edge[0]===home.id?edge[1]:edge[0]]:w.settlements.find(s=>s.owner===null);
      home.troops={militia:160,spears:80,raiders:50,cavalry:20};
      home.resources={food:5000,wood:5000,iron:5000};
      target.troops={militia:0,spears:0,raiders:0,cavalry:0};target.buildings.walls=0;target.buildings.keep=1;
      window.__CROWNFALL__.refresh();
      return {home:home.id,target:target.id,reports:w.battleReports.length};
    }""")
    page.locator(f'#map .settlement[data-id="{setup["target"]}"]').click();page.wait_for_timeout(80)
    raid_visible=page.locator('[data-prepare="raid"]').is_visible()
    page.locator('[data-prepare="raid"]').click();page.wait_for_timeout(80)
    for k,v in {"militia":"40","spears":"20","raiders":"10","cavalry":"0"}.items():
        if page.locator(f"#u_{k}").count(): page.locator(f"#u_{k}").fill(v)
    click(page,"#sendArmy");page.wait_for_timeout(80)
    raid_army=page.evaluate("window.__CROWNFALL__.getWorld().armies.find(a=>a.owner===0&&a.mission==='raid')")
    if raid_army:
        delta=max(1,raid_army["arriveDay"]-page.evaluate("window.__CROWNFALL__.getWorld().day"))
        page.evaluate(f"window.__CROWNFALL__.advance({delta})");page.wait_for_timeout(100)
    report_count=page.evaluate("window.__CROWNFALL__.getWorld().battleReports.length")
    raid_stat=page.evaluate("window.__CROWNFALL__.getWorld().stats.raids")
    click(page,'nav .tab[data-tab="chronicle"]')
    report_btn=page.locator('[data-report]').first
    report_open=False;report_text=""
    if report_btn.count():
        report_btn.click();page.wait_for_timeout(80)
        report_open=not page.locator("#modal").evaluate("e=>e.classList.contains('hidden')")
        report_text=page.locator("#modalContent").inner_text()
        click(page,"#closeModal")
    result["raidReport"]={"raidButtonVisible":raid_visible,"newReport":report_count>setup["reports"],"raidStat":raid_stat,
                          "reportModal":report_open,"reportText":report_text}

    # Guaranteed Annex through UI.
    page.evaluate(f"""() => {{
      const w=window.__CROWNFALL__.getWorld(),home=w.settlements[{setup["home"]}],t=w.settlements[{setup["target"]}];
      home.troops={{militia:180,spears:90,raiders:60,cavalry:20}};
      t.troops={{militia:0,spears:0,raiders:0,cavalry:0}};t.owner=null;t.buildings.walls=0;
      w.factions[0].influence=Math.max(w.factions[0].influence,100);
      window.__CROWNFALL__.refresh();
    }}""")
    inf_before=page.evaluate("window.__CROWNFALL__.getWorld().factions[0].influence")
    page.locator(f'#map .settlement[data-id="{setup["target"]}"]').click();page.wait_for_timeout(80)
    page.locator('[data-prepare="annex"]').click();page.wait_for_timeout(80)
    for k,v in {"militia":"50","spears":"25","raiders":"15","cavalry":"5"}.items():
        if page.locator(f"#u_{k}").count(): page.locator(f"#u_{k}").fill(v)
    click(page,"#sendArmy");page.wait_for_timeout(80)
    annex_army=page.evaluate("window.__CROWNFALL__.getWorld().armies.find(a=>a.owner===0&&a.mission==='annex')")
    if annex_army:
        delta=max(1,annex_army["arriveDay"]-page.evaluate("window.__CROWNFALL__.getWorld().day"))
        page.evaluate(f"window.__CROWNFALL__.advance({delta})");page.wait_for_timeout(100)
    owner_after=page.evaluate(f"window.__CROWNFALL__.getWorld().settlements[{setup['target']}].owner")
    inf_after=page.evaluate("window.__CROWNFALL__.getWorld().factions[0].influence")
    annex_report=page.evaluate("window.__CROWNFALL__.getWorld().battleReports.slice().reverse().find(r=>r.annexed)")
    result["annex"]={"owner":owner_after,"influenceSpent":inf_before-inf_after,
                     "reportSpent":annex_report["influenceSpent"] if annex_report else None}

    # Post-truce war button and actual relation transition.
    page.evaluate("""() => {const w=window.__CROWNFALL__.getWorld();if(w.day<100)window.__CROWNFALL__.advance(100-w.day);}""")
    click(page,'nav .tab[data-tab="diplomacy"]')
    war_btn=page.locator('[data-dip="war"][data-f="2"]')
    war_enabled=war_btn.count()>0 and not war_btn.is_disabled()
    if war_enabled: war_btn.click();page.wait_for_timeout(80)
    war_status=page.evaluate("window.__CROWNFALL__.getWorld().relations['0:2'].status")
    result["war"]={"enabledAfterTruce":war_enabled,"status":war_status}

    # Threat Pause through the actual animation/tick loop. Force a deterministic enemy frontier.
    page.evaluate("""() => {
      const w=window.__CROWNFALL__.getWorld(),target=w.settlements.find(s=>s.owner===0);
      for(const s of w.settlements){s.owner=2;s.capital=false;s.troops={militia:120,spears:80,raiders:60,cavalry:20};}
      target.owner=0;target.troops={militia:0,spears:0,raiders:0,cavalry:0};target.buildings={keep:1,farms:1,lumber:1,mine:1,barracks:1,walls:0,hall:0};
      w.factions[2].alive=true;w.factions[2].lastMilitaryDay=-99;w.factions[2].lastAdminDay=101;w.factions[2].influence=500;
      w.day=101;w.armies=[];w.relations['0:2']={status:'war',value:-80,since:101};
      window.__CROWNFALL__.refresh();
    }""")
    # Ensure Threat Pause is ON by reading/toggling the button.
    if "OFF" in page.locator("#threatPause").inner_text(): page.locator("#threatPause").click()
    page.locator('.time [data-speed="4"]').click()
    page.wait_for_timeout(900)
    result["threatPause"]={
      "warning": "Time paused" in page.locator("#status").inner_text(),
      "pauseActive":page.locator('.time [data-speed="0"]').evaluate("e=>e.classList.contains('active')"),
      "incomingArmies":page.evaluate("window.__CROWNFALL__.getWorld().armies.filter(a=>a.owner!==0&&window.__CROWNFALL__.getWorld().settlements[a.target]?.owner===0).length")
    }

    # New World + manual-save survival. First Hour marker means no repeat and Steward returns to Balanced.
    old_seed=page.evaluate("window.__CROWNFALL__.getWorld().seed")
    page.once("dialog",lambda d:d.accept())
    page.locator("#newGame").click();page.wait_for_timeout(250)
    new_seed=page.evaluate("window.__CROWNFALL__.getWorld().seed")
    result["newWorld"]={
      "seedChanged":new_seed!=old_seed,
      "tutorialActive":page.evaluate("!!window.__CROWNFALL__.getWorld().onboarding?.active"),
      "steward":page.evaluate("window.__CROWNFALL__.getWorld().playerSteward.policy")
    }
    click(page,"#load");page.wait_for_timeout(180)
    result["newWorld"]["manualSaveRestored"]=page.evaluate("window.__CROWNFALL__.getWorld().seed")==saved["seed"]

    result["errors"]=errors
    ctx.close()
    return result

def mobile_journey(browser):
    ctx=browser.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True)
    page=ctx.new_page();errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
    page.goto(BASE,wait_until="networkidle")
    page.wait_for_function("window.__CROWNFALL__ && window.__CROWNFALL__.getWorld()")
    page.wait_for_timeout(500);skip_intro(page);page.wait_for_timeout(350)
    if page.locator('.time [data-speed="0"]').count(): page.locator('.time [data-speed="0"]').click()
    result={"errors":errors}

    nav=page.locator(".mobileSettlementNav")
    result["nav"]={"exists":nav.count()>0,"mapButton":page.locator(".v14-map-button").count()>0}
    if page.locator('[data-mobile-jump="buildingsCard"]').count():
        page.locator('[data-mobile-jump="buildingsCard"]').click();page.wait_for_timeout(120)
        result["nav"]["panelFocusAfterBuild"]=page.locator("body").evaluate("e=>e.classList.contains('v14-panel-focus')")
    if page.locator(".v14-map-button").count():
        page.locator(".v14-map-button").click();page.wait_for_timeout(120)
        result["nav"]["panelFocusAfterMap"]=page.locator("body").evaluate("e=>e.classList.contains('v14-panel-focus')")

    click(page,'nav .tab[data-tab="realm"]');page.wait_for_timeout(100)
    result["realmFocus"]=page.locator("body").evaluate("e=>e.classList.contains('v14-panel-focus')")
    click(page,'nav .tab[data-tab="settlement"]');page.wait_for_timeout(100)

    # Help sheet remains on-screen and dismisses.
    click(page,"#help");page.wait_for_timeout(80)
    card=page.locator("#modal .modalCard").bounding_box();vp=page.viewport_size
    result["help"]={"visible":not page.locator("#modal").evaluate("e=>e.classList.contains('hidden')"),
                    "withinViewport":bool(card and card["x"]>=-1 and card["y"]>=-1 and card["x"]+card["width"]<=vp["width"]+1 and card["y"]+card["height"]<=vp["height"]+1)}
    click(page,"#closeModal")

    # Save/load controls operate after skip.
    result["footer"]={"saveVisible":page.locator("#save").is_visible(),"loadEnabled":not page.locator("#load").is_disabled(),
                      "newEnabled":not page.locator("#newGame").is_disabled(),"musicVisible":page.locator("#v13Music").count()>0 and page.locator("#v13Music").is_visible()}
    click(page,"#save")
    before=page.evaluate("window.__CROWNFALL__.getWorld().settlements.find(s=>s.owner===0).buildings.farms")
    page.locator('[data-build="farms"]').click();page.wait_for_timeout(80)
    changed=page.evaluate("window.__CROWNFALL__.getWorld().settlements.find(s=>s.owner===0).buildings.farms")
    click(page,"#load");page.wait_for_timeout(100)
    restored=page.evaluate("window.__CROWNFALL__.getWorld().settlements.find(s=>s.owner===0).buildings.farms")
    result["saveLoad"]={"changed":changed==before+1,"restored":restored==before}

    # Fast speed actually advances time on WebKit after onboarding.
    d0=page.evaluate("window.__CROWNFALL__.getWorld().day")
    page.locator('.time [data-speed="4"]').click();page.wait_for_timeout(650)
    page.locator('.time [data-speed="0"]').click()
    d1=page.evaluate("window.__CROWNFALL__.getWorld().day")
    result["clock"]={"before":d0,"after":d1,"advanced":d1>d0}

    result["errors"]=errors
    ctx.close()
    return result

with sync_playwright() as p:
    chromium=p.chromium.launch(headless=True)
    desktop=desktop_journey(chromium)
    chromium.close()
    webkit=p.webkit.launch(headless=True)
    mobile=mobile_journey(webkit)
    webkit.close()

payload={"desktop":desktop,"mobile":mobile}
print(json.dumps(payload,indent=2))
(OUT/"results.json").write_text(json.dumps(payload,indent=2))

fails=[]
d=desktop
if d["errors"]: fails.append("desktop browser errors: "+" | ".join(d["errors"]))
if d["baseline"]["settlements"]!=48: fails.append("desktop: full map did not show 48 settlements after skip")
if not d["baseline"]["tabsEnabled"] or not d["baseline"]["loadNewEnabled"]: fails.append("desktop: controls stayed locked after skip")
if not d["baseline"]["musicVisible"]: fails.append("desktop: music control missing after onboarding")
if not d["help"]["visible"] or "How to Rule" not in d["help"]["text"]: fails.append("desktop: help modal failed")
if not d.get("musicToggle",{}).get("changed"): fails.append("desktop: music button did not toggle")
if not all(d["buildRecruitSave"].values()): fails.append("desktop: build/recruit/manual-save flow failed")
if d["steward"]!={"military":"military","off":"off"}: fails.append("desktop: steward policy buttons failed")
a=d["alliance"]
if a["envoyRelationGain"]!=54 or a["envoyInfluenceSpent"]!=36 or a["status"]!="alliance": fails.append("desktop: diplomacy/envoy/alliance flow failed")
if not a["alliedSupport"] or a["hostileButtonsOnAlly"]!=0 or "Reinforce" not in a["missionText"] or not a["reinforcementArrived"]: fails.append("desktop: allied reinforcement UI/arrival failed")
r=d["raidReport"]
if not r["raidButtonVisible"] or not r["newReport"] or r["raidStat"]<1 or not r["reportModal"] or "Survivors" not in r["reportText"]: fails.append("desktop: raid/Chronicle/report flow failed")
if d["annex"]["owner"]!=0 or d["annex"]["influenceSpent"]!=35 or d["annex"]["reportSpent"]!=35: fails.append("desktop: annex flow/accounting failed")
if not d["war"]["enabledAfterTruce"] or d["war"]["status"]!="war": fails.append("desktop: post-truce war flow failed")
if not d["threatPause"]["warning"] or not d["threatPause"]["pauseActive"] or d["threatPause"]["incomingArmies"]<1: fails.append("desktop: Threat Pause failed")
if not d["newWorld"]["seedChanged"] or d["newWorld"]["tutorialActive"] or d["newWorld"]["steward"]!="balanced" or not d["newWorld"]["manualSaveRestored"]: fails.append("desktop: New World/manual-save behavior failed")

m=mobile
if m["errors"]: fails.append("mobile browser errors: "+" | ".join(m["errors"]))
if not m["nav"].get("exists") or not m["nav"].get("mapButton") or not m["nav"].get("panelFocusAfterBuild") or m["nav"].get("panelFocusAfterMap"): fails.append("mobile: workspace navigation failed")
if not m["realmFocus"]: fails.append("mobile: non-settlement tab did not expand workspace")
if not m["help"]["visible"] or not m["help"]["withinViewport"]: fails.append("mobile: help modal overflow/visibility failed")
if not all(m["footer"].values()): fails.append("mobile: footer/music controls unavailable after skip")
if not m["saveLoad"]["changed"] or not m["saveLoad"]["restored"]: fails.append("mobile: save/load/build flow failed")
if not m["clock"]["advanced"]: fails.append("mobile: time controls did not advance game")

if fails:
    print("\nFULL GAME QA FAILURES:")
    for x in fails: print("-",x)
    raise SystemExit(1)
