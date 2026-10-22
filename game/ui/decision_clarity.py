"""Read-only decision cues grounded in the current, authoritative Match.

Never predict random outcomes or execute core commands from the UI.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EconomyCue:
    vacant_income: int | None
    rounds_to_auction: int | None


@dataclass(frozen=True)
class PositionCue:
    owner: int
    slot: int
    label: str
    uid: str | None


def economy_cue(game) -> EconomyCue:
    """Current-board estimate, explicitly not a guaranteed end-turn payout."""
    income = None
    if (getattr(game, "phase", None) == "turn" and game.active == 0
            and getattr(game, "vacant_income_enabled", False)
            and game.players[0].hp > 0):
        income = max(0, 5 - len(game.players[0].board))
    countdown = None
    if (getattr(game, "auctions_enabled", False)
            and getattr(game, "auction_catalog", None) in ("v4", "v22", "v3")
            and len(getattr(game, "auction_bag", ())) >= 3):
        if game.phase == "auction":
            countdown = 0
        elif game.phase in ("turn", "mulligan"):
            countdown = 3 - ((game.round - 1) % 3)
    return EconomyCue(income, countdown)


def positional_cues(game, uid: str | None) -> tuple[PositionCue, ...]:
    """Display geometry used by S34 and S108; effects can still be blocked.

    S34 ally mode prefers the right-hand neighbour, then the left, exactly
    matching Match._update_auras. S108 marks the opposing slot as a future
    first-sighting reaction *area*, not an unconditional guaranteed stun.
    """
    if (not getattr(game, "fixed_board_slots", False)
            or uid not in game.units or uid not in game.cards):
        return ()
    card = game.cards[uid]
    unit = game.units[uid]
    if card.definition.id not in ("S34", "S108"):
        return ()
    owner, slot = unit.owner, game.slot_of(uid)
    if card.definition.id == "S108":
        return (PositionCue(1 - owner, slot, "NAPRZECIW / REAKCJA", 
                            game.unit_at(1 - owner, slot)),)
    if unit.aura_mode == "ally":
        target = (game.unit_at(owner, slot + 1) if slot < 4 else None)
        if target is None and slot > 0:
            target = game.unit_at(owner, slot - 1)
        if target is None:
            return ()
        return (PositionCue(owner, game.slot_of(target), "AURA +ATK", target),)
    target = game.unit_at(1 - owner, slot)
    if target is None:
        return ()
    return (PositionCue(1 - owner, slot, "AURA -ATK", target),)
