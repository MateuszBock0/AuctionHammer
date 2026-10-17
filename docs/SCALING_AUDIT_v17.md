# AuctionHammer — Full Ability Scaling Audit (Game Master v17)

**Scope:** all 70 unique starter cards, all 5 factions, all 14 ability families. Reviewed against `docs/GAME_MASTER_v17.md`, `data/cards_base_70.json`, `game/core/models.py`, and `game/core/engine.py`.

## Authoritative timing

A card earns its regular stat growth at the **end of its controller's own turn while it is still in hand**. It receives no growth during the opponent's turn, while in a deck, on the battlefield or in the graveyard.

The ability-upgrade tier is `k = floor(completed_own_hand_turns / 3)`. Thus, at 0–2 turns `k=0`, at 3–5 `k=1`, at 6–8 `k=2` and at 9–11 `k=3`. The played unit snapshots this level; additional turns on the battlefield cannot improve that unit. Its hand-turn history resets upon leaving the battlefield.

All cards additionally receive **2 total points of base ATK/MAX HP growth per own completed hand turn**, distributed according to their individual catalogue profiles.

## Upgrade effect by family

Each family contains precisely 5 starter cards, one in each faction.

| Ability family | Extra benefit for each 3 completed own hand turns |
|---|---|
| Damage | +1 ability damage per successful numeric occurrence |
| Healing | +1 ability healing per occurrence |
| ATK +/- | +1 to the magnitude of the relevant ATK buff/debuff |
| MAX HP +/- | +1 to the magnitude of the MAX HP buff/debuff |
| Armor | +1 armor granted or stripped |
| Shield | **+3 unit MAX HP**, not additional shield charges |
| Poison | +1 damage **per complete poison application**, not per poison tick; original duration unchanged |
| Stun | +1 direct damage **only when the stun is successfully applied**; duration unchanged |
| Regeneration | +1 healing **per complete regeneration application**, not per regeneration tick; duration unchanged |
| Taunt | **+3 unit MAX HP**, no additional taunt or extension |
| Cleansing | +1 healing for an allied target or +1 damage for an enemy **only if an eligible temporary effect was actually removed** |
| Immunity | +1 permanent armor for the protected unit on the source's **first successful immunity activation** during its current battlefield stay |
| Quick Attack | **+2 unit ATK and +1 unit MAX HP**, not an extra attack |
| Double Attack | **+2 unit ATK**, not a third attack |

The quality bonus is in addition to the regular per-own-hand-turn stat growth. Its magnitude is multiplied by `k` where relevant. For example, a level-2 upgraded poison application adds +2 **total** damage; it does not add +2 on every poison tick.

### Special passive, attack, death and end-of-turn abilities

The tests exercise actual effect resolution for 50 cards with numeric ability upgrades, including passive retaliation (S103), passive healing amplification (S104), armor aura (S105), retaliatory poison (S107), positioning stun (S108), per-turn healing (S109), and the intrinsic immunity bonus (S39). They additionally exercise the operative trigger or property of each of the other 20 cards for which the upgrade modifies only unit stats.

## Issues corrected in the audit

1. **S111 — Field Surgeon / Chirurg Frontowy:** the card previously calculated an upgraded ability level but did not use it when its passive cleansing intercepted a temporary negative status. A successfully intercepted temporary negative now heals the unit by `k`. Permanent negative modifiers are not cleansed by S111, consistent with the text specifying *temporary* effects only. Poison uses the same central status mechanism, so the rule covers it.
2. **Action-duration effects:** cleansing used to miss certain temporary buffs/debuffs with an `expire_action` value but no turn-based `expires` value (for example, the temporary ATK effect from S68). Such statuses are now included among eligible temporary cleansing targets, so the upgraded cleansing effect can trigger correctly.
3. **Regression coverage:** independent expected-value tests now cover **all 70 cards** at hand-turn thresholds 0/3/6/9; statistics are checked also at 1/2/4/5/8/12 to verify exact step timing. Poison, regeneration, immunity, stun and cleansing have specific timing/conditional tests, including failure or resistance cases.

## Implementation verification

Run `python -m unittest discover -s tests -v` from the project root. The regression source is `tests/test_full_scaling_v17.py`.

These tests verify the code's deterministic behaviour against documented, independently entered expected values. They do not substitute for a complete manual playthrough of every possible multi-card interaction. Game Master v17 remains authoritative.
