# AuctionHammer 0.9.26 — kompletne lokalne demo i ostateczne zasady aukcji v4

## Stan po audycie PR #26

PR #26 (merge `63eb6dbd`) dodał wykonanie **A001–A012 w trzech
wariantach rzadkości, tj. 36 opisów efektów**. Obejmuje całość zakresu,
który wcześniej planowano w czterech wersjach 0.9.23–0.9.26:
- kradzież i generowanie monet A005, wyciszanie A006, zmiana PŻ A012,
- aury A002, ratowanie bohatera A007, wspólna fala zgonów A011,
- przejęcie A001, wskrzeszenie A003, wygnanie A008, wymiana rąk A009,
- kopiowanie A004 i przywołania A010.

Karty aukcyjne są wystawiane jak zwykłe jednostki (maksimum **jedna
karta zagrywana z ręki w turze**, maksimum pięć jednostek na planszy).
Nie ma kosztu wystawiania kart. Warianty zdolności pochodzą z
`data/auction/KATALOG_AUKCYJNY_12_v4.json`.

## Poprawione rozdzielenie zasobów: niekupione karty ZOSTAJĄ

Po 3., 6., 9. ... ukończonej rundzie licytuje się pierwszeństwo wyboru.
W każdej aukcji wystawiamy **trzy różne** archetypy z osobnej puli v4.
Każdy gracz kupuje najwyżej jedną z dwóch przydzielanych kart.
**Trzeci, niewybrany archetyp wraca do osobnego woreczka aukcyjnego.**
Może zostać wylosowany ponownie w kolejnej aukcji; nie jest tracony ani
nie trafia do banku 70 kart podstawowych.

- `auction_bag`: pozostałe **niekupione** archetypy, w tym wcześniej
  pokazane, ale niewybrane. Podczas otwartej aukcji 3 oferty są chwilowo
  zarezerwowane poza tym woreczkiem; po rozstrzygnięciu trzecia wraca.
- `auction_discarded`: **wyłącznie dziennik identyfikatorów poprzednich
  niewybranych ofert**, NIE magazyn trwale usuniętych archetypów. Same
  instancje poprzednich ofert nie są kartami i nie trafiają do rozgrywki.
- `auction_awards`: zakupione fizyczne karty, od tej chwili niedostępne
  w woreczku ofert; wchodzą bezpośrednio na rękę kupującego.
- `auction_used`: zakupione karty po zejściu z planszy albo odrzuceniu.
  Te karty **nigdy** nie przechodzą do standardowego cmentarza, talii
  ani losowania podstawowych 70 kart.
- `bank`: wyłącznie 70 bazowych kart `S...`. Rozdawanie, dobieranie,
  mulligan i przetasowania własnego cmentarza nie korzystają z żadnego
  woreczka aukcyjnego.

Dla fizycznie unikalnych 12 archetypów działa zasada zachowania liczby
egzemplarzy: **kupione + bieżące oferty niewybrane + pozostałe w woreczku
= 12**. Nigdy nie można kupić jednego archetypu dwukrotnie. Z każdym
rozstrzygnięciem aukcji liczba pozostałych archetypów maleje o dwa.
Przy obowiązkowych 3 odrębnych ofertach można przeprowadzić maksymalnie
**pięć aukcji**, czyli kupić maksymalnie 10 kart; dwa pozostałe
archetypy dalej pozostają w woreczku, ale przy mniej niż trzech
dostępnych archetypach nie otwiera się kolejnej aukcji.

Ponownie wystawiony archetyp jest **nową ofertą**: jego rzadkość
losujemy niezależnie, a statystyki wyznaczamy dla aktualnej ukończonej
rundy zakupu `R`, zgodnie ze specyfikacją:
`ATK(R) = ATK(3)+(R-3)//3`, `MAXHP(R) = R+8-ATK(R)`.
Po kupnie podstawowe ATK/HP karty są zamrożone; rzadkość zakupionej
karty ewoluuje po trzech kolejnych ukończonych rundach.

## Poprawność rozgrywki i kompatybilność

W 0.9.23 niekupiona trzecia oferta została omyłkowo odrzucona
permanentnie. Zapisane stany v4 ze starszej wersji są migrowane
przez odtworzenie niekupionych archetypów z historii i porównanie ich
z kupionymi i aktualnie oferowanymi. Stare mecze v3 zachowują
wcześniejszą logikę i nie otrzymują nowych zdolności v4.

Jednostka obrońcy z 0 ATK nadal pozostaje legalnym celem ataku, także
z Prowokacją. A009 może odrzucić maksymalnie dwie karty po zamianie
rąk; odrzucona fizyczna karta aukcyjna pozostaje poza obiegiem
kart bazowych.

## Kryteria walidacyjne kompletnego dema

1. Pełny `python -m unittest discover -s tests -v` na Pythonie 3.12
   z `pygame-ce`, w tym testy starszej rozgrywki v3 i wszystkich
   36 wariantów aktywnych kart v4.
2. Losowanie i zakup: każdy z trzech oferowanych archetypów jest różny,
   kupione nie pojawiają się ponownie, trzeci wraca do woreczka.
3. Wielokrotne aukcje: 12-archetypowa pula nigdy nie przecieka do
   70 kart podstawowych; po pięciu aukcjach zostają dwa niekupione.
4. Zapis/wczytanie: po odtworzeniu stan woreczka i audyt są identyczne;
   ponadto stary zapis v4 z 0.9.23 odzyskuje niekupioną ofertę.
5. 0 ATK, Prowokacja, źródła śmierci, zdolności A001–A012,
   powtórka deterministyczna z dotychczasowym AI i render Pygame.
6. Wydanie Windows portable powstaje dopiero po przejściu regresji.

W tej wersji **nie dodano multiplayera, gry online, dodatkowych
trudności ani nowych heurystyk AI**. Dokładne balansowanie wielotysięcy
rozgrywek może stanowić następny, niezależny etap; nie należy
przedstawiać jednostkowych smoke testów jako dowodu balansu.
