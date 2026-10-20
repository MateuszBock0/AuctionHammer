"""Read-only gameplay indicators for AuctionHammer 0.9.47.

Match remains authoritative: legal actions and committed journal events are
observed, never guessed from stats or card names.
"""
from __future__ import annotations
from dataclasses import dataclass
from game.ui.attack_view import attack_display


@dataclass(frozen=True)
class TurnReadout:
    is_human_turn: bool
    played_cards: int
    can_play: bool
    ready_units: int

    @property
    def can_act(self) -> bool:
        return self.can_play or self.ready_units > 0


@dataclass(frozen=True)
class CardReadout:
    label: str
    color: tuple[int,int,int]
    action: str


@dataclass(frozen=True)
class CombatNotice:
    label: str
    message: str
    color: tuple[int,int,int]


def _can_play_any(game) -> bool:
    if game.phase != 'turn' or game.active != 0 or game.pending:
        return False
    player = game.players[0]
    if player.played_this_turn or not player.hand:
        return False
    if len(player.board) < 5:
        return any(game.can_play(0, uid, None) for uid in player.hand)
    return any(game.can_play(0, uid, replaced)
               for uid in player.hand for replaced in player.board)


def turn_readout(game) -> TurnReadout:
    player=game.players[0]
    human=game.phase=='turn' and game.active==0 and game.pending is None
    ready=(sum(1 for uid in player.board if uid in game.units
               and bool(game.legal_attacks(uid))) if human else 0)
    return TurnReadout(human,int(bool(player.played_this_turn)),
                       _can_play_any(game) if human else False,ready)


def selected_card_readout(game, uid: str) -> CardReadout:
    """Small ownership-aware status chip sourced from engine legal actions."""
    if uid not in game.cards:
        return CardReadout('BRAK KARTY',(159,175,183),'')
    human=game.players[0]
    if uid in human.hand:
        if game.phase!='turn' or game.active!=0 or game.pending:
            return CardReadout('NA RĘCE',(206,189,160),
                               'Zagrywanie dostępne podczas własnej tury.')
        playable=(game.can_play(0,uid,None) if len(human.board)<5
                  else any(game.can_play(0,uid,old) for old in human.board))
        if playable:
            return CardReadout('ZAGRAJ KARTĘ',(228,183,94),
                               'Kliknij podświetlone pole lub dozwoloną wymianę.')
        return CardReadout('BRAK ZAGRANIA',(159,175,183),
                           'Nie można teraz wystawić tej karty.')
    if uid in human.board and uid in game.units:
        attack=attack_display(game,uid)
        if attack.ready:
            return CardReadout('ATAK GOTOWY',(114,203,153),
                               'Wybierz turkusowo oznaczony legalny cel.')
        return CardReadout('ATAK WSTRZYMANY',(206,189,160),attack.reason)
    if uid in game.players[1].board:
        return CardReadout('KARTA RYWALA',(238,111,112),
                           'Jednostka przeciwnika; wybierz własną kartę, aby działać.')
    return CardReadout('PODGLĄD KARTY',(159,175,183),'')


def combat_notice(message: str) -> CombatNotice | None:
    """Classify only committed journal lines and retain their exact wording."""
    lower=message.lower()
    # Shield / armor absorption must take precedence over generic damage.
    if any(key in lower for key in ('tarcza blokuje',
                                   'tarcza bohatera blokuje',
                                   'pancerz pochłania',
                                   'pancerz bohatera pochłania')):
        return CombatNotice('OBRONA / BLOKADA',message,(123,183,236))
    if any(key in lower for key in ('zgon','umiera','ginie')):
        return CombatNotice('JEDNOSTKA POLEGŁA',message,(236,188,132))
    if any(key in lower for key in ('leczy','ulecz','regeneracj','odzyskuje')):
        return CombatNotice('LECZENIE',message,(115,222,166))
    if any(key in lower for key in ('obrażen','zadaje','rani','traci pż')):
        return CombatNotice('OBRAŻENIA',message,(224,116,120))
    if any(key in lower for key in ('trucizn','ogłusz','wyciszenie','status')):
        return CombatNotice('EFEKT / STATUS',message,(190,145,242))
    if any(key in lower for key in ('tarcz','pancerz','zmiana aury')):
        return CombatNotice('OCHRONA / EFEKT',message,(123,183,236))
    return None
