# AuctionHammer 0.9.22 — korekty interfejsu po audycie ostatniego meczu

Źródło: `AuctionHammer-OSTATNI-MECZ(1).json`, kompletny audyt rozgrywki zapisany z kompilacji `c3c606bc` (0.9.21, GAME_MASTER_v19, aktywny Balance v20), seed `205882526`.

## Wyniki audytu

- 262 komendy, 38 odrzuconych: 25 × `auction_bid` (za mało monet), 7 × `play` (limit wystawienia / plansza 5/5), 6 × `attack` (nielegalny cel).
- Gracz przeciwko AI `normalny`, 19 rund, 6 aukcji, zwycięstwo AI.
- Odrzucone komendy były poprawnymi decyzjami walidatora silnika. Źródło nadmiarowych prób: interfejs nie uniemożliwiał ich wysyłania.
- Kombinacja S91 + S09: 10 ATK S09, 3 obrażenia aktywowane przed atakiem, podwójny atak; w rundach 7 i 8 po 26 obrażeń bohaterowi — razem 52. Regresja odtwarza tę konfigurację w izolowanym Match.

## Zmiany w 0.9.22

1. Licytacja: przycisk PODBIJ +1 nieaktywny przy niewystarczających monetach. LICYTUJ aktywne tylko dla kwot mieszczących się między minimalną ofertą a stanem monet. Klawisz Enter, kliknięcia i przycisk +1 sprawdzane po stronie interfejsu, zanim powstanie komenda Match. Gdy brakuje monet, widoczny komunikat z sugestią PASUJ.
2. Pełna plansza: po wybraniu karty na ręce zaznaczane są tylko własne jednostki możliwe do zastąpienia (niezużyty atak), a próba zagrania na puste pole na planszy 5/5 nie generuje odrzuconej komendy silnika.
3. Atak: niedozwolone cele blokowane po stronie interfejsu; komunikat wyjaśnia Prowokację lub brak gotowości/wykorzystany limit. Podświetlenie legalnych celów pozostało turkusowe.
4. Testy: nowe regresje z zachowaniem istniejących reguł, w tym S91+S09 i czterech ataków w dwóch turach, bez sztucznego obniżania obrażeń.

## Czego NIE zmieniono

- Bez zmian w `game/core/engine.py`, `game/core/auction.py`, danych kart, AI i zasadach Game Master v19.
- Ujemne PŻ w surowym audycie (np. -1) są dopuszczalne dla rozstrzygania śmierci / remisu; widoczny pasek życia już stosował `max(0,min(100,hp))`. Nie zmieniamy wartości w silniku, żeby zachować integralność mechaniki i odtwarzalność starszych audytów.
- Katalog aukcyjny v4 nadal jest roboczą specyfikacją, zdolności aukcyjne nie zostały aktywowane.

## Walidacja

`python -m unittest discover -s tests -v`, render Pygame i publikacja Windows zgodnie z GitHub Actions. Nie należy utożsamiać poprawnego odtwarzania w izolowanych testach z pomiarem bilansu PvP — S91 + S09 wymaga dalszych gier symulacyjnych dla oceny częstotliwości i kontrowania tej kombinacji.
