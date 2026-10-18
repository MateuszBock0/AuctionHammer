# AuctionHammer 0.9.23 — karty aukcyjne v4 i oddzielne woreczki

## Zakres

Gra pozostaje **lokalna, jednoosobowa przeciwko dotychczasowemu AI**.
Nie wprowadzamy PvP, połączenia online ani zmian w strategii przeciwnika.

Dla **nowych meczów solo** aktywowano 12 archetypów kart aukcyjnych (A001–A012),
łącznie 36 wariantów zdolności zależnych od rzadkości. Podstawowe 70 kart
pozostaje zgodne z balansem v20 i regułami bazowymi Game Master v19.

## Dwa całkowicie odrębne źródła kart

1. **Bank podstawowy**: dokładnie 70 fizycznych kart S; zwykłe dobieranie
   może korzystać tylko z talii i cmentarza podstawowych kart danego gracza.
2. **Woreczek aukcyjny** `auction_bag`: 12 fizycznie niepowtarzalnych archetypów
   A001–A012, żaden nie należy do banku, talii ani cmentarza kart podstawowych.
3. Co trzy pełne rundy, dopóki w aukcyjnym woreczku są co najmniej trzy
   archetypy, losowane są **trzy nowe, różne** oferty. Natychmiast opuszczają
   woreczek dostępnych archetypów, niezależnie od przebiegu licytacji.
4. **Dwie kupione karty** trafiają bezpośrednio do rąk graczy (jedna na gracza).
   Każda podlega standardowemu limitowi jednej karty wystawianej w turze.
5. **Trzecia, niewybrana oferta** trafia do osobnego, stałego woreczka
   `auction_discarded`. Nie jest nawet tworzona jako grywalna instancja
   `Card`, nie wraca na kolejną aukcję i nie trafia do żadnej talii.
6. **Zakupiona karta aukcyjna po utracie/zastąpieniu jednostki** trafia do
   `auction_used` (zużyte aukcyjne), a nie do zwykłego cmentarza.
   Nie wraca do standardowego tasowania i dobierania. To samo dotyczy
   odrzucenia zakupionej karty przez zdolność A009.
7. Po **czwartej aukcji** 12 archetypów jest już rozdysponowanych jako
   8 zakupionych i 4 trwale odrzucone. Nie ma piątej aukcji w tym meczu.
   Gra toczy się dalej na normalnych zasadach.

**To świadomie skończona podaż**, a nie wcześniejsze losowanie trzech
archetypów wielokrotnie z całego katalogu. Ewidencja woreczków jest
zapisywana do savegame i audytu meczu oraz weryfikowana niezmiennikami silnika.

## Jednostki z zerowym atakiem

Obrońca z **0 ATK nadal może być celem ataku**; Prowokacja takiej jednostki
nadal obowiązuje. Atakujący z 0 ATK również może deklarować legalny atak
(sam standardowy atak może zadać 0 obrażeń), o ile jest gotowy, nie jest
ogłuszony i nie wyczerpał limitu. Reguła jest taka sama jak w 0.9.22.
Dodano oddzielne testy silnika i podświetlania celu w interfejsie.

## Integracja zdolności

- A001: zabicie, przejęcie i łańcuch przejęcia
- A002: aura obu plansz, wybrany sojusznik i nowe jednostki z podwójnymi atakami
- A003: powrót karty podstawowej z cmentarza albo wskrzeszenie
- A004: efemeryczne kopie, zabezpieczenie przed rekurencją kopiowania A004
- A005: kradzież i generowanie monet
- A006: wyciszenie jednej, dwóch lub wszystkich wrogich jednostek
- A007: jednorazowe ratowanie bohatera przed śmiercią
- A008: opóźnione wygnanie, natychmiastowe wygnanie jednostek/kart z ręki
- A009: wymiana kart/rąk, odrzucenie **maksymalnie dwóch**, nie całej ręki
- A010: przywołania i trwałe kumulujące się wzmocnienia
- A011: obrażenia pośmiertne oraz masowa jednoczesna fala śmierci
- A012: zmiany PŻ bohaterów, wybrany kierunek kopiowania PŻ

Statystyki ofert przy zakupie w zakończonej rundzie `R=3,6,9,...`:
`ATK(R)=ATK(3)+(R-3)//3`, `MAX_HP(R)=R+8-ATK(R)`. Statystyki są
zamrażane po zakupie. Rzadkość wzrasta co trzy kolejne rundy od kupna.

## Zgodność starych meczów

Zapisane gry `auction_catalog='v3'` zachowują historyczną logikę v3,
niezależnie od zmian dla nowych gier `v4`. Zapewnia to odtwarzalność
poprzednich audytów 0.9.21/0.9.22. Nowe mechaniki i gwarancje oddzielnych
woreczków dotyczą nowych meczów w trybie v4; nie zmieniają wstecz historii.

## Walidacja

`python -m unittest discover -s tests -v`: regresje banku 70x1,
0 ATK, Prowokacji, czterech aukcji, trwałego odrzucenia ofert,
dobierania, zapisu/wczytania, audytu i A009. CI zawiera także
headless render Pygame. Testy regresyjne nie są jednak równoważne
pełnej kalibracji balansu wszystkich kombinacji w długich meczach.

Źródła: `data/auction/KATALOG_AUKCYJNY_12_v4.json`,
`game/core/auction_catalog.py`, `game/core/auction_abilities.py`.
