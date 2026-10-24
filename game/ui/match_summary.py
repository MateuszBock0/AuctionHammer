"""Read-only end-of-match statistics, strictly from signed match history.

Historical saves may lack a complete audit. In that case, detailed numbers
are deliberately absent rather than inferred from the final board or log text.
No engine command, simulation, replay or game-state mutation is performed.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitRecord:
    uid: str
    name: str
    attack: int
    max_hp: int

    @property
    def power(self) -> int:
        # Transparent comparison metric, not an invented combat power rating.
        return self.attack+self.max_hp


@dataclass(frozen=True)
class DamageRecord:
    target: str
    target_name: str
    hp_lost: int


@dataclass(frozen=True)
class LevelRecord:
    uid: str
    name: str
    level: int


@dataclass(frozen=True)
class MatchSummary:
    rounds: int
    hero_hp: tuple[int, int]
    coins: tuple[int, int]
    deaths: tuple[int, int] | None
    complete: bool
    plays: int | None
    attacks: int | None
    levelled_cards: int | None
    strongest: UnitRecord | None
    largest_damage: DamageRecord | None
    leader: LevelRecord | None


def build_match_summary(game) -> MatchSummary:
    """Describe the actual FINISHED game, not hypothetical achievements."""
    if game.phase!='finished':
        raise ValueError('Podsumowanie wymaga zakończonego meczu.')
    counts=(tuple(game.death_counts)
            if getattr(game,'death_counts_complete',False)
            and getattr(game,'death_counts',None) is not None else None)
    common=dict(
        rounds=game.round,
        hero_hp=(max(0,game.players[0].hp),max(0,game.players[1].hp)),
        coins=(game.players[0].coins,game.players[1].coins),
        deaths=counts,
    )
    if (not getattr(game,'audit_complete',False)
            or not isinstance(getattr(game,'audit_initial',None),dict)
            or not isinstance(getattr(game,'audit_actions',None),list)
            or not isinstance(getattr(game,'audit_internal',None),list)):
        return MatchSummary(**common,complete=False,plays=None,attacks=None,
                            levelled_cards=None,strongest=None,
                            largest_damage=None,leader=None)

    actions=game.audit_actions
    successful=[a for a in actions if a.get('result')=='ok']
    plays=sum(a.get('operation')=='play' and
              a.get('command_owner',a.get('actor_before'))==0
              for a in successful)
    attacks=sum(a.get('operation')=='attack' and
                a.get('command_owner',a.get('actor_before'))==0
                for a in successful)

    strongest=None
    def observe_unit(uid,record):
        nonlocal strongest
        if not isinstance(record,dict) or uid not in game.cards:
            return
        atk=record.get('current_attack',record.get('atk'))
        hp=record.get('current_max_hp',record.get('max_hp'))
        if not isinstance(atk,int) or not isinstance(hp,int):
            return
        candidate=UnitRecord(uid,game.cards[uid].definition.name,atk,hp)
        if strongest is None or candidate.power>strongest.power:
            strongest=candidate

    levelled=set()
    leader=None
    def observe_card(uid,record):
        nonlocal leader
        if (uid not in game.cards or uid in game.auction_awards
                or not isinstance(record,dict) or record.get('owner')!=0):
            return
        level=record.get('ability_level')
        if not isinstance(level,int) or level<1:
            return
        levelled.add(uid)
        candidate=LevelRecord(uid,game.cards[uid].definition.name,level)
        if leader is None or level>leader.level:
            leader=candidate

    initial=game.audit_initial
    for uid,unit in (initial.get('units') or {}).items():
        observe_unit(uid,unit)
    for uid,card in (initial.get('cards') or {}).items():
        observe_card(uid,card)
    for action in actions:
        changes=action.get('changes') or {}
        for uid,entry in (changes.get('units') or {}).items():
            observe_unit(uid,entry.get('before'))
            observe_unit(uid,entry.get('after'))
        for uid,entry in (changes.get('cards') or {}).items():
            observe_card(uid,entry.get('before'))
            observe_card(uid,entry.get('after'))
    for uid,unit in game.units.items():
        observe_unit(uid,{'atk':unit.atk,'max_hp':unit.max_hp})
    for uid,card in game.cards.items():
        observe_card(uid,{'owner':card.owner,
                          'ability_level':card.ability_level})

    largest=None
    for entry in game.audit_internal:
        if entry.get('operation')!='_damage' or entry.get('error'):
            continue
        arguments=entry.get('args') or ()
        if not arguments or not isinstance(arguments[0],str):
            continue
        uid=arguments[0]
        before=(entry.get('before') or {}).get(uid)
        after=(entry.get('after') or {}).get(uid)
        # An absent post-state (e.g. after death) gives no independently
        # verifiable HP delta. Never infer it from requested attack power.
        if not isinstance(before,dict) or not isinstance(after,dict):
            continue
        old,new=before.get('hp'),after.get('hp')
        if not isinstance(old,int) or not isinstance(new,int) or old<=new:
            continue
        delta=old-new
        name=(game.players[int(uid.split(':')[1])].name
              if uid in ('hero:0','hero:1')
              else game.cards[uid].definition.name if uid in game.cards
              else uid)
        if largest is None or delta>largest.hp_lost:
            largest=DamageRecord(uid,name,delta)

    return MatchSummary(**common,complete=True,plays=plays,attacks=attacks,
                        levelled_cards=len(levelled),strongest=strongest,
                        largest_damage=largest,leader=leader)
