# Crownfall Marches v1.3

A single-player browser strategy game about building one settlement into a regional power through development, recruitment, diplomacy, raiding, and conquest.

## Play

**Live build:** https://toiletslayer.github.io/Crownfall-/

The GitHub Pages build is the recommended version on phones and tablets. It runs entirely in the browser with no paid APIs, accounts, or game server.

The standalone HTML build remains available for desktop/offline use.

## v1.3 presentation pass

This release keeps the v1.2 simulation and fairness rules intact while making the strategic map feel more like a place rather than a diagram.

- **Original ambient soundtrack:** a small procedural score generated locally with the browser Web Audio API. Music is opt-in with a Music ON/OFF button because mobile browsers require a user gesture before audio playback.
- **Road treatment:** settlement connections now read as worn roads instead of plain network lines, with brighter roads around the player's holdings.
- **Army standards:** moving armies are represented by faction-colored flags rather than abstract markers.
- **Richer campaign map:** layered terrain texture, fields/scrub, forests, ridgelines, lakes, a river, and a subtle compass treatment are generated from the world seed.
- **Less synthetic faction naming:** the six powers are now House Calder, House Vale, House Harker, House Fenner, House Morcant, and House Bellamy.
- Existing worlds are visually renamed when loaded; simulation mechanics and diplomatic state are unchanged.

## v1.2.2 iPhone file-preview compatibility

This release prevents storage failures from crashing startup when the standalone HTML is opened inside iOS/ChatGPT/Files-style document preview. A normal hosted browser origin, such as the GitHub Pages build above, remains the preferred mobile route.

- Game startup no longer depends on persistent browser storage succeeding.
- If localStorage is blocked, the world still renders and plays normally.
- New World continues to work in preview mode.
- Save / Load fall back to an in-memory session save when persistent storage is unavailable.
- The Save button changes to **Save (session)** so the limitation is explicit.
- Session saves survive while that preview remains open, but may disappear after closing the preview.
- Autosave is storage-safe and can no longer crash the game at an autosave tick.

## v1.2.1 phone / touch pass

- **Portrait phones:** the map remains visible above a compact, independently scrollable settlement panel.
- **Landscape phones:** map and settlement panel sit side-by-side for a more desktop-like play view.
- **Touch-sized controls:** time controls, tabs, build/recruit actions, army inputs, footer controls, reports, and diplomacy controls use larger hit areas.
- **Compact settlement navigation:** a sticky Overview / Build / Recruit / Orders bar jumps directly to the important part of a long settlement panel.
- **Mobile map cleanup:** neutral settlement labels are hidden until selected, reducing clutter on narrow screens while keeping faction/player labels readable.
- **Safe-area support:** layout accounts for modern iPhone display insets and uses dynamic viewport height.
- **Touch modals:** help and battle reports open as phone-sized bottom sheets; landscape modals remain contained inside the viewport.

## v1.2 fairness model

This release specifically addresses the human-vs-AI action-speed imbalance found during playtesting.

- **All six houses start equally:** one capital each, identical capital development, troops, resources, and influence.
- **Founding Truce:** through day 99, factions may raid/annex independent settlements but cannot attack another sovereign realm. Open conflict begins on day 100.
- **AI command limits:** AI realms no longer upgrade and recruit in every settlement simultaneously. Administration is limited to a small number of capped decisions every five days, scaling only modestly with realm size.
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
- Rival houses expand and conduct diplomacy autonomously.

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

Manual saves and autosaves use browser localStorage when available. The hosted GitHub Pages build provides the normal browser environment intended for reopen-and-continue saves. Older v1.x saves retain their mechanics; v1.3 updates the visible house names without changing ownership, diplomacy, armies, resources, or balance.

## Technical notes

Crownfall Marches is deliberately backend-free. The simulation runs locally in the browser. v1.3's soundtrack is synthesized locally and does not stream audio or call an external service.
