# Crownfall Marches v1.2.2

A self-contained single-player browser strategy game. Start with one settlement, build a resource base, recruit troops, expand through independent territory, and compete with five autonomous rival kingdoms.

## Play

### Simplest
Double-click **`Crownfall-Marches-PLAY.html`**. It contains the complete game in one file with no external assets, APIs, accounts, or paid services.

### Fallback local server
- Windows: double-click `START-WINDOWS.bat`
- macOS/Linux: run `python3 -m http.server 8080`, then open `http://localhost:8080`



## v1.2.2 iPhone file-preview compatibility

This release fixes the blank-map failure seen when the standalone HTML is opened inside iOS/ChatGPT/Files-style document preview instead of a normal hosted browser origin. Some preview containers expose browser storage inconsistently or reject larger localStorage writes.

- Game startup no longer depends on persistent browser storage succeeding.
- If localStorage is blocked, the world still renders and plays normally.
- New World continues to work in preview mode.
- Save / Load fall back to an in-memory session save when persistent storage is unavailable.
- The Save button changes to **Save (session)** so the limitation is explicit.
- Session saves survive while that preview remains open, but may disappear after closing the preview. For reopen-and-continue persistence, a normal hosted webpage remains preferable.
- Autosave is also storage-safe and can no longer crash the game at an autosave tick.

## v1.2.1 phone / touch pass

This release keeps the v1.2 simulation and fairness rules intact and makes the production UI practical on phones.

- **Portrait phones:** the map remains visible above a compact, independently scrollable settlement panel.
- **Landscape phones:** map and settlement panel sit side-by-side for a more desktop-like play view.
- **Touch-sized controls:** time controls, tabs, build/recruit actions, army inputs, footer controls, reports, and diplomacy controls use larger hit areas.
- **Compact settlement navigation:** a sticky Overview / Build / Recruit / Orders bar jumps directly to the important part of a long settlement panel.
- **Mobile map cleanup:** neutral settlement labels are hidden until selected, reducing clutter on narrow screens while keeping faction/player labels readable.
- **Safe-area support:** layout accounts for modern iPhone display insets and uses dynamic viewport height.
- **Touch modals:** help and battle reports open as phone-sized bottom sheets; landscape modals remain contained inside the viewport.
- **No server/backend added:** the standalone HTML is still the entire game.

## v1.2 fairness model

This release specifically addresses the human-vs-AI action-speed imbalance found during playtesting.

- **All six kingdoms start equally:** one capital each, identical capital development, troops, resources, and influence.
- **Founding Truce:** through day 99, kingdoms may raid/annex independent settlements but cannot attack another sovereign realm. Open conflict begins on day 100.
- **AI command limits:** AI kingdoms no longer upgrade and recruit in every settlement simultaneously. Administration is limited to a small number of capped decisions every five days, scaling only modestly with realm size.
- **Military command limits:** each AI realm has a strategic dispatch cooldown and a cap on simultaneous field armies.
- **Realm Steward:** the player's steward can automate routine development and recruitment at the same capped administrative pace used by rivals. Policies: Off, Balanced, Economy, Defense, Military. Balanced is the default.
- **Threat Pause:** enabled by default. When a hostile army is sent toward your realm during normal play, the clock pauses so you can inspect the threat and react.
- **Faction status is explicit:** the map legend and Diplomacy panel show land counts and clearly mark eliminated realms.

## Core rules

- Farms produce food; Lumber Camps produce wood; Mines produce iron.
- Upgrade the Keep for storage and defense, Barracks for advanced troops, Walls for defense, Council Hall for influence.
- Recruit Militia, Spearmen, Raiders, and Cavalry.
- Click any settlement to inspect it. Foreign settlements expose quick Raid / Attack / Annex preparation.
- Raids steal resources. Annexation costs 35 Influence and captures a settlement after a successful battle with enough survivors.
- Incoming enemy attacks show destination, force size, mission, and ETA.
- Battle Chronicle entries open detailed reports with armies, casualties, survivors, battle power, Keep/Wall contribution, loot, and annexation results.
- Rival kingdoms expand and conduct diplomacy autonomously.

## Victory

Two routes:

1. **Territorial supremacy:** control 58% of the 48 settlements.
2. **Hegemony:** after the Founding Truce, control at least 44% of the map and at least twice as many settlements as the strongest remaining rival.

Play continues in sandbox mode after victory.

## Time controls

- **Ⅱ Pause**
- **▶ Normal:** 0.25 simulated days per real second
- **▶▶ Fast:** 1 simulated day per real second
- **▶▶▶ Very fast:** 4 simulated days per real second

## Saves

Manual saves and autosaves use browser localStorage when available. If an iPhone/document preview blocks persistent storage, v1.2.2 automatically falls back to a session-only in-memory save so gameplay, New World, Save, Load, and autosave continue to function without crashing. Older v1.x saves are migrated with defaults for newer fields, although a fresh world is recommended for the v1.2 equal-start balance rules.

## QA

- Simulation engine: `src/sim.js`
- Browser/UI: `src/app.js`, `index.html`, `styles.css`
- Deterministic tests: `tests/test.mjs`
- Campaign simulator: `tests/simulate.mjs`
- Browser QA: `tests/browser_qa.py`
- Phone/touch QA: `tests/mobile_qa.py`
- File-preview/storage-denial QA: `tests/file_preview_qa.py`
- Fairness sweep: `tests/fairness_sweep.json`
- Final campaign batch: `tests/final_simulation.json`
- Full report: `QA_REPORT.md`

Commands:

- `npm test`
- `npm run simulate`
- `python3 tests/browser_qa.py`
- `python3 tests/mobile_qa.py`
- `python3 tests/file_preview_qa.py`
- `python3 tests/build_standalone.py`
