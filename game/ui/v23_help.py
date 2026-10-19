"""Presentation-only clarifications for v23 base-card conditional fallbacks.

Do not mutate the immutable v19 card catalogue or existing saved definitions.
"""
from __future__ import annotations

_V23_NOTES={
    'S86':'Gdy po śmierci brak innego własnego sojusznika: +3 pancerza bohatera.',
    'S87':'Gdy po śmierci brak innego własnego sojusznika: ulecz bohatera o 4 PŻ (może zadziałać A014).',
    'S88':'Gdy po śmierci brak innego własnego sojusznika: jedna Tarcza bohatera (bez kumulacji).',
    'S32':'Gdy wszyscy wrogowie są już zatruci przez tę kartę: 2 zwykłe obrażenia wrogowi z najmniejszym PŻ.',
    'S95':'Gdy nie ma nowego legalnego celu ogłuszenia: 2 zwykłe obrażenia najsłabszemu wrogowi bez ogłuszenia.',
}


def v23_base_card_note(card_id:str,ruleset:str='v22')->str:
    return _V23_NOTES.get(card_id,'') if ruleset=='v23' else ''
