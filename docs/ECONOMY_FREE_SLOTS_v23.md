# Economy v23 (proposal) — coins for vacant board slots

Status: PR candidate; **not yet on `main`**.

## Exact user rule

At the end of **each player's own turn**, after *all* on-end effects,
deaths, death triggers, summons, and resulting choices have resolved, the
current player gains `5 - len(current_player.board)` extra coins.
The board has exactly five slots. Both player 0 and the computer player 1
use the same formula:

| Units remaining | Free slots | Extra coins |
|---|---|---|
| 0 | 5 | +5 |
| 1 | 4 | +4 |
| 2 | 3 | +3 |
| 3 | 2 | +2 |
| 4 | 1 | +1 |
| 5 | 0 | +0 |

**Additive, not a replacement:** the original +1 coin to both players per
completed full round remains in place, as do the +3 coins granted at match
start to the second player, hero-HP threshold coins, kill bounties,
Bankier Widm, and every other source of coins. The reward is per **own**
turn only. It is independent of auction rarity and does not cost a card play.

## Implementation

- `game/core/engine.py`: schedule one payout when `_finalize_end_turn`
  completes, deliver it in `_next_turn_due` *after* draining death waves
  but before starting the next turn / auction. Log +0 through +5 visibly.
- `_space_income_due` is serialized, is cleared **before** entering an
  auction, and is never paid twice when auction choices resume the queue.
- `game/core/persistence.py`: old saves lacking the flag load with false.
- `game/core/audit.py`: include pending payout flag in state digest.
- `game/core/ai.py`: keep the original difficulty-based auction ceiling,
  but let normal/hard AI raise its ceiling by its currently empty slots
  (up to 5). Easy difficulty remains low by design.

## Balance boundaries and risks

A 1-unit player earns 4 per own turn vs. zero for the 5-unit player,
meaning up to 12 coins of relative advantage over three full rounds.
This helps the disadvantaged bidder access first pick of auction cards,
**not** immediate survival or direct board damage. It may also encourage
players to intentionally keep slots empty to save for auctions.

The money also continues to accumulate after the last auction if no card
can spend it. Further balancing (caps, timing or extra coin sinks) requires
match-level simulation and a separate decision; none is included here.

## Acceptance criteria

- Six exact board occupancies, +5 down to +0.
- Symmetric for both players, retains +1 per full round.
- No payout for board changes during opponent turn.
- After on-end triggers and death waves, before auction.
- Exactly once across auction pause, save, and reload.
- Old save compatibility and integrity checks.
- v21 card scaling and all v22 17/51 auction effects unchanged.
