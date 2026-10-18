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
