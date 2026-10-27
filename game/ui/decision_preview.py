"""Read-only, conservative combat/replacement/tavern decision aids.

The preview reports STANDARD hit/retaliation from the current visible board.
On-attack abilities, death waves and phase effects can modify actual results,
so this module never promises a final HP or death event.
"""
from __future__ import annotations

from dataclasses import dataclass

from game.core import auction_abilities


@dataclass(frozen=True)
class HitProjection:
    raw: int
    absorbed: int
    hp_loss: int
    after_hp: int
    blocked_by_shield: bool


def hit_projection(target,raw:int,hero:bool=False):
    """Mirror the _damage shield-first, armor-second basic defensive path."""
    raw=max(0,int(raw))
    shield=(target.hero_shield if hero else target.shield)
    armor=(target.hero_armor if hero else target.armor)
    hp=target.hp
    if not raw:
        return HitProjection(0,0,0,hp,False)
    if shield:
        return HitProjection(raw,raw,0,hp,True)
    absorbed=min(raw,max(0,int(armor)))
    hp_loss=raw-absorbed
    return HitProjection(raw,absorbed,hp_loss,hp-hp_loss,False)


def _attack_power(game,uid):
    result=game.units[uid].atk
    if (game.auction_catalog in ('v4','v22')
            and auction_abilities.boosted_attack(game,uid)):
        result*=2
    return result


@dataclass(frozen=True)
class AttackProjection:
    target: str
    strike: HitProjection
    counter: HitProjection | None
    extra_effects_possible: bool


def preview_standard_attack(game,uid,target):
    """Only a CURRENTLY legal attack. No hidden data, Match commands or RNG."""
    if uid not in game.units or target not in game.legal_attacks(uid):
        return None
    raw=_attack_power(game,uid)
    hero=target.startswith('hero:')
    defender=(game.players[int(target.split(':')[1])] if hero
              else game.units[target])
    strike=hit_projection(defender,raw,hero=hero)
    counter=(None if hero else
             hit_projection(game.units[uid],_attack_power(game,target)))
    # Wild-beast ON_ATTACK and passive S103 act BEFORE basic combat.
    # Any reactive/death ability can subsequently change actual outcomes.
    extra=(game.cards[uid].definition.faction=='Dzikie bestie'
           or (not hero and game.cards[target].definition.id=='S103'))
    return AttackProjection(target,strike,counter,extra)


@dataclass(frozen=True)
class ReplacementProjection:
    old_uid: str
    new_uid: str
    old_atk: int
    old_hp: int
    new_atk: int
    new_hp: int
    loses_outgoing_aura: bool


def preview_replacement(game,new_uid,old_uid):
    """Initial new-card stats vs live old unit; engine must approve replacement."""
    if (new_uid not in game.cards or old_uid not in game.units
            or new_uid not in game.players[0].hand
            or old_uid not in game.players[0].board
            or len(game.players[0].board)!=5
            or not game.can_play(0,new_uid,old_uid)):
        return None
    from game.ui.aura_links import live_aura_links
    old=game.units[old_uid]
    new=game.cards[new_uid]
    links=live_aura_links(game,old_uid)
    return ReplacementProjection(
        old_uid,new_uid,old.atk,old.hp,new.attack,new.max_hp,
        any(link.source==old_uid for link in links))


def next_brawl_damage(game):
    if not getattr(game,'tavern_beer_enabled',False):
        return 0
    remaining=max(0,int(getattr(game,'beer_turns_remaining',0)))
    return (remaining if getattr(game,'tavern_scaled_damage_enabled',False)
            else int(remaining>0))


def brawl_at_risk(game,uid):
    """Lethal RISK at next tick on current board (before end-turn triggers)."""
    if not any(uid in p.board for p in game.players) or uid not in game.units:
        return False
    hit=next_brawl_damage(game)
    if hit<=0:
        return False
    proj=hit_projection(game.units[uid],hit)
    return proj.hp_loss>0 and proj.after_hp<=0
