"""Roboczy katalog aukcyjny v3: 12 archetypów, 36 wariantów.

Source: KATALOG_AUKCYJNY_12_v3(2).md, October 18, 2026.
Do not confuse these tier-specific abilities with the original 3-HP
placeholder. Four interpretation points remain marked provisional.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AuctionArchetype:
    ident: str
    name: str
    atk_at_round3: int
    trigger: str
    basic: str
    rare: str
    legendary: str

CATALOG=(
    AuctionArchetype("A001","Władca Dusz",3,"death",
        "Zabij wskazaną wrogą jednostkę.",
        "Zabij jednostkę albo przejmij ją na stałe (wymaga miejsca).",
        "Zabij, przejmij lub przejmij i nadaj łańcuch przejęcia po śmierci."),
    AuctionArchetype("A002","Generał Oddziału Natarcia",2,"passive",
        "Obie armie, łącznie z Generałem, mają +1 ATK.",
        "Wybrany sojusznik: Podwójny atak i 2× obrażenia zwykłych ataków.",
        "Nowo wystawiani sojusznicy: Podwójny atak i 2× obrażenia."),
    AuctionArchetype("A003","Matka Kości",2,"death",
        "Przenieś inną własną jednostkę podstawową z cmentarza na rękę.",
        "Na rękę lub na prawe wolne pole z 1 PŻ (bez Przy wystawieniu).",
        "Na rękę, na pole z 1 PŻ albo dwie: pełne PŻ na pole i druga na rękę."),
    AuctionArchetype("A004","Regent Krzywych Zwierciadeł",4,"play",
        "Przywołaj efemeryczną kopię innej własnej jednostki na wolne pole.",
        "Przywołaj efemeryczną kopię innej dowolnej jednostki na wolne pole.",
        "Przywołaj kopię dowolnej jednostki z bonusami, statusami i Tarczą."),
    AuctionArchetype("A005","Bankier Widm",1,"play",
        "Ukradnij do 3 monet przeciwnika i wygeneruj dodatkowe 3.",
        "Ukradnij max(3, ceil(połowa salda)) i wygeneruj 4.",
        "Ukradnij wszystkie monety przeciwnika i wygeneruj 5."),
    AuctionArchetype("A006","Królowa Zakazanych Słów",2,"play",
        "Wycisz 1 wroga do końca jego najbliższej własnej tury.",
        "Wycisz do 2 różnych wrogów do końca ich najbliższych tur.",
        "Wycisz wszystkich obecnych wrogów do końca ich najbliższych tur."),
    AuctionArchetype("A007","Strażnik Ostatniego Tchnienia",1,"passive",
        "Raz na mecz: poświęć tę jednostkę, by ocalić bohatera z 1 PŻ.",
        "Raz na mecz: poświęć jednostkę i ocal bohatera z 20 PŻ.",
        "Raz na mecz: ocal bohatera z 25 PŻ i ogłusz obecnych wrogów."),
    AuctionArchetype("A008","Architekt Pustki",3,"play",
        "Naznacz wroga, by wygnać go po jego najbliższej własnej turze.",
        "Wygnaj 1 wroga i losową kartę z ręki przeciwnika.",
        "Wygnaj do 3 wrogów i losową kartę z ręki przeciwnika."),
    AuctionArchetype("A009","Złodziej Wspomnień",2,"play",
        "Wymień własną wskazaną kartę z ręki na losową kartę wroga.",
        "Podejrzyj rękę wroga i wybierz dwie karty do wymiany.",
        "Zamień całe ręce; przeciwnik odrzuca do 2 kart z nowej ręki."),
    AuctionArchetype("A010","Królowa Tysiąca Twarzy",2,"end",
        "Przywołaj Żołnierza 1/1 albo daj Królowej trwałe +1/+1.",
        "Przywołaj do 2 Żołnierzy 2/2 z Prowokacją albo +4/+4 i Prowokację.",
        "Przywołaj do 2 bezsilnych kopii najsilniejszego sojusznika albo jego ATK/PŻ."),
    AuctionArchetype("A011","Jeździec Czarnej Komety",6,"death",
        "Zadaj 5 obrażeń wszystkim wrogim jednostkom jednocześnie.",
        "Zadaj 5 obrażeń wszystkim wrogom i wrogiemu bohaterowi.",
        "Zniszcz wszystkie inne jednostki w jednej fali i zadaj bohaterowi 10."),
    AuctionArchetype("A012","Tkaczka Drugiego Losu",1,"play",
        "Ustaw oba PŻ bohaterów na średnią, następnie ulecz swojego o 10.",
        "Skopiuj PŻ jednego bohatera na drugiego, ulecz swojego o 10.",
        "Odbierz wrogiemu bohaterowi 20 PŻ i ulecz swojego o 20."),
)
BY_ID={a.ident:a for a in CATALOG}
RARITIES=("podstawowa","rzadka","legendarna")
RARITY_CHANCES=(.6,.3,.1)
PROVISIONAL={
    "A002":"Rzadki beneficjent wybrany przy wejściu lub ewolucji; ponowny wybór po zgonie nierozstrzygnięty.",
    "A004":"Kopie uruchamiają Przy wystawieniu; wymagane zabezpieczenie przed pętlą rekurencji.",
    "A010":"Trwałe bonusy kumulują się co własną turę, nie w ręce.",
    "A012":"Rzadka wersja kopiuje HP w wybranym kierunku; NIE zamienia HP."
}

def stats(archetype: AuctionArchetype,completed_round: int):
    """No hidden multiplier by rarity; always ATK + HP = R+8."""
    if completed_round<3 or completed_round%3:
        raise ValueError("Aukcja dopuszczalna tylko po pełnych rundach 3,6,...")
    atk=archetype.atk_at_round3
    hp=completed_round+8-atk
    return atk,hp

def tier_text(ident: str,rarity: str):
    item=BY_ID[ident]
    return dict(zip(RARITIES,(item.basic,item.rare,item.legendary)))[rarity]
