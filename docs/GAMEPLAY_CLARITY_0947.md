# AuctionHammer 0.9.47 — Gameplay Clarity

## Zakres

Usprawnienie czytelności podczas tury, wystawiania, ataków, wyświetlania wybranej karty i prezentacji rozstrzygnięć. Bez zmian silnika v23, katalogu kart i aukcji v22, AI, RNG, serializacji i audytów.

## Komponenty

- KARTA 0/1 albo 1/1: licznik zagrania na turę według players[0].played_this_turn.
- GOTOWE DO ATAKU: N: liczba własnych jednostek mających przynajmniej jeden legalny cel z Match.legal_attacks; N nie oznacza liczby trafień.
- Złote ramki: aktualnie legalne wystawienia i dozwolone zastąpienia na planszy 5/5 z Match.can_play. Turkus: atak z Match.legal_attacks. Fiolet: wybór zdolności z pending.choices.
- Panel karty: chip z kontekstową akcją i rozróżnieniem własnej karty na ręce, własnej jednostki oraz jednostki rywala.
- Zakończ turę: dozwolone zawsze we własnej turze, bardziej wyróżnione po wyczerpaniu legalnego zagrania i gotowych jednostek.
- Potwierdzony ticker zdarzeń: wyświetla dosłowny zapis event_journal i etykietę m.in. tarcza/pancerz, obrażenia, leczenie, status, zgon. Działa także przy wyłączonym VFX.

Nie ma prognozowania wyniku walki ani samodzielnego określania legalności poza Match.legal_attacks i Match.can_play. Wcześniejsze mecze są odtwarzane identycznie.

## Weryfikacja

- python -m unittest discover -s tests -v
- tests/test_gameplay_clarity_0947.py: walidacja wyboru 0/1 i 1/1, blokady pending, planszy 5/5, kontekstu własnej karty, rozróżniania blokady i obrażeń, odczytu dziennika również przy wyłączonym VFX, porównania SHA256 snapshot przed/po rysowaniu.
- GitHub Actions: testy i Windows portable launcher QA oraz forensic replay.
- Ręcznie nadal należy sprawdzić czytelność na Windows 1366x768 / 1536x864 / 1920x1080 i różne ustawienia DPI oraz krótkie serie ataków, w tym wieloetapowe zdolności.
