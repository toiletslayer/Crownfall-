# Crownfall Marches — First-Hour UX QA

Last updated: 2026-09-25  
Branch: `feature/v1.4.8-first-hour`

This pass responds to first-time-player feedback that Crownfall presents too much information at once and does not explain several important visual and economic systems clearly enough.

## Feedback mapped to changes

### “I am thrown into the game and do not know what to do.”

First-time flow is now staged:

1. Start paused on Day 0 with only the player capital visible.
2. Explain Food, Wood, Iron, and Influence.
3. Ask the player to upgrade Farms II → III.
4. Ask the player to recruit 5 Militia.
5. Reveal only directly connected neighboring settlements.
6. Ask the player to inspect an Independent neighbor.
7. Ask the player to prepare a Raid / Attack / Annex order.
8. Reveal the full Marches and let the player start the clock.

The tutorial can be skipped. Returning players who already completed the prior tutorial are not forced through the new first-hour sequence.

### “The game may be spending things before I understand them.”

During the guided introduction:

- time is paused;
- the Realm Steward is OFF;
- completing the introduction does not automatically enable the Steward.

The player is told explicitly that automation remains off until enabled from the Realm tab.

### “Raiders and Cavalry are too much information immediately.”

Raiders and Cavalry are hidden during the first recruitment lesson. Militia and Spearmen remain visible. Advanced units appear after the player completes the first Militia recruitment.

This is presentation gating only; v1.4.7 combat balance and starting army state are not changed in this pass.

### “I cannot tell what the resources are.”

Resource cards and cost chips now spell out:

- 🌾 Food
- 🪵 Wood
- ⛏ Iron
- ✦ Influence

Zero-cost resources are omitted from cost rows.

Influence is explicitly described as realm-wide currency rather than a settlement resource.

### “My gold disappeared.”

The apparent “gold” is Influence.

Current mechanics are now surfaced in the UI:

- Annexation: 35 Influence on successful capture.
- Envoy / improve relations: 12 Influence.
- Council Halls increase Influence generation.

Successful annex battle reports include the 35-Influence spend.

### “Upgrades do not tell me what they actually do.”

Building cards now show the next level's numerical effect before purchase.

Examples:

- Farms: Food/day and troop-supply capacity before → after.
- Lumber Camp: Wood/day before → after.
- Mine: Iron/day before → after.
- Keep: +500 storage and +9 base defense.
- Walls: exact settlement-defense multiplier before → after.
- Council Hall: Influence/day contribution before → after.
- Barracks: Raiders unlock at II; Cavalry unlock at III.

A separate design question remains: Barracks IV–VI currently add no new troop unlock. This pass exposes that fact rather than inventing an undocumented benefit.

## River and roads

### River

The previous presentation had two overlapping river treatments: an older broad river wash and the newer v1.4 river. The old wash has been removed.

The v1.4 river now:

- evaluates 64 deterministic routes for the world seed;
- chooses the route with the fewest close settlement conflicts;
- uses a narrower water channel with visible banks;
- places dry ground beneath the rare unavoidable settlement crossing;
- draws bridge decks where existing roads cross the river.

A 300-world route-selection test found the selected route averaged fewer than one settlement within 4 map units of the river centerline (0.77/world), with no tested world exceeding two such close settlements.

### Roads

The travel graph itself remains unchanged.

A threshold-based road rewrite was tested because the feedback described roads as random. Across 300 generated worlds, however, the v1.4.7 graph already connected approximately 99.9% of each settlement's two nearest-neighbor relationships.

A threshold-16 rewrite reduced visual distance inversions but changed campaign behavior:

- optimized QA wins through day 1800: 42/60 → 34/60;
- casual QA wins: 9/60 → 7/60;
- unresolved campaigns increased.

Because the UX complaint can be addressed visually without disturbing travel balance, the rewrite was rejected. Roads now use a more road-like solid earth treatment and river crossings are visually explained with bridges.

## Regression checks

- JavaScript parse check: PASS.
- 60-world simulation smoke test to day 1500: 38 wins / 0 defeats / 22 unresolved.
- No Siege Crew or siege mechanic is included.
- No road-topology change is included.
- Existing save schema remains version 1.

## Still needs human visual testing

Before merge, check on desktop and iPhone:

- tutorial does not obscure the required controls;
- Farm and Recruit buttons remain easy to reach while tutorial is open;
- staged map reveal feels intentional rather than broken;
- resource labels remain readable without crowding mobile cards;
- bridges and river clearings look like geography rather than artifacts;
- full-map reveal after preparing the first order feels smooth.

