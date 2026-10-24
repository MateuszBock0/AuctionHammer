"""Read-only live aura/synergy links derived from Match's resolved board.

The rules below mirror Match._update_auras (S34, S35, S105, bronze A002).
No ability is invoked and no future trigger is predicted. A link describes
one source's modifier, not the recipient's net combined stat change.
"""
from __future__ import annotations

from dataclasses import dataclass
from game.core.auction_abilities import rarity


@dataclass(frozen=True)
class AuraLink:
    source: str
    target: str
    kind: str
    amount: int
    label: str
    # The amount is the modifier contributed by THIS source.
    # Other auras and stat clamping can change the resulting total.


def live_aura_links(game, focus_uid: str | None) -> tuple[AuraLink, ...]:
    """Outgoing links for aura sources; incoming when inspecting a beneficiary.

    Units must remain on an actual board and be present in the committed Match.
    On S105, show remaining recorded shield-like aura armor, not its nominal
    original grant after some armor was consumed.
    """
    if focus_uid not in game.units or focus_uid not in game.cards:
        return ()
    on_board={
        uid for player in game.players for uid in player.board
        if uid in game.units and uid in game.cards
    }
    if focus_uid not in on_board:
        return ()
    all_links=[]
    for source in sorted(on_board):
        unit=game.units[source]
        if game._disabled(unit):
            continue
        cid=game.cards[source].definition.id
        owner=unit.owner
        friendly=[uid for uid in game.players[owner].board if uid in on_board]
        hostile=[uid for uid in game.players[1-owner].board if uid in on_board]

        if cid=='S34' and unit.aura_mode in ('ally','enemy'):
            pos=game.slot_of(source)
            target=None
            if unit.aura_mode=='ally':
                if game.fixed_board_slots:
                    # The engine explicitly prefers RIGHT over LEFT.
                    target=(game.unit_at(owner,pos+1)
                            or game.unit_at(owner,pos-1))
                elif len(friendly)>1:
                    target=(friendly[pos+1] if pos+1<len(friendly)
                            else friendly[pos-1])
            else:
                target=game.unit_at(1-owner,pos)
            if target in on_board:
                delta=(1+unit.ability_level)*(1 if unit.aura_mode=='ally' else -1)
                all_links.append(AuraLink(source,target,'atk',delta,
                                          f'ATK {delta:+d}'))
        elif cid=='S35' and unit.aura_mode in ('ally','enemy'):
            delta=(1+unit.ability_level)*(1 if unit.aura_mode=='ally' else -1)
            for target in friendly if unit.aura_mode=='ally' else hostile:
                if target!=source:
                    all_links.append(AuraLink(source,target,'max_hp',delta,
                                              f'MAX PŻ {delta:+d}'))
        elif cid=='S105':
            for target in friendly:
                if target==source:
                    continue
                armor=game.units[target].aura_armor.get(source,0)
                if armor>0:
                    all_links.append(AuraLink(source,target,'armor',armor,
                                              f'PANC. +{armor}'))
        elif (cid=='A002' and game.auction_catalog in ('v4','v22')
              and source in game.auction_awards and rarity(game,source)==0):
            # Bronze General strengthens every unit on BOTH boards, including
            # itself. Self-link is shown as a self badge, not a zero-length arrow.
            for target in sorted(on_board):
                all_links.append(AuraLink(source,target,'atk',1,'ATK +1'))

    outgoing=tuple(link for link in all_links if link.source==focus_uid)
    if outgoing:
        return outgoing
    return tuple(link for link in all_links if link.target==focus_uid)
