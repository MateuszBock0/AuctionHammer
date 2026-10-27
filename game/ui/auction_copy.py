"""Verified, presentation-only descriptions for v23 auction cards (0.9.48).

CardDefinition.effect MUST remain byte-identical for historical savegames and
signed audit replays. Exact canonical variant matching is mandatory.
"""
from __future__ import annotations

from game.core.auction_catalog import V22_CARDS, V4_CARDS, live_variant, v23_variant

RARITIES=('podstawowa','rzadka','legendarna')

_V23_DISPLAY={
    ("A014","podstawowa"):"Dopóki Kapłan pozostaje na planszy i jego zdolność działa, przeciwnik nie może leczyć swojego bohatera ani własnych jednostek. Próby leczenia nie przywracają PŻ.",
    ("A014","rzadka"):"Gdy Kapłan działa na planszy, połowa nominalnego leczenia wroga (zaokrąglona w górę) staje się zwykłymi obrażeniami celu; reszta leczy. Działa także przy pełnym PŻ; Tarcza i pancerz chronią. Na koniec własnej tury losowy sojusznik (także Kapłan) zyskuje regenerację 2 PŻ przez 2 własne tury.",
    ("A014","legendarna"):"Gdy Kapłan działa: całe nominalne leczenie wroga to zwykłe obrażenia, nawet przy pełnym PŻ; Tarcza i pancerz chronią. Na koniec tury każdy sojusznik (także Kapłan) zyskuje regenerację 2 PŻ na 2 własne tury. Porcje się kumulują.",
    ("A015","podstawowa"):"Dopóki Wieszczka działa na planszy, anuluje pierwszą wrogą zdolność „Przy wystawieniu”, jeśli wybrany efekt wymierzono w Twoją stronę. Nie blokuje zdolności sojuszników.",
    ("A015","rzadka"):"Dopóki Wieszczka działa na planszy, anuluje pierwszą ofensywną wrogą zdolność „Przy wystawieniu” i blokuje wszystkie wrogie zdolności „Przy śmierci”. Własne zdolności działają.",
    ("A015","legendarna"):"Dopóki Wieszczka działa na planszy, blokuje tylko wrogie zdolności „Przy wystawieniu”, „Przy śmierci” i „Na koniec tury”. Nie blokuje własnych zdolności, zwykłych ataków ani pozostałych pasywnych efektów.",
    ("A018","legendarna"):"Przy wystawieniu: jeśli kolejna aukcja jest możliwa, wygrywasz ją za 0 monet i wybierasz kartę jako pierwszy. Jeśli kolejna aukcja nie może się odbyć, zamiast tego zyskaj trwale +5 ATK, +5 MAX PŻ i +5 bieżących PŻ (nie ponad MAX PŻ).",
    ("A003","rzadka"):"Przy śmierci: wybierz efekt podstawowy ALBO przywróć inną własną kartę podstawową z cmentarza na prawe wolne pole z 1 PŻ (bez „Przy wystawieniu”); jeśli brak pola, na rękę. Gdy w cmentarzu brak takich kart, przywołaj Szkieleta bez zdolności: min. 7/7 lub wyższe statystyki najlepszej karty w ręce.",
    ("A003","legendarna"):"Przy śmierci: wybierz efekt podstawowy, rzadki ALBO przywróć do 2 różnych własnych kart podstawowych z cmentarza: pierwszą na prawe wolne pole z pełnym PŻ, drugą na rękę (przy braku pola obie na rękę). Bez „Przy wystawieniu”. Gdy brak takich kart, przywołaj Szkieleta bez zdolności: min. 8/8 lub wyższe statystyki najlepszej karty w ręce.",
    ("A016","rzadka"):"Najpierw dobierz 1 z maks. 3 wierzchnich kart własnej talii. Potem zagraj 1 z maks. 3 wierzchnich własnej talii lub wierzchnią kartę wroga. Przy pełnej planszy zamiast dodatkowego zagrania Kartograf zyskuje Tarczę i połowę ATK/MAX PŻ wskazanej innej jednostki; dobraną kartę zachowujesz.",
    ("A016","legendarna"):"Wybierz spośród maks. 3 wierzchnich kart własnej talii i maks. 3 kart talii wroga. Kartę wroga przejmij; wybraną od razu zagraj. Przy pełnej planszy zamiast dodatkowego zagrania Kartograf zyskuje Tarczę i pełne ATK/MAX PŻ wskazanej innej jednostki.",
    ("A009","legendarna"):"Zamień całe ręce obu graczy wraz z własnością kart. Przeciwnik odrzuca 2 karty z nowej ręki (lub wszystkie, jeśli ma mniej). Wszystkie karty w Twojej nowej ręce zyskują trwale +3 ATK/+3 MAX PŻ.",
    ("A009","rzadka"):"Podejrzyj rękę wroga; wymień swoją wskazaną kartę na wybraną kartę wroga. Twoje karty na ręce zyskują trwale +2 ATK/+2 MAX PŻ. Jeśli wymiana niemożliwa, wzmocnij obecną rękę.",
    ("A012","rzadka"):"Przy wystawieniu wybierz: ustaw swoje bieżące PŻ na PŻ wrogiego bohatera ALBO jego PŻ na swoje (drugi bohater bez zmian). Następnie ulecz swojego bohatera o 10 PŻ, nie ponad MAX PŻ.",
    ("A004","legendarna"):"Skopiuj dowolną inną jednostkę (także wrogą) z jej bieżącymi bonusami i efektami. Efemeryczna kopia z Tarczą trafia od razu na Twoją planszę. Jeśli brak pola, Regent zamiast kopii zyskuje Tarczę i pełne ATK/MAX PŻ wskazanej jednostki.",
    ("A002","rzadka"):"Gdy Generał działa na planszy, wskazany sojusznik ma Podwójny atak i podwójne obrażenia swoich ataków. Przy wystawieniu Generał zyskuje Tarczę i 2 trwałego pancerza.",
    ("A002","legendarna"):"Gdy Generał działa na planszy, każda Twoja nowo zagrana jednostka zyskuje Podwójny atak i podwójne obrażenia swoich ataków. Przy wystawieniu Generał otrzymuje Tarczę i 4 trwałego pancerza.",

}

_V23_PREVIEW={
    ("A014","podstawowa"):"Pasywna: blokuje leczenie wroga.",
    ("A014","rzadka"):"Pasywna: połowa leczenia wroga → obrażenia; co turę regeneruje sojusznika.",
    ("A014","legendarna"):"Pasywna: leczenie wroga → obrażenia; co turę regeneruje wszystkich sojuszników.",
    ("A015","podstawowa"):"Anuluje pierwszą wrogą ofensywną zdolność „Przy wystawieniu”.",
    ("A015","rzadka"):"Pierwszy wrogi ofensywny „Przy wystawieniu” + wszystkie wrogie „Przy śmierci” zablokowane.",
    ("A015","legendarna"):"Blokuje wrogie „Przy wystawieniu”, „Przy śmierci” i „Na koniec tury”.",
    ("A018","legendarna"):"Przy wystawieniu: darmowa wygrana następnej aukcji albo trwałe +5/+5, jeśli aukcji nie będzie.",
    ("A003","rzadka"):"Po śmierci: karta z cmentarza na rękę lub na planszę z 1 PŻ; gdy cmentarz pusty — Szkielet.",
    ("A003","legendarna"):"Po śmierci: do 2 kart z cmentarza (plansza + ręka); gdy pusty — Szkielet.",
    ("A016","rzadka"):"Dobierz kartę, potem zagraj kartę z talii (także wroga); pełna plansza → Tarcza + statystyki.",
    ("A016","legendarna"):"Przejmij lub wybierz kartę z talii i zagraj; pełna plansza → Tarcza + statystyki.",
    ("A009","legendarna"):"Zamień całe ręce; wróg odrzuca 2 karty, Twoja nowa ręka zyskuje +3/+3.",
    ("A009","rzadka"):"Podejrzyj i wymień wybraną kartę z ręki wroga; Twoja ręka +2/+2.",
    ("A012","rzadka"):"Wybierz, który bohater kopiuje bieżące PŻ drugiego, potem ulecz siebie o 10 PŻ.",
    ("A004","legendarna"):"Skopiuj dowolną jednostkę z bonusami i Tarczą; przy pełnej planszy wzmocnij Regenta.",
    ("A002","rzadka"):"Wybrany sojusznik: Podwójny atak i ×2 obrażeń; Generał: Tarcza +2 pancerza.",
    ("A002","legendarna"):"Nowi sojusznicy: Podwójny atak i ×2 obrażeń; Generał: Tarcza +4 pancerza.",

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
