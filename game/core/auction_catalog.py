"""Auction catalog v3: 12 draft archetypes, three rarity rule texts each.

User-approved for IMPLEMENTATION as a prototype; source is the uploaded
KATALOG_AUKCYJNY_12_v3(2).md. Provisional interpretations for A002/A012,
copy recursion (A004), and persistent A010 scaling are documented explicitly.
"""
from __future__ import annotations
from dataclasses import dataclass

RARITIES=("podstawowa","rzadka","legendarna")
TRIGGER={"play":"Przy wystawieniu","death":"Przy śmierci",
         "end":"Na koniec tury","passive":"Pasywna"}
@dataclass(frozen=True)
class AuctionArchetype:
    id: str
    name: str
    atk: int                 # at completed purchase round R=3
    trigger: str
    family: str
    abilities: tuple[str,str,str]

CATALOG={
"A001":AuctionArchetype("A001","Władca Dusz",3,"death","Obrażenia",(
 "Po śmierci zabija wybraną wrogą jednostkę.",
 "Po śmierci zabija wroga albo przejmuje go, jeśli jest wolne miejsce.",
 "Po śmierci zabija albo przejmuje wroga; można nadać mu łańcuch przejęcia.")),
"A002":AuctionArchetype("A002","Generał Oddziału Natarcia",2,"passive","ATK ±",(
 "Aura: +1 ATAK wszystkim jednostkom na obu planszach.",
 "Wybrany sojusznik zyskuje Podwójny atak i podwójne obrażenia z ataków.",
 "Nowo zagrani sojusznicy zyskują Podwójny atak i podwójne obrażenia.")),
"A003":AuctionArchetype("A003","Matka Kości",2,"death","Regeneracja",(
 "Po śmierci zwraca inną własną kartę podstawową z cmentarza na rękę.",
 "Zwraca kartę na rękę lub wskrzesza ją na planszę z 1 PŻ.",
 "Zwraca albo wskrzesza dwie różne własne karty, jedną z pełnym PŻ.")),
"A004":AuctionArchetype("A004","Regent Krzywych Zwierciadeł",4,"play","Oczyszczanie",(
 "Przy wystawieniu kopiuje inną własną jednostkę na wolne miejsce.",
 "Kopiuje inną dowolną jednostkę (również wrogą).",
 "Kopiuje inną jednostkę wraz z jej bonusami i nadaje kopii Tarczę.")),
"A005":AuctionArchetype("A005","Bankier Widm",1,"play","Pancerz",(
 "Kradnie do 3 monet i tworzy dodatkowe 3 monety.",
 "Kradnie max(3, połowa monet rywala), następnie tworzy 4.",
 "Kradnie wszystkie monety wroga, następnie tworzy 5.")),
"A006":AuctionArchetype("A006","Królowa Zakazanych Słów",2,"play","Ogłuszenie",(
 "Wycisza wskazaną wrogą jednostkę do końca jej tury.",
 "Wycisza do dwóch różnych wrogich jednostek.",
 "Wycisza wszystkie wrogie jednostki.")),
"A007":AuctionArchetype("A007","Strażnik Ostatniego Tchnienia",1,"passive","Tarcza",(
 "Raz na mecz ratuje bohatera przed zgonem, pozostawia 1 PŻ.",
 "Raz na mecz ratuje bohatera, pozostawia 20 PŻ.",
 "Raz na mecz ratuje bohatera z 25 PŻ i ogłusza wrogie jednostki.")),
"A008":AuctionArchetype("A008","Architekt Pustki",3,"play","Oczyszczanie",(
 "Znakuje wroga: wygnanie po jego najbliższej własnej turze.",
 "Wygania wroga i losową kartę z ręki rywala.",
 "Wygania do 3 wrogów i losową kartę z ręki rywala.")),
"A009":AuctionArchetype("A009","Złodziej Wspomnień",2,"play","Oczyszczanie",(
 "Wymienia własną wskazaną kartę na losową z ręki rywala.",
 "Wymienia własną wskazaną kartę na wybraną z ręki rywala.",
 "Zamienia całe ręce; przeciwnik odrzuca do dwóch kart na cmentarz.")),
"A010":AuctionArchetype("A010","Królowa Tysiąca Twarzy",2,"end","Regeneracja",(
 "Na koniec tury: Żołnierz 1/1 albo trwały bonus +1/+1.",
 "Na koniec tury: do 2 Żołnierzy 2/2 z Prowokacją albo +4/+4 z Prowokacją.",
 "Na koniec tury: do 2 kopii najlepszego sojusznika bez zdolności albo jego statystyki.")),
"A011":AuctionArchetype("A011","Jeździec Czarnej Komety",6,"death","Obrażenia",(
 "Po śmierci: 5 obrażeń każdej wrogiej jednostce jednocześnie.",
 "Po śmierci: 5 obrażeń każdemu wrogowi i wrogiemu bohaterowi.",
 "Po śmierci: wszystkie inne jednostki giną w fali i 10 obrażeń bohaterowi.")),
"A012":AuctionArchetype("A012","Tkaczka Drugiego Losu",1,"play","Leczenie",(
 "Wyrównuje PŻ bohaterów do średniej i leczy swojego o 10.",
 "Kopiuje PŻ w wybranym kierunku, potem leczy swojego o 10.",
 "Odbiera 20 PŻ wrogiemu bohaterowi, leczy swojego o 20.")),
}
assert len(CATALOG)==12
assert all(len(x.abilities)==3 for x in CATALOG.values())


def stats(archetype: str, completed_round: int):
    """Current approved formula: ATK+MAX HP = R+8, no hand scaling."""
    atk=CATALOG[archetype].atk
    if completed_round<3:
        raise ValueError("An auction cannot be completed before round 3")
    return atk,completed_round+8-atk


def rarity_from_roll(roll: float):
    if not 0<=roll<1:
        raise ValueError("Rarity roll outside [0,1)")
    return RARITIES[0 if roll<.60 else 1 if roll<.90 else 2]


def evolve(rarity: str, stages: int = 1):
    return RARITIES[min(2,RARITIES.index(rarity)+max(0,stages))]


# The reference dataset is versioned independently from the active v3 catalog.
# Normal play started in 0.9.23 uses this exact v4 source; old v3 saves
# continue to use the original CATALOG above.
import json
import sys
from pathlib import Path
_V4_ROOT=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[2]))
_V4_DATA=json.loads((_V4_ROOT/'data'/'auction'/'KATALOG_AUKCYJNY_12_v4.json').read_text(encoding='utf-8'))
V4_CARDS={card['id']:card for card in _V4_DATA['cards']}
_V4_RARITIES={'podstawowa':'basic','rzadka':'rare','legendarna':'legendary'}
assert len(V4_CARDS)==12 and all(len(c['variants'])==3 for c in V4_CARDS.values())


def v4_variant(archetype: str, rarity: str) -> str:
    return V4_CARDS[archetype]['variants'][_V4_RARITIES[rarity]]


def stats_v4(archetype: str, completed_round: int):
    if (archetype not in V4_CARDS or completed_round<3
            or completed_round%3):
        raise ValueError('Invalid v4 archetype or auction round')
    atk=V4_CARDS[archetype]['stats_at_round_3_example']['atk']
    atk+=(completed_round-3)//3
    hp=completed_round+8-atk
    return atk,hp


# Live v22 extends the v4 catalog; v3/v4 historical games retain their
# original twelve-archetype rule set for deterministic save/replay.
_V22_DATA=json.loads((_V4_ROOT/'data'/'auction'/'KATALOG_AUKCYJNY_17_v22.json').read_text(encoding='utf-8'))
V22_CARDS={card['id']:card for card in _V22_DATA['cards']}
assert len(V22_CARDS)==17 and 'A017' not in V22_CARDS
assert all(len(card['variants'])==3 for card in V22_CARDS.values())
_V22_NEW={
    'A013':('Łamacz Bastionów',4,'play','Obrażenia'),
    'A014':('Kapłan Odwróconej Łaski',3,'passive','Leczenie'),
    'A015':('Wieszczka Zerwanych Zaklęć',2,'passive','Oczyszczanie'),
    'A016':('Kartograf Utraconych Ścieżek',3,'play','Oczyszczanie'),
    'A018':('Licytator Złamanego Paktu',1,'play','Pancerz'),
}
CATALOG_V22=dict(CATALOG)
for _key,(_name,_atk,_trigger,_family) in _V22_NEW.items():
    _texts=V22_CARDS[_key]['variants']
    CATALOG_V22[_key]=AuctionArchetype(
        _key,_name,_atk,_trigger,_family,
        (_texts['basic'],_texts['rare'],_texts['legendary']))
# Unlike legacy v4, v22's Queen has a separately approved balance.
_v22_queen=V22_CARDS['A010']['variants']
_old_queen=CATALOG_V22['A010']
CATALOG_V22['A010']=AuctionArchetype(
    _old_queen.id,_old_queen.name,_old_queen.atk,_old_queen.trigger,
    _old_queen.family,(_v22_queen['basic'],_v22_queen['rare'],
                       _v22_queen['legendary']))
assert len(CATALOG_V22)==17

def catalog_for(mode):
    return CATALOG_V22 if mode=='v22' else CATALOG

def active_auction_cards(mode):
    return V22_CARDS if mode=='v22' else V4_CARDS

def live_variant(mode,archetype,rarity):
    return active_auction_cards(mode)[archetype]['variants'][_V4_RARITIES[rarity]]

def stats_v22(archetype,completed_round):
    if archetype not in V22_CARDS or completed_round<3 or completed_round%3:
        raise ValueError('Invalid v22 archetype or auction round')
    attack=V22_CARDS[archetype]['stats_at_round_3_example']['atk']+(completed_round-3)//3
    return attack, completed_round+8-attack
