"""Archiwum wszystkich zatwierdzonych zdarzeń i widokowe migawki meczu.

Migawki są kopiami tylko-do-odczytu, nie odtwarzają komend na żywym silniku.
Każda zachowana klatka odpowiada ZATWIERDZONEMU stanowi po akcji.
"""
from __future__ import annotations
from dataclasses import dataclass
import copy


@dataclass(frozen=True)
class ReplayFrame:
    seq: int
    round: int
    active: int
    game: object


class MatchRecorder:
    def __init__(self, max_frames: int = 480):
        self.max_frames=max_frames
        self.frames: list[ReplayFrame] = []
        self._fingerprint = None

    @staticmethod
    def fingerprint(game):
        # Dodatkowe zmiany w mulliganie/wyborze celu nie muszą generować logu.
        player_state=tuple(
            (tuple(p.hand),tuple(p.board),p.hp,p.hero_armor,p.hero_shield,
             tuple(p.mulligan_selected),p.turn_count)
            for p in game.players
        )
        unit_state=tuple(sorted(
            (uid,u.hp,u.atk,u.max_hp,u.shield,u.armor,u.attacks,
             tuple((e.kind,e.value,e.remaining,e.expires,e.source) for e in u.effects))
            for uid,u in game.units.items()
        ))
        pending=(game.pending.uid,game.pending.context,
                 tuple((ch.mode,ch.target) for ch in game.pending.choices)) if game.pending else None
        return (len(game.event_journal),game.phase,game.active,game.round,
                game.winner,player_state,unit_state,pending)

    def capture(self,game):
        signature=self.fingerprint(game)
        if signature==self._fingerprint:
            return False
        self._fingerprint=signature
        # Omit full audit ledger from each of the 480 presentation snapshots.
        # Otherwise N snapshots would repeatedly duplicate earlier commands.
        memo={}
        if getattr(game,'audit_enabled',False) and hasattr(game,'audit_actions'):
            memo[id(game.audit_actions)]=[]
            if hasattr(game,'audit_internal'):
                memo[id(game.audit_internal)]=[]
            memo[id(game.audit_initial)]=None
        frozen=copy.deepcopy(game,memo)
        frozen.audit_enabled=False
        if hasattr(frozen,'audit_actions'):
            frozen.audit_actions=[]
            if hasattr(frozen,'audit_internal'):
                frozen.audit_internal=[]
            frozen.audit_initial=None
        # Dziennik trzymany jest w bieżącym Match; nie duplikujemy historii
        # przy każdej klatce, aby oszczędzić RAM.
        frozen.event_journal=[]
        self.frames.append(ReplayFrame(len(game.event_journal),
                                       game.round,game.active,frozen))
        if len(self.frames)>self.max_frames:
            del self.frames[:len(self.frames)-self.max_frames]
        return True

    @property
    def last_index(self):
        return len(self.frames)-1

    def get(self,index):
        if not 0<=index<len(self.frames):
            raise IndexError(index)
        return self.frames[index]
