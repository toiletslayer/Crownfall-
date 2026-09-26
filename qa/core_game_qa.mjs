import fs from 'node:fs';

const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('const RESOURCE_KEYS');
const end=html.indexOf('\nlet world;');
if(start<0||end<0)throw new Error('Could not locate Crownfall core.');
const core=html.slice(start,end);
const api=new Function(core+`
return {
 RESOURCE_KEYS,BUILDINGS,UNITS,FOUNDING_TRUCE_DAYS,costFor,storageCap,production,
 settlementDefense,armyPower,armySize,supplyCapacity,unitSupply,supplyUsed,factionPower,
 createWorld,canAfford,upgradeBuilding,recruit,sendArmy,resolveArmy,ownedSettlements,
 neighborsOf,shortestPath,getRelation,getDiplomacy,setDiplomacy,runPlayerSteward,
 setPlayerStewardPolicy,playerDiplomacyAction,dailyEconomy,checkStates,advanceDays,
 serializeWorld,deserializeWorld,worldSummary,runAutoplayerAction,rngFrom
};`)();

const failures=[];
const metrics={};
const check=(ok,msg)=>{if(!ok)failures.push(msg);};
const clone=x=>JSON.parse(JSON.stringify(x));
const armySize=u=>Object.values(u).reduce((a,b)=>a+b,0);

function invariant(w,label){
  check(w.version===1,`${label}: save version changed unexpectedly`);
  check(w.settlements.length===48,`${label}: expected 48 settlements, got ${w.settlements.length}`);
  check(w.factions.length===6,`${label}: expected 6 factions, got ${w.factions.length}`);
  check(new Set(w.settlements.map(s=>s.id)).size===w.settlements.length,`${label}: duplicate settlement ids`);
  const edges=new Set();
  for(const [a,b] of w.roads){
    check(a!==b,`${label}: self-loop road ${a}`);
    const key=a<b?`${a}-${b}`:`${b}-${a}`;
    check(!edges.has(key),`${label}: duplicate road ${key}`);
    edges.add(key);
  }
  const seen=new Set([0]),queue=[0];
  while(queue.length){
    const id=queue.shift();
    for(const n of api.neighborsOf(w,id))if(!seen.has(n.id)){seen.add(n.id);queue.push(n.id);}
  }
  check(seen.size===w.settlements.length,`${label}: road graph disconnected (${seen.size}/${w.settlements.length})`);
  for(const s of w.settlements){
    check(s.owner===null||(Number.isInteger(s.owner)&&s.owner>=0&&s.owner<w.factions.length),`${label}: invalid owner at ${s.id}`);
    for(const k of api.RESOURCE_KEYS){
      check(Number.isFinite(s.resources[k])&&s.resources[k]>=0,`${label}: invalid ${k} at ${s.id}`);
      check(s.resources[k]<=api.storageCap(s)+1e-9,`${label}: ${k} exceeds storage cap at ${s.id}`);
    }
    for(const [k,d] of Object.entries(api.BUILDINGS))check(Number.isInteger(s.buildings[k])&&s.buildings[k]>=0&&s.buildings[k]<=d.max,`${label}: invalid ${k} level at ${s.id}`);
    for(const [k,n] of Object.entries(s.troops))check(api.UNITS[k]&&Number.isInteger(n)&&n>=0,`${label}: invalid troop ${k} at ${s.id}`);
  }
  const armyIds=new Set();
  for(const a of w.armies){
    check(!armyIds.has(a.id),`${label}: duplicate army id ${a.id}`);armyIds.add(a.id);
    check(['raid','attack','annex','reinforce'].includes(a.mission),`${label}: invalid mission ${a.mission}`);
    check(armySize(a.units)>0,`${label}: empty army ${a.id}`);
    check(a.arriveDay>a.departDay,`${label}: invalid army timing ${a.id}`);
    for(const n of Object.values(a.units))check(Number.isInteger(n)&&n>=0,`${label}: invalid army troop count`);
  }
}

// World generation, fairness, connectivity and tutorial affordability.
for(let i=0;i<250;i++){
  const w=api.createWorld('gen-'+i);invariant(w,'gen-'+i);
  const caps=w.factions.map(f=>w.settlements.find(s=>s.owner===f.id));
  check(caps.every(Boolean),`gen-${i}: missing starting capital`);
  const sig=caps.map(s=>JSON.stringify({b:s.buildings,t:s.troops,r:s.resources}));
  check(sig.every(x=>x===sig[0]),`gen-${i}: unequal faction starting capital`);
  const player=caps[0],farmCost=api.costFor('farms',player.buildings.farms+1);
  check(api.RESOURCE_KEYS.every(k=>player.resources[k]>=(farmCost[k]||0)),`gen-${i}: tutorial Farm upgrade unaffordable`);
  const farm=api.upgradeBuilding(w,player.id,'farms');
  const militia=api.recruit(w,player.id,'militia',5);
  check(farm.ok&&militia.ok,`gen-${i}: required tutorial actions deadlock`);
  check(api.neighborsOf(w,player.id).length>0,`gen-${i}: capital has no neighbor`);
}
metrics.generatedWorlds=250;

// Production/storage arithmetic.
for(let i=0;i<2500;i++){
  const w=api.createWorld('econ-'+i),s=w.settlements.find(x=>x.owner===0);
  for(const [j,k] of Object.keys(api.BUILDINGS).entries())s.buildings[k]=(i+j)%(api.BUILDINGS[k].max+1);
  const cap=api.storageCap(s),p=api.production(s);
  for(const [j,k] of api.RESOURCE_KEYS.entries())s.resources[k]=((i*37+j*113)%1000)/1000*cap;
  const before=clone(s.resources);api.dailyEconomy(w);
  for(const k of api.RESOURCE_KEYS)check(Math.abs(s.resources[k]-Math.min(cap,before[k]+p[k]))<1e-9,`econ-${i}: ${k} mismatch`);
}
metrics.economyChecks=2500;

// Upgrade/recruitment/unlock/supply rules.
for(let i=0;i<500;i++){
  const w=api.createWorld('rules-'+i),s=w.settlements.find(x=>x.owner===0);
  s.resources={food:999999,wood:999999,iron:999999};
  s.buildings.barracks=1;
  check(!api.recruit(w,s.id,'raiders',1).ok,`rules-${i}: Raiders before Barracks II`);
  check(!api.recruit(w,s.id,'cavalry',1).ok,`rules-${i}: Cavalry before Barracks III`);
  s.buildings.barracks=2;
  check(api.recruit(w,s.id,'raiders',1).ok,`rules-${i}: Raiders unavailable at Barracks II`);
  check(!api.recruit(w,s.id,'cavalry',1).ok,`rules-${i}: Cavalry available at Barracks II`);
  s.buildings.barracks=3;
  check(api.recruit(w,s.id,'cavalry',1).ok,`rules-${i}: Cavalry unavailable at Barracks III`);
  s.buildings.farms=1;s.troops={militia:105,spears:0,raiders:0,cavalry:0};
  check(api.supplyUsed(w,s.id)===api.supplyCapacity(s),`rules-${i}: supply arithmetic mismatch`);
  check(!api.recruit(w,s.id,'militia',1).ok,`rules-${i}: recruitment allowed over supply cap`);
}
metrics.recruitmentChecks=500;

// Army mission, truce and alliance semantics.
{
  const w=api.createWorld('mission-rules'),home=w.settlements.find(s=>s.owner===0);
  const neutral=api.neighborsOf(w,home.id).find(s=>s.owner===null);
  const enemy=w.settlements.find(s=>s.owner===1);
  home.troops={militia:200,spears:100,raiders:60,cavalry:30};
  check(!!neutral,'mission-rules: no neutral neighbor');
  check(!api.sendArmy(w,0,home.id,enemy.id,{militia:1},'raid').ok,'mission-rules: sovereign raid allowed during truce');
  check(api.sendArmy(w,0,home.id,neutral.id,{militia:10},'raid').ok,'mission-rules: neutral raid blocked during truce');
  w.day=120;api.setDiplomacy(w,0,1,'alliance',70);
  check(!api.sendArmy(w,0,home.id,enemy.id,{militia:5},'raid').ok,'mission-rules: allied raid allowed');
  check(!api.sendArmy(w,0,home.id,enemy.id,{militia:5},'annex').ok,'mission-rules: allied annex allowed');
  check(api.sendArmy(w,0,home.id,enemy.id,{militia:5},'reinforce').ok,'mission-rules: allied reinforce blocked');
  check(!api.sendArmy(w,0,home.id,neutral.id,{militia:1},'reinforce').ok,'mission-rules: neutral reinforce allowed');
  check(!api.sendArmy(w,0,home.id,neutral.id,{militia:1},'nonsense').ok,'mission-rules: unknown mission allowed');

  // Reinforcements must never turn into attacks if diplomacy changes in transit.
  const stale=api.sendArmy(w,0,home.id,enemy.id,{militia:6},'reinforce');
  check(stale.ok,'mission-rules: stale reinforce setup failed');
  if(stale.ok){
    w.armies=w.armies.filter(a=>a.id!==stale.army.id);
    api.setDiplomacy(w,0,1,'peace',0);
    const beforeTarget=enemy.troops.militia;
    const beforeHome=home.troops.militia;
    api.resolveArmy(w,stale.army,()=>0.5);
    check(enemy.troops.militia===beforeTarget,'mission-rules: stale reinforce altered former ally garrison');
    check(home.troops.militia===beforeHome+6,'mission-rules: stale reinforce did not return home');
    check(w.battleReports.length===0,'mission-rules: stale reinforce created a battle report');
  }
}
metrics.missionRuleChecks=11;

// Diplomacy costs and truce.
{
  const w=api.createWorld('dip-rules'),f=w.factions[0],rel=api.getRelation(w,0,1),inf=f.influence;
  const envoy=api.playerDiplomacyAction(w,1,'improve');
  check(envoy.ok&&f.influence===inf-12,'diplomacy: envoy influence cost wrong');
  check(api.getRelation(w,0,1)===Math.min(100,rel+18),'diplomacy: envoy relation wrong');
  check(!api.playerDiplomacyAction(w,1,'war').ok,'diplomacy: player war allowed during truce');
  w.day=100;check(api.playerDiplomacyAction(w,1,'war').ok&&api.getDiplomacy(w,0,1)==='war','diplomacy: war failed after truce');
}
metrics.diplomacyChecks=4;

// Raid loot is delivered only into available storage and follows the army home if its origin was lost.
{
  const w=api.createWorld('raid-storage'),home=w.settlements.find(s=>s.owner===0),target=api.neighborsOf(w,home.id).find(s=>s.owner===null);
  home.troops={militia:220,spears:120,raiders:80,cavalry:30};
  const cap=api.storageCap(home);home.resources={food:cap-1,wood:cap-1,iron:cap-1};
  target.troops={militia:0,spears:0,raiders:0,cavalry:0};target.resources={food:1000,wood:1000,iron:1000};
  const sent=api.sendArmy(w,0,home.id,target.id,{militia:120,spears:60,raiders:40,cavalry:15},'raid');
  check(sent.ok,'raid-storage: dispatch failed');
  if(sent.ok){
    w.armies=w.armies.filter(a=>a.id!==sent.army.id);api.resolveArmy(w,sent.army,()=>0.5);
    for(const k of api.RESOURCE_KEYS)check(home.resources[k]===cap,`raid-storage: ${k} exceeded cap or did not fill available room`);
    const rp=w.battleReports.at(-1);for(const k of api.RESOURCE_KEYS)check(rp.loot[k]===1,`raid-storage: reported ${k} loot ignored storage room`);
  }
}
metrics.raidStorageChecks=6;

// Guaranteed annex accounting and battle-report reconciliation.
{
  const w=api.createWorld('annex-rules'),home=w.settlements.find(s=>s.owner===0),target=api.neighborsOf(w,home.id).find(s=>s.owner===null);
  home.troops={militia:220,spears:120,raiders:80,cavalry:30};const influence=w.factions[0].influence;
  const sent=api.sendArmy(w,0,home.id,target.id,{militia:120,spears:60,raiders:40,cavalry:15},'annex');
  check(sent.ok,'annex: dispatch failed');w.armies=w.armies.filter(a=>a.id!==sent.army.id);api.resolveArmy(w,sent.army,()=>0.5);
  const rp=w.battleReports.at(-1);
  check(rp?.annexed&&target.owner===0,'annex: ownership did not transfer');
  check(w.factions[0].influence===influence-35&&rp.influenceSpent===35,'annex: influence accounting wrong');
}

// Chunk-independent deterministic simulation.
for(let i=0;i<100;i++){
  const seed='det-'+i,w1=api.createWorld(seed),w2=api.createWorld(seed);
  api.advanceDays(w1,240);for(let d=0;d<240;d++)api.advanceDays(w2,1);
  check(api.serializeWorld(w1)===api.serializeWorld(w2),`det-${i}: chunking changed state`);
}
metrics.determinismWorlds=100;

// Save round-trip and legacy v1 migration.
for(let i=0;i<180;i++){
  const w=api.createWorld('save-'+i);api.advanceDays(w,30+(i%40));
  check(api.serializeWorld(api.deserializeWorld(api.serializeWorld(w)))===api.serializeWorld(w),`save-${i}: round-trip changed state`);
  const legacy=JSON.parse(api.serializeWorld(w));delete legacy.playerSteward;delete legacy.battleReports;delete legacy.nextReportId;
  for(const f of legacy.factions){delete f.lastAdminDay;delete f.lastMilitaryDay;delete f.adminCursor;}
  const migrated=api.deserializeWorld(JSON.stringify(legacy));
  check(migrated.playerSteward&&Array.isArray(migrated.battleReports)&&Number.isInteger(migrated.nextReportId),`save-${i}: legacy migration failed`);
}
metrics.saveChecks=180;

// Victory/defeat thresholds.
{
  let w=api.createWorld('territorial');for(let i=0;i<28;i++)w.settlements[i].owner=0;w.day=100;api.checkStates(w);
  check(w.victory&&w.victoryType==='territorial','state: territorial victory failed');
  w=api.createWorld('hegemony');w.day=100;for(const s of w.settlements)s.owner=null;for(let i=0;i<22;i++)w.settlements[i].owner=0;for(let i=22;i<32;i++)w.settlements[i].owner=1;api.checkStates(w);
  check(w.victory&&w.victoryType==='hegemony','state: hegemony victory failed');
  w=api.createWorld('defeat');for(const s of w.settlements)if(s.owner===0)s.owner=null;api.checkStates(w);
  check(w.defeat,'state: defeat failed');

  // State changes are recognized on the next simulated day, not delayed to a 10-day boundary.
  w=api.createWorld('immediate-defeat');w.day=101;for(const s of w.settlements)if(s.owner===0)s.owner=null;api.advanceDays(w,1);
  check(w.defeat&&w.day===102,'state: defeat recognition was delayed');
  w=api.createWorld('immediate-victory');w.day=101;for(let i=0;i<28;i++)w.settlements[i].owner=0;api.advanceDays(w,1);
  check(w.victory&&w.day===102,'state: victory recognition was delayed');
}
metrics.stateChecks=5;

// Long-running human-like campaigns and battle-report arithmetic.
let reports=0;const outcomes={victory:0,defeat:0,unresolved:0};
for(let i=0;i<80;i++){
  const w=api.createWorld('campaign-'+i);api.setPlayerStewardPolicy(w,'balanced');
  for(let d=0;d<2000&&!w.victory&&!w.defeat;d++){
    if(d%3===0)api.runAutoplayerAction(w,0);
    api.advanceDays(w,1);
    if(d%100===0)invariant(w,`campaign-${i}-day-${w.day}`);
  }
  api.checkStates(w);invariant(w,`campaign-${i}-end`);
  if(w.victory)outcomes.victory++;else if(w.defeat)outcomes.defeat++;else outcomes.unresolved++;
  for(const r of w.battleReports){
    reports++;
    for(const k of Object.keys(api.UNITS)){
      check((r.attackerUnits[k]||0)===(r.attackerSurvivors[k]||0)+(r.attackerLosses[k]||0),`campaign-${i} report ${r.id}: attacker ${k} mismatch`);
      check((r.defenderUnits[k]||0)===(r.defenderSurvivors[k]||0)+(r.defenderLosses[k]||0),`campaign-${i} report ${r.id}: defender ${k} mismatch`);
    }
    if(r.annexed)check(r.influenceSpent===35,`campaign-${i} report ${r.id}: annex spend mismatch`);
  }
}
metrics.longCampaigns=80;metrics.campaignOutcomes=outcomes;metrics.battleReportsChecked=reports;

const result={failureCount:failures.length,failures:failures.slice(0,100),metrics};
console.log(JSON.stringify(result,null,2));
if(failures.length)process.exit(1);
