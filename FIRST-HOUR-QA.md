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

The tutorial can be skipped immediately. Returning v1.4.7 players who only have the older tutorial marker are shown the v1.4.8 First Hour once. Completing or skipping it writes a v1.4.8-specific marker so it is not forced again. If that returning player already has a campaign autosave/manual save, the tutorial uses a separate progress slot; their existing campaign is restored paused after the First Hour instead of being overwritten.

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

The route scorer now balances two competing goals: avoid settlements first, while also penalizing rivers that hug the outer map edge. A 500-world merge-risk audit of the current scorer averaged about 1.4 settlements within 4 map units of the river centerline, with a worst case of 3; those close cases receive explicit dry-ground treatment. In the browser QA sample, every close settlement was covered and bridge counts matched visual road/river crossings exactly. A stricter scorer that eliminated all rare 3-town cases pushed too many rivers back toward the edge, so the current balance is intentional.

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
- Selector-list audit: PASS; no single-element `$()` selector is used with `.forEach()`.
- 60-world simulation smoke test to day 1500: 38 wins / 0 defeats / 22 unresolved.
- 500 generated-world tutorial seed audit: all 500 could afford Farms II → III and 5 Militia; every capital had at least one connected neighbor.
- Desktop Chromium guided flow: PASS.
- iPhone-sized WebKit (390×844, touch enabled) guided flow: PASS.
- Day 0 exposes one settlement, zero roads/bridges, one settlement-linked field/decor marker, and keeps the faction legend/music control hidden.
- Time controls and Realm/Diplomacy/Chronicle tabs stay disabled throughout onboarding and re-enable afterward.
- Stage 2 and Stage 3 tutorial progress is written immediately to the dedicated `crownfall-first-hour-v148-progress` slot, not the normal campaign autosave.
- Refreshing or reopening during an unfinished First Hour resumes that tutorial-progress slot and keeps time paused; Load remains locked until the First Hour is completed or skipped.
- A returning v1.4.7 campaign autosave/manual save is preserved while the one-time First Hour runs, then restored paused after completion or Skip.
- Normal page reopen resumes the campaign autosave paused instead of silently replacing it with a new world.
- Stage 4 persists the inspected Independent target; loading restores its target panel and contextual Raid button.
- A stale Stage 4 save without a target safely falls back to the Neighbors lesson.
- Legacy version-1 saves without an `onboarding` field still load with tutorial chrome hidden.
- A completed user cannot be trapped by an older active-onboarding save; it normalizes to completed Stage 6.
- “Start the clock” selects normal speed and reaches Day 1 in both browser profiles.
- Load/New Game are locked while the one-time First Hour is active. The old campaign is preserved behind the tutorial and restored automatically for returning players; skipping or completing the First Hour unlocks normal save controls immediately.
- Bridge count matches actual curved-river road crossings in the browser sample, with zero uncovered close settlements.
- No Siege Crew or siege mechanic is included.
- No road-topology change is included.
- Existing save schema remains version 1.
- The UI QA workflow now runs on pull requests to `main`, pushes to `main`, and manual dispatch, so it remains useful after this feature branch is merged/deleted.

## Merge-risk review

The focused merge-risk pass found and fixed issues that the initial visual QA did not cover:

- onboarding progress previously could be lost before the normal Day-15 autosave;
- an initial rollout implementation could overwrite a returning player's normal campaign autosave while showing the new First Hour; tutorial progress now has its own storage key and the prior campaign is restored afterward;
- ordinary page startup previously created a fresh world before preserving the existing autosave; startup now resumes the campaign autosave paused;
- loading an onboarding save did not rebuild the matching tutorial state;
- a stale completed-user autosave could reopen an active tutorial world;
- Stage 4 depended on non-persisted UI selection state;
- time and advanced tabs could still be used during the supposedly paused tutorial;
- hidden settlement-linked fields/decor could leak map information;
- the QA workflow originally only ran on the feature branch and would have gone dormant after merge;
- the page title still said `v1.4.8-dev`;
- several selector-list regressions were caught and fixed before merge.

## Whole-game regression added during final QA

The PR now keeps a permanent core and browser regression pass in addition to the focused First Hour checks.

Latest green run on the final gameplay code covered:

- 250 generated worlds and graph/start-fairness checks;
- 2,500 production/storage assertions;
- 500 recruitment/unlock/supply checks;
- army mission, truce, alliance and stale-reinforcement edge cases;
- diplomacy and exact annex accounting;
- raid-loot storage-cap behavior;
- 100 deterministic chunking comparisons;
- 180 save/migration round-trips;
- immediate victory/defeat state recognition;
- 80 long human-like QA campaigns with 35,017 battle reports reconciled;
- desktop Chromium build/recruit/save/load, Steward, diplomacy, allied reinforcement, raid/report, annex, war, Threat Pause, New World, and victory/sandbox paths;
- blocked-localStorage session Save/Load/New World behavior;
- iPhone-sized WebKit workspace, help, footer/music, save/load and clock behavior.

During this pass the following whole-game issues were fixed: hostile orders against allies, reinforcements becoming accidental attacks after diplomacy changed in transit, raid loot exceeding storage, delayed victory/defeat recognition, incorrect hegemony victory copy, First Hour skip not rebuilding the full map, and campaign autosave loss/replacement on reopen or tutorial rollout.

## Known residuals / intentional behavior

- Returning v1.4.7 players who only have the older `crownfall-tutorial-seen` flag are shown the v1.4.8 First Hour once. They may choose **Skip First Hour** immediately; once completed or skipped, it does not repeat.
- This QA uses iPhone-sized WebKit rather than a physical iPhone. A real-device spot check is still worthwhile after deployment, but there is no current browser-QA blocker.
- The river scorer can still place up to three settlements close to the river in rare generated worlds; dry-ground treatment prevents water from visibly running underneath those towns.
- Barracks IV–VI still have no new troop unlock or documented mechanical benefit. That is pre-existing game-design debt, not introduced by this PR.

