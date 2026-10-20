"""Verified, presentation-only descriptions for v23 auction cards (0.9.48).

CardDefinition.effect MUST remain byte-identical for historical savegames and
signed audit replays. Exact canonical variant matching is mandatory.
"""
from __future__ import annotations

from game.core.auction_catalog import V22_CARDS, V4_CARDS, live_variant, v23_variant

RARITIES=('podstawowa','rzadka','legendarna')

_V23_DISPLAY={
    ("A014","podstawowa"):"Dopóki Kapłan pozostaje na planszy i jego zdolność działa, przeciwnik nie może leczyć swojego bohatera ani własnych jednostek. Próby leczenia nie przywracają PŻ.",
    ("A014","rzadka"):"Dopóki Kapłan pozostaje na planszy i jego zdolność działa, każda nominalna próba leczenia wrogiego bohatera lub wrogiej jednostki zamienia połowę wartości (zaokrągloną w górę) w zwykłe obrażenia tego samego celu; reszta wartości może leczyć. Efekt działa także przy pełnych PŻ celu. Tarcza i pancerz chronią normalnie.",
    ("A014","legendarna"):"Dopóki Kapłan pozostaje na planszy i jego zdolność działa, całe nominalne leczenie wrogiego bohatera lub wrogiej jednostki zamienia się w zwykłe obrażenia tego samego celu, także przy pełnych PŻ. Tarcza i pancerz chronią normalnie.",
    ("A015","podstawowa"):"Dopóki Wieszczka pozostaje na planszy i jej zdolność działa, anuluje pierwszą aktywację wrogiej zdolności „Przy wystawieniu”, której faktycznie wybrany efekt jest skierowany przeciwko Twojej stronie. Sojuszniczych zdolności nie blokuje.",
    ("A015","rzadka"):"Dopóki Wieszczka pozostaje na planszy i jej zdolność działa, zachowuje anulowanie pierwszej ofensywnej zdolności „Przy wystawieniu”, a dodatkowo blokuje zdolności „Przy śmierci” wyłącznie przeciwnika. Własne zdolności działają normalnie.",
    ("A015","legendarna"):"Dopóki Wieszczka pozostaje na planszy i jej zdolność działa, blokuje zdolności przeciwnika „Przy wystawieniu”, „Przy śmierci” i „Na koniec tury”. Nie blokuje zdolności własnych jednostek. Nie obejmuje zwykłych ataków ani pasywnych zdolności innych typów.",
    ("A018","legendarna"):"Przy wystawieniu, jeżeli kolejna aukcja jest jeszcze możliwa, automatycznie ją wygrywasz, płacisz 0 monet i wybierasz kartę jako pierwszy. Jeśli przyszła aukcja nie może już wystąpić, Licytator zamiast tego otrzymuje jednorazowo trwałe +5 ATK, +5 MAX PŻ i +5 bieżących PŻ (nie powyżej MAX PŻ).",
}

_V23_PREVIEW={
    ("A014","podstawowa"):"Pasywna: blokuje leczenie wroga.",
    ("A014","rzadka"):"Pasywna: połowa nominalnego leczenia wroga → obrażenia (w górę).",
    ("A014","legendarna"):"Pasywna: całe nominalne leczenie wroga → obrażenia.",
    ("A015","podstawowa"):"Pasywna: anuluje pierwszy ofensywny efekt wroga Przy wystawieniu.",
    ("A015","rzadka"):"Pasywna: pierwszy ofensywny Przy wystawieniu + wrogie Przy śmierci.",
    ("A015","legendarna"):"Pasywna: blokuje Przy wystawieniu/Przy śmierci/Koniec tury TYLKO wroga.",
    ("A018","legendarna"):"Przy wystawieniu: darmowa wygrana następnej aukcji albo trwałe +5/+5, jeśli aukcji nie będzie.",
}


def identify_auction_variant(definition):
    """Return (rarity, catalog_mode, kind) or None, with strict effect matching."""
    aid=definition.id
    if not aid.startswith('A0') or definition.effect.startswith('NIEAKTYWNA'):
        return None
    for mode,catalog in (('v22',V22_CARDS),('v4',V4_CARDS)):
        if aid not in catalog:
            continue
        for rarity in RARITIES:
            if definition.effect==live_variant(mode,aid,rarity):
                return rarity,mode,'canonical'
            if mode=='v22' and definition.effect==v23_variant(mode,aid,rarity,'v23'):
                return rarity,mode,'v23'
    return None


def display_auction_copy(definition):
    """Never modify the canonical stored effect; only return rendered copy."""
    hit=identify_auction_variant(definition)
    if hit is not None:
        rarity,mode,kind=hit
        if mode=='v22' and kind=='v23':
            return _V23_DISPLAY.get((definition.id,rarity),definition.effect)
    return definition.effect


def preview_auction_copy(archetype,rarity,ruleset,fallback):
    """Short UI copy for a known v23 variant, with safe legacy fallback."""
    if ruleset=='v23':
        return _V23_PREVIEW.get((archetype,rarity),fallback)
    return fallback


def full_preview_auction_copy(archetype,rarity,ruleset,fallback):
    """Read-only inspection without producing CardDefinitions."""
    if ruleset=='v23':
        return _V23_DISPLAY.get((archetype,rarity),fallback)
    return fallback
