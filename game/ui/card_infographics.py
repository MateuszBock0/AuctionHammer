"""Pure, data-driven card infographics. No game-state mutation or Pygame dependency.

The effect text comes from the actual Game Master v19 catalogue; the semantic
rule identifies *which* number is improved, rather than bolding every digit
(in particular durations and number-of-attacks are deliberately not upgraded).
"""
from __future__ import annotations
from dataclasses import dataclass
import re

TRIGGER_SHORT = {
    'Przy wystawieniu': 'PRZY ZAGRANIU',
    'Przy ataku': 'PRZY ATAKU',
    'Przy śmierci': 'PRZY ŚMIERCI',
    'Na koniec tury': 'KONIEC TURY',
    'Pasywna': 'PASYWNA',
}
FAMILY_SYMBOLS = {
    'Obrażenia':'OBR','Leczenie':'LECZ','ATK ±':'ATAK','MAX HP ±':'PŻ',
    'Pancerz':'PANC','Tarcza':'TARCZA','Trucizna':'TRUC','Ogłuszenie':'OGŁ',
    'Regeneracja':'REGEN','Prowokacja':'PROW','Oczyszczanie':'OCZ',
    'Odporność':'ODP','Szybki atak':'SZYBKI','Podwójny atak':'2 ATAKI',
}
FAMILY_COLORS = {
    'Obrażenia':(239,119,112),'Leczenie':(103,213,168),'ATK ±':(118,214,133),
    'MAX HP ±':(143,216,163),'Pancerz':(168,191,213),'Tarcza':(94,191,244),
    'Trucizna':(176,220,88),'Ogłuszenie':(193,144,244),'Regeneracja':(84,218,160),
    'Prowokacja':(243,174,70),'Oczyszczanie':(193,223,244),'Odporność':(114,164,255),
    'Szybki atak':(79,223,223),'Podwójny atak':(255,155,99),
}
UPGRADES = {
    'Obrażenia':'+1 OBR / 3T','Leczenie':'+1 LECZ / 3T',
    'ATK ±':'±1 ATAK / 3T','MAX HP ±':'±1 PŻ / 3T','Pancerz':'+1 PANC / 3T',
    'Tarcza':'+3 PŻ / 3T','Trucizna':'+1 ŁĄCZ / 3T',
    'Ogłuszenie':'+1 OBR / 3T','Regeneracja':'+1 ŁĄCZ / 3T',
    'Prowokacja':'+3 PŻ / 3T','Oczyszczanie':'+1 ZA OCZ / 3T',
    'Odporność':'1× +1 PANC / 3T','Szybki atak':'+2 ATAK +1 PŻ / 3T',
    'Podwójny atak':'+2 ATAK / 3T',
}


def highlighted_numeric_ranges(definition) -> tuple[tuple[int,int],...]:
    """Span(s) of the *scaling* numerical quantities in the printed effect.

    For a stun, '1 turn' is not bolded: the improved number is damage.
    Poison/regen bold their per-tick baseline but the separate upgrade badge
    explicitly says TOTAL, avoiding the claim that ticks become stronger.
    """
    text=definition.effect
    family=definition.family
    if family in {'Tarcza','Prowokacja','Oczyszczanie','Odporność','Szybki atak','Podwójny atak'}:
        return ()
    nums=list(re.finditer(r'\d+',text))
    if not nums:return ()
    if family=='Ogłuszenie':
        # Find the damage quantity, not the number of turns.
        found=list(re.finditer(r'(\d+)\s+obraż',text,re.IGNORECASE))
        return tuple(x.span(1) for x in found[-1:])  # zero base damage is implied
    if family in {'ATK ±','MAX HP ±'}:
        # The positive and negative branches have independently scaling sizes.
        return tuple(x.span() for x in nums[:2])
    return (nums[0].span(),)


def first_scalable_value(definition) -> int | None:
    spans=highlighted_numeric_ranges(definition)
    return int(definition.effect[spans[0][0]:spans[0][1]]) if spans else None


@dataclass(frozen=True)
class CardCue:
    trigger: str
    family: str
    color: tuple[int,int,int]
    base: str
    upgrade: str
    effect_value: int | None
    ability_level: int
    growth: str
    next_threshold: str


def card_cue(card, unit=None) -> CardCue:
    d=card.definition
    family=d.family
    level=unit.ability_level if unit is not None else card.ability_level
    base=first_scalable_value(d)
    if family=='Ogłuszenie' and base is None:base=0
    value=base
    if base is not None:
        if family=='Regeneracja' and d.id=='S109':
            value=base+level  # v19: +1 each own end-of-turn heal
        elif family not in {'Trucizna','Regeneracja'}:
            value=base+level
    if family=='Trucizna':
        cue=f'{base} / TURA' if base is not None else 'TRUCIZNA'
    elif family=='Regeneracja' and d.id!='S109':
        cue=f'{base} / TURA' if base is not None else 'REGENERACJA'
    elif value is not None:
        suffix={'Obrażenia':' OBR','Leczenie':' LECZ','Pancerz':' PANC',
                'ATK ±':' ATAK','MAX HP ±':' PŻ','Ogłuszenie':' OBR',
                'Regeneracja':' LECZ'}.get(family,'')
        cue=f'{value}{suffix}'
    else:
        cue=FAMILY_SYMBOLS[family]
    upgrade='STAŁE PARAMETRY' if d.id.startswith('AUC') else UPGRADES[family]
    if family=='Regeneracja' and d.id=='S109':upgrade='+1 CO TURĘ / 3T'
    if unit is not None:
        threshold='POZIOM UTRWALONY'
    else:
        threshold=f'ZA {3-card.hand_turns%3} TUR' if card.hand_turns%3 else 'ZA 3 TURY'
    return CardCue(
        trigger=TRIGGER_SHORT[d.trigger],family=FAMILY_SYMBOLS[family],
        color=FAMILY_COLORS[family],base=cue,upgrade=upgrade,
        effect_value=value,ability_level=level,
        growth=('Bez skalowania na ręce' if d.id.startswith('AUC') else\n                f'+{d.growth_atk} ATAK  +{d.growth_hp} PŻ / wł. turę na ręce'),
        next_threshold=threshold,
    )
