"""Tylko-do-odczytu: oddziel licznik użytych ataków od gotowości TERAZ.

Silnik Match.legal_attacks() jest jedynym źródłem prawdy o dozwolonych celach.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AttackDisplay:
    remaining: int
    limit: int
    spent: int
    ready: bool
    reason: str
    next_attack_bonus: bool = False

    @property
    def label(self) -> str:
        return f'ATAKI {self.remaining}/{self.limit}'


def attack_display(game, uid: str) -> AttackDisplay:
    u = game.units[uid]
    owner = game.players[u.owner]
    d = game.cards[uid].definition
    limit = 2 if game._double(u) else 1
    spent = max(0, u.attacks)
    remaining = max(0, limit - spent)
    legal = bool(game.legal_attacks(uid))
    conditional = (
        d.id == 'S79' and spent == 0 and not game._disabled(u)
        and not game._has(u, 'stun')
    )
    if legal:
        reason = 'GOTOWA'
    elif game._has(u, 'stun'):
        reason = 'OGŁUSZONA'
    elif game.phase != 'turn' or game.active != u.owner:
        reason = 'CZEKA NA TURĘ'
    elif game.pending is not None:
        reason = 'TRWA WYBÓR'
    elif u.played_turn == owner.turn_count and not game._fast(u):
        reason = 'NOWA JEDNOSTKA'
    elif remaining == 0:
        reason = 'ATAKI WYKORZYSTANE'
    else:
        reason = 'BRAK LEGALNEGO CELU'
    if conditional:
        reason += ' · 2. PO 1. ATAKU'
    return AttackDisplay(remaining,limit,spent,legal,reason,conditional)
