"""Maszynowa specyfikacja wyborów kart startowych; tekst kart jest tylko opisem.

Każdy z 70 archetypów ma przypisany rodzinny typ operacji, docelowe
wybory i szczególne wyjątki zgodne z GAME_MASTER v19. Nie ma aukcji.
"""
from __future__ import annotations
from .models import Choice

# Efekty bez celu i bez możliwości wyboru rozstrzyga engine._execute.
SELF_OR_AUTOMATIC = {
    'S09', 'S10', 'S12', 'S70', 'S11', 'S15', 'S71', 'S72', 'S74', 'S76', 'S79',
    'S21', 'S17', 'S27', 'S95', 'S90', 'S103', 'S104', 'S105', 'S106', 'S107', 'S108',
    'S109', 'S33', 'S111', 'S39', 'S114', 'S115',
}


def options(game, uid: str, context: str, attacked: str | None = None) -> list[Choice]:
    card = game.cards[uid].definition
    cid = card.id
    owner = game.cards[uid].owner
    own = game.players[owner]
    other = game.players[1-owner]
    ally = list(own.board)
    enemy = list(other.board)
    if context == 'death':
        ally = [c for c in ally if c != uid]
    # Mode identifiers are internal engine commands; only Polish labels reach UI.
    public_modes={
        'hand_quick':'Nadaj Szybki atak karcie na ręce',
        'board_double':'Nadaj Podwójny atak jednostce',
    }
    def c(mode, targets):
        label=public_modes.get(mode,mode)
        return [Choice(mode, target, f"{label}  →  {game.label(target)}") for target in targets]

    # v19: elven traits are mutually exclusive on-play choices.
    if cid == 'S66':
        choices=[Choice('self_quick',uid,'Szybki atak: Mag otrzymuje cechę teraz')]
        choices += c('hand_quick',[x for x in own.hand if x!=uid])
        return choices
    if cid == 'S67':
        return c('board_double',[x for x in ally if x in game.units])
    # v18/v19: when no allied board recipient survives a death, fall back.
    if cid in ('S20','S82') and not ally:
        return [Choice('auto',f'hero:{owner}','Bohater otrzymuje ochronę')]
    if cid == 'S91' and not ally:
        return [Choice('auto',None,'Losowa karta w ręce otrzymuje bonus')]
    if cid in SELF_OR_AUTOMATIC:
        return [Choice('auto', attacked, 'Aktywuj')]  # may resolve without a modal
    if cid in ('S01','S58','S59','S83','S84','S32'):
        valid = enemy
        if cid == 'S32':
            valid = [x for x in enemy if not any(e.kind == 'poison' and e.source == uid for e in game.units[x].effects)]
        return c('Cel wrogi', valid)
    if cid in ('S02',):
        return c('Leczenie', ally+[f'hero:{owner}'])
    if cid in ('S03','S05','S60','S61','S64','S25','S26','S31','S94','S96','S97','S99'):
        return c('Cel sojuszniczy', ally)
    if cid in ('S04','S08','S23','S81','S28','S93'):
        return c('Wzmocnij', ally) + c('Osłab', enemy)
    if cid == 'S07':
        return c('Oczyść własną',ally)+c('Oczyść wrogą',enemy)
    if cid in ('S82','S20','S85','S86','S87','S88','S91'):
        return c('Pozostała jednostka',ally)
    if cid in ('S68','S69'):
        arr = [Choice('Wzmocnij siebie',uid,'Wzmocnij siebie')]
        if attacked in game.units: arr += [Choice('Osłab cel',attacked,'Osłab atakowany cel')]
        return arr
    if cid == 'S78':
        return c('Nadaj szybki atak', [x for x in ally if x!=uid and game.units[x].played_turn==own.turn_count])
    if cid == 'S74':
        return [Choice('auto',attacked,'Rozprosz efekty celu')]
    if cid == 'S101':
        return c('Szybki atak w kolejnej turze',own.hand)
    if cid == 'S102':
        return c('Podwójny atak na następną turę',ally)
    if cid in ('S34','S35'):
        return [Choice('ally', None, 'Aura wzmacniająca sojuszników'), Choice('enemy',None,'Aura osłabiająca wrogów')]
    # Every listed ability must be accounted for. Unknown ID is an implementation error.
    raise ValueError(f'Brak definicji wyborów dla {cid} ({context})')
