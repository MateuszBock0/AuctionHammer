# AuctionHammer — Game Master v19 integration and card UI

**Source reviewed:** user-supplied `GRA_KARCIANA_ONLINE_GAME_MASTER_v19(1).zip`, especially `CHANGELOG_v19.md`, `MECHANICS_AUDIT_v19.md`, `data/cards_base_70.json`, `src/trait_grants_v19.py`, and the v19 validation report. The ZIP explicitly labels its isolated Python modules as reference fragments rather than a complete playable engine. This integration applies its rules to AuctionHammer's existing 70-card `Match` engine.

## Approved new v19 card rules

| ID | Rule integrated |
|---|---|
| S66 | On play, choose **self haste** or exactly one **other card currently in your hand**. Hand grant is attached to that specific physical card and consumed on its first summon. Selecting the hand card does **not** grant self haste |
| S67 | On play, grant Double Attack to **self or one other ally on the board**. The grant does not bypass summoning sickness or create a third attack |
| S79 | Base stat update to **2 ATK / 6 HP**; conditional double is enabled only after the first legal attack and only while the ability works |
| S114 | Base stat update to **1 ATK / 5 HP**; intrinsic Quick Attack is **self-only** |
| S115 | Base stat update to **1 ATK / 6 HP**; intrinsic Double Attack is **self-only** |

## v18 mechanics carried forward in v19

- **S20:** on death, grant one shield and two permanent armor to another allied unit, or to the owner hero if none survives.
- **S82:** on death, grant six permanent armor to another allied unit, or to the owner hero if none survives.
- **S90:** on death, select up to two *different* random cards from the owner's actual hand, using the match RNG; grant each Quick Attack on their next summon, nonstacking.
- **S91:** on death, select another allied board unit for permanent Double Attack; when no such unit survives, grant it to one random physical card in hand for its first later legally attack-capable own turn (including its summon turn if it has Quick Attack).
- **S105:** aura armor is a source-specific, one-time portion per contact; consumed points do not refill during aura recomputation.
- **S109:** scaling quality increases self-regeneration by one HP **every own end turn**, not once per whole lifetime.
- **S74/S87/S97/S111:** the approved conditional cleansing scaling descriptions replace generic/incorrect target branches.

The other 65 base card entries remain unchanged by v19 *except* the explicit v18 carryovers listed above. Per-own-hand-turn stat growth and the quality level at completed turn thresholds 3/6/9/12 remain authoritative. There are still exactly 70 unique starting cards, no purchasable starting cards and no active auction gameplay.

## New UI

Each compact card has a colored activation-time label, a distinctive family emblem or existing image, a large bold current numerical effect where relevant, a green quality-scaling ribbon, and current ATK/HP. The expanded card details show the original full ability and upgrade wording, highlight only semantically scalable quantities in green bold and keep the entire text scrollable. The target-choice pane remains separate from the card description, uses a paged six-choice list, and allows clicking highlighted units, heroes **or hand cards** (for S66). Mulligan selections have a stronger gold border and a numbered replacement badge. The display auto-fits the laptop screen with correct cursor mapping when resized or fullscreen.

The colored numbers represent the correct operation rather than blindly bolding every digit: for stun, the duration is not upgraded; for poison/regeneration the bonus is to the **total portion**, not every tick; for shield/taunt and Quick/Double Attack the bonus applies to stats without multiplying charges or attacks.

## Testing

Run `python -m unittest discover -s tests -v`. The focused regression file is `tests/test_v19_integration.py`. It tests the actual Match engine, hand-grant identity and consumption, v19 hero fallbacks, two-attack caps, S105 one-time armor, S109 per-turn regeneration, full 70-card infographics and Pygame rendering.

Automated tests verify these specific cases and all earlier regressions; they are not a full statistical PvP balance validation or proof that every possible chain of 70 card effects has been exhaustively exercised. The v19 source archive itself notes that its new stat values were not calibrated with a full win-rate simulation.
