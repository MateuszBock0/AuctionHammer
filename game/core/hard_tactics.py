"""Bounded, read-only tactical lookahead for HARD AI (0.9.94).

No Match clone, no RNG and no speculative command. Inspects public board only.
Each decision expands at most WIDTH*DEPTH*10 tactical alternatives, never
the whole game tree; all unknown reactive/death effects stay authoritative in
Match and are deliberately *not* simulated here.
"""
from __future__ import annotations

DEPTH=3
WIDTH=5
MAX_ATTACKERS=5
MAX_TARGETS=5


def _ready(game,owner,target):
    """Return actual legal attackers and their available attack charges."""
    from . import auction_abilities
    result=[]
    for uid in game.players[owner].board[:MAX_ATTACKERS]:
        if uid not in game.units or target not in game.legal_attacks(uid):
            continue
        unit=game.units[uid]
        doubled=game.auction_catalog in ('v4','v22') and auction_abilities.boosted_attack(game,uid)
        hit=unit.atk*(2 if doubled else 1)
        charges=(2 if game._double(unit) else 1)-unit.attacks
        if charges>0:
            result.append((uid,hit,min(2,charges)))
    return result


def _walk(hits,health,shield,armor):
    """At most 3 sequential hits; bounded-width, deterministic beam.

    Returns the first attack in a confirmed (simple damage-only) lethal
    sequence, if any. The engine remains the source of truth for reactive
    effects, armor sources, and death-wave triggers.
    """
    if health<=0 or not hits:
        return None
    # state: (hp, shield, armor, remaining charges, first index, moves)
    root=(health,bool(shield),max(0,armor),
          tuple(item[2] for item in hits),None,0)
    frontier=[root]
    for _ in range(DEPTH):
        candidates=[]
        for hp,protected,arm,charges,first,moves in frontier:
            for index,(_,raw,_) in enumerate(hits):
                if charges[index]==0:
                    continue
                if protected:
                    next_hp,next_armor,next_shield=hp,arm,False
                else:
                    absorbed=min(arm,raw)
                    next_hp=hp-max(0,raw-absorbed)
                    next_armor=arm-absorbed
                    next_shield=False
                picked=index if first is None else first
                if next_hp<=0:
                    return hits[picked][0]
                remaining=list(charges)
                remaining[index]-=1
                # Beam prefers future damage, avoiding huge shield-breaking
                # strikes and preserving high-hit attacks for the final blow.
                potential=sum(max(0,hits[i][1])*min(remaining[i],DEPTH)
                              for i in range(len(hits)))
                rank=(-next_hp + .1*potential -
                      (2.0 if next_shield else 0) - next_armor*.15)
                candidates.append((rank,(next_hp,next_shield,next_armor,
                                         tuple(remaining),picked,moves+1)))
        if not candidates:
            return None
        # Tuple index gives a deterministic tiebreaker; never RNG.
        candidates.sort(key=lambda item:(-item[0],item[1][4]))
        frontier=[state for _,state in candidates[:WIDTH]]
    return None


def forced_hero_finish(game,owner):
    """Return first legal attack for a <=3-hit hero finish, otherwise None."""
    opponent=1-owner
    hero=f'hero:{opponent}'
    hits=_ready(game,owner,hero)
    if not hits:
        return None
    player=game.players[opponent]
    source=_walk(hits,player.hp,player.hero_shield,player.hero_armor)
    return (source,hero) if source is not None else None


def shield_break_setup(game,owner):
    """Find a cheap shield break enabling an immediate follow-up kill.

    Evaluates only public shielded enemies, two attacks and legal attackers.
    Avoids sacrificing aura sources and avoids automatic death-trigger chains
    (those are governed by Match and may need choices or reactive effects).
    """
    own=game.players[owner]
    enemy=game.players[1-owner]
    from . import auction_abilities
    best=None
    for target in enemy.board[:MAX_TARGETS]:
        victim=game.units.get(target)
        if victim is None or not victim.shield:
            continue
        victim_def=game.cards[target].definition
        if victim_def.id in ('A001','A003') or victim_def.faction=='Potwory':
            continue
        hitters=_ready(game,owner,target)
        if len(hitters)<2 and (not hitters or hitters[0][2]<2):
            continue
        for src,raw,charges in hitters:
            attacker=game.units[src]
            own_def=game.cards[src].definition
            # S103 hits the attacker before conventional combat.
            if victim_def.id=='S103' and attacker.hp<=2+victim.ability_level:
                continue
            ret=0 if attacker.shield else max(0,victim.atk-attacker.armor)
            if ret>=attacker.hp:
                continue
            if own_def.id in ('A002','S34','S35','S105'):
                continue  # don't trade support engines for a shield
            # A first hit consumes the shield; one follow-up must be able
            # to kill after armor. This is a *setup*, not damage guessing.
            for next_src,next_raw,next_charges in hitters:
                if src==next_src and charges<2:
                    continue
                if next_raw<victim.hp+victim.armor:
                    continue
                # Prefer removing dangerous engines and spending the
                # smallest viable hit on the shield itself.
                priority=victim.atk + (9 if victim_def.id in ('A002','S34','S35','S105') else 0)
                score=priority*2-raw*.35-ret*.4
                candidate=(score,-own.board.index(src),src,target)
                if best is None or candidate>best:
                    best=candidate
    return (best[2],best[3]) if best else None
