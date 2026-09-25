# Crownfall Marches — Balance & Simulation QA

Last updated: 2026-09-25  
Release target: v1.4.7

This file records the mechanics and balance findings from the September 2026 QA pass so future tuning can be compared against measured behavior rather than memory.

## Correctness fixes now on main

1. **Repelled-army survivors**
   - Battle reports already calculated surviving attackers correctly.
   - Previously, survivors from a lost attack disappeared from world state after the army object was removed.
   - Survivors now return using the same return path used by other non-annexing outcomes.

2. **House Bellamy diplomacy cadence**
   - The old modulo condition could never be true on Bellamy's AI-action days.
   - Diplomacy timing is now aligned with the other AI realms.

3. **Chunk-independent seeded simulation**
   - RNG is initialized per simulated day inside `advanceDays()`.
   - A multi-day advance now matches the same number of one-day advances for the same world state/seed.

## Arithmetic/property audit

Randomized mechanical checks completed during this pass:

- 15,000 resource production / storage-cap assertions
- 3,000 building-upgrade spend and level assertions
- 3,000 recruitment spend and unit-count assertions
- 5,990 battle casualty / survivor assertions
- 108,000+ battle reports inspected in large campaign batches

No arithmetic mismatch was found in those checks.

The Settlement panel's displayed resource rate and `dailyEconomy()` both use the same `production(s)` calculation. Production therefore matches the display until a settlement reaches its storage cap.

## Supply model

Current rule:

```
capacity = 70 + Farms level * 35
```

Unit supply:

| Unit | Supply |
| --- | ---: |
| Militia | 1 |
| Spearmen | 1 |
| Raiders | 2 |
| Cavalry | 3 |

A starting capital has 140 supply capacity. Farms VIII provides 350.

Armies in transit remain charged to their origin settlement. Reinforcements may cause a destination to exceed its local capacity; existing troops remain, but additional recruitment is blocked until capacity is available.

A legacy pre-supply save was loaded during QA and round-tripped successfully without changing its core world state.

## Recruitment composition

Before composition-aware recruiting, long-campaign armies were overwhelmingly Spearmen and routine administration effectively produced no Cavalry.

Representative pre-change aggregate:

- Militia: ~1%
- Spearmen: ~91%
- Raiders: ~8%
- Cavalry: 0%

Representative current aggregate on identical-seed QA:

- Militia: ~11%
- Spearmen: ~44%
- Raiders: ~31%
- Cavalry: ~14%

The change chooses the eligible unit furthest below the Steward policy's target composition instead of always recruiting the first affordable preferred unit.

## Paired balance comparison

40 identical world seeds, up to day 2,200.

### Optimized QA player

| Build | Wins | Defeats | Unresolved | Median win day |
| --- | ---: | ---: | ---: | ---: |
| Correctness-only baseline | 32 | 0 | 8 | 835 |
| Current v1.4.7 rules | 30 | 0 | 10 | 790 |

### Imperfect / casual QA player

The casual model acts less frequently, sometimes skips useful actions, introduces scouting-estimate error, and does not always pick the mathematically strongest target.

| Build | Wins | Defeats | Unresolved | Median win day |
| --- | ---: | ---: | ---: | ---: |
| Correctness-only baseline | 9 | 0 | 31 | 1,380 |
| Current v1.4.7 rules | 9 | 0 | 31 | 1,430 |

Interpretation: the supply and composition changes substantially improve internal behavior without materially changing the default campaign difficulty in this sample.

## AI attack quality

An early full target-aware force-sizing experiment made the AI much more efficient, but it also pushed normal campaigns toward long stalemates. It is intentionally **not** part of the default game.

The current default instead uses a light guard:
- retain the existing aggressive/permissive dispatch behavior;
- reject only extremely weak sent armies;
- try to stage reinforcements when a frontier cannot locally raise a viable force.

The stronger target-aware model remains an experiment for a possible future harder difficulty mode.

## Known edge case: passive fortress

A player who leaves the default Steward running but never issues a military order can still become effectively irrelevant rather than conquered.

Current-main passive test:
- 80 worlds
- 3,000 days each
- 0 attacks against the player's one-settlement realm
- 0 player defeats
- average passive-capital defense: ~5,833
- average largest rival realm: ~14.1 settlements
- largest rival observed: 21 settlements

This is no longer caused by unlimited recruitment; the supply cap works. The remaining issue is strategic concentration / siege behavior. Rival realms tend to prefer more attainable fronts instead of coordinating enough force to assault the isolated fortress.

This edge case is **not being fixed by globally buffing the AI**, because tests showed that smarter universal force sizing can make ordinary active campaigns too grindy.

## Future experiments

Candidates, in order of preference:

1. **Hard AI / difficulty option** using more target-aware force sizing.
2. **Better late-game mustering** so AI realms can deliberately concentrate several settlements on one strategic target.
3. **Siege mechanic** if mustering alone is insufficient. A wall-breaking Ram/Siege Crew is historically consistent with the game's inspiration and would create a specific counter to high Wall levels instead of nerfing Walls globally.
4. **Rival victory / campaign-resolution rules** if late-game multi-realm stalemates remain common after strategic improvements.

Any future change should be measured on identical world seeds against this v1.4.7 baseline.
