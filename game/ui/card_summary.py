"""Zwięzłe, ręcznie zweryfikowane opisy 70 kart Game Master v19.

Nie jest to silnik reguł. Statystyki, poziomy i docelowa legalność pochodzą
wyłącznie z Card / Unit / Match. Szablony opisują tylko znaczenie zdolności.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from game.ui.card_infographics import first_scalable_value


# Klucze są ID z data/cards_base_70.json, a nie kolejnymi pozycjami w banku.
# Każdy wpis: krótka linia karty i pełniejsze wyjaśnienie celu/warunku.
SPECS = {
    "S01": {
        "short": "Cel: wybrany wróg",
        "full": "Zadaje {v} obrażeń wybranej wrogiej jednostce."
    },
    "S02": {
        "short": "Leczy {v}: sojusznik / bohater",
        "full": "Leczy o {v} PŻ wybranego sojusznika ALBO własnego bohatera."
    },
    "S04": {
        "short": "Wybór: +{v} ATAK swój / -{v} wróg",
        "full": "Wybór: sojusznik +{v} ATAK albo wróg -{v} ATAK; do opuszczenia planszy."
    },
    "S08": {
        "short": "Wybór: +{v} PŻ swój / -{v} wróg",
        "full": "Wybór: sojusznik +{v} MAX PŻ i bieżącego PŻ albo wróg -{v} MAX PŻ; do opuszczenia."
    },
    "S03": {
        "short": "+{v} pancerza → sojusznik",
        "full": "Wybrany sojusznik dostaje {v} trwałego pancerza."
    },
    "S05": {
        "short": "Tarcza + pancerz → sojusznik",
        "full": "Daje sojusznikowi tarczę i 1 trwałego pancerza; rozwój dodaje MAX PŻ, nie tarcze."
    },
    "S58": {
        "short": "Trucizna → wróg; suma {total}",
        "full": "Wybrany wróg: trucizna {tick} na aktywację przez {ticks} tury, łącznie {total} obrażeń."
    },
    "S59": {
        "short": "Ogłusza wroga + {v} obr.",
        "full": "Wybranego wroga ogłusza na 1 jego turę i zadaje {v} obrażeń."
    },
    "S60": {
        "short": "Regen. → sojusznik; suma {total}",
        "full": "Wybrany sojusznik: regeneracja {tick} PŻ na aktywację przez {ticks} tury, łącznie {total}."
    },
    "S61": {
        "short": "Prowokacja → sojusznik",
        "full": "Wybranemu sojusznikowi nadaje Prowokację do opuszczenia planszy."
    },
    "S07": {
        "short": "Oczyszcza: swój / wróg",
        "full": "Wybór: usuwa negatywne efekty z własnej jednostki (leczy o {v} PŻ) ALBO pozytywne z wroga."
    },
    "S64": {
        "short": "Sojusznik: odp. na truciznę",
        "full": "Wybrany sojusznik staje się odporny na truciznę do opuszczenia planszy."
    },
    "S66": {
        "short": "Szybki: sam / inny na ręce",
        "full": "Wybór: Szybki atak dla siebie TERAZ albo dla innej własnej karty w ręce przy jej wystawieniu; nie obie opcje."
    },
    "S67": {
        "short": "Podwójny: sam / inny sojusznik",
        "full": "Wybór: Podwójny atak dla siebie lub innego sojusznika na planszy; maks. 2 ataki, bez Szybkiego nie od razu."
    },
    "S09": {
        "short": "Cel ataku",
        "full": "Przed standardową walką zadaje {v} dodatkowych obrażeń celowi ataku."
    },
    "S10": {
        "short": "Leczy siebie {v} przed walką",
        "full": "Przed standardową walką leczy siebie o {v} PŻ."
    },
    "S68": {
        "short": "Przed walką: +{v} ATAK / -{v} wróg",
        "full": "Wybór: sobie +{v} ATAK albo atakowanemu wrogowi -{v} ATAK; do końca bieżącej tury."
    },
    "S69": {
        "short": "Przed walką: +{v} PŻ / -{v} wróg",
        "full": "Wybór: sobie +{v} MAX/bieżącego PŻ albo wrogowi -{v} MAX PŻ do jego najbliższej tury."
    },
    "S12": {
        "short": "Usuwa do {v} pancerza celu",
        "full": "Przed walką odbiera celowi ataku maks. {v} pancerza."
    },
    "S70": {
        "short": "Tarcza dla siebie przed walką",
        "full": "Przed walką otrzymuje tarczę tylko wtedy, gdy jej nie ma."
    },
    "S11": {
        "short": "Trucizna → cel; suma {total}",
        "full": "Cel ataku: trucizna {tick} na aktywację przez {ticks} tury, łącznie {total} obrażeń."
    },
    "S15": {
        "short": "Ogłusza atakowaną jednostkę",
        "full": "Przed walką ogłusza atakowaną jednostkę na 1 jej turę; bonus obrażeń za poziom: {level}."
    },
    "S71": {
        "short": "Regen. siebie; suma {total}",
        "full": "Przed walką nakłada sobie regenerację {tick} PŻ przez {ticks} własne tury (łącznie {total})."
    },
    "S72": {
        "short": "Prowokacja sobie na 1 turę",
        "full": "Przed walką zyskuje Prowokację do końca swojej najbliższej własnej tury."
    },
    "S74": {
        "short": "Usuwa premie atakowanego wroga",
        "full": "Przed walką z jednostką usuwa jej wszystkie tymczasowe pozytywne efekty."
    },
    "S76": {
        "short": "Odporność na ogłuszenie: sobie",
        "full": "Przed walką zyskuje odporność na ogłuszenie do końca swojej najbliższej tury."
    },
    "S78": {
        "short": "Szybki dla innego nowego sojusz.",
        "full": "Przed walką pozwala innej własnej jednostce wystawionej w tej turze atakować natychmiast."
    },
    "S79": {
        "short": "2. atak dopiero po 1. legalnym",
        "full": "Po pierwszym legalnym ataku w turze zyskuje drugi, jeśli zdolność działa i nie jest ogłuszona."
    },
    "S21": {
        "short": "Cel: wrogi bohater",
        "full": "Po śmierci zadaje wrogiemu bohaterowi {v} obrażeń."
    },
    "S17": {
        "short": "Leczy bohatera o {v}",
        "full": "Po śmierci leczy własnego bohatera o {v} PŻ."
    },
    "S23": {
        "short": "Wybór: +{v} ATAK swój / -{v} wróg",
        "full": "Po śmierci wybór: pozostały sojusznik +{v} ATAK albo wróg -{v} ATAK; do opuszczenia."
    },
    "S81": {
        "short": "Wybór: +{v} PŻ swój / -{v} wróg",
        "full": "Po śmierci wybór: pozostały sojusznik +{v} MAX/bieżącego PŻ albo wróg -{v} MAX PŻ."
    },
    "S82": {
        "short": "Pancerz → sojusznik, inaczej boh.",
        "full": "Po śmierci {v} trwałego pancerza dla pozostałego sojusznika, a gdy brak — dla własnego bohatera."
    },
    "S20": {
        "short": "Tarcza + pancerz, inaczej boh.",
        "full": "Po śmierci tarcza i 2 pancerza dla pozostałego sojusznika; gdy brak — dla własnego bohatera."
    },
    "S83": {
        "short": "Trucizna → wróg; suma {total}",
        "full": "Po śmierci wybrany wróg dostaje truciznę {tick} na aktywację przez {ticks} tury (łącznie {total})."
    },
    "S84": {
        "short": "Ogłusza wroga + {v} obr.",
        "full": "Po śmierci ogłusza wroga na 1 jego turę i zadaje {v} obrażeń."
    },
    "S85": {
        "short": "Regen. → sojusznik; suma {total}",
        "full": "Po śmierci pozostały sojusznik otrzymuje regenerację {tick} przez {ticks} tury (łącznie {total})."
    },
    "S86": {
        "short": "Prowokacja → pozostały sojusz.",
        "full": "Po śmierci daje Prowokację pozostałemu wybranemu sojusznikowi do opuszczenia."
    },
    "S87": {
        "short": "Oczyszcza sojusznika + pancerz",
        "full": "Po śmierci czyści negatywne efekty pozostałego sojusznika i daje 2 trwałego pancerza."
    },
    "S88": {
        "short": "Sojusznik: odp. truc. + ogł.",
        "full": "Po śmierci pozostały sojusznik zyskuje odporność na truciznę i ogłuszenie do opuszczenia."
    },
    "S90": {
        "short": "Szybki → do 2 losowych w ręce",
        "full": "Po śmierci nadaje Szybki atak maks. 2 różnym losowym kartom w ręce; przy najbliższym wystawieniu."
    },
    "S91": {
        "short": "Podwójny: plansza, potem ręka",
        "full": "Po śmierci daje Podwójny atak pozostałemu sojusznikowi; gdy brak — losowej karcie w ręce na pierwszą legalną turę."
    },
    "S27": {
        "short": "{v} obr. → wróg z min. PŻ",
        "full": "Na koniec tury rani za {v} wroga o najniższym aktualnym PŻ."
    },
    "S25": {
        "short": "Leczy {v} → wybrany sojusz.",
        "full": "Na koniec tury leczy wybraną własną jednostkę o {v} PŻ."
    },
    "S28": {
        "short": "Wybór: +{v} ATAK swój / -{v} wróg",
        "full": "Na koniec tury wybór: sojusznik +{v} ATAK albo wróg -{v} ATAK do końca jego najbliższej tury."
    },
    "S93": {
        "short": "Wybór: +{v} PŻ swój / -{v} wróg",
        "full": "Na koniec tury wybór: sojusznik +{v} MAX/bieżącego PŻ albo wróg -{v} MAX PŻ do jego tury."
    },
    "S26": {
        "short": "Pancerz {v} → sojusznik, czasowy",
        "full": "Na koniec tury daje sojusznikowi {v} czasowego pancerza do końca jego najbliższej tury."
    },
    "S94": {
        "short": "Tarcza → sojusznik bez tarczy",
        "full": "Na koniec tury daje tarczę sojusznikowi, jeśli ten jeszcze jej nie ma."
    },
    "S32": {
        "short": "Trucizna → wróg; suma {total}",
        "full": "Na koniec tury trucizna {tick} × {ticks} tur (łącznie {total}); najwyżej jedna porcja od tego źródła."
    },
    "S95": {
        "short": "Ogłusza wr. o najmniejszym ATAK",
        "full": "Na koniec tury ogłusza na 1 turę wroga o najniższym ATAK; nie dwa razy z rzędu tego samego."
    },
    "S31": {
        "short": "Regen. → sojusznik; suma {total}",
        "full": "Na koniec tury nakłada sojusznikowi regenerację {tick} przez {ticks} tury (łącznie {total})."
    },
    "S96": {
        "short": "Prowokacja → sojusznik, czasowa",
        "full": "Na koniec tury daje sojusznikowi Prowokację do końca jego najbliższej własnej tury."
    },
    "S97": {
        "short": "Oczyszcza negatywy sojusznika",
        "full": "Na koniec tury usuwa wszystkie tymczasowe negatywne efekty wybranego sojusznika."
    },
    "S99": {
        "short": "Sojusznik: odp. na truciznę",
        "full": "Na koniec tury daje sojusznikowi odporność na truciznę do końca jego najbliższej tury."
    },
    "S101": {
        "short": "Szybki → karta w ręce na nast. turę",
        "full": "Na koniec tury daje Szybki atak wybranej karcie w ręce tylko na najbliższą własną turę."
    },
    "S102": {
        "short": "Podwójny → sojusznik na 1 turę",
        "full": "Na koniec tury daje sojusznikowi Podwójny atak wyłącznie na jego najbliższą turę."
    },
    "S103": {
        "short": "Wróg atakujący tę jednostkę",
        "full": "Pasywnie zadaje {v} obrażeń każdemu wrogowi atakującemu tę jednostkę przed walką."
    },
    "S104": {
        "short": "Leczenie sojuszników +{v}",
        "full": "Pasywnie zwiększa o {v} PŻ leczenie własnych jednostek ze zdolności."
    },
    "S34": {
        "short": "Aura: +{v} ATAK swój / -{v} wróg",
        "full": "Wybór stałej aury: najbliższy inny sojusznik +{v} ATAK albo wróg naprzeciw -{v} ATAK."
    },
    "S35": {
        "short": "Aura: +{v} PŻ swoi / -{v} wrogowie",
        "full": "Wybór stałej aury: inni sojusznicy +{v} MAX/bieżącego PŻ albo wszyscy wrogowie -{v} MAX PŻ."
    },
    "S105": {
        "short": "Jednorazowo +{v} pancerza z aury",
        "full": "Aura daje każdemu innemu sojusznikowi jednorazowo {v} czasowego pancerza; nie odnawia zużytych."
    },
    "S106": {
        "short": "Tarcza wrodzona, bez odnowy",
        "full": "Pasywnie ma tarczę, której nie odzyskuje po zużyciu w tym wystawieniu."
    },
    "S107": {
        "short": "Trucizna za cios; suma {total}",
        "full": "Wróg raniący tę jednostkę standardowo otrzymuje truciznę {tick} przez {ticks} tury (łącznie {total})."
    },
    "S108": {
        "short": "Ogłusza pierwszy raz naprzeciw",
        "full": "Pierwsze ustawienie wroga naprzeciw ogłusza go na 1 turę; tego samego nie drugi raz; bonus obr.: {level}."
    },
    "S109": {
        "short": "Samoregeneracja {v} co turę",
        "full": "Pasywnie leczy siebie o {v} PŻ na koniec KAŻDEJ własnej tury, gdy zdolność działa."
    },
    "S33": {
        "short": "Wrodzona Prowokacja",
        "full": "Pasywna Prowokacja: wrogowie muszą wybierać cele z Prowokacją."
    },
    "S111": {
        "short": "Samoczyszczenie; leczy {level} po efekcie",
        "full": "Natychmiast usuwa nowe negatywne efekty czasowe; po skutecznym usunięciu leczy o {level} PŻ."
    },
    "S39": {
        "short": "Odporność na truciznę",
        "full": "Pasywnie odporny na truciznę; po wystawieniu zyskuje jednorazowo +{level} pancerza z rozwoju."
    },
    "S114": {
        "short": "Szybki atak tylko dla siebie",
        "full": "Wrodzony Szybki atak wyłącznie dla siebie, o ile nie jest ogłuszony lub wyciszony."
    },
    "S115": {
        "short": "Dwa ataki tylko dla siebie",
        "full": "Wrodzony Podwójny atak tylko dla siebie: maks. dwa razy we własnej turze; bez Szybkiego nie w turze wystawienia."
    }
}


@dataclass(frozen=True)
class AbilitySummary:
    short: str
    full: str


def ability_summary(card, unit=None) -> AbilitySummary:
    """Zwróć wartości aktualne, nie bazowe statyczne liczby na grafice."""
    d = card.definition
    if d.id.startswith('A0'):
        # v3 historical auction cards are inert, but ALL 36 v4 variants
        # execute. The card definition is authoritative and evolves in place.
        if d.effect.startswith('NIEAKTYWNA'):
            return AbilitySummary('ZDOLNOŚĆ NIEAKTYWNA',
                                  d.effect+' Brak skalowania na ręce.')
        from game.core.auction_catalog import V4_CARDS
        variants=V4_CARDS.get(d.id,{}).get('variants',{})
        label={'basic':'PODSTAWOWA','rare':'RZADKA',
               'legendary':'LEGENDARNA'}
        rarity=next((label[tier] for tier,text in variants.items()
                     if text==d.effect),None)
        if rarity is not None:
            return AbilitySummary(f'AKTYWNA · {rarity}',
                                  d.effect+' Statystyki po zakupie pozostają stałe; '
                                  'rzadkość rośnie co 3 ukończone rundy od zakupu.')
        # Noncanonical or legacy text must not be falsely certified as v4.
        return AbilitySummary('OPIS AUKCYJNY — SPRAWDŹ WERSJĘ',d.effect)
    if d.id.startswith('AUC'):
        return AbilitySummary('Prowokacja + Tarcza',
                              'Karta testowej aukcji: Prowokacja i 1 Tarcza po wystawieniu. '
                              'Nie skaluje się w ręce. Poziom i rzadkość aukcji '
                              'zapisane są oddzielnie.')
    spec = SPECS[d.id]
    level = unit.ability_level if unit is not None else card.ability_level
    base = first_scalable_value(d)
    if d.id == 'S07':
        base = 1  # stała wartość leczenia własnego celu, +1 za próg
    if base is None:
        base = 0
    if d.family in ('Trucizna', 'Regeneracja') and d.id != 'S109':
        tick = base
        match = re.search(r'przez\s+(\d+)\s+', d.effect)
        if not match:
            raise ValueError(f'Brak czasu efektu dla {d.id}')
        ticks = int(match.group(1))
        total = tick * ticks + level  # bonus jednorazowy, nie wzrost każdej aktywacji
        current = tick
    else:
        tick = base
        ticks = 0
        total = 0
        current = base + level
    values = {
        'v': current,
        'tick': tick,
        'ticks': ticks,
        'total': total,
        'level': level,
    }
    return AbilitySummary(spec['short'].format(**values),
                          spec['full'].format(**values))
