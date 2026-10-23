"""Zwięzłe, ręcznie zweryfikowane opisy 70 kart Game Master v19.

Nie jest to silnik reguł. Statystyki, poziomy i docelowa legalność pochodzą
wyłącznie z Card / Unit / Match. Szablony opisują tylko znaczenie zdolności.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from game.ui.card_infographics import first_scalable_value
from game.ui.auction_copy import identify_auction_variant, display_auction_copy


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
        "short": "Tarcza + 1 pancerza; rozwój: +1 ATK/+2 MAX PŻ",
        "full": "Tarcza i 1 trwałego pancerza dla sojusznika. Rozwój co 3 tury w ręce dodaje tej karcie +1 ATK i +2 MAX PŻ; nie zwiększa liczby Tarcz."
    },
    "S58": {
        "short": "Trucizna → wróg; suma {total}",
        "full": "Wybrany wróg: trucizna {tick} na aktywację przez {ticks} tury, łącznie {total} obrażeń."
    },
    "S59": {
        "short": "Ogłuszenie; 3 obr., przy sukcesie {s59_success} obr.",
        "full": "Spróbuj ogłuszyć wybraną wrogą jednostkę na 1 jej własną turę. Zadaj 3 obrażenia; jeżeli ogłuszenie faktycznie zadziałało, zadaj zamiast tego {s59_success} obrażeń (3 + poziom)."
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
        "short": "Czyszczenie: swój cel 1 lub {s07_heal_if_clean} PŻ; wróg do {level} obr.",
        "full": "Wybór: oczyść własną jednostkę z ujemnych efektów i ulecz ją o 1 PŻ (lub {s07_heal_if_clean}, jeśli usunięto efekt); ALBO usuń dodatnie efekty wroga i, jeśli cokolwiek usunięto, zadaj {level} obrażeń."
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
        "short": "Usuń do {s12_value} pancerza; bez pancerza: {s12_value} obr.",
        "full": "Przed standardową walką usuń do {s12_value} pancerza z celu ataku (jednostki lub bohatera). Jeśli nie ma pancerza, zamiast tego zadaj mu {s12_value} obrażeń."
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
        "short": "Ogłuszenie przy ataku; gdy skuteczne: +{s15_if_stunned} obr.",
        "full": "Przy ataku jednostki: spróbuj ogłuszyć cel na 1 jego własną turę. Tylko gdy ogłuszenie zadziała, zadaj przed walką {s15_if_stunned} dodatkowych obrażeń (1 bazowe + poziom). W przeciwnym razie brak dodatkowych obrażeń tej zdolności."
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
        "short": "Oczyszcza wroga; {s74_success}/{s74_other} obr.",
        "full": "Przed standardową walką z jednostką usuń jej tymczasowe dodatnie efekty. Jeśli cokolwiek usunięto, zadaj {s74_success} dodatkowych obrażeń; jeśli nic nie usunięto, zadaj {s74_other} dodatkowych obrażeń."
    },
    "S76": {
        "short": "Odporność na ogłuszenie: sobie",
        "full": "Przed walką zyskuje odporność na ogłuszenie do końca swojej najbliższej tury."
    },
    "S78": {
        "short": "Szybki: świeży sojusznik / karta na ręce",
        "full": "Przy ataku nadaj Szybki atak innej własnej jednostce wystawionej w tej turze. Jeśli takiej nie ma, wybierz własną kartę w ręce: otrzyma Szybki atak przy najbliższym wystawieniu."
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
        "short": "Po śmierci: ogłuszenie; 4 lub {s84_success} obr.",
        "full": "Przy śmierci spróbuj ogłuszyć wybraną wrogą jednostkę na 1 jej własną turę. Zadaj 4 obrażenia; jeżeli ogłuszenie faktycznie zadziałało, zadaj zamiast tego {s84_success} obrażeń (4 + poziom)."
    },
    "S85": {
        "short": "Po śmierci: regeneracja sojusznika / +{s85_hero} PŻ bohatera",
        "full": "Przy śmierci nałóż na inną własną jednostkę regenerację {tick} PŻ przez {ticks} jej własne tury (łącznie {total}). Jeżeli nie ma innej własnej jednostki, zamiast tego ulecz bohatera jednorazowo o {s85_hero} PŻ."
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
        "short": "Koniec tury: {v} obr. najsłabszy wróg / bohater",
        "full": "Na koniec własnej tury zadaj {v} obrażeń wrogiej jednostce o najniższym bieżącym PŻ; jeśli brak wrogich jednostek, zadaj {v} obrażeń wrogiemu bohaterowi."
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
        "short": "Oczyść; ulecz {s97_success}/{s97_other} PŻ",
        "full": "Na koniec własnej tury usuń tymczasowe ujemne efekty wybranego sojusznika. Jeśli usunięto co najmniej jeden efekt, ulecz go o {s97_success} PŻ; w przeciwnym razie o {s97_other} PŻ."
    },
    "S99": {
        "short": "Odporność na truciznę +1 pancerza; rozwój +{level} trwałego",
        "full": "Na koniec własnej tury nadaj sojusznikowi odporność na truciznę oraz 1 tymczasowego pancerza do końca jego najbliższej własnej tury. Przy pierwszej aktywacji zdolności po wystawieniu rozwój daje chronionemu celowi dodatkowo {level} trwałego pancerza."
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
        "short": "Nowy wróg naprzeciw: ogłuszenie +{s108_if_stunned} obr.",
        "full": "Gdy wroga jednostka po raz pierwszy znajdzie się naprzeciw Trębacza, spróbuj ją ogłuszyć na 1 jej własną turę. Jeśli to się uda, zadaj jej {s108_if_stunned} obrażeń (1 bazowe + poziom); jeśli nie, nie zadaj obrażeń. Ten sam wróg nie aktywuje ponownie zdolności podczas tego wystawienia."
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
        variant=identify_auction_variant(d)
        if variant is not None:
            rarity={'podstawowa':'PODSTAWOWA',
                    'rzadka':'RZADKA',
                    'legendarna':'LEGENDARNA'}[variant[0]]
            return AbilitySummary(f'AKTYWNA · {rarity}',
                                  display_auction_copy(d)+' Statystyki po zakupie '
                                  'pozostają stałe; rzadkość rośnie co 3 '
                                  'ukończone rundy od zakupu.')
        # Noncanonical or legacy text must not be falsely certified as v4.
        return AbilitySummary('OPIS AUKCYJNY — SPRAWDŹ WERSJĘ',d.effect)
    # Only the new armored starting guard has this unique signed description.
    # Old 3/5 or 2/5 archived tokens keep their original historical copy.
    if d.id=='SUM_START_GUARD':
        if '4 trwałego pancerza na start' in d.effect:
            return AbilitySummary(
                'ZABÓJSTWA: +1 ATK / +2 PŻ',
                d.effect+' Pancerz początkowy nie odnawia się po zabójstwie. '
                'Po opuszczeniu planszy nie wraca do talii.'
            )
        return AbilitySummary(
            'BEZ ZDOLNOŚCI',
            d.effect+' Jest to historyczna jednostka startowa bez zdolności specjalnych; '
            'po opuszczeniu planszy nie wraca do talii.'
        )
    # Summoned Queen soldiers are real board units but not among the 70
    # collectible basic cards. Looking them up in SPECS caused KeyError
    # 'SUM0000007' and crashed the packaged application during board render.
    if d.id.startswith('SUM'):
        has_taunt=d.family=='Prowokacja'
        short='PROWOKACJA' if has_taunt else 'BEZ ZDOLNOŚCI'
        return AbilitySummary(
            short,
            ('Jednostka przywołana z Prowokacją.' if has_taunt
             else 'Jednostka przywołana bez zdolności.')+
            ' Jest efemeryczna i nie wraca do talii ani cmentarza.'
        )
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
        's07_heal_if_clean':1+level,
        's12_value':2+level,
        's15_if_stunned':1+level,
        's59_success':3+level,
        's74_success':3+level,
        's74_other':2+level,
        's84_success':4+level,
        's85_hero':4+level,
        's97_success':2+level,
        's97_other':1+level,
        's108_if_stunned':1+level,
    }
    return AbilitySummary(spec['short'].format(**values),
                          spec['full'].format(**values))
